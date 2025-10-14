"""
Unit tests for LiteratureAgent.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from biomerkin.agents.literature_agent import LiteratureAgent, PubMedClient, BedrockClient
from biomerkin.models.literature import Article, StudySummary, LiteratureSummary, LiteratureResults
from biomerkin.models.genomics import GenomicsResults, Gene, Mutation, ProteinSequence
from biomerkin.models.proteomics import ProteomicsResults, FunctionAnnotation, ProteinDomain
from biomerkin.models.base import GenomicLocation, QualityMetrics, MutationType


class TestPubMedClient:
    """Test cases for PubMedClient."""
    
    @pytest.fixture
    def pubmed_client(self):
        """Create PubMedClient instance for testing."""
        return PubMedClient(api_key="test_key", email="test@example.com")
    
    @patch('requests.get')
    def test_search_success(self, mock_get, pubmed_client):
        """Test successful PubMed search."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'esearchresult': {
                'idlist': ['12345', '67890']
            }
        }
        mock_get.return_value = mock_response
        
        # Test search
        pmids = pubmed_client.search("BRCA1", max_results=10)
        
        assert pmids == ['12345', '67890']
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_search_failure(self, mock_get, pubmed_client):
        """Test PubMed search failure."""
        # Mock failed response
        mock_get.side_effect = Exception("Network error")
        
        # Test search
        pmids = pubmed_client.search("BRCA1")
        
        assert pmids == []
    
    @patch('requests.get')
    def test_fetch_articles_success(self, mock_get, pubmed_client):
        """Test successful article fetching."""
        # Mock XML response
        xml_response = '''<?xml version="1.0"?>
        <PubmedArticleSet>
            <PubmedArticle>
                <MedlineCitation>
                    <PMID>12345</PMID>
                    <Article>
                        <ArticleTitle>Test Article Title</ArticleTitle>
                        <AuthorList>
                            <Author>
                                <LastName>Smith</LastName>
                                <ForeName>John</ForeName>
                            </Author>
                        </AuthorList>
                        <Journal>
                            <Title>Test Journal</Title>
                        </Journal>
                        <PubDate>
                            <Year>2023</Year>
                            <Month>Jan</Month>
                        </PubDate>
                        <Abstract>
                            <AbstractText>Test abstract content</AbstractText>
                        </Abstract>
                    </Article>
                </MedlineCitation>
                <PubmedData>
                    <ArticleIdList>
                        <ArticleId IdType="doi">10.1234/test</ArticleId>
                    </ArticleIdList>
                </PubmedData>
            </PubmedArticle>
        </PubmedArticleSet>'''
        
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = xml_response
        mock_get.return_value = mock_response
        
        # Test fetch
        articles = pubmed_client.fetch_articles(['12345'])
        
        assert len(articles) == 1
        article = articles[0]
        assert article.pmid == '12345'
        assert article.title == 'Test Article Title'
        assert article.authors == ['Smith, John']
        assert article.journal == 'Test Journal'
        assert article.publication_date == '2023-Jan'
        assert article.abstract == 'Test abstract content'
        assert article.doi == '10.1234/test'
    
    def test_rate_limiting(self, pubmed_client):
        """Test rate limiting functionality."""
        import time
        
        # Set a high rate limit for testing
        pubmed_client.rate_limit = 1000
        
        start_time = time.time()
        pubmed_client._rate_limit_wait()
        pubmed_client._rate_limit_wait()
        end_time = time.time()
        
        # Should be very fast with high rate limit
        assert end_time - start_time < 0.1


class TestBedrockClient:
    """Test cases for BedrockClient."""
    
    @pytest.fixture
    def bedrock_client(self):
        """Create BedrockClient instance for testing."""
        with patch('boto3.client'):
            return BedrockClient()
    
    @patch('boto3.client')
    def test_initialization_success(self, mock_boto_client):
        """Test successful Bedrock client initialization."""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        bedrock_client = BedrockClient()
        
        assert bedrock_client.client == mock_client
        mock_boto_client.assert_called_once_with('bedrock-runtime', region_name='us-east-1')
    
    @patch('boto3.client')
    def test_initialization_failure(self, mock_boto_client):
        """Test Bedrock client initialization failure."""
        mock_boto_client.side_effect = Exception("AWS error")
        
        bedrock_client = BedrockClient()
        
        assert bedrock_client.client is None
    
    def test_generate_text_success(self, bedrock_client):
        """Test successful text generation."""
        # Mock successful response
        mock_response = {
            'body': Mock()
        }
        mock_response['body'].read.return_value = json.dumps({
            'content': [{'text': 'Generated text response'}]
        }).encode()
        
        bedrock_client.client = Mock()
        bedrock_client.client.invoke_model.return_value = mock_response
        
        # Test text generation
        result = bedrock_client.generate_text("Test prompt")
        
        assert result == 'Generated text response'
        bedrock_client.client.invoke_model.assert_called_once()
    
    def test_generate_text_failure(self, bedrock_client):
        """Test text generation failure."""
        bedrock_client.client = Mock()
        bedrock_client.client.invoke_model.side_effect = Exception("Bedrock error")
        
        # Test text generation
        result = bedrock_client.generate_text("Test prompt")
        
        assert result is None


class TestLiteratureAgent:
    """Test cases for LiteratureAgent."""
    
    @pytest.fixture
    def sample_genomics_results(self):
        """Create sample genomics results for testing."""
        return GenomicsResults(
            genes=[
                Gene(
                    id="gene1",
                    name="BRCA1",
                    location=GenomicLocation(chromosome="17", start_position=43044295, end_position=43125483),
                    function="DNA repair",
                    confidence_score=0.95,
                    synonyms=["BRCA1_HUMAN"]
                ),
                Gene(
                    id="gene2",
                    name="TP53",
                    location=GenomicLocation(chromosome="17", start_position=7661779, end_position=7687550),
                    function="tumor suppressor",
                    confidence_score=0.90
                )
            ],
            mutations=[
                Mutation(
                    position=43045677,
                    reference_base="C",
                    alternate_base="T",
                    mutation_type=MutationType.SNP,
                    clinical_significance="pathogenic",
                    gene_id="gene1"
                )
            ],
            protein_sequences=[
                ProteinSequence(
                    sequence="MDFQVDLTKRSKKQEIEIDVDVSKPDKKGKSKGKDTKGKGKKGKDTKGKGKKGKDTKGKGKK",
                    gene_id="gene1",
                    length=60,
                    molecular_weight=6500.0
                )
            ],
            quality_metrics=QualityMetrics(
                coverage_depth=30.0,
                quality_score=35.0,
                confidence_level=0.95
            )
        )
    
    @pytest.fixture
    def sample_proteomics_results(self):
        """Create sample proteomics results for testing."""
        return ProteomicsResults(
            protein_id="P38398",
            structure_data=None,
            functional_annotations=[
                FunctionAnnotation(
                    function_type="molecular_function",
                    description="DNA binding",
                    confidence_score=0.9,
                    source="UniProt"
                )
            ],
            domains=[
                ProteinDomain(
                    domain_id="PF00533",
                    name="BRCT domain",
                    start_position=1650,
                    end_position=1750,
                    description="BRCA1 C-terminal domain"
                )
            ],
            interactions=[]
        )
    
    @pytest.fixture
    def sample_articles(self):
        """Create sample articles for testing."""
        return [
            Article(
                pmid="12345",
                title="BRCA1 mutations in breast cancer",
                authors=["Smith, J", "Doe, A"],
                journal="Nature Genetics",
                publication_date="2023-01",
                abstract="This study investigates BRCA1 mutations and their role in breast cancer development.",
                doi="10.1038/ng.2023.001",
                relevance_score=0.9
            ),
            Article(
                pmid="67890",
                title="TP53 tumor suppressor function",
                authors=["Johnson, B"],
                journal="Cell",
                publication_date="2022-12",
                abstract="Analysis of TP53 tumor suppressor mechanisms in cancer cells.",
                doi="10.1016/j.cell.2022.001",
                relevance_score=0.8
            )
        ]
    
    @pytest.fixture
    def literature_agent(self):
        """Create LiteratureAgent instance for testing."""
        with patch('biomerkin.agents.literature_agent.get_config') as mock_config:
            # Mock configuration
            mock_config.return_value = Mock(
                api=Mock(
                    pubmed_api_key="test_key",
                    pubmed_email="test@example.com"
                ),
                aws=Mock(
                    region="us-east-1",
                    bedrock_model_id="anthropic.claude-3-sonnet-20240229-v1:0"
                )
            )
            
            with patch('biomerkin.agents.literature_agent.PubMedClient'), \
                 patch('biomerkin.agents.literature_agent.BedrockClient'):
                return LiteratureAgent()
    
    def test_generate_search_terms(self, literature_agent, sample_genomics_results, sample_proteomics_results):
        """Test search term generation."""
        search_terms = literature_agent.generate_search_terms(
            sample_genomics_results, 
            sample_proteomics_results
        )
        
        assert len(search_terms) > 0
        assert any("BRCA1" in term for term in search_terms)
        assert any("TP53" in term for term in search_terms)
        assert any("DNA repair" in term for term in search_terms)
    
    def test_score_relevance(self, literature_agent, sample_articles, sample_genomics_results):
        """Test article relevance scoring."""
        scored_articles = literature_agent.score_relevance(
            sample_articles, 
            sample_genomics_results
        )
        
        assert len(scored_articles) == 2
        assert all(article.relevance_score is not None for article in scored_articles)
        assert all(0 <= article.relevance_score <= 1 for article in scored_articles)
        
        # Both articles should have reasonable relevance scores
        brca1_article = next(article for article in scored_articles if "BRCA1" in article.title)
        tp53_article = next(article for article in scored_articles if "TP53" in article.title)
        
        # Both articles should have positive relevance scores since they match gene names
        assert brca1_article.relevance_score > 0
        assert tp53_article.relevance_score > 0
    
    def test_generate_summary_with_ai(self, literature_agent, sample_articles, sample_genomics_results):
        """Test summary generation with AI."""
        # Mock AI response
        literature_agent.bedrock_client.generate_text = Mock(return_value="""
        KEY FINDINGS:
        - BRCA1 mutations are associated with increased breast cancer risk
        - TP53 plays a crucial role in tumor suppression
        - DNA repair mechanisms are critical for genomic stability
        
        RESEARCH GAPS:
        - Limited functional studies for rare variants
        - Need for larger clinical cohorts
        
        CONFIDENCE ASSESSMENT:
        - Overall confidence: 0.8 (high confidence based on strong evidence)
        """)
        
        summary = literature_agent.generate_summary(
            sample_articles, 
            ["BRCA1", "TP53"], 
            sample_genomics_results
        )
        
        assert isinstance(summary, LiteratureSummary)
        assert len(summary.key_findings) > 0
        assert len(summary.research_gaps) > 0
        assert 0 <= summary.confidence_level <= 1
        assert summary.total_articles_found == 2
        assert summary.articles_analyzed == 2
    
    def test_generate_summary_without_ai(self, literature_agent, sample_articles, sample_genomics_results):
        """Test summary generation without AI (fallback)."""
        # Mock AI failure
        literature_agent.bedrock_client.generate_text = Mock(return_value=None)
        
        summary = literature_agent.generate_summary(
            sample_articles, 
            ["BRCA1", "TP53"], 
            sample_genomics_results
        )
        
        assert isinstance(summary, LiteratureSummary)
        assert len(summary.key_findings) > 0
        assert len(summary.research_gaps) > 0
        assert summary.confidence_level == 0.6  # Default fallback confidence
    
    def test_generate_summary_no_articles(self, literature_agent, sample_genomics_results):
        """Test summary generation with no articles."""
        summary = literature_agent.generate_summary(
            [], 
            ["BRCA1"], 
            sample_genomics_results
        )
        
        assert isinstance(summary, LiteratureSummary)
        assert summary.total_articles_found == 0
        assert summary.articles_analyzed == 0
        assert "No relevant articles found" in summary.key_findings
        assert summary.confidence_level == 0.0
    
    def test_analyze_literature_success(self, literature_agent, sample_genomics_results, sample_proteomics_results, sample_articles):
        """Test successful literature analysis."""
        # Mock PubMed client methods
        literature_agent.pubmed_client.search = Mock(return_value=['12345', '67890'])
        literature_agent.pubmed_client.fetch_articles = Mock(return_value=sample_articles)
        
        # Mock Bedrock client
        literature_agent.bedrock_client.generate_text = Mock(return_value="""
        KEY FINDINGS:
        - Test finding 1
        - Test finding 2
        
        RESEARCH GAPS:
        - Test gap 1
        
        CONFIDENCE ASSESSMENT:
        - Confidence: 0.7
        """)
        
        results = literature_agent.analyze_literature(
            sample_genomics_results, 
            sample_proteomics_results
        )
        
        assert isinstance(results, LiteratureResults)
        assert len(results.articles) > 0
        assert isinstance(results.summary, LiteratureSummary)
        assert 'search_terms_used' in results.search_metadata
    
    def test_analyze_literature_error_handling(self, literature_agent, sample_genomics_results):
        """Test literature analysis error handling."""
        # Mock error in PubMed client
        literature_agent.pubmed_client.search = Mock(side_effect=Exception("API error"))
        
        results = literature_agent.analyze_literature(sample_genomics_results)
        
        assert isinstance(results, LiteratureResults)
        assert len(results.articles) == 0
        assert "Error occurred during literature analysis" in results.summary.key_findings
        assert results.summary.confidence_level == 0.0
        assert 'error' in results.search_metadata
    
    def test_extract_section(self, literature_agent):
        """Test section extraction from AI text."""
        text = """
        Some intro text.
        
        KEY FINDINGS:
        - Finding 1
        - Finding 2
        - Finding 3
        
        RESEARCH GAPS:
        - Gap 1
        - Gap 2
        
        Other text.
        """
        
        findings = literature_agent._extract_section(text, "KEY FINDINGS:")
        gaps = literature_agent._extract_section(text, "RESEARCH GAPS:")
        
        assert findings == ["Finding 1", "Finding 2", "Finding 3"]
        assert gaps == ["Gap 1", "Gap 2"]
    
    def test_extract_confidence_score(self, literature_agent):
        """Test confidence score extraction."""
        # Test with decimal score
        text1 = ["Overall confidence is 0.8 based on evidence"]
        score1 = literature_agent._extract_confidence_score(text1)
        assert score1 == 0.8
        
        # Test with percentage
        text2 = ["Confidence level: 75%"]
        score2 = literature_agent._extract_confidence_score(text2)
        assert score2 == 0.75
        
        # Test with keywords
        text3 = ["High confidence in the results"]
        score3 = literature_agent._extract_confidence_score(text3)
        assert score3 == 0.8
        
        # Test fallback
        text4 = ["No clear confidence indicator"]
        score4 = literature_agent._extract_confidence_score(text4)
        assert score4 == 0.6
    
    def test_create_study_summaries(self, literature_agent, sample_articles):
        """Test study summary creation."""
        summaries = literature_agent._create_study_summaries(sample_articles)
        
        assert len(summaries) == 2
        assert all(isinstance(summary, StudySummary) for summary in summaries)
        assert all(summary.study_type in ['Clinical Trial', 'Meta-analysis', 'Cohort Study', 'Case-Control Study', 'Observational Study'] 
                  for summary in summaries)
        assert all(len(summary.key_findings) > 0 for summary in summaries)


if __name__ == '__main__':
    pytest.main([__file__])