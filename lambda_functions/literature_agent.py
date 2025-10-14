"""
Lambda handler for Literature Agent.
Searches and analyzes scientific literature using PubMed and AI summarization.
"""

import json
import os
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import Biomerkin modules
import sys
sys.path.append('/opt/python')
from biomerkin.agents.literature_agent import LiteratureAgent
from biomerkin.models.literature import LiteratureResults


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for literature analysis.
    
    Args:
        event: Lambda event containing genomics/proteomics results
        context: Lambda context
        
    Returns:
        Response dictionary with literature results
    """
    logger.info(f"Literature Agent Lambda invoked with event: {json.dumps(event)}")
    
    try:
        # Extract parameters
        genomics_results = event.get('genomics_results')
        proteomics_results = event.get('proteomics_results')
        max_articles = event.get('max_articles', 20)
        
        if not genomics_results:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'genomics_results is required'
                })
            }
        
        # Initialize literature agent
        agent = LiteratureAgent()
        
        # Analyze literature
        results = agent.analyze_literature(
            genomics_results=genomics_results,
            proteomics_results=proteomics_results,
            max_articles=max_articles
        )
        
        # Return results
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'literature_results': results.to_dict(),
                'agent': 'LiteratureAgent'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in literature agent handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'agent': 'LiteratureAgent'
            })
        }
