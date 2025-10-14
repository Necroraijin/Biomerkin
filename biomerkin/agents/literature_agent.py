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
            if "anthropic" in self.model_id.lower():
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
            title_matches = sum(1 for term in key_terms if term in article.title.lower())
            score += title_matches * 2.0
            
            # Count matches in abstract
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
            article_summaries.append(f"""
Article {i+1}:
Title: {article.title}
Journal: {article.journal}
Year: {article.publication_date}
Abstract: {article.abstract[:500]}...
Relevance Score: {article.relevance_score:.2f}
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
            text = f"{article.title} {article.abstract}".lower()
            
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