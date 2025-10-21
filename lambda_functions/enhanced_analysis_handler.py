"""
Enhanced Lambda Handler for Genomics Analysis
Optimized for performance, accuracy, and AWS integration
"""

import json
import os
import boto3
import asyncio
from typing import Dict, Any
from datetime import datetime
import tempfile
import traceback

# CORS Headers for all responses
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
}

# AWS Service Clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime')
sns_client = boto3.client('sns')

# Environment Variables
WORKFLOWS_TABLE = os.environ.get('WORKFLOWS_TABLE', 'biomerkin-workflows')
RESULTS_BUCKET = os.environ.get('RESULTS_BUCKET', 'biomerkin-results')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', '')

# Import Biomerkin services (deployed as Lambda layer)
try:
    from biomerkin.services.enhanced_bedrock_service import get_enhanced_bedrock_service
    from biomerkin.services.dataset_validation_service import get_dataset_validation_service
    from biomerkin.agents.genomics_agent import GenomicsAgent
    from biomerkin.agents.proteomics_agent import ProteomicsAgent
    from biomerkin.agents.literature_agent import LiteratureAgent
    from biomerkin.agents.drug_agent import DrugAgent
    from biomerkin.agents.decision_agent import DecisionAgent
    BIOMERKIN_AVAILABLE = True
except ImportError:
    BIOMERKIN_AVAILABLE = False
    print("Warning: Biomerkin modules not available")


def lambda_handler(event, context):
    """
    Main Lambda handler for genomics analysis.
    
    Supports multiple invocation patterns:
    - API Gateway (HTTP)
    - Direct invoke (JSON)
    - S3 trigger
    - Step Functions
    """
    # Handle OPTIONS request for CORS
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS
        }
    
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Parse event based on source
        if 'httpMethod' in event:
            # API Gateway invocation
            return handle_api_gateway_request(event, context)
        elif 'Records' in event and event['Records'][0].get('eventSource') == 'aws:s3':
            # S3 trigger
            return handle_s3_trigger(event, context)
        else:
            # Direct invocation or Step Functions
            return handle_direct_invocation(event, context)
    
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        print(traceback.format_exc())
        return error_response(str(e), 500)


def handle_api_gateway_request(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle API Gateway HTTP request."""
    method = event['httpMethod']
    path = event['path']
    
    # Route to appropriate handler
    if method == 'POST' and '/validate' in path:
        return handle_validation_request(event, context)
    elif method == 'POST' and '/analyze' in path:
        return handle_analysis_request(event, context)
    elif method == 'GET' and '/status' in path:
        return handle_status_request(event, context)
    elif method == 'GET' and '/results' in path:
        return handle_results_request(event, context)
    else:
        return error_response('Endpoint not found', 404)


def handle_validation_request(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Validate uploaded dataset.
    Returns validation results without running analysis.
    """
    try:
        if not BIOMERKIN_AVAILABLE:
            return error_response('Biomerkin services not available', 500)
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        file_key = body.get('file_key')
        bucket = body.get('bucket', RESULTS_BUCKET)
        
        if not file_key:
            return error_response('file_key is required', 400)
        
        # Download file from S3
        with tempfile.NamedTemporaryFile(delete=False, suffix='.fasta') as tmp_file:
            s3_client.download_fileobj(bucket, file_key, tmp_file)
            temp_path = tmp_file.name
        
        try:
            # Validate dataset
            validation_service = get_dataset_validation_service()
            validation_result = validation_service.validate_dataset(temp_path)
            
            # Generate quality report
            quality_report = validation_service.generate_quality_report(validation_result)
            validation_result['quality_report'] = quality_report
            
            return success_response({
                'validation': validation_result,
                'message': 'Dataset validated successfully'
            })
        
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        print(f"Validation error: {str(e)}")
        return error_response(f'Validation failed: {str(e)}', 500)


def handle_analysis_request(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Start analysis workflow.
    Returns workflow ID for tracking.
    """
    try:
        if not BIOMERKIN_AVAILABLE:
            return error_response('Biomerkin services not available', 500)
        
        # Parse request
        body = json.loads(event.get('body', '{}'))
        file_key = body.get('file_key')
        bucket = body.get('bucket', RESULTS_BUCKET)
        workflow_id = body.get('workflow_id', f'workflow-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}')
        options = body.get('options', {})
        
        if not file_key:
            return error_response('file_key is required', 400)
        
        # Download file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.fasta') as tmp_file:
            s3_client.download_fileobj(bucket, file_key, tmp_file)
            temp_path = tmp_file.name
        
        try:
            # Initialize workflow state
            workflow_state = {
                'workflow_id': workflow_id,
                'status': 'running',
                'progress': 0,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat(),
                'input_file': file_key,
                'options': options
            }
            
            # Save initial state
            save_workflow_state(workflow_id, workflow_state)
            
            # Run analysis
            results = run_comprehensive_analysis(temp_path, workflow_id, options)
            
            # Update workflow with results
            workflow_state['status'] = 'completed'
            workflow_state['progress'] = 100
            workflow_state['results'] = results
            workflow_state['completed_at'] = datetime.utcnow().isoformat()
            workflow_state['updated_at'] = datetime.utcnow().isoformat()
            
            save_workflow_state(workflow_id, workflow_state)
            
            # Upload results to S3
            results_key = f'results/{workflow_id}/analysis_results.json'
            s3_client.put_object(
                Bucket=RESULTS_BUCKET,
                Key=results_key,
                Body=json.dumps(results, indent=2),
                ContentType='application/json'
            )
            
            # Send notification if configured
            if SNS_TOPIC_ARN:
                send_completion_notification(workflow_id, 'completed')
            
            return success_response({
                'workflow_id': workflow_id,
                'status': 'completed',
                'results_key': results_key,
                'message': 'Analysis completed successfully'
            })
        
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        print(traceback.format_exc())
        
        # Update workflow with error
        try:
            workflow_state = {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e),
                'updated_at': datetime.utcnow().isoformat()
            }
            save_workflow_state(workflow_id, workflow_state)
            
            if SNS_TOPIC_ARN:
                send_completion_notification(workflow_id, 'failed', str(e))
        except:
            pass
        
        return error_response(f'Analysis failed: {str(e)}', 500)


def handle_status_request(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Get workflow status."""
    try:
        # Extract workflow ID from path parameters
        workflow_id = event.get('pathParameters', {}).get('workflowId')
        
        if not workflow_id:
            return error_response('workflow_id is required', 400)
        
        # Load workflow state
        workflow_state = load_workflow_state(workflow_id)
        
        if not workflow_state:
            return error_response('Workflow not found', 404)
        
        return success_response(workflow_state)
    
    except Exception as e:
        print(f"Status request error: {str(e)}")
        return error_response(f'Failed to get status: {str(e)}', 500)


def handle_results_request(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Get workflow results."""
    try:
        workflow_id = event.get('pathParameters', {}).get('workflowId')
        
        if not workflow_id:
            return error_response('workflow_id is required', 400)
        
        # Load workflow state
        workflow_state = load_workflow_state(workflow_id)
        
        if not workflow_state:
            return error_response('Workflow not found', 404)
        
        if workflow_state['status'] != 'completed':
            return error_response('Workflow not completed', 400)
        
        # Get results from S3
        results_key = f'results/{workflow_id}/analysis_results.json'
        try:
            response = s3_client.get_object(Bucket=RESULTS_BUCKET, Key=results_key)
            results = json.loads(response['Body'].read())
            return success_response(results)
        except s3_client.exceptions.NoSuchKey:
            # Fallback to workflow state results
            return success_response(workflow_state.get('results', {}))
    
    except Exception as e:
        print(f"Results request error: {str(e)}")
        return error_response(f'Failed to get results: {str(e)}', 500)


def handle_direct_invocation(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle direct Lambda invocation or Step Functions."""
    try:
        sequence_file = event.get('sequence_file')
        workflow_id = event.get('workflow_id', f'workflow-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}')
        options = event.get('options', {})
        
        if not sequence_file:
            return {'error': 'sequence_file is required'}
        
        # Run analysis
        results = run_comprehensive_analysis(sequence_file, workflow_id, options)
        
        return {
            'statusCode': 200,
            'workflow_id': workflow_id,
            'results': results
        }
    
    except Exception as e:
        return {'error': str(e)}


def handle_s3_trigger(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle S3 object creation trigger."""
    try:
        # Extract S3 information
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        workflow_id = f'workflow-s3-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}'
        
        print(f"Processing S3 object: s3://{bucket}/{key}")
        
        # Download file
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            s3_client.download_fileobj(bucket, key, tmp_file)
            temp_path = tmp_file.name
        
        try:
            # Run analysis
            results = run_comprehensive_analysis(temp_path, workflow_id, {})
            
            # Upload results
            results_key = f'results/{workflow_id}/analysis_results.json'
            s3_client.put_object(
                Bucket=bucket,
                Key=results_key,
                Body=json.dumps(results, indent=2),
                ContentType='application/json'
            )
            
            return {
                'statusCode': 200,
                'workflow_id': workflow_id,
                'results_key': results_key
            }
        
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except Exception as e:
        print(f"S3 trigger error: {str(e)}")
        return {'error': str(e)}


def run_comprehensive_analysis(
    sequence_file: str,
    workflow_id: str,
    options: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run comprehensive multi-agent analysis.
    
    Args:
        sequence_file: Path to sequence file
        workflow_id: Workflow identifier
        options: Analysis options
        
    Returns:
        Complete analysis results
    """
    results = {
        'workflow_id': workflow_id,
        'started_at': datetime.utcnow().isoformat(),
        'analysis_steps': []
    }
    
    try:
        # Step 1: Genomics Analysis
        print("Running genomics analysis...")
        update_progress(workflow_id, 10, 'genomics')
        genomics_agent = GenomicsAgent()
        genomics_results = genomics_agent.analyze_sequence(sequence_file=sequence_file)
        results['genomics'] = genomics_results.__dict__ if hasattr(genomics_results, '__dict__') else genomics_results
        results['analysis_steps'].append({'step': 'genomics', 'status': 'completed'})
        
        # Step 2: Proteomics Analysis
        if genomics_results.proteins:
            print("Running proteomics analysis...")
            update_progress(workflow_id, 30, 'proteomics')
            proteomics_agent = ProteomicsAgent()
            protein_results = []
            for protein in genomics_results.proteins[:5]:  # Limit to first 5 for Lambda timeout
                try:
                    result = proteomics_agent.analyze_protein(protein_sequence=protein.sequence)
                    protein_results.append(result.__dict__ if hasattr(result, '__dict__') else result)
                except Exception as e:
                    print(f"Proteomics error for protein: {str(e)}")
            results['proteomics'] = protein_results
            results['analysis_steps'].append({'step': 'proteomics', 'status': 'completed'})
        
        # Step 3: Literature Analysis (using Bedrock)
        print("Running literature analysis...")
        update_progress(workflow_id, 50, 'literature')
        try:
            bedrock_service = get_enhanced_bedrock_service()
            literature_summary = asyncio.run(bedrock_service.summarize_literature(
                articles=[],  # Placeholder - would integrate with PubMed API
                focus_areas=['genomics', 'precision medicine']
            ))
            results['literature'] = literature_summary
            results['analysis_steps'].append({'step': 'literature', 'status': 'completed'})
        except Exception as e:
            print(f"Literature analysis error: {str(e)}")
            results['literature'] = {'error': str(e)}
        
        # Step 4: Medical Report Generation
        print("Generating medical report...")
        update_progress(workflow_id, 80, 'decision')
        try:
            bedrock_service = get_enhanced_bedrock_service()
            medical_report = asyncio.run(bedrock_service.generate_medical_report(
                genomics_data=results.get('genomics', {}),
                proteomics_data=results.get('proteomics', {}),
                literature_data=results.get('literature', {}),
                drug_data={},
                patient_context=options.get('patient_context')
            ))
            results['medical_report'] = medical_report
            results['analysis_steps'].append({'step': 'decision', 'status': 'completed'})
        except Exception as e:
            print(f"Medical report error: {str(e)}")
            results['medical_report'] = {'error': str(e)}
        
        results['completed_at'] = datetime.utcnow().isoformat()
        results['status'] = 'success'
        update_progress(workflow_id, 100, 'completed')
        
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        results['error'] = str(e)
        results['status'] = 'failed'
        raise
    
    return results


def save_workflow_state(workflow_id: str, state: Dict[str, Any]):
    """Save workflow state to DynamoDB."""
    try:
        table = dynamodb.Table(WORKFLOWS_TABLE)
        table.put_item(Item=state)
    except Exception as e:
        print(f"Error saving workflow state: {str(e)}")


def load_workflow_state(workflow_id: str) -> Dict[str, Any]:
    """Load workflow state from DynamoDB."""
    try:
        table = dynamodb.Table(WORKFLOWS_TABLE)
        response = table.get_item(Key={'workflow_id': workflow_id})
        return response.get('Item')
    except Exception as e:
        print(f"Error loading workflow state: {str(e)}")
        return None


def update_progress(workflow_id: str, progress: int, current_step: str):
    """Update workflow progress."""
    try:
        table = dynamodb.Table(WORKFLOWS_TABLE)
        table.update_item(
            Key={'workflow_id': workflow_id},
            UpdateExpression='SET progress = :p, current_step = :s, updated_at = :u',
            ExpressionAttributeValues={
                ':p': progress,
                ':s': current_step,
                ':u': datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        print(f"Error updating progress: {str(e)}")


def send_completion_notification(workflow_id: str, status: str, error: str = None):
    """Send SNS notification on workflow completion."""
    try:
        message = {
            'workflow_id': workflow_id,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        if error:
            message['error'] = error
        
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f'Biomerkin Analysis {status.upper()}: {workflow_id}',
            Message=json.dumps(message, indent=2)
        )
    except Exception as e:
        print(f"Error sending notification: {str(e)}")


def success_response(data: Any) -> Dict[str, Any]:
    """Create successful API Gateway response."""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(data)
    }


def error_response(message: str, status_code: int = 500) -> Dict[str, Any]:
    """Create error API Gateway response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps({'error': message})
    }

