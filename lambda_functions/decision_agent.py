"""
Lambda handler for Decision Agent.
Generates comprehensive medical reports and treatment recommendations.
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
from biomerkin.agents.decision_agent import DecisionAgent
from biomerkin.models.medical import MedicalReport


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for decision analysis and report generation.
    
    Args:
        event: Lambda event containing all analysis results
        context: Lambda context
        
    Returns:
        Response dictionary with medical report
    """
    logger.info(f"Decision Agent Lambda invoked with event: {json.dumps(event)}")
    
    try:
        # Extract parameters
        genomics_results = event.get('genomics_results')
        proteomics_results = event.get('proteomics_results')
        literature_results = event.get('literature_results')
        drug_results = event.get('drug_results')
        patient_id = event.get('patient_id', 'anonymous')
        
        if not genomics_results:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'genomics_results is required'
                })
            }
        
        # Initialize decision agent
        agent = DecisionAgent()
        
        # Generate medical report
        report = agent.generate_medical_report(
            genomics_results=genomics_results,
            proteomics_results=proteomics_results,
            literature_results=literature_results,
            drug_results=drug_results,
            patient_id=patient_id
        )
        
        # Return results
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'medical_report': report.to_dict(),
                'agent': 'DecisionAgent'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in decision agent handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'agent': 'DecisionAgent'
            })
        }
