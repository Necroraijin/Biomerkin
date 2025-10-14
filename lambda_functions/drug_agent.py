"""
Lambda handler for Drug Agent.
Identifies drug candidates and clinical trial information.
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
from biomerkin.agents.drug_agent import DrugAgent
from biomerkin.models.drug import DrugResults


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for drug discovery analysis.
    
    Args:
        event: Lambda event containing genomics results
        context: Lambda context
        
    Returns:
        Response dictionary with drug results
    """
    logger.info(f"Drug Agent Lambda invoked with event: {json.dumps(event)}")
    
    try:
        # Extract parameters
        genomics_results = event.get('genomics_results')
        
        if not genomics_results:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'genomics_results is required'
                })
            }
        
        # Initialize drug agent
        agent = DrugAgent()
        
        # Analyze drug candidates
        results = agent.analyze_drug_candidates(genomics_results)
        
        # Return results
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'drug_results': results.to_dict(),
                'agent': 'DrugAgent'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in drug agent handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'agent': 'DrugAgent'
            })
        }
