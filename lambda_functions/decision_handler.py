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
    """AWS Lambda handler for Decision Agent."""
    
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
        
        # Mock decision analysis
        medical_report = {
            "patient_id": "DEMO_001",
            "analysis_summary": "Comprehensive genomic analysis identified pathogenic BRCA1 variant with high clinical significance.",
            "risk_assessment": {
                "overall_risk": "HIGH",
                "cancer_risk": "80% lifetime breast cancer risk",
                "confidence": 0.95
            },
            "recommendations": [
                "Immediate genetic counseling recommended",
                "Enhanced screening protocols advised", 
                "PARP inhibitor therapy consideration",
                "Family cascade testing recommended"
            ],
            "treatment_options": [
                {
                    "name": "PARP Inhibitor Therapy",
                    "effectiveness": 0.85,
                    "description": "Olaparib or Talazoparib for BRCA1-mutated cancers"
                },
                {
                    "name": "Enhanced Surveillance",
                    "effectiveness": 0.90,
                    "description": "Annual MRI and mammography screening"
                }
            ]
        }
        
        response = {
            "statusCode": 200,
            "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
            "body": json.dumps({
                "success": True,
                "message": "Medical decision analysis completed",
                "medical_report": medical_report,
                "agent": "DecisionAgent",
                "timestamp": "2025-10-14T23:00:00Z"
            })
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Error in decision analysis: {str(e)}")
        
        return {
            "statusCode": 500,
            "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
            "body": json.dumps({
                "success": False,
                "error": str(e),
                "agent": "DecisionAgent"
            })
        }