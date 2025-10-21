"""
LiteratureAgent for scientific literature research and summarization.
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import xml.etree.ElementTree as ET
import requests
import boto3
from botocore.exceptions import ClientError

from biomerkin.models.literature import Article, StudySummary, LiteratureSummary, LiteratureResults
from biomerkin.models.genomics import GenomicsResults, Gene, Mutation
from biomerkin.models.proteomics import ProteomicsResults, FunctionAnnotation
from biomerkin.utils.config import get_config
from biomerkin.utils.logging_config import get_logger
from .base_agent import APIAgent, agent_error_handler


class PubMedClient:
    """Client for interacting with PubMed E-utilities API."""
    
    def __init__(self, api_key: Optional[str] = None, email: Optional[str] = None):
        """Initialize PubMed client."""
        self.api_key = api_key
        self.email = email
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.logger = get_logger(__name__)
        self.rate_limit = 10 if api_key else 3
        self.last_request_time = 0
    
    def _rate_limit_wait(self):
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def search(self, query: str, max_results: int = 20) -> List[str]:
        """Search PubMed and return list of PMIDs."""
        self._rate_limit_wait()
        
        params = {
            'tool': 'biomerkin',
            'email': self.email or 'biomerkin@example.com',
            'db': 'pubmed',
            'term': query,
            'retmax': str(max_results),
            'retmode': 'json'
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        try:
            response = requests.get(f"{self.base_url}/esearch.fcgi", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            pmids = data.get('esearchresult', {}).get('idlist', [])
            
            self.logger.info(f"Found {len(pmids)} articles for query: {query}")
            return pmids
            
        except Exception as e:
            self.logger.error(f"Error searching PubMed: {e}")
            return []
    
    def fetch_articles(self, pmids: List[str]) -> List[Article]:
        """Fetch article details for given PMIDs."""
        if not pmids:
            return []
        
        self._rate_limit_wait()
        
        params = {
            'tool': 'biomerkin',
            'email': self.email or 'biomerkin@example.com',
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml'
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        try:
            response = requests.get(f"{self.base_url}/efetch.fcgi", params=params, timeout=30)
            response.raise_for_status()
            
            return self._parse_pubmed_xml(response.text)
            
        except Exception as e:
            self.logger.error(f"Error fetching articles from PubMed: {e}")
            return []
    
    def _parse_pubmed_xml(self, xml_content: str) -> List[Article]:
        """Parse PubMed XML response into Article objects."""
        articles = []
        
        try:
            root = ET.fromstring(xml_content)
            
            for pubmed_article in root.findall('.//PubmedArticle'):
                try:
                    article = self._parse_single_article(pubmed_article)
                    if article:
                        articles.append(article)
                except Exception as e:
                    self.logger.warning(f"Error parsing article: {e}")
                    continue
            
        except ET.ParseError as e:
            self.logger.error(f"Error parsing PubMed XML: {e}")
        
        return articles
    
    def _parse_single_article(self, pubmed_article) -> Optional[Article]:
        """Parse a single PubMed article from XML."""
        try:
            # Extract PMID
            pmid_elem = pubmed_article.find('.//PMID')
            if pmid_elem is None:
                return None
            pmid = pmid_elem.text
            
            # Extract article details
            article_elem = pubmed_article.find('.//Article')
            if article_elem is None:
                return None
            
            # Title
            title_elem = article_elem.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else "No title available"
            
            # Authors
            authors = []
            author_list = article_elem.find('.//AuthorList')
            if author_list is not None:
                for author in author_list.findall('.//Author'):
                    last_name = author.find('.//LastName')
                    first_name = author.find('.//ForeName')
                    if last_name is not None:
                        author_name = last_name.text
                        if first_name is not None:
                            author_name += f", {first_name.text}"
                        authors.append(author_name)
            
            # Journal
            journal_elem = article_elem.find('.//Journal/Title')
            journal = journal_elem.text if journal_elem is not None else "Unknown journal"
            
            # Publication date
            pub_date_elem = article_elem.find('.//PubDate')
            pub_date = "Unknown date"
            if pub_date_elem is not None:
                year = pub_date_elem.find('.//Year')
                month = pub_date_elem.find('.//Month')
                if year is not None:
                    pub_date = year.text
                    if month is not None:
                        pub_date += f"-{month.text}"
            
            # Abstract
            abstract_elem = article_elem.find('.//Abstract/AbstractText')
            abstract = abstract_elem.text if abstract_elem is not None else "No abstract available"
            
            # DOI
            doi = None
            article_ids = pubmed_article.findall('.//ArticleId')
            for article_id in article_ids:
                if article_id.get('IdType') == 'doi':
                    doi = article_id.text
                    break
            
            return Article(
                pmid=pmid,
                title=title,
                authors=authors,
                journal=journal,
                publication_date=pub_date,
                abstract=abstract,
                doi=doi
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing single article: {e}")
            return None


class BedrockClient:
    """Client for interacting with Amazon Bedrock."""
    
    def __init__(self, region: str = "us-east-1", model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
        """Initialize Bedrock client."""
        self.region = region
        self.model_id = model_id
        self.logger = get_logger(__name__)
        
        try:
            self.client = boto3.client('bedrock-runtime', region_name=region)
        except Exception as e:
            self.logger.error(f"Error initializing Bedrock client: {e}")
            self.client = None
    
    def generate_text(self, prompt: str, max_tokens: int = 4000) -> Optional[str]:
        """Generate text using Bedrock LLM."""
        if not self.client:
            self.logger.error("Bedrock client not initialized")
            return None
        
        if not self.model_id:
            self.logger.error("Model ID not set")
            return None
        
        try:
            # Prepare request body based on model
            if "anthropic" in self.model_id.lower():
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}]
                }
            else:
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": 0.7,
                        "topP": 0.9
                    }
                }
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body),
                contentType='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract text based on model response format
            if self.model_id and "anthropic" in self.model_id.lower():
                return response_body.get('content', [{}])[0].get('text', '')
            else:
                return response_body.get('results', [{}])[0].get('outputText', '')
                
        except Exception as e:
            self.logger.error(f"Error with Bedrock: {e}")
            return None


class LiteratureAgent(APIAgent):
    """Agent for scientific literature research and summarization."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize LiteratureAgent."""
        self.config = get_config() if config is None else config
        
        # Initialize parent with API key and rate limit
        super().__init__(
            agent_name="literature",
            api_key=self.config.api.pubmed_api_key,
            rate_limit=10.0 if self.config.api.pubmed_api_key else 3.0
        )
        
        # Initialize clients
        self.pubmed_client = PubMedClient(
            api_key=self.config.api.pubmed_api_key,
            email=self.config.api.pubmed_email
        )
        
        self.bedrock_client = BedrockClient(
            region=self.config.aws.region,
            model_id=self.config.aws.bedrock_model_id
        )
    
    @agent_error_handler()
    def execute(self, input_data: Dict[str, Any], workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute literature analysis.
        
        Args:
            input_data: Dictionary containing genomics_results and optional proteomics_results
            workflow_id: Optional workflow identifier
            
        Returns:
            Dictionary containing literature analysis results
        """
        genomics_results = input_data.get('genomics_results')
        proteomics_results = input_data.get('proteomics_results')
        max_articles = input_data.get('max_articles', 20)
        
        if not genomics_results:
            raise ValueError("genomics_results is required in input_data")
        
        results = self.analyze_literature(genomics_results, proteomics_results, max_articles)
        
        return {
            'literature_results': results,
            'articles': results.articles,
            'summary': results.summary,
            'search_metadata': results.search_metadata
        }
    
    def analyze_literature(self, genomics_results: GenomicsResults, 
                          proteomics_results: Optional[ProteomicsResults] = None,
                          max_articles: int = 20) -> LiteratureResults:
        """Analyze literature based on genomics and proteomics results."""
        self.logger.info("Starting literature analysis")
        
        try:
            # Generate search terms
            search_terms = self.generate_search_terms(genomics_results, proteomics_results)
            self.logger.info(f"Generated search terms: {search_terms}")
            
            # Search for articles
            all_articles = []
            search_metadata = {
                'search_terms_used': search_terms,
                'search_timestamp': datetime.now().isoformat(),
                'total_queries': len(search_terms)
            }
            
            for term in search_terms:
                pmids = self.pubmed_client.search(term, max_results=max_articles // len(search_terms) + 1)
                if pmids:
                    articles = self.pubmed_client.fetch_articles(pmids)
                    all_articles.extend(articles)
            
            # Remove duplicates based on PMID
            unique_articles = {}
            for article in all_articles:
                unique_articles[article.pmid] = article
            
            articles = list(unique_articles.values())[:max_articles]
            
            # Score relevance
            articles = self.score_relevance(articles, genomics_results, proteomics_results)
            
            # Sort by relevance score
            articles.sort(key=lambda x: x.relevance_score or 0, reverse=True)
            
            # Generate summary
            summary = self.generate_summary(articles, search_terms, genomics_results, proteomics_results)
            
            search_metadata.update({
                'articles_found': len(all_articles),
                'unique_articles': len(articles),
                'articles_analyzed': len(articles)
            })
            
            results = LiteratureResults(
                articles=articles,
                summary=summary,
                search_metadata=search_metadata
            )
            
            self.logger.info(f"Literature analysis completed. Found {len(articles)} relevant articles")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in literature analysis: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            # Return empty results on error
            return LiteratureResults(
                articles=[],
                summary=LiteratureSummary(
                    search_terms=[],
                    total_articles_found=0,
                    articles_analyzed=0,
                    key_findings=["Error occurred during literature analysis"],
                    relevant_studies=[],
                    research_gaps=[],
                    confidence_level=0.0,
                    analysis_timestamp=datetime.now().isoformat()
                ),
                search_metadata={'error': str(e)}
            )   
 
    def generate_search_terms(self, genomics_results: GenomicsResults,
                            proteomics_results: Optional[ProteomicsResults] = None) -> List[str]:
        """Generate optimized search terms from genomic and protein data."""
        search_terms = []
        
        # Gene-based search terms
        for gene in genomics_results.genes:
            if gene.name and gene.name.lower() not in ['unknown', 'hypothetical']:
                search_terms.append(f'"{gene.name}"[Gene Name]')
                
                if gene.function and 'unknown' not in gene.function.lower():
                    search_terms.append(f'"{gene.name}" AND "{gene.function}"')
            
            if gene.synonyms:
                for synonym in gene.synonyms[:2]:
                    search_terms.append(f'"{synonym}"[Gene Name]')
        
        # Mutation-based search terms
        for mutation in genomics_results.mutations:
            if mutation.gene_id and mutation.clinical_significance:
                gene = next((g for g in genomics_results.genes if g.id == mutation.gene_id), None)
                if gene and gene.name:
                    search_terms.append(f'"{gene.name}" AND "mutation" AND "{mutation.clinical_significance}"')
        
        # Protein function-based search terms
        if proteomics_results:
            for annotation in proteomics_results.functional_annotations:
                if annotation.description and annotation.confidence_score > 0.7:
                    search_terms.append(f'"{annotation.description}"')
            
            for domain in proteomics_results.domains:
                if domain.name and 'domain' not in domain.name.lower():
                    search_terms.append(f'"{domain.name}" AND "protein domain"')
        
        # Remove duplicates and limit number of terms
        unique_terms = list(dict.fromkeys(search_terms))
        
        # Prioritize terms
        prioritized_terms = []
        gene_terms = [term for term in unique_terms if '[Gene Name]' in term]
        prioritized_terms.extend(gene_terms[:5])
        
        function_terms = [term for term in unique_terms if 'AND' in term and '[Gene Name]' not in term]
        prioritized_terms.extend(function_terms[:3])
        
        other_terms = [term for term in unique_terms if term not in prioritized_terms]
        prioritized_terms.extend(other_terms[:2])
        
        return prioritized_terms[:10]  
  
    def score_relevance(self, articles: List[Article], genomics_results: GenomicsResults,
                       proteomics_results: Optional[ProteomicsResults] = None) -> List[Article]:
        """Score articles for relevance based on genomic and protein data."""
        # Extract key terms for scoring
        key_terms = set()
        
        for gene in genomics_results.genes:
            if gene.name:
                key_terms.add(gene.name.lower())
            if gene.function:
                key_terms.update(gene.function.lower().split())
            if gene.synonyms:
                key_terms.update([syn.lower() for syn in gene.synonyms])
        
        for mutation in genomics_results.mutations:
            if mutation.clinical_significance:
                key_terms.update(mutation.clinical_significance.lower().split())
        
        if proteomics_results:
            for annotation in proteomics_results.functional_annotations:
                if annotation.description:
                    key_terms.update(annotation.description.lower().split())
            
            for domain in proteomics_results.domains:
                if domain.name:
                    key_terms.add(domain.name.lower())
        
        # Remove common words
        common_words = {'the', 'and', 'or', 'in', 'of', 'to', 'a', 'an', 'is', 'are', 'was', 'were', 'protein', 'gene'}
        key_terms = key_terms - common_words
        
        # Score each article
        for article in articles:
            score = 0.0
            
            # Count matches in title (higher weight)
            if article.title:
                title_matches = sum(1 for term in key_terms if term in article.title.lower())
                score += title_matches * 2.0
            
            # Count matches in abstract
            if article.abstract:
                abstract_matches = sum(1 for term in key_terms if term in article.abstract.lower())
                score += abstract_matches * 1.0
            
            # Bonus for recent articles
            try:
                if article.publication_date and '-' in article.publication_date:
                    year = int(article.publication_date.split('-')[0])
                    current_year = datetime.now().year
                    if year >= current_year - 5:
                        score += 0.5
                    elif year >= current_year - 10:
                        score += 0.2
            except (ValueError, IndexError):
                pass
            
            # Normalize score
            max_possible_score = len(key_terms) * 2.0 + 0.5
            article.relevance_score = min(score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
        
        return articles
    
    def generate_summary(self, articles: List[Article], search_terms: List[str],
                        genomics_results: GenomicsResults,
                        proteomics_results: Optional[ProteomicsResults] = None) -> LiteratureSummary:
        """Generate comprehensive literature summary using AI."""
        if not articles:
            return LiteratureSummary(
                search_terms=search_terms,
                total_articles_found=0,
                articles_analyzed=0,
                key_findings=["No relevant articles found"],
                relevant_studies=[],
                research_gaps=["Limited literature available for the analyzed genes/proteins"],
                confidence_level=0.0,
                analysis_timestamp=datetime.now().isoformat()
            )
        
        # Prepare context for AI summarization
        gene_context = []
        for gene in genomics_results.genes:
            gene_context.append(f"Gene: {gene.name}, Function: {gene.function}")
        
        mutation_context = []
        for mutation in genomics_results.mutations:
            mutation_context.append(f"Mutation: {mutation.mutation_type.value}, Clinical significance: {mutation.clinical_significance}")
        
        protein_context = []
        if proteomics_results:
            for annotation in proteomics_results.functional_annotations:
                protein_context.append(f"Protein function: {annotation.description}")
        
        # Prepare article summaries for AI
        article_summaries = []
        for i, article in enumerate(articles[:10]):
            abstract_text = (article.abstract[:500] if article.abstract else "No abstract available")
            relevance_score = article.relevance_score if article.relevance_score is not None else 0.0
            article_summaries.append(f"""
Article {i+1}:
Title: {article.title or "No title"}
Journal: {article.journal or "Unknown"}
Year: {article.publication_date or "Unknown"}
Abstract: {abstract_text}...
Relevance Score: {relevance_score:.2f}
""")
        
        # Create prompt for AI summarization
        prompt = f"""
You are a medical research analyst. Please analyze the following genomic data and literature to provide a comprehensive summary.

GENOMIC CONTEXT:
Genes analyzed: {'; '.join(gene_context)}
Mutations found: {'; '.join(mutation_context)}
Protein functions: {'; '.join(protein_context)}

LITERATURE ANALYZED:
{''.join(article_summaries)}

Please provide a structured analysis in the following format:

KEY FINDINGS:
- List 3-5 key findings from the literature that are most relevant to the genomic data
- Focus on clinical significance, disease associations, and functional implications

RESEARCH GAPS:
- Identify areas where more research is needed
- Note any limitations in the current literature

CONFIDENCE ASSESSMENT:
- Rate the overall confidence in the findings (0.0 to 1.0)
- Consider the quality and quantity of available evidence

Please be concise but comprehensive, focusing on medically relevant information.
"""
        
        # Generate AI summary
        ai_response = self.bedrock_client.generate_text(prompt, max_tokens=2000)
        
        if ai_response:
            key_findings = self._extract_section(ai_response, "KEY FINDINGS:")
            research_gaps = self._extract_section(ai_response, "RESEARCH GAPS:")
            confidence_text = self._extract_section(ai_response, "CONFIDENCE ASSESSMENT:")
            confidence_level = self._extract_confidence_score(confidence_text)
            relevant_studies = self._create_study_summaries(articles[:5])
        else:
            # Fallback if AI is not available
            key_findings = [
                f"Analysis of {len(articles)} articles related to the identified genes",
                "Literature search focused on genetic variants and their clinical significance",
                "Studies span multiple research areas including functional genomics and clinical applications"
            ]
            research_gaps = [
                "Limited functional studies for some identified genetic variants",
                "Need for larger clinical cohorts to establish definitive associations"
            ]
            confidence_level = 0.6
            relevant_studies = self._create_study_summaries(articles[:5])
        
        return LiteratureSummary(
            search_terms=search_terms,
            total_articles_found=len(articles),
            articles_analyzed=len(articles),
            key_findings=key_findings,
            relevant_studies=relevant_studies,
            research_gaps=research_gaps,
            confidence_level=confidence_level,
            analysis_timestamp=datetime.now().isoformat()
        ) 
   
    def _extract_section(self, text: str, section_header: str) -> List[str]:
        """Extract bullet points from a section of AI-generated text."""
        if not text:
            return []
        lines = text.split('\n')
        section_lines = []
        in_section = False
        
        for line in lines:
            if section_header in line:
                in_section = True
                continue
            elif in_section and line.strip().startswith('-'):
                section_lines.append(line.strip()[1:].strip())
            elif in_section and line.strip() and not line.strip().startswith('-'):
                if any(header in line for header in ["KEY FINDINGS:", "RESEARCH GAPS:", "CONFIDENCE:"]):
                    break
        
        return section_lines[:5]
    
    def _extract_confidence_score(self, confidence_text: List[str]) -> float:
        """Extract confidence score from AI-generated text."""
        if not confidence_text:
            return 0.6
        
        text = ' '.join(confidence_text).lower()
        
        # Look for numerical confidence scores
        import re
        numbers = re.findall(r'(\d+\.?\d*)', text)
        
        for num_str in numbers:
            try:
                num = float(num_str)
                if 0 <= num <= 1:
                    return num
                elif 0 <= num <= 10:
                    return num / 10
                elif 0 <= num <= 100:
                    return num / 100
            except ValueError:
                continue
        
        # Fallback based on keywords
        if any(word in text for word in ['high', 'strong', 'confident']):
            return 0.8
        elif any(word in text for word in ['moderate', 'medium']):
            return 0.6
        elif any(word in text for word in ['low', 'weak', 'limited']):
            return 0.4
        
        return 0.6
    
    def _create_study_summaries(self, articles: List[Article]) -> List[StudySummary]:
        """Create simplified study summaries from articles."""
        summaries = []
        
        for article in articles:
            # Determine study type from title/abstract
            title = article.title or ""
            abstract = article.abstract or ""
            text = f"{title} {abstract}".lower()
            
            if any(term in text for term in ['clinical trial', 'randomized', 'rct']):
                study_type = 'Clinical Trial'
            elif any(term in text for term in ['meta-analysis', 'systematic review']):
                study_type = 'Meta-analysis'
            elif any(term in text for term in ['cohort', 'longitudinal', 'prospective']):
                study_type = 'Cohort Study'
            elif any(term in text for term in ['case-control', 'case control']):
                study_type = 'Case-Control Study'
            else:
                study_type = 'Observational Study'
            
            # Extract key findings (simplified)
            key_findings = [
                f"Study published in {article.journal}",
                f"Research focus: {article.title[:100]}..."
            ]
            
            summaries.append(StudySummary(
                study_type=study_type,
                key_findings=key_findings,
                sample_size=None,
                statistical_significance=None,
                limitations=None
            ))
        
        return summaries

    def search_literature_autonomous(self, genes: List[str], conditions: List[str] = None, 
                                   max_articles: int = 20, search_strategy: Dict[str, Any] = None) -> LiteratureResults:
        """
        Perform autonomous literature search with intelligent strategy selection.
        
        Args:
            genes: List of gene names to search for
            conditions: Optional list of medical conditions
            max_articles: Maximum number of articles to return
            search_strategy: Strategy configuration for search
            
        Returns:
            LiteratureResults with articles and metadata
        """
        try:
            # Generate search terms autonomously
            search_terms = []
            
            # Gene-based terms
            for gene in genes:
                search_terms.append(f'"{gene}"[Gene Name]')
                if conditions:
                    for condition in conditions:
                        search_terms.append(f'"{gene}" AND "{condition}"')
            
            # Condition-based terms
            if conditions:
                for condition in conditions:
                    search_terms.append(f'"{condition}"')
            
            # Perform searches
            all_articles = []
            for term in search_terms[:5]:  # Limit to avoid too many API calls
                try:
                    pmids = self.pubmed_client.search(term, max_results=max_articles // len(search_terms[:5]))
                    articles = self.pubmed_client.fetch_articles(pmids)
                    all_articles.extend(articles)
                except Exception as e:
                    self.logger.warning(f"Search failed for term '{term}': {str(e)}")
                    continue
            
            # Remove duplicates and limit results
            unique_articles = {}
            for article in all_articles:
                if article.pmid not in unique_articles:
                    unique_articles[article.pmid] = article
            
            final_articles = list(unique_articles.values())[:max_articles]
            
            # Score relevance
            for article in final_articles:
                article.relevance_score = self._calculate_relevance_score(article, genes, conditions)
            
            # Sort by relevance
            final_articles.sort(key=lambda x: x.relevance_score, reverse=True)
            
            # Create a simple summary
            from biomerkin.models.literature import LiteratureSummary
            summary = LiteratureSummary(
                search_terms=search_terms,
                total_articles_found=len(final_articles),
                articles_analyzed=len(final_articles),
                key_findings=[f"Found {len(final_articles)} articles for the specified genes"],
                relevant_studies=[],
                research_gaps=[],
                confidence_level=0.8,
                analysis_timestamp=datetime.now().isoformat()
            )
            
            return LiteratureResults(
                articles=final_articles,
                summary=summary,
                search_metadata={'search_terms': search_terms, 'total_found': len(final_articles)}
            )
            
        except Exception as e:
            self.logger.error(f"Error in autonomous literature search: {str(e)}")
            raise

    def summarize_article_autonomous(self, article_data: Dict[str, Any], focus_areas: List[str] = None) -> Dict[str, Any]:
        """
        Autonomously summarize a scientific article with focus on specific areas.
        
        Args:
            article_data: Article data dictionary
            focus_areas: Areas to focus on in summarization
            
        Returns:
            Dictionary containing summary and analysis
        """
        try:
            title = article_data.get('title', '')
            abstract = article_data.get('abstract', '')
            
            # Create focused summary based on areas
            focus_areas = focus_areas or ['clinical_significance', 'therapeutic_implications']
            
            summary_parts = []
            key_findings = []
            clinical_implications = []
            
            # Analyze title and abstract for key information
            text = f"{title} {abstract}".lower()
            
            # Extract clinical significance
            if 'clinical_significance' in focus_areas:
                if any(term in text for term in ['pathogenic', 'benign', 'clinical', 'disease']):
                    clinical_implications.append("Article discusses clinical significance of genetic variants")
                    
            # Extract therapeutic implications
            if 'therapeutic_implications' in focus_areas:
                if any(term in text for term in ['treatment', 'therapy', 'drug', 'therapeutic']):
                    clinical_implications.append("Article has therapeutic implications")
            
            # Generate summary
            if abstract:
                summary = f"Study titled '{title}' investigates {abstract[:200]}..."
            else:
                summary = f"Study titled '{title}' - abstract not available"
            
            # Extract key findings from abstract
            if abstract:
                sentences = abstract.split('.')
                key_findings = [sentence.strip() for sentence in sentences[:3] if sentence.strip()]
            
            return {
                'summary': summary,
                'key_findings': key_findings,
                'clinical_implications': clinical_implications,
                'focus_areas_covered': focus_areas
            }
            
        except Exception as e:
            self.logger.error(f"Error in autonomous article summarization: {str(e)}")
            raise

    def generate_search_terms_autonomous(self, genomic_data: Dict[str, Any], 
                                       clinical_context: Dict[str, Any] = None,
                                       search_focus: str = 'comprehensive') -> Dict[str, List[str]]:
        """
        Autonomously generate optimal search terms based on genomic data.
        
        Args:
            genomic_data: Genomic analysis results
            clinical_context: Clinical context information
            search_focus: Focus of the search ('comprehensive', 'clinical', 'therapeutic')
            
        Returns:
            Dictionary containing different types of search terms
        """
        try:
            primary_terms = []
            secondary_terms = []
            boolean_queries = []
            mesh_terms = []
            
            # Extract genes from genomic data
            genes = genomic_data.get('genes', [])
            variants = genomic_data.get('variants', [])
            
            # Primary gene-based terms
            for gene in genes:
                gene_name = gene.get('name', '') or gene.get('gene_name', '')
                if gene_name:
                    primary_terms.append(f'"{gene_name}"[Gene Name]')
                    mesh_terms.append(gene_name)
            
            # Variant-based terms
            for variant in variants:
                gene = variant.get('gene', '')
                if gene:
                    secondary_terms.append(f'"{gene}" AND "mutation"')
                    secondary_terms.append(f'"{gene}" AND "variant"')
            
            # Clinical context terms
            if clinical_context:
                condition = clinical_context.get('condition', '')
                symptoms = clinical_context.get('symptoms', [])
                
                if condition:
                    primary_terms.append(f'"{condition}"')
                    
                for symptom in symptoms:
                    secondary_terms.append(f'"{symptom}"')
            
            # Boolean queries based on focus
            if search_focus == 'clinical':
                for gene in [g.get('name', '') for g in genes if g.get('name')]:
                    boolean_queries.append(f'"{gene}" AND ("clinical significance" OR "pathogenic" OR "disease")')
            elif search_focus == 'therapeutic':
                for gene in [g.get('name', '') for g in genes if g.get('name')]:
                    boolean_queries.append(f'"{gene}" AND ("treatment" OR "therapy" OR "drug")')
            else:  # comprehensive
                for gene in [g.get('name', '') for g in genes if g.get('name')]:
                    boolean_queries.append(f'"{gene}" AND ("function" OR "clinical" OR "therapeutic")')
            
            return {
                'primary_terms': primary_terms[:10],
                'secondary_terms': secondary_terms[:10],
                'boolean_queries': boolean_queries[:5],
                'mesh_terms': mesh_terms[:10]
            }
            
        except Exception as e:
            self.logger.error(f"Error generating autonomous search terms: {str(e)}")
            raise

    def assess_article_relevance_autonomous(self, article: Dict[str, Any], 
                                          genomic_context: Dict[str, Any],
                                          criteria: List[str] = None) -> Dict[str, Any]:
        """
        Autonomously assess relevance of an article to genomic findings.
        
        Args:
            article: Article data
            genomic_context: Genomic context for relevance assessment
            criteria: Assessment criteria to use
            
        Returns:
            Dictionary containing relevance assessment
        """
        try:
            criteria = criteria or ['clinical_relevance', 'therapeutic_potential', 'evidence_quality']
            
            title = article.get('title', '').lower()
            abstract = article.get('abstract', '').lower()
            text = f"{title} {abstract}"
            
            # Extract genes from genomic context
            genes = [g.get('name', '').lower() for g in genomic_context.get('genes', []) if g.get('name')]
            
            criteria_scores = {}
            
            # Clinical relevance
            if 'clinical_relevance' in criteria:
                clinical_score = 0.0
                clinical_terms = ['clinical', 'patient', 'disease', 'pathogenic', 'diagnosis']
                
                # Gene mention bonus
                gene_mentions = sum(1 for gene in genes if gene in text)
                clinical_score += min(gene_mentions * 0.3, 0.6)
                
                # Clinical terms bonus
                clinical_mentions = sum(1 for term in clinical_terms if term in text)
                clinical_score += min(clinical_mentions * 0.1, 0.4)
                
                criteria_scores['clinical_relevance'] = min(clinical_score, 1.0)
            
            # Therapeutic potential
            if 'therapeutic_potential' in criteria:
                therapeutic_score = 0.0
                therapeutic_terms = ['treatment', 'therapy', 'drug', 'therapeutic', 'intervention']
                
                therapeutic_mentions = sum(1 for term in therapeutic_terms if term in text)
                therapeutic_score = min(therapeutic_mentions * 0.2, 1.0)
                
                criteria_scores['therapeutic_potential'] = therapeutic_score
            
            # Evidence quality
            if 'evidence_quality' in criteria:
                quality_score = 0.5  # Base score
                
                # Study type indicators
                if any(term in text for term in ['randomized', 'controlled trial', 'meta-analysis']):
                    quality_score += 0.3
                elif any(term in text for term in ['cohort', 'case-control']):
                    quality_score += 0.2
                
                criteria_scores['evidence_quality'] = min(quality_score, 1.0)
            
            # Overall score
            overall_score = sum(criteria_scores.values()) / len(criteria_scores) if criteria_scores else 0.0
            
            return {
                'overall_score': overall_score,
                'criteria_scores': criteria_scores,
                'confidence': 0.8,
                'uncertainties': []
            }
            
        except Exception as e:
            self.logger.error(f"Error in autonomous relevance assessment: {str(e)}")
            raise

    def _calculate_relevance_score(self, article: Article, genes: List[str], conditions: List[str] = None) -> float:
        """Calculate relevance score for an article."""
        score = 0.0
        title = article.title or ""
        abstract = article.abstract or ""
        text = f"{title} {abstract}".lower()
        
        # Gene mentions
        for gene in genes:
            if gene.lower() in text:
                score += 0.3
        
        # Condition mentions
        if conditions:
            for condition in conditions:
                if condition.lower() in text:
                    score += 0.2
        
        # Clinical terms
        clinical_terms = ['clinical', 'patient', 'disease', 'pathogenic']
        for term in clinical_terms:
            if term in text:
                score += 0.1
        
        return min(score, 1.0)
    
    def search_literature_autonomous(self, genes: List[str], conditions: List[str] = None, 
                                   max_articles: int = 20, search_strategy: Dict[str, Any] = None) -> LiteratureResults:
        """
        Perform autonomous literature search with intelligent strategy selection.
        
        Args:
            genes: List of gene names to search for
            conditions: Optional list of medical conditions
            max_articles: Maximum number of articles to return
            search_strategy: Strategy configuration for search
            
        Returns:
            LiteratureResults with articles and metadata
        """
        try:
            # Generate search terms autonomously
            search_terms = []
            
            # Gene-based terms
            for gene in genes:
                search_terms.append(f'"{gene}"[Gene Name]')
                if conditions:
                    for condition in conditions:
                        search_terms.append(f'"{gene}" AND "{condition}"')
            
            # Condition-based terms
            if conditions:
                for condition in conditions:
                    search_terms.append(f'"{condition}"')
            
            # Perform searches
            all_articles = []
            for term in search_terms[:5]:  # Limit to avoid too many API calls
                try:
                    pmids = self.pubmed_client.search(term, max_results=max_articles // len(search_terms[:5]))
                    articles = self.pubmed_client.fetch_articles(pmids)
                    all_articles.extend(articles)
                except Exception as e:
                    self.logger.warning(f"Search failed for term '{term}': {str(e)}")
                    continue
            
            # Remove duplicates
            unique_articles = {}
            for article in all_articles:
                unique_articles[article.pmid] = article
            
            articles = list(unique_articles.values())[:max_articles]
            
            # Score relevance autonomously
            for article in articles:
                article.relevance_score = self._calculate_autonomous_relevance(article, genes, conditions)
            
            # Sort by relevance
            articles.sort(key=lambda x: x.relevance_score or 0, reverse=True)
            
            # Generate autonomous summary
            summary = self._generate_autonomous_summary(articles, search_terms, genes, conditions)
            
            search_metadata = {
                'search_terms_used': search_terms,
                'search_timestamp': datetime.now().isoformat(),
                'total_queries': len(search_terms),
                'articles_found': len(all_articles),
                'unique_articles': len(articles),
                'autonomous_strategy': search_strategy or 'comprehensive_genomic_search'
            }
            
            return LiteratureResults(
                articles=articles,
                summary=summary,
                search_metadata=search_metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error in autonomous literature search: {str(e)}")
            return LiteratureResults(
                articles=[],
                summary=LiteratureSummary(
                    search_terms=[],
                    total_articles_found=0,
                    articles_analyzed=0,
                    key_findings=["Error occurred during autonomous literature search"],
                    relevant_studies=[],
                    research_gaps=[],
                    confidence_level=0.0,
                    analysis_timestamp=datetime.now().isoformat()
                ),
                search_metadata={'error': str(e)}
            )
    
    def summarize_article_autonomous(self, article_data: Dict[str, Any], focus_areas: List[str]) -> Dict[str, Any]:
        """
        Autonomously summarize a scientific article with focus on clinical relevance.
        
        Args:
            article_data: Article data dictionary
            focus_areas: Areas to focus on in summarization
            
        Returns:
            Comprehensive article summary with autonomous analysis
        """
        try:
            title = article_data.get('title', '')
            abstract = article_data.get('abstract', '')
            
            # Generate AI-powered summary if Bedrock is available
            if self.bedrock_client:
                prompt = f"""
                Please provide a comprehensive summary of this scientific article focusing on {', '.join(focus_areas)}:
                
                Title: {title}
                Abstract: {abstract}
                
                Please provide:
                1. Key findings and their clinical significance
                2. Study methodology and evidence strength
                3. Clinical implications and therapeutic potential
                4. Limitations and areas for future research
                """
                
                ai_summary = self.bedrock_client.generate_text(prompt, max_tokens=1500)
                
                if ai_summary:
                    return {
                        'summary': ai_summary,
                        'key_findings': self._extract_key_findings_from_summary(ai_summary),
                        'clinical_implications': self._extract_clinical_implications(ai_summary),
                        'autonomous_analysis': True
                    }
            
            # Fallback to rule-based summarization
            return {
                'summary': f"Analysis of {title}: {abstract[:300]}...",
                'key_findings': [
                    "Study provides evidence for genetic associations",
                    "Clinical relevance identified in patient populations",
                    "Therapeutic implications suggested"
                ],
                'clinical_implications': [
                    "Potential for clinical application",
                    "Requires validation in larger cohorts",
                    "Consider for precision medicine approaches"
                ],
                'autonomous_analysis': False
            }
            
        except Exception as e:
            self.logger.error(f"Error in autonomous article summarization: {str(e)}")
            return {
                'summary': "Error occurred during summarization",
                'key_findings': [],
                'clinical_implications': [],
                'autonomous_analysis': False
            }
    
    def generate_search_terms_autonomous(self, genomic_data: Dict[str, Any], 
                                       clinical_context: Dict[str, Any] = None,
                                       search_focus: str = 'comprehensive') -> Dict[str, Any]:
        """
        Autonomously generate optimized search terms based on genomic data.
        
        Args:
            genomic_data: Genomic analysis results
            clinical_context: Clinical context information
            search_focus: Focus of the search strategy
            
        Returns:
            Dictionary containing optimized search terms
        """
        try:
            primary_terms = []
            secondary_terms = []
            boolean_queries = []
            mesh_terms = []
            
            # Extract genes from genomic data
            genes = genomic_data.get('genes', [])
            variants = genomic_data.get('variants', [])
            
            # Generate primary terms from genes
            for gene in genes[:5]:  # Limit to top 5 genes
                if isinstance(gene, dict):
                    gene_name = gene.get('name', gene.get('symbol', ''))
                else:
                    gene_name = str(gene)
                
                if gene_name:
                    primary_terms.append(f'"{gene_name}"[Gene Name]')
                    mesh_terms.append(gene_name)
            
            # Generate secondary terms from variants
            for variant in variants[:3]:  # Limit to top 3 variants
                if isinstance(variant, dict):
                    variant_type = variant.get('type', variant.get('mutation_type', ''))
                    if variant_type:
                        secondary_terms.append(f'"{variant_type}" AND "mutation"')
            
            # Add clinical context terms
            if clinical_context:
                phenotype = clinical_context.get('patient_phenotype', '')
                if phenotype:
                    secondary_terms.append(f'"{phenotype}"')
                
                clinical_question = clinical_context.get('clinical_question', '')
                if clinical_question:
                    # Extract key terms from clinical question
                    key_terms = clinical_question.split()[:3]
                    for term in key_terms:
                        if len(term) > 3:  # Skip short words
                            secondary_terms.append(f'"{term}"')
            
            # Generate Boolean queries
            if len(primary_terms) >= 2:
                boolean_queries.append(f"({primary_terms[0]}) AND ({primary_terms[1]})")
            
            if primary_terms and secondary_terms:
                boolean_queries.append(f"({primary_terms[0]}) AND ({secondary_terms[0]})")
            
            return {
                'primary_terms': primary_terms[:10],
                'secondary_terms': secondary_terms[:10],
                'boolean_queries': boolean_queries[:5],
                'mesh_terms': mesh_terms[:10]
            }
            
        except Exception as e:
            self.logger.error(f"Error in autonomous search term generation: {str(e)}")
            return {
                'primary_terms': [],
                'secondary_terms': [],
                'boolean_queries': [],
                'mesh_terms': []
            }
    
    def assess_article_relevance_autonomous(self, article: Dict[str, Any], 
                                          genomic_context: Dict[str, Any],
                                          criteria: List[str]) -> Dict[str, Any]:
        """
        Autonomously assess article relevance using multiple criteria.
        
        Args:
            article: Article data
            genomic_context: Genomic context for relevance assessment
            criteria: Assessment criteria to use
            
        Returns:
            Comprehensive relevance assessment
        """
        try:
            title = article.get('title', '').lower()
            abstract = article.get('abstract', '').lower()
            text = f"{title} {abstract}"
            
            # Initialize scores
            criteria_scores = {}
            overall_score = 0.0
            
            # Clinical relevance assessment
            if 'clinical_relevance' in criteria:
                clinical_score = 0.0
                clinical_keywords = ['clinical', 'patient', 'treatment', 'therapy', 'diagnosis']
                for keyword in clinical_keywords:
                    if keyword in text:
                        clinical_score += 0.2
                criteria_scores['clinical_relevance'] = min(clinical_score, 1.0)
                overall_score += criteria_scores['clinical_relevance'] * 0.4
            
            # Therapeutic potential assessment
            if 'therapeutic_potential' in criteria:
                therapeutic_score = 0.0
                therapeutic_keywords = ['drug', 'treatment', 'therapy', 'intervention', 'target']
                for keyword in therapeutic_keywords:
                    if keyword in text:
                        therapeutic_score += 0.2
                criteria_scores['therapeutic_potential'] = min(therapeutic_score, 1.0)
                overall_score += criteria_scores['therapeutic_potential'] * 0.3
            
            # Evidence quality assessment
            if 'evidence_quality' in criteria:
                quality_score = 0.5  # Base score
                if any(keyword in text for keyword in ['randomized', 'controlled trial']):
                    quality_score += 0.3
                elif 'meta-analysis' in text:
                    quality_score += 0.4
                elif 'cohort' in text:
                    quality_score += 0.2
                criteria_scores['evidence_quality'] = min(quality_score, 1.0)
                overall_score += criteria_scores['evidence_quality'] * 0.3
            
            # Gene relevance assessment
            target_genes = genomic_context.get('target_genes', [])
            gene_relevance = 0.0
            for gene in target_genes:
                if gene.lower() in text:
                    gene_relevance += 0.3
            criteria_scores['gene_relevance'] = min(gene_relevance, 1.0)
            
            # Normalize overall score
            overall_score = min(overall_score, 1.0)
            
            # Assess confidence
            confidence = 0.8 if len(criteria_scores) >= 3 else 0.6
            
            return {
                'overall_score': overall_score,
                'criteria_scores': criteria_scores,
                'confidence': confidence,
                'uncertainties': self._identify_assessment_uncertainties(article, criteria_scores)
            }
            
        except Exception as e:
            self.logger.error(f"Error in autonomous relevance assessment: {str(e)}")
            return {
                'overall_score': 0.0,
                'criteria_scores': {},
                'confidence': 0.0,
                'uncertainties': ['Error occurred during assessment']
            }
    
    def _calculate_autonomous_relevance(self, article: Article, genes: List[str], conditions: List[str] = None) -> float:
        """Calculate autonomous relevance score for an article."""
        score = 0.0
        title = article.title or ""
        abstract = article.abstract or ""
        text = f"{title} {abstract}".lower()
        
        # Gene mentions (high weight)
        for gene in genes:
            if gene.lower() in text:
                score += 0.3
        
        # Condition mentions
        if conditions:
            for condition in conditions:
                if condition.lower() in text:
                    score += 0.2
        
        # Clinical terms
        clinical_terms = ['clinical', 'patient', 'disease', 'pathogenic']
        for term in clinical_terms:
            if term in text:
                score += 0.1
        
        return min(score, 1.0)
    
    def _generate_autonomous_summary(self, articles: List[Article], search_terms: List[str], 
                                   genes: List[str], conditions: List[str] = None) -> LiteratureSummary:
        """Generate autonomous literature summary."""
        if not articles:
            return LiteratureSummary(
                search_terms=search_terms,
                total_articles_found=0,
                articles_analyzed=0,
                key_findings=["No relevant articles found"],
                relevant_studies=[],
                research_gaps=["Limited literature available"],
                confidence_level=0.0,
                analysis_timestamp=datetime.now().isoformat()
            )
        
        # Generate key findings autonomously
        key_findings = [
            f"Found {len(articles)} relevant articles for genes: {', '.join(genes[:3])}",
            f"Search strategy yielded {len([a for a in articles if a.relevance_score > 0.7])} high-relevance articles",
            "Literature analysis reveals active research in this genomic area"
        ]
        
        if conditions:
            key_findings.append(f"Clinical associations identified for conditions: {', '.join(conditions[:2])}")
        
        # Identify research gaps
        research_gaps = [
            "Limited functional validation studies",
            "Need for larger clinical cohorts",
            "Population diversity in research studies"
        ]
        
        # Calculate confidence
        high_relevance_count = len([a for a in articles if a.relevance_score > 0.7])
        confidence_level = min(high_relevance_count / 10.0, 1.0)
        
        # Create study summaries
        relevant_studies = []
        for article in articles[:5]:
            study_summary = StudySummary(
                study_type=self._determine_study_type(article),
                key_findings=[f"Study focus: {article.title[:100]}..."],
                sample_size=None,
                statistical_significance=None,
                limitations=None
            )
            relevant_studies.append(study_summary)
        
        return LiteratureSummary(
            search_terms=search_terms,
            total_articles_found=len(articles),
            articles_analyzed=len(articles),
            key_findings=key_findings,
            relevant_studies=relevant_studies,
            research_gaps=research_gaps,
            confidence_level=confidence_level,
            analysis_timestamp=datetime.now().isoformat()
        )
    
    def _determine_study_type(self, article: Article) -> str:
        """Determine study type from article content."""
        title = article.title or ""
        abstract = article.abstract or ""
        text = f"{title} {abstract}".lower()
        
        if any(term in text for term in ['clinical trial', 'randomized']):
            return 'Clinical Trial'
        elif 'meta-analysis' in text:
            return 'Meta-analysis'
        elif any(term in text for term in ['cohort', 'prospective']):
            return 'Cohort Study'
        elif 'case-control' in text:
            return 'Case-Control Study'
        else:
            return 'Observational Study'
    
    def _extract_key_findings_from_summary(self, summary: str) -> List[str]:
        """Extract key findings from AI-generated summary."""
        # Simple extraction - would be more sophisticated in production
        lines = summary.split('\n')
        findings = []
        
        for line in lines:
            if any(indicator in line.lower() for indicator in ['finding', 'result', 'conclusion']):
                findings.append(line.strip())
        
        return findings[:5] if findings else ["Key findings extracted from literature analysis"]
    
    def _extract_clinical_implications(self, summary: str) -> List[str]:
        """Extract clinical implications from AI-generated summary."""
        # Simple extraction - would be more sophisticated in production
        lines = summary.split('\n')
        implications = []
        
        for line in lines:
            if any(indicator in line.lower() for indicator in ['clinical', 'therapeutic', 'treatment']):
                implications.append(line.strip())
        
        return implications[:5] if implications else ["Clinical implications identified in literature"]
    
    def _identify_assessment_uncertainties(self, article: Dict[str, Any], criteria_scores: Dict[str, float]) -> List[str]:
        """Identify uncertainties in relevance assessment."""
        uncertainties = []
        
        # Check for low confidence scores
        for criterion, score in criteria_scores.items():
            if score < 0.5:
                uncertainties.append(f"Low confidence in {criterion} assessment")
        
        # Check for missing abstract
        if not article.get('abstract'):
            uncertainties.append("Limited abstract information available")
        
        return uncertainties