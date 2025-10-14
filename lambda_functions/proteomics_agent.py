"""
Lambda handler for Proteomics Agent.
Analyzes protein structures, functions, and interactions.
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
from biomerkin.agents.proteomics_agent import ProteomicsAgent
from biomerkin.models.proteomics import ProteomicsResults


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for proteomics analysis.
    
    Args:
        event: Lambda event containing protein data
        context: Lambda context
        
    Returns:
        Response dictionary with proteomics results
    """
    logger.info(f"Proteomics Agent Lambda invoked with event: {json.dumps(event)}")
    
    try:
        # Extract parameters
        protein_sequence = event.get('protein_sequence')
        protein_id = event.get('protein_id')
        
        if not protein_sequence:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'protein_sequence is required'
                })
            }
        
        # Initialize proteomics agent
        agent = ProteomicsAgent()
        
        # Analyze protein
        results = agent.analyze_protein(protein_sequence, protein_id)
        
        # Return results
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'proteomics_results': results.to_dict(),
                'agent': 'ProteomicsAgent'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in proteomics agent handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'agent': 'ProteomicsAgent'
            })
        }
