"""
Bedrock Agent Action Group Executor for Literature Research.
This Lambda function serves as an action group executor for AWS Bedrock Agents,
providing autonomous literature research and analysis capabilities.
"""

import json
import os
import logging
from typing import Dict, Any, List
import boto3
from datetime import datetime

# CORS Headers for all responses
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
}

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import Biomerkin modules
import sys
sys.path.append('/opt/python')

try:
    from biomerkin.agents.literature_agent import LiteratureAgent
    from biomerkin.models.literature import LiteratureResults, Article
    from biomerkin.utils.logging_config import get_logger
except ImportError as e:
    logger.warning(f"Could not import Biomerkin modules: {e}")
    # Fallback for testing without full Biomerkin installation
    LiteratureAgent = None


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Bedrock Agent Action Group handler for literature research.
    
    This function is called by Bedrock Agents to perform autonomous literature analysis.
    It supports multiple operations for scientific literature research and summarization.
    
    Args:
        event: Bedrock Agent event containing action details
        context: Lambda context
        
    Returns:
        Response dictionary formatted for Bedrock Agent consumption
    """
    # Handle OPTIONS request for CORS
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS
        }
    
    logger.info(f"Bedrock Literature Action invoked with event: {json.dumps(event)}")
    
    try:
        # Extract Bedrock Agent parameters
        action_group = event.get('actionGroup', '')
        api_path = event.get('apiPath', '')
        http_method = event.get('httpMethod', 'POST')
        parameters = event.get('parameters', [])
        request_body = event.get('requestBody', {})
        
        # Convert parameters to dictionary
        param_dict = {}
        for param in parameters:
            param_dict[param['name']] = param['value']
        
        # Route to appropriate literature function
        if api_path == '/search-literature':
            result = search_literature_action(request_body, param_dict)
        elif api_path == '/summarize-articles':
            result = summarize_articles_action(request_body, param_dict)
        elif api_path == '/generate-search-terms':
            result = generate_search_terms_action(request_body, param_dict)
        elif api_path == '/assess-relevance':
            result = assess_relevance_action(request_body, param_dict)
        else:
            raise ValueError(f"Unknown API path: {api_path}")
        
        # Format response for Bedrock Agent
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(result)
                    }
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error in Bedrock literature action: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': action_group,
                'apiPath': api_path,
                'httpMethod': http_method,
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({
                            'error': str(e),
                            'timestamp': datetime.now().isoformat()
                        })
                    }
                }
            }
        }


def search_literature_action(request_body: Dict[str, Any], parameters: Dict[str, str]) -> Dict[str, Any]:
    """
    Autonomous literature search action.
    
    This function performs intelligent literature search based on genomic findings,
    using autonomous reasoning to select optimal search strategies.
    
    Args:
        request_body: Request body from Bedrock Agent
        parameters: URL parameters
        
    Returns:
        Literature search results with autonomous analysis
    """
    try:
        # Extract search parameters
        content = request_body.get('content', {})
        genes = content.get('genes', [])
        conditions = content.get('conditions', [])
        max_articles = content.get('max_articles', 20)
        
        if not genes:
            raise ValueError("At least one gene is required for literature search")
        
        # Initialize literature agent
        if LiteratureAgent is None:
            raise ImportError("LiteratureAgent not available - check Biomerkin installation")
        
        agent = LiteratureAgent()
        
        # Generate autonomous search strategy
        search_strategy = _generate_autonomous_search_strategy(genes, conditions)
        
        # Perform literature search with autonomous term optimization
        search_results = agent.search_literature_autonomous(
            genes=genes,
            conditions=conditions,
            max_articles=max_articles,
            search_strategy=search_strategy
        )
        
        # Add autonomous analysis and insights
        result = {
            'search_strategy': search_strategy,
            'total_articles_found': len(search_results.articles),
            'articles': [
                {
                    'pmid': article.pmid,
                    'title': article.title,
                    'authors': article.authors,
                    'journal': article.journal,
                    'publication_date': article.publication_date,
                    'abstract': article.abstract,
                    'relevance_score': article.relevance_score,
                    'autonomous_analysis': {
                        'key_findings': _extract_key_findings(article),
                        'clinical_relevance': _assess_clinical_relevance(article, genes),
                        'evidence_level': _determine_evidence_level(article),
                        'therapeutic_implications': _identify_therapeutic_implications(article)
                    }
                }
                for article in search_results.articles
            ],
            'search_summary': {
                'high_relevance_articles': len([a for a in search_results.articles if a.relevance_score > 0.8]),
                'clinical_studies': len([a for a in search_results.articles if _is_clinical_study(a)]),
                'recent_publications': len([a for a in search_results.articles if _is_recent_publication(a)]),
                'review_articles': len([a for a in search_results.articles if _is_review_article(a)])
            },
            'autonomous_insights': _generate_literature_insights(search_results.articles, genes),
            'research_gaps': _identify_research_gaps(search_results.articles, genes),
            'confidence_assessment': _assess_search_confidence(search_results.articles),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Autonomous literature search completed: {len(search_results.articles)} articles found for genes: {genes}")
        return result
        
    except Exception as e:
        logger.error(f"Error in literature search action: {str(e)}")
        raise


def summarize_articles_action(request_body: Dict[str, Any], parameters: Dict[str, str]) -> Dict[str, Any]:
    """
    Autonomous article summarization action.
    
    This function uses AI to summarize scientific articles with focus on
    clinical relevance and therapeutic implications.
    
    Args:
        request_body: Request body from Bedrock Agent
        parameters: URL parameters
        
    Returns:
        Comprehensive article summaries with autonomous analysis
    """
    try:
        content = request_body.get('content', {})
        articles = content.get('articles', [])
        focus_areas = content.get('focus_areas', ['clinical_significance', 'therapeutic_implications'])
        
        if not articles:
            raise ValueError("Articles are required for summarization")
        
        # Initialize literature agent
        agent = LiteratureAgent()
        
        # Perform autonomous summarization
        summaries = []
        for article_data in articles:
            summary = agent.summarize_article_autonomous(
                article_data=article_data,
                focus_areas=focus_areas
            )
            
            # Add autonomous analysis
            enhanced_summary = {
                'article_id': article_data.get('pmid', 'unknown'),
                'title': article_data.get('title', ''),
                'summary': summary.get('summary', ''),
                'key_findings': summary.get('key_findings', []),
                'clinical_implications': summary.get('clinical_implications', []),
                'autonomous_analysis': {
                    'evidence_strength': _assess_evidence_strength(article_data, summary),
                    'clinical_actionability': _assess_clinical_actionability(summary),
                    'therapeutic_potential': _assess_therapeutic_potential(summary),
                    'study_limitations': _identify_study_limitations(article_data, summary),
                    'future_research_directions': _suggest_future_research(summary)
                },
                'confidence_scores': {
                    'summary_accuracy': 0.85,  # Would be calculated based on model confidence
                    'clinical_relevance': _calculate_clinical_relevance_score(summary),
                    'therapeutic_applicability': _calculate_therapeutic_score(summary)
                }
            }
            summaries.append(enhanced_summary)
        
        # Generate meta-analysis
        meta_analysis = _generate_meta_analysis(summaries)
        
        result = {
            'total_articles_summarized': len(summaries),
            'article_summaries': summaries,
            'meta_analysis': meta_analysis,
            'autonomous_insights': {
                'consensus_findings': _identify_consensus_findings(summaries),
                'conflicting_evidence': _identify_conflicting_evidence(summaries),
                'research_trends': _analyze_research_trends(summaries),
                'clinical_recommendations': _generate_clinical_recommendations(summaries)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Autonomous article summarization completed: {len(summaries)} articles summarized")
        return result
        
    except Exception as e:
        logger.error(f"Error in article summarization action: {str(e)}")
        raise


def generate_search_terms_action(request_body: Dict[str, Any], parameters: Dict[str, str]) -> Dict[str, Any]:
    """
    Autonomous search term generation action.
    
    This function intelligently generates optimal search terms based on
    genomic findings and clinical context.
    
    Args:
        request_body: Request body from Bedrock Agent
        parameters: URL parameters
        
    Returns:
        Optimized search terms with reasoning
    """
    try:
        content = request_body.get('content', {})
        genomic_data = content.get('genomic_data', {})
        clinical_context = content.get('clinical_context', {})
        search_focus = content.get('search_focus', 'comprehensive')
        
        if not genomic_data:
            raise ValueError("Genomic data is required for search term generation")
        
        # Initialize literature agent
        agent = LiteratureAgent()
        
        # Generate autonomous search terms
        search_terms = agent.generate_search_terms_autonomous(
            genomic_data=genomic_data,
            clinical_context=clinical_context,
            search_focus=search_focus
        )
        
        # Add autonomous reasoning and optimization
        result = {
            'primary_search_terms': search_terms.get('primary_terms', []),
            'secondary_search_terms': search_terms.get('secondary_terms', []),
            'boolean_queries': search_terms.get('boolean_queries', []),
            'mesh_terms': search_terms.get('mesh_terms', []),
            'autonomous_reasoning': {
                'term_selection_strategy': _explain_term_selection_strategy(genomic_data, clinical_context),
                'search_optimization': _explain_search_optimization(search_terms),
                'expected_relevance': _predict_search_relevance(search_terms),
                'alternative_strategies': _suggest_alternative_strategies(genomic_data)
            },
            'search_predictions': {
                'estimated_articles': _estimate_article_count(search_terms),
                'relevance_distribution': _predict_relevance_distribution(search_terms),
                'coverage_assessment': _assess_topic_coverage(search_terms, genomic_data)
            },
            'optimization_suggestions': _generate_optimization_suggestions(search_terms),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Autonomous search term generation completed: {len(search_terms.get('primary_terms', []))} primary terms")
        return result
        
    except Exception as e:
        logger.error(f"Error in search term generation action: {str(e)}")
        raise


def assess_relevance_action(request_body: Dict[str, Any], parameters: Dict[str, str]) -> Dict[str, Any]:
    """
    Autonomous relevance assessment action.
    
    This function assesses the relevance of articles to specific genomic findings
    using autonomous reasoning and multiple assessment criteria.
    
    Args:
        request_body: Request body from Bedrock Agent
        parameters: URL parameters
        
    Returns:
        Relevance assessment with detailed reasoning
    """
    try:
        content = request_body.get('content', {})
        articles = content.get('articles', [])
        genomic_context = content.get('genomic_context', {})
        assessment_criteria = content.get('assessment_criteria', ['clinical_relevance', 'therapeutic_potential', 'evidence_quality'])
        
        if not articles:
            raise ValueError("Articles are required for relevance assessment")
        
        # Initialize literature agent
        agent = LiteratureAgent()
        
        # Perform autonomous relevance assessment
        assessments = []
        for article in articles:
            assessment = agent.assess_article_relevance_autonomous(
                article=article,
                genomic_context=genomic_context,
                criteria=assessment_criteria
            )
            
            # Add detailed autonomous analysis
            enhanced_assessment = {
                'article_id': article.get('pmid', 'unknown'),
                'title': article.get('title', ''),
                'overall_relevance_score': assessment.get('overall_score', 0.0),
                'criteria_scores': assessment.get('criteria_scores', {}),
                'autonomous_analysis': {
                    'relevance_reasoning': _explain_relevance_reasoning(article, assessment),
                    'key_relevance_factors': _identify_relevance_factors(article, genomic_context),
                    'clinical_applicability': _assess_clinical_applicability(article, genomic_context),
                    'evidence_quality_assessment': _assess_evidence_quality(article),
                    'therapeutic_relevance': _assess_therapeutic_relevance(article, genomic_context)
                },
                'confidence_metrics': {
                    'assessment_confidence': assessment.get('confidence', 0.0),
                    'uncertainty_factors': assessment.get('uncertainties', []),
                    'reliability_score': _calculate_reliability_score(article, assessment)
                },
                'recommendations': {
                    'priority_level': _determine_priority_level(assessment),
                    'follow_up_actions': _suggest_follow_up_actions(article, assessment),
                    'related_searches': _suggest_related_searches(article, genomic_context)
                }
            }
            assessments.append(enhanced_assessment)
        
        # Generate summary analysis
        summary_analysis = _generate_relevance_summary(assessments, genomic_context)
        
        result = {
            'total_articles_assessed': len(assessments),
            'relevance_assessments': assessments,
            'summary_analysis': summary_analysis,
            'autonomous_insights': {
                'high_relevance_articles': [a for a in assessments if a['overall_relevance_score'] > 0.8],
                'research_priorities': _identify_research_priorities(assessments),
                'knowledge_gaps': _identify_knowledge_gaps(assessments, genomic_context),
                'clinical_actionability': _assess_overall_clinical_actionability(assessments)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Autonomous relevance assessment completed: {len(assessments)} articles assessed")
        return result
        
    except Exception as e:
        logger.error(f"Error in relevance assessment action: {str(e)}")
        raise


# Helper functions for autonomous literature analysis
def _generate_autonomous_search_strategy(genes: List[str], conditions: List[str]) -> Dict[str, Any]:
    """Generate autonomous search strategy based on input parameters."""
    return {
        'strategy_type': 'comprehensive_genomic_search',
        'primary_focus': 'clinical_significance',
        'search_phases': [
            'gene_specific_search',
            'condition_specific_search',
            'therapeutic_implications_search',
            'recent_developments_search'
        ],
        'optimization_approach': 'relevance_maximization',
        'reasoning': f"Selected comprehensive strategy for {len(genes)} genes and {len(conditions)} conditions to maximize clinical relevance"
    }


def _extract_key_findings(article: Article) -> List[str]:
    """Extract key findings from an article using autonomous analysis."""
    # This would use NLP to extract key findings from abstract/content
    # Mock implementation
    return [
        "Significant association found between gene variant and disease phenotype",
        "Novel therapeutic target identified",
        "Clinical trial results show promising efficacy"
    ]


def _assess_clinical_relevance(article: Article, genes: List[str]) -> float:
    """Assess clinical relevance of an article to specific genes."""
    # This would analyze the article content for clinical relevance
    # Mock implementation based on title/abstract keywords
    clinical_keywords = ['clinical', 'patient', 'treatment', 'therapy', 'diagnosis']
    title_lower = article.title.lower() if article.title else ""
    abstract_lower = article.abstract.lower() if article.abstract else ""
    
    relevance_score = 0.0
    for keyword in clinical_keywords:
        if keyword in title_lower:
            relevance_score += 0.2
        if keyword in abstract_lower:
            relevance_score += 0.1
    
    # Check for gene mentions
    for gene in genes:
        if gene.lower() in title_lower or gene.lower() in abstract_lower:
            relevance_score += 0.3
    
    return min(relevance_score, 1.0)


def _determine_evidence_level(article: Article) -> str:
    """Determine the level of evidence for an article."""
    # This would analyze study design and methodology
    # Mock implementation based on title keywords
    title_lower = article.title.lower() if article.title else ""
    
    if any(keyword in title_lower for keyword in ['randomized', 'controlled trial', 'rct']):
        return 'Level I - Randomized Controlled Trial'
    elif any(keyword in title_lower for keyword in ['cohort', 'prospective']):
        return 'Level II - Cohort Study'
    elif any(keyword in title_lower for keyword in ['case-control']):
        return 'Level III - Case-Control Study'
    elif any(keyword in title_lower for keyword in ['case series', 'case report']):
        return 'Level IV - Case Series/Report'
    else:
        return 'Level V - Expert Opinion/Review'


def _identify_therapeutic_implications(article: Article) -> List[str]:
    """Identify therapeutic implications from an article."""
    # This would use NLP to extract therapeutic information
    # Mock implementation
    return [
        "Potential for targeted therapy development",
        "Biomarker for treatment response prediction",
        "Drug repurposing opportunity identified"
    ]


def _is_clinical_study(article: Article) -> bool:
    """Determine if an article describes a clinical study."""
    clinical_indicators = ['clinical trial', 'patient', 'cohort', 'case-control', 'randomized']
    title_abstract = f"{article.title} {article.abstract}".lower()
    return any(indicator in title_abstract for indicator in clinical_indicators)


def _is_recent_publication(article: Article) -> bool:
    """Determine if an article is a recent publication (within 3 years)."""
    # This would parse the publication date
    # Mock implementation
    return True  # Assume recent for demo


def _is_review_article(article: Article) -> bool:
    """Determine if an article is a review article."""
    review_indicators = ['review', 'meta-analysis', 'systematic review']
    title_lower = article.title.lower() if article.title else ""
    return any(indicator in title_lower for indicator in review_indicators)


def _generate_literature_insights(articles: List[Article], genes: List[str]) -> List[str]:
    """Generate autonomous insights from literature search results."""
    insights = []
    
    if len(articles) > 50:
        insights.append("Extensive literature available - suggests well-studied genes with established clinical significance")
    elif len(articles) < 5:
        insights.append("Limited literature found - may indicate novel genes requiring further research")
    
    clinical_studies = [a for a in articles if _is_clinical_study(a)]
    if len(clinical_studies) > 10:
        insights.append(f"Strong clinical evidence base with {len(clinical_studies)} clinical studies identified")
    
    recent_articles = [a for a in articles if _is_recent_publication(a)]
    if len(recent_articles) > len(articles) * 0.5:
        insights.append("Active area of research with significant recent publications")
    
    return insights


def _identify_research_gaps(articles: List[Article], genes: List[str]) -> List[str]:
    """Identify research gaps based on literature analysis."""
    # This would analyze the literature to identify gaps
    # Mock implementation
    return [
        "Limited functional studies on protein variants",
        "Lack of diverse population studies",
        "Need for long-term clinical outcome data"
    ]


def _assess_search_confidence(articles: List[Article]) -> Dict[str, float]:
    """Assess confidence in search results."""
    return {
        'search_completeness': 0.85,  # Based on search strategy coverage
        'result_relevance': sum(a.relevance_score for a in articles) / len(articles) if articles else 0.0,
        'evidence_quality': 0.75  # Based on study types and journals
    }


def _assess_evidence_strength(article_data: Dict[str, Any], summary: Dict[str, Any]) -> str:
    """Assess the strength of evidence in an article."""
    # This would analyze study design, sample size, methodology
    # Mock implementation
    return "Moderate"  # Could be "Strong", "Moderate", "Weak"


def _assess_clinical_actionability(summary: Dict[str, Any]) -> float:
    """Assess how actionable the clinical findings are."""
    # This would analyze the clinical implications
    # Mock implementation
    return 0.7


def _assess_therapeutic_potential(summary: Dict[str, Any]) -> float:
    """Assess therapeutic potential based on article summary."""
    # This would analyze therapeutic implications
    # Mock implementation
    return 0.6


def _identify_study_limitations(article_data: Dict[str, Any], summary: Dict[str, Any]) -> List[str]:
    """Identify limitations in the study."""
    # This would analyze methodology and identify limitations
    # Mock implementation
    return [
        "Small sample size",
        "Single-center study",
        "Short follow-up period"
    ]


def _suggest_future_research(summary: Dict[str, Any]) -> List[str]:
    """Suggest future research directions."""
    # This would analyze gaps and suggest research directions
    # Mock implementation
    return [
        "Larger multi-center validation studies needed",
        "Functional characterization of variants required",
        "Long-term clinical outcome studies"
    ]


def _calculate_clinical_relevance_score(summary: Dict[str, Any]) -> float:
    """Calculate clinical relevance score for a summary."""
    # This would analyze clinical content
    # Mock implementation
    return 0.8


def _calculate_therapeutic_score(summary: Dict[str, Any]) -> float:
    """Calculate therapeutic applicability score."""
    # This would analyze therapeutic content
    # Mock implementation
    return 0.65


def _generate_meta_analysis(summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate meta-analysis of multiple article summaries."""
    return {
        'consensus_findings': _identify_consensus_findings(summaries),
        'evidence_synthesis': "Strong evidence supports clinical significance of identified variants",
        'therapeutic_landscape': "Multiple therapeutic approaches under investigation",
        'research_maturity': "Well-established field with ongoing developments"
    }


def _identify_consensus_findings(summaries: List[Dict[str, Any]]) -> List[str]:
    """Identify consensus findings across multiple summaries."""
    # This would analyze common themes across summaries
    # Mock implementation
    return [
        "Consistent association between variants and disease phenotype",
        "Agreement on pathogenic mechanisms",
        "Convergent evidence for therapeutic targets"
    ]


def _identify_conflicting_evidence(summaries: List[Dict[str, Any]]) -> List[str]:
    """Identify conflicting evidence across summaries."""
    # Mock implementation
    return [
        "Discrepant results in different populations",
        "Conflicting therapeutic efficacy data"
    ]


def _analyze_research_trends(summaries: List[Dict[str, Any]]) -> List[str]:
    """Analyze research trends from summaries."""
    # Mock implementation
    return [
        "Increasing focus on precision medicine approaches",
        "Growing emphasis on functional validation",
        "Trend toward multi-omics integration"
    ]


def _generate_clinical_recommendations(summaries: List[Dict[str, Any]]) -> List[str]:
    """Generate clinical recommendations based on summaries."""
    # Mock implementation
    return [
        "Consider genetic testing for high-risk patients",
        "Implement targeted screening protocols",
        "Evaluate for precision therapy options"
    ]


# Additional helper functions would continue here...
# (Truncated for brevity, but would include all the remaining helper functions)

def _explain_term_selection_strategy(genomic_data: Dict[str, Any], clinical_context: Dict[str, Any]) -> str:
    """Explain the autonomous term selection strategy."""
    return "Selected terms based on gene function, clinical phenotype, and therapeutic relevance to maximize search precision and recall"


def _explain_search_optimization(search_terms: Dict[str, Any]) -> str:
    """Explain search optimization approach."""
    return "Optimized search terms using Boolean logic and MeSH terms to balance sensitivity and specificity"


def _predict_search_relevance(search_terms: Dict[str, Any]) -> float:
    """Predict expected relevance of search results."""
    return 0.75  # Mock prediction


def _suggest_alternative_strategies(genomic_data: Dict[str, Any]) -> List[str]:
    """Suggest alternative search strategies."""
    return [
        "Pathway-based search approach",
        "Phenotype-driven literature mining",
        "Therapeutic area focused search"
    ]


def _estimate_article_count(search_terms: Dict[str, Any]) -> int:
    """Estimate number of articles the search will return."""
    return 150  # Mock estimate


def _predict_relevance_distribution(search_terms: Dict[str, Any]) -> Dict[str, int]:
    """Predict distribution of article relevance scores."""
    return {
        'high_relevance': 25,
        'moderate_relevance': 75,
        'low_relevance': 50
    }


def _assess_topic_coverage(search_terms: Dict[str, Any], genomic_data: Dict[str, Any]) -> float:
    """Assess how well search terms cover the topic."""
    return 0.85  # Mock assessment


def _generate_optimization_suggestions(search_terms: Dict[str, Any]) -> List[str]:
    """Generate suggestions for search optimization."""
    return [
        "Consider adding pathway-specific terms",
        "Include disease-specific MeSH terms",
        "Add recent publication date filters"
    ]


def _explain_relevance_reasoning(article: Dict[str, Any], assessment: Dict[str, Any]) -> str:
    """Explain the reasoning behind relevance assessment."""
    return f"Article scored {assessment.get('overall_score', 0.0):.2f} based on clinical relevance, evidence quality, and therapeutic potential"


def _identify_relevance_factors(article: Dict[str, Any], genomic_context: Dict[str, Any]) -> List[str]:
    """Identify key factors contributing to article relevance."""
    factors = []
    
    # Check for gene mentions
    target_genes = genomic_context.get('target_genes', [])
    title_abstract = f"{article.get('title', '')} {article.get('abstract', '')}".lower()
    
    for gene in target_genes:
        if gene.lower() in title_abstract:
            factors.append(f"Direct mention of target gene: {gene}")
    
    # Check for clinical keywords
    clinical_keywords = ['clinical trial', 'patient', 'treatment', 'therapy']
    for keyword in clinical_keywords:
        if keyword in title_abstract:
            factors.append(f"Clinical relevance indicator: {keyword}")
    
    return factors


def _assess_clinical_applicability(article: Dict[str, Any], genomic_context: Dict[str, Any]) -> float:
    """Assess clinical applicability of article findings."""
    # Mock implementation - would analyze clinical content
    return 0.75


def _assess_evidence_quality(article: Dict[str, Any]) -> Dict[str, Any]:
    """Assess the quality of evidence in the article."""
    title_abstract = f"{article.get('title', '')} {article.get('abstract', '')}".lower()
    
    quality_indicators = {
        'study_design': 'observational',
        'sample_size': 'medium',
        'methodology': 'standard',
        'statistical_power': 'adequate'
    }
    
    # Upgrade based on keywords
    if any(keyword in title_abstract for keyword in ['randomized', 'controlled trial']):
        quality_indicators['study_design'] = 'randomized_controlled_trial'
    elif 'meta-analysis' in title_abstract:
        quality_indicators['study_design'] = 'meta_analysis'
    
    return quality_indicators


def _assess_therapeutic_relevance(article: Dict[str, Any], genomic_context: Dict[str, Any]) -> float:
    """Assess therapeutic relevance of article to genomic context."""
    # Mock implementation - would analyze therapeutic content
    return 0.65


def _calculate_reliability_score(article: Dict[str, Any], assessment: Dict[str, Any]) -> float:
    """Calculate reliability score for the assessment."""
    # Based on journal impact, study design, sample size, etc.
    return 0.8


def _determine_priority_level(assessment: Dict[str, Any]) -> str:
    """Determine priority level based on assessment scores."""
    overall_score = assessment.get('overall_score', 0.0)
    
    if overall_score >= 0.8:
        return 'High Priority'
    elif overall_score >= 0.6:
        return 'Medium Priority'
    else:
        return 'Low Priority'


def _suggest_follow_up_actions(article: Dict[str, Any], assessment: Dict[str, Any]) -> List[str]:
    """Suggest follow-up actions based on article assessment."""
    actions = []
    
    overall_score = assessment.get('overall_score', 0.0)
    
    if overall_score >= 0.8:
        actions.append("Include in primary evidence synthesis")
        actions.append("Consider for clinical guideline development")
    elif overall_score >= 0.6:
        actions.append("Include in secondary analysis")
        actions.append("Monitor for additional supporting evidence")
    else:
        actions.append("Consider for background information only")
    
    return actions


def _suggest_related_searches(article: Dict[str, Any], genomic_context: Dict[str, Any]) -> List[str]:
    """Suggest related search terms based on article content."""
    # Extract key terms from title and abstract for related searches
    return [
        "Functional validation studies",
        "Population-specific analyses",
        "Therapeutic intervention trials"
    ]


def _generate_relevance_summary(assessments: List[Dict[str, Any]], genomic_context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary analysis of relevance assessments."""
    total_articles = len(assessments)
    high_relevance = len([a for a in assessments if a['overall_relevance_score'] > 0.8])
    medium_relevance = len([a for a in assessments if 0.6 <= a['overall_relevance_score'] <= 0.8])
    
    return {
        'total_articles': total_articles,
        'high_relevance_count': high_relevance,
        'medium_relevance_count': medium_relevance,
        'average_relevance': sum(a['overall_relevance_score'] for a in assessments) / total_articles if total_articles > 0 else 0.0,
        'recommendation': f"Found {high_relevance} high-relevance articles out of {total_articles} assessed"
    }


def _identify_research_priorities(assessments: List[Dict[str, Any]]) -> List[str]:
    """Identify research priorities based on assessments."""
    high_priority_articles = [a for a in assessments if a['overall_relevance_score'] > 0.8]
    
    priorities = []
    if len(high_priority_articles) > 5:
        priorities.append("Strong evidence base - focus on clinical implementation")
    elif len(high_priority_articles) > 0:
        priorities.append("Moderate evidence - additional validation studies needed")
    else:
        priorities.append("Limited evidence - fundamental research required")
    
    return priorities


def _identify_knowledge_gaps(assessments: List[Dict[str, Any]], genomic_context: Dict[str, Any]) -> List[str]:
    """Identify knowledge gaps based on assessment results."""
    gaps = []
    
    # Analyze assessment patterns to identify gaps
    clinical_studies = len([a for a in assessments if 'clinical' in str(a).lower()])
    
    if clinical_studies < len(assessments) * 0.3:
        gaps.append("Limited clinical validation studies")
    
    gaps.extend([
        "Functional characterization studies needed",
        "Population diversity in research cohorts",
        "Long-term outcome data"
    ])
    
    return gaps


def _assess_overall_clinical_actionability(assessments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Assess overall clinical actionability of the evidence."""
    high_actionability = len([a for a in assessments if a.get('autonomous_analysis', {}).get('clinical_actionability', 0) > 0.7])
    
    return {
        'actionable_findings': high_actionability,
        'total_assessed': len(assessments),
        'actionability_score': high_actionability / len(assessments) if assessments else 0.0,
        'recommendation': "Sufficient evidence for clinical consideration" if high_actionability > 3 else "Additional evidence needed for clinical action"
    {assessment.get('overall_score', 0.0):.2f} based on gene mention frequency, clinical content, and therapeutic implications"


def _identify_relevance_factors(article: Dict[str, Any], genomic_context: Dict[str, Any]) -> List[str]:
    """Identify key factors contributing to relevance."""
    return [
        "Direct gene mention in title",
        "Clinical study design",
        "Therapeutic implications discussed",
        "Recent publication date"
    ]


def _assess_clinical_applicability(article: Dict[str, Any], genomic_context: Dict[str, Any]) -> float:
    """Assess clinical applicability of article findings."""
    return 0.7  # Mock assessment


def _assess_evidence_quality(article: Dict[str, Any]) -> str:
    """Assess the quality of evidence in the article."""
    return "High"  # Could be "High", "Moderate", "Low"


def _assess_therapeutic_relevance(article: Dict[str, Any], genomic_context: Dict[str, Any]) -> float:
    """Assess therapeutic relevance of the article."""
    return 0.6  # Mock assessment


def _calculate_reliability_score(article: Dict[str, Any], assessment: Dict[str, Any]) -> float:
    """Calculate reliability score for the assessment."""
    return 0.8  # Mock calculation


def _determine_priority_level(assessment: Dict[str, Any]) -> str:
    """Determine priority level based on assessment."""
    score = assessment.get('overall_score', 0.0)
    if score > 0.8:
        return "High Priority"
    elif score > 0.5:
        return "Medium Priority"
    else:
        return "Low Priority"


def _suggest_follow_up_actions(article: Dict[str, Any], assessment: Dict[str, Any]) -> List[str]:
    """Suggest follow-up actions based on assessment."""
    return [
        "Include in systematic review",
        "Cite in clinical recommendations",
        "Consider for meta-analysis"
    ]


def _suggest_related_searches(article: Dict[str, Any], genomic_context: Dict[str, Any]) -> List[str]:
    """Suggest related searches based on article content."""
    return [
        "Search for similar variants in same gene",
        "Look for functional studies",
        "Find clinical outcome studies"
    ]


def _generate_relevance_summary(assessments: List[Dict[str, Any]], genomic_context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary of relevance assessments."""
    return {
        'average_relevance': sum(a['overall_relevance_score'] for a in assessments) / len(assessments),
        'high_relevance_count': len([a for a in assessments if a['overall_relevance_score'] > 0.8]),
        'clinical_applicability': "High - multiple clinically relevant studies identified",
        'evidence_strength': "Strong - consistent findings across multiple studies"
    }


def _identify_research_priorities(assessments: List[Dict[str, Any]]) -> List[str]:
    """Identify research priorities based on assessments."""
    return [
        "Functional validation of variants",
        "Clinical outcome studies",
        "Therapeutic development"
    ]


def _identify_knowledge_gaps(assessments: List[Dict[str, Any]], genomic_context: Dict[str, Any]) -> List[str]:
    """Identify knowledge gaps from assessments."""
    return [
        "Limited population diversity in studies",
        "Lack of long-term follow-up data",
        "Need for mechanistic studies"
    ]


def _assess_overall_clinical_actionability(assessments: List[Dict[str, Any]]) -> float:
    """Assess overall clinical actionability across all assessments."""
    return 0.75  # Mock assessment