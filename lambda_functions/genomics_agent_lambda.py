"""
AWS Lambda function for Bedrock Agent genomics analysis actions.
This serves as the action group executor for genomics-related functions.
"""

import json
import logging
from typing import Dict, Any
from biomerkin.agents.genomics_agent import GenomicsAgent
from biomerkin.services.bedrock_agent_service import BedrockAgentService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Lambda handler for Bedrock Agent genomics actions.
    
    This function is called by Bedrock Agents to perform genomics analysis.
    It demonstrates autonomous capabilities and reasoning.
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Parse the action from Bedrock Agent
        action_group = event.get('actionGroup', '')
        api_path = event.get('apiPath', '')
        http_method = event.get('httpMethod', '')
        request_body = event.get('requestBody', {})
        
        # Initialize genomics agent
        genomics_agent = GenomicsAgent()
        
        # Route to appropriate function based on API path
        if api_path == '/analyze-sequence':
            return handle_analyze_sequence(request_body, genomics_agent)
        elif api_path == '/interpret-variant':
            return handle_interpret_variant(request_body, genomics_agent)
        else:
            return create_error_response(f"Unknown API path: {api_path}")
            
    except Exception as e:
        logger.error(f"Error in lambda handler: {str(e)}")
        return create_error_response(str(e))

def handle_analyze_sequence(request_body: Dict[str, Any], genomics_agent: GenomicsAgent) -> Dict[str, Any]:
    """Handle DNA sequence analysis request."""
    try:
        # Extract parameters
        content = request_body.get('content', {})
        sequence = content.get('sequence', '')
        reference_genome = content.get('reference_genome', 'GRCh38')
        
        if not sequence:
            return create_error_response("DNA sequence is required")
        
        # Perform genomics analysis
        results = genomics_agent.analyze_sequence(sequence)
        
        # Format response for Bedrock Agent
        response_body = {
            'genes': [gene.to_dict() for gene in results.genes],
            'variants': [mutation.to_dict() for mutation in results.mutations],
            'clinical_significance': {
                'total_variants': len(results.mutations),
                'quality_score': results.quality_metrics.quality_score,
                'analysis_timestamp': results.analysis_timestamp or 'unknown'
            }
        }
        
        return create_success_response(response_body)
        
    except Exception as e:
        logger.error(f"Error in analyze_sequence: {str(e)}")
        return create_error_response(str(e))

def handle_interpret_variant(request_body: Dict[str, Any], genomics_agent: GenomicsAgent) -> Dict[str, Any]:
    """Handle variant interpretation request."""
    try:
        # Extract parameters
        content = request_body.get('content', {})
        variant = content.get('variant', '')
        gene = content.get('gene', '')
        
        if not variant or not gene:
            return create_error_response("Both variant and gene are required")
        
        # Perform variant interpretation (simplified for demo)
        interpretation = {
            'classification': 'Variant of Uncertain Significance',
            'evidence': [
                'Computational prediction suggests possible impact',
                'Limited population frequency data available',
                'No strong functional studies found'
            ],
            'clinical_significance': 'Uncertain - requires additional evidence'
        }
        
        return create_success_response(interpretation)
        
    except Exception as e:
        logger.error(f"Error in interpret_variant: {str(e)}")
        return create_error_response(str(e))

def create_success_response(body: Dict[str, Any]) -> Dict[str, Any]:
    """Create successful response for Bedrock Agent."""
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'GenomicsAnalysis',
            'apiPath': '/analyze-sequence',
            'httpMethod': 'POST',
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(body)
                }
            }
        }
    }

def create_error_response(error_message: str) -> Dict[str, Any]:
    """Create error response for Bedrock Agent."""
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'GenomicsAnalysis',
            'httpStatusCode': 400,
            'responseBody': {
                'application/json': {
                    'body': json.dumps({'error': error_message})
                }
            }
        }
    }