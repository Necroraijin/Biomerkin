import json
import logging

# CORS Headers for all responses
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
}

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """AWS Lambda handler for Proteomics Agent."""
    
    # Handle OPTIONS request for CORS
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS
        }
    
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract input data
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            input_data = body.get('input_data', {})
        else:
            input_data = event.get('input_data', {})
        
        # Mock proteomics analysis
        analysis_results = {
            "protein_structures": [
                {
                    "name": "BRCA1",
                    "length": 1863,
                    "domains": ["RING", "BRCT1", "BRCT2"],
                    "confidence": 0.91
                }
            ],
            "functional_annotations": [
                {
                    "description": "DNA repair protein",
                    "confidence": 0.95,
                    "source": "UniProt"
                }
            ],
            "binding_sites": [
                {
                    "name": "DNA_binding",
                    "location": "residues 1560-1863",
                    "confidence": 0.88
                }
            ]
        }
        
        response = {
            "statusCode": 200,
            "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
            "body": json.dumps({
                "success": True,
                "message": "Proteomics analysis completed",
                "proteomics_results": analysis_results,
                "agent": "ProteomicsAgent",
                "timestamp": "2025-10-14T23:00:00Z"
            })
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in proteomics analysis: {str(e)}")
        
        return {
            "statusCode": 500,
            "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
            "body": json.dumps({
                "success": False,
                "error": str(e),
                "agent": "ProteomicsAgent"
            })
        }