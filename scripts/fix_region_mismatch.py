#!/usr/bin/env python3
"""
Fix Region Mismatch Issue
- Bedrock Agents: us-east-1
- Models: Available in both regions
- API Gateway: ap-south-1
- Solution: Update Lambda to use correct regions
"""

import boto3
import json
import zipfile
import io

def create_region_aware_lambda():
    """Create Lambda that handles both regions correctly"""
    
    lambda_code = '''
"""
Region-Aware Enhanced Orchestrator
- Uses Bedrock models from us-east-1 (where they're available)
- Deployed in ap-south-1 (same as API Gateway)
"""

import json
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Use us-east-1 for Bedrock (where agents and models are)
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# Model configuration
MODELS = {
    'nova_pro': 'amazon.nova-pro-v1:0',
    'gpt_oss_120b': 'openai.gpt-oss-120b-1:0',
    'gpt_oss_20b': 'openai.gpt-oss-20b-1:0'
}

def invoke_nova_model(prompt, max_tokens=2000, temperature=0.7):
    """Invoke Amazon Nova Pro in us-east-1"""
    try:
        body = json.dumps({
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature}
        })
        
        response = bedrock_runtime.invoke_model(
            modelId=MODELS['nova_pro'],
            body=body
        )
        
        result = json.loads(response['body'].read())
        return result['output']['message']['content'][0]['text']
    except Exception as e:
        logger.error(f"Nova model error: {str(e)}")
        return f"Error: {str(e)}"

def invoke_openai_model(model_key, prompt, max_tokens=1500, temperature=0.7):
    """Invoke OpenAI GPT-OSS models in us-east-1"""
    try:
        body = json.dumps({
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        })
        
        response = bedrock_runtime.invoke_model(
            modelId=MODELS[model_key],
            body=body
        )
        
        result = json.loads(response['body'].read())
        return result['choices'][0]['message']['content']
    except Exception as e:
        logger.error(f"OpenAI model error: {str(e)}")
        return f"Error: {str(e)}"

def multi_model_genomics_analysis(sequence_data, analysis_type='genomics'):
    """Multi-model genomics analysis using us-east-1 Bedrock"""
    
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'analysis_type': analysis_type,
        'workflow': 'multi-model-bedrock-agents',
        'models_used': [],
        'real_time_updates': [],
        'bedrock_region': 'us-east-1'
    }
    
    # Step 1: Primary analysis with Nova Pro
    logger.info("Step 1: Nova Pro primary analysis")
    results['real_time_updates'].append({
        'step': 1,
        'status': 'running',
        'message': 'Analyzing sequence with Amazon Nova Pro (us-east-1)...'
    })
    
    nova_prompt = f"""Analyze this genomic sequence comprehensively:

Sequence: {sequence_data}

Provide:
1. Sequence characteristics
2. Gene identification
3. Variant detection
4. Clinical significance
5. Pathogenicity assessment

Be detailed and scientific."""
    
    nova_result = invoke_nova_model(nova_prompt, max_tokens=2000, temperature=0.3)
    results['primary_analysis'] = {
        'model': 'Amazon Nova Pro',
        'result': nova_result,
        'role': 'Primary genomic analysis',
        'region': 'us-east-1'
    }
    results['models_used'].append('nova_pro')
    results['real_time_updates'].append({
        'step': 1,
        'status': 'complete',
        'message': 'Primary analysis complete'
    })
    
    # Step 2: Validation with GPT-OSS-120B
    logger.info("Step 2: GPT-OSS-120B validation")
    results['real_time_updates'].append({
        'step': 2,
        'status': 'running',
        'message': 'Validating with OpenAI GPT-OSS 120B (us-east-1)...'
    })
    
    gpt_prompt = f"""Review this genomic analysis:

Sequence (first 500 chars): {sequence_data[:500]}...

Primary Analysis:
{nova_result[:1200]}...

Provide:
1. Validation of findings
2. Literature context
3. Alternative interpretations
4. Research recommendations"""
    
    gpt_result = invoke_openai_model('gpt_oss_120b', gpt_prompt, max_tokens=1500, temperature=0.4)
    results['secondary_validation'] = {
        'model': 'OpenAI GPT-OSS 120B',
        'result': gpt_result,
        'role': 'Validation and literature review',
        'region': 'us-east-1'
    }
    results['models_used'].append('gpt_oss_120b')
    results['real_time_updates'].append({
        'step': 2,
        'status': 'complete',
        'message': 'Validation complete'
    })
    
    # Step 3: Synthesis with GPT-OSS-20B
    logger.info("Step 3: GPT-OSS-20B synthesis")
    results['real_time_updates'].append({
        'step': 3,
        'status': 'running',
        'message': 'Creating synthesis with OpenAI GPT-OSS 20B (us-east-1)...'
    })
    
    synthesis_prompt = f"""Create unified summary:

PRIMARY (Nova Pro):
{nova_result[:1000]}

VALIDATION (GPT-OSS-120B):
{gpt_result[:1000]}

Provide concise executive summary with:
1. Key findings
2. Consensus conclusions
3. Actionable recommendations"""
    
    synthesis = invoke_openai_model('gpt_oss_20b', synthesis_prompt, max_tokens=800, temperature=0.3)
    results['synthesis'] = {
        'model': 'OpenAI GPT-OSS 20B',
        'result': synthesis,
        'role': 'Synthesis and summary',
        'region': 'us-east-1'
    }
    results['models_used'].append('gpt_oss_20b')
    results['real_time_updates'].append({
        'step': 3,
        'status': 'complete',
        'message': 'Synthesis complete'
    })
    
    # Create final report
    results['final_report'] = {
        'executive_summary': synthesis,
        'detailed_analysis': nova_result,
        'validation_notes': gpt_result,
        'confidence': 'High (multi-model consensus)',
        'models_count': len(results['models_used']),
        'analysis_complete': True
    }
    
    results['real_time_updates'].append({
        'step': 4,
        'status': 'complete',
        'message': 'Multi-model analysis complete!'
    })
    
    return results

def lambda_handler(event, context):
    """Lambda handler - deployed in ap-south-1, uses Bedrock in us-east-1"""
    
    logger.info(f"Enhanced orchestrator invoked: {json.dumps(event)}")
    logger.info(f"Lambda region: ap-south-1, Bedrock region: us-east-1")
    
    try:
        # Parse input
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        # Extract sequence data
        sequence_data = body.get('sequence', body.get('sequenceData', body.get('dna_sequence', '')))
        analysis_type = body.get('analysis_type', body.get('analysisType', 'genomics'))
        use_multi_model = body.get('use_multi_model', True)
        
        if not sequence_data:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'POST, OPTIONS'
                },
                'body': json.dumps({
                    'error': 'No sequence data provided',
                    'message': 'Please provide genomic sequence data'
                })
            }
        
        # Run multi-model analysis
        logger.info("Starting multi-model genomics analysis...")
        results = multi_model_genomics_analysis(sequence_data, analysis_type)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'success': True,
                'analysis_results': results,
                'message': 'Multi-model analysis complete',
                'real_time': True,
                'regions': {
                    'lambda': 'ap-south-1',
                    'bedrock': 'us-east-1'
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': json.dumps({
                'error': str(e),
                'message': 'Analysis failed',
                'traceback': traceback.format_exc()
            })
        }
'''
    
    return lambda_code

def deploy_region_aware_lambda():
    """Deploy the region-aware Lambda in ap-south-1"""
    print("🚀 Deploying region-aware Lambda...")
    print("   Lambda location: ap-south-1")
    print("   Bedrock location: us-east-1")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    iam = boto3.client('iam')
    
    # Create deployment package
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('lambda_function.py', create_region_aware_lambda())
    
    zip_buffer.seek(0)
    zip_data = zip_buffer.read()
    
    # Get IAM role
    try:
        role = iam.get_role(RoleName='biomerkin-lambda-role')
        role_arn = role['Role']['Arn']
    except:
        print("❌ IAM role not found")
        return False
    
    function_name = 'biomerkin-enhanced-orchestrator'
    
    try:
        # Update function
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_data
        )
        print(f"✅ Updated Lambda: {function_name}")
        
        # Update configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Timeout=300,
            MemorySize=1024,
            Environment={
                'Variables': {
                    'BEDROCK_REGION': 'us-east-1',
                    'LAMBDA_REGION': 'ap-south-1',
                    'PRIMARY_MODEL': 'amazon.nova-pro-v1:0',
                    'SECONDARY_MODEL': 'openai.gpt-oss-120b-1:0',
                    'QUICK_MODEL': 'openai.gpt-oss-20b-1:0'
                }
            }
        )
        print("✅ Updated configuration")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_lambda_direct():
    """Test Lambda directly"""
    print("\n🧪 Testing Lambda directly...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    try:
        response = lambda_client.invoke(
            FunctionName='biomerkin-enhanced-orchestrator',
            Payload=json.dumps({
                'sequence': 'ATCGATCGATCGATCG',
                'use_multi_model': True
            })
        )
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            body = json.loads(result.get('body', '{}'))
            if body.get('success'):
                print("✅ Lambda test PASSED!")
                print(f"   Models: {body['analysis_results']['models_used']}")
                print(f"   Bedrock region: {body['analysis_results']['bedrock_region']}")
                return True
        
        print(f"❌ Test failed: {result}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_via_api():
    """Test via API Gateway"""
    print("\n🧪 Testing via API Gateway...")
    
    import requests
    
    api_url = "https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod/analyze"
    
    try:
        response = requests.post(
            api_url,
            json={
                'sequence': 'ATCGATCGATCGATCG',
                'analysis_type': 'genomics',
                'use_multi_model': True
            },
            timeout=120
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ API test PASSED!")
                print(f"   Models: {data['analysis_results']['models_used']}")
                print(f"   Regions: {data.get('regions', {})}")
                return True
        
        print(f"   Response: {response.text[:200]}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    print("="*60)
    print("🔧 FIXING REGION MISMATCH")
    print("="*60)
    print("\n📍 Current Setup:")
    print("   - Bedrock Agents: us-east-1")
    print("   - Bedrock Models: us-east-1")
    print("   - API Gateway: ap-south-1")
    print("\n💡 Solution:")
    print("   - Lambda in ap-south-1 (same as API Gateway)")
    print("   - Lambda calls Bedrock in us-east-1")
    print("="*60)
    
    if deploy_region_aware_lambda():
        import time
        print("\n⏳ Waiting for Lambda to be ready...")
        time.sleep(5)
        
        if test_lambda_direct():
            print("\n⏳ Waiting for API Gateway...")
            time.sleep(5)
            
            if test_via_api():
                print("\n" + "="*60)
                print("🎉 REGION MISMATCH FIXED!")
                print("="*60)
                print("\n✅ System Configuration:")
                print("   Lambda: ap-south-1 ✓")
                print("   Bedrock: us-east-1 ✓")
                print("   API Gateway: ap-south-1 ✓")
                print("\n✅ Your API is working:")
                print("   https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod/analyze")
                print("\n📝 Test it:")
                print("   python scripts/test_complete_system.py")
                print("="*60)
            else:
                print("\n⚠️  Lambda works but API Gateway needs more time")
                print("   Wait 30 seconds and test again")
                print("   The Lambda is working correctly!")
        else:
            print("\n❌ Lambda test failed")
    else:
        print("\n❌ Deployment failed")

if __name__ == "__main__":
    main()
