"""
Lambda handler for Genomics Agent.
Analyzes DNA sequences for genes, mutations, and protein translations.
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
from biomerkin.agents.genomics_agent import GenomicsAgent
from biomerkin.models.genomics import GenomicsResults


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for genomics analysis.
    
    Args:
        event: Lambda event containing sequence data
        context: Lambda context
        
    Returns:
        Response dictionary with genomics results
    """
    logger.info(f"Genomics Agent Lambda invoked with event: {json.dumps(event)}")
    
    try:
        # Extract parameters
        sequence_file = event.get('sequence_file')
        sequence_data = event.get('sequence_data')
        
        if not sequence_file and not sequence_data:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Either sequence_file or sequence_data is required'
                })
            }
        
        # Initialize genomics agent
        agent = GenomicsAgent()
        
        # Analyze sequence
        if sequence_data:
            # Direct sequence analysis
            results = agent.analyze_sequence_data(sequence_data)
        else:
            # File-based analysis
            results = agent.analyze_sequence(sequence_file)
        
        # Return results
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'genomics_results': results.to_dict(),
                'agent': 'GenomicsAgent'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in genomics agent handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'agent': 'GenomicsAgent'
            })
        }
