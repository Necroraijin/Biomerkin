import json
import logging

# CORS Headers for all responses
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
}

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Lambda handler for Genomics Agent.
    """
    
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
            # API Gateway format
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            input_data = body.get('input_data', {})
        else:
            # Direct Lambda invocation
            input_data = event.get('input_data', {})
        
        # Get sequence data
        sequence_data = input_data.get('sequence_data', '')
        reference_genome = input_data.get('reference_genome', 'GRCh38')
        
        logger.info(f"Processing sequence: {sequence_data[:50]}...")
        
        # Mock genomics analysis (replace with real analysis)
        analysis_results = {
            "genes_identified": [
                {
                    "name": "BRCA1",
                    "location": "chr17:43044295-43125483",
                    "function": "DNA repair",
                    "confidence": 0.95
                },
                {
                    "name": "TP53", 
                    "location": "chr17:7661779-7687550",
                    "function": "Tumor suppressor",
                    "confidence": 0.92
                }
            ],
            "variants_detected": [
                {
                    "gene": "BRCA1",
                    "variant": "c.5266dupC",
                    "type": "frameshift",
                    "significance": "pathogenic",
                    "confidence": 0.94
                }
            ],
            "sequence_length": len(sequence_data),
            "reference_genome": reference_genome,
            "analysis_time": "2.3 minutes",
            "confidence_score": 0.94
        }
        
        # Return success response
        response = {
            "statusCode": 200,
            "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
            "body": json.dumps({
                "success": True,
                "message": "Genomics analysis completed successfully",
                "genomics_results": analysis_results,
                "agent": "GenomicsAgent",
                "timestamp": "2025-10-14T23:00:00Z"
            })
        }
        
        logger.info("Genomics analysis completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error in genomics analysis: {str(e)}")
        
        error_response = {
            "statusCode": 500,
            "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
            "body": json.dumps({
                "success": False,
                "error": str(e),
                "message": "Genomics analysis failed",
                "agent": "GenomicsAgent"
            })
        }
        
        return error_response