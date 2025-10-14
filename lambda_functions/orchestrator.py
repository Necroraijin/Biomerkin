"""
Lambda handler for Biomerkin Orchestrator.
Coordinates multi-agent bioinformatics analysis workflow.
"""

import json
import asyncio
import os
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import Biomerkin modules
import sys
sys.path.append('/opt/python')
from biomerkin.services.orchestrator import WorkflowOrchestrator
from biomerkin.models import WorkflowState, AnalysisResults
from biomerkin.utils.logging_config import get_logger


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for orchestrator workflow.
    
    Args:
        event: Lambda event containing workflow parameters
        context: Lambda context
        
    Returns:
        Response dictionary with workflow results
    """
    logger.info(f"Orchestrator Lambda invoked with event: {json.dumps(event)}")
    
    try:
        # Extract workflow parameters
        workflow_id = event.get('workflow_id', f"workflow_{context.aws_request_id}")
        sequence_file = event.get('sequence_file')
        
        if not sequence_file:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'sequence_file is required',
                    'workflow_id': workflow_id
                })
            }
        
        # Create workflow state
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            status="running",
            input_data={
                'sequence_file': sequence_file,
                'max_articles': event.get('max_articles', 20)
            }
        )
        
        # Initialize orchestrator
        orchestrator = WorkflowOrchestrator()
        
        # Run workflow
        result = asyncio.run(orchestrator.execute_workflow(workflow_state))
        
        # Return results
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': result.success,
                'workflow_id': result.workflow_id,
                'results': result.results.to_dict() if result.results else None,
                'error_message': result.error_message,
                'warnings': result.warnings
            })
        }
        
    except Exception as e:
        logger.error(f"Error in orchestrator handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'workflow_id': workflow_id
            })
        }
