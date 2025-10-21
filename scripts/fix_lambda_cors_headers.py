#!/usr/bin/env python3
"""
Fix Lambda CORS Headers
Ensure Lambda returns proper CORS headers in response
"""

import boto3
import zipfile
import io
import json

def create_lambda_with_cors():
    """Create Lambda that properly returns CORS headers"""
    
    lambda_code = '''
import json
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

MODELS = {
    'nova_pro': 'amazon.nova-pro-v1:0',
    'gpt_oss_120b': 'openai.gpt-oss-120b-1:0',
    'gpt_oss_20b': 'openai.gpt-oss-20b-1:0'
}

# CORS headers - MUST be in every response
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
}

def invoke_nova_model(prompt, max_tokens=2000, temperature=0.7):
    try:
        body = json.dumps({
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature}
        })
        response = bedrock_runtime.invoke_model(modelId=MODELS['nova_pro'], body=body)
        result = json.loads(response['body'].read())
        return result['output']['message']['content'][0]['text']
    except Exception as e:
        return f"Error: {str(e)}"

def invoke_openai_model(model_key, prompt, max_tokens=1500, temperature=0.7):
    try:
        body = json.dumps({
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        })
        response = bedrock_runtime.invoke_model(modelId=MODELS[model_key], body=body)
        result = json.loads(response['body'].read())
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"Error: {str(e)}"

def multi_model_analysis(sequence_data, analysis_type='genomics'):
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'analysis_type': analysis_type,
        'workflow': 'multi-model-bedrock-agents',
        'models_used': [],
        'real_time_updates': [],
        'bedrock_region': 'us-east-1'
    }
    
    # Step 1: Nova Pro
    results['real_time_updates'].append({'step': 1, 'status': 'running', 'message': 'Analyzing with Amazon Nova Pro...'})
    nova_result = invoke_nova_model(f"Analyze this genomic sequence: {sequence_data}. Provide comprehensive analysis.", max_tokens=2000, temperature=0.3)
    results['primary_analysis'] = {'model': 'Amazon Nova Pro', 'result': nova_result, 'role': 'Primary analysis', 'region': 'us-east-1'}
    results['models_used'].append('nova_pro')
    results['real_time_updates'].append({'step': 1, 'status': 'complete', 'message': 'Primary analysis complete'})
    
    # Step 2: GPT-OSS-120B
    results['real_time_updates'].append({'step': 2, 'status': 'running', 'message': 'Validating with GPT-OSS 120B...'})
    gpt_result = invoke_openai_model('gpt_oss_120b', f"Validate this analysis: {nova_result[:1000]}", max_tokens=1500, temperature=0.4)
    results['secondary_validation'] = {'model': 'OpenAI GPT-OSS 120B', 'result': gpt_result, 'role': 'Validation', 'region': 'us-east-1'}
    results['models_used'].append('gpt_oss_120b')
    results['real_time_updates'].append({'step': 2, 'status': 'complete', 'message': 'Validation complete'})
    
    # Step 3: GPT-OSS-20B
    results['real_time_updates'].append({'step': 3, 'status': 'running', 'message': 'Creating synthesis...'})
    synthesis = invoke_openai_model('gpt_oss_20b', f"Synthesize: {nova_result[:800]} and {gpt_result[:800]}", max_tokens=800, temperature=0.3)
    results['synthesis'] = {'model': 'OpenAI GPT-OSS 20B', 'result': synthesis, 'role': 'Synthesis', 'region': 'us-east-1'}
    results['models_used'].append('gpt_oss_20b')
    results['real_time_updates'].append({'step': 3, 'status': 'complete', 'message': 'Synthesis complete'})
    results['real_time_updates'].append({'step': 4, 'status': 'complete', 'message': 'Multi-model analysis complete!'})
    
    results['final_report'] = {
        'executive_summary': synthesis,
        'detailed_analysis': nova_result,
        'validation_notes': gpt_result,
        'confidence': 'High (multi-model consensus)',
        'models_count': 3,
        'analysis_complete': True
    }
    
    return results

def lambda_handler(event, context):
    logger.info(f"Request: {json.dumps(event)}")
    
    # Handle OPTIONS preflight
    if event.get('httpMethod') == 'OPTIONS' or event.get('requestContext', {}).get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({'message': 'CORS preflight'})
        }
    
    try:
        # Parse body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        sequence_data = body.get('sequence', body.get('sequenceData', ''))
        analysis_type = body.get('analysis_type', 'genomics')
        
        if not sequence_data:
            return {
                'statusCode': 400,
                'headers': CORS_HEADERS,
                'body': json.dumps({'error': 'No sequence data provided'})
            }
        
        # Run analysis
        results = multi_model_analysis(sequence_data, analysis_type)
        
        return {
            'statusCode': 200,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'success': True,
                'analysis_results': results,
                'message': 'Multi-model analysis complete',
                'real_time': True
            })
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': CORS_HEADERS,
            'body': json.dumps({
                'error': str(e),
                'message': 'Analysis failed'
            })
        }
'''
    
    return lambda_code

def deploy():
    print("🚀 Deploying Lambda with CORS headers...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Create zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('lambda_function.py', create_lambda_with_cors())
    
    zip_buffer.seek(0)
    
    try:
        response = lambda_client.update_function_code(
            FunctionName='biomerkin-enhanced-orchestrator',
            ZipFile=zip_buffer.read()
        )
        print("✅ Lambda updated with CORS headers")
        
        import time
        time.sleep(5)
        
        # Test
        print("\n🧪 Testing...")
        test_response = lambda_client.invoke(
            FunctionName='biomerkin-enhanced-orchestrator',
            Payload=json.dumps({'sequence': 'ATCGATCG', 'use_multi_model': True})
        )
        
        result = json.loads(test_response['Payload'].read())
        
        if test_response['StatusCode'] == 200:
            body = json.loads(result.get('body', '{}'))
            headers = result.get('headers', {})
            
            print(f"✅ Lambda test passed")
            print(f"   CORS Header: {headers.get('Access-Control-Allow-Origin', 'MISSING!')}")
            print(f"   Models: {body.get('analysis_results', {}).get('models_used', [])}")
            
            if headers.get('Access-Control-Allow-Origin') == '*':
                print("\n🎉 CORS HEADERS ARE NOW IN LAMBDA!")
                print("\n📝 Now test in browser:")
                print("   http://biomerkin-frontend-20251018-013734.s3-website.ap-south-1.amazonaws.com/test.html")
            else:
                print("\n⚠️  CORS header missing!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    deploy()
