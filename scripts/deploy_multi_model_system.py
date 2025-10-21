#!/usr/bin/env python3
"""
Deploy Multi-Model System: Amazon Nova Pro + OpenAI GPT-OSS
Uses both models for enhanced genomics analysis
"""

import boto3
import json
from botocore.exceptions import ClientError

# Model Configuration
MODELS = {
    'nova_pro': {
        'id': 'amazon.nova-pro-v1:0',
        'name': 'Amazon Nova Pro',
        'use_case': 'Primary analysis, complex reasoning',
        'strengths': ['Medical analysis', 'Long context', 'Multimodal']
    },
    'gpt_oss_120b': {
        'id': 'openai.gpt-oss-120b-1:0',
        'name': 'OpenAI GPT-OSS 120B',
        'use_case': 'Secondary validation, literature review',
        'strengths': ['Large parameter count', 'General knowledge', 'Fast inference']
    },
    'gpt_oss_20b': {
        'id': 'openai.gpt-oss-20b-1:0',
        'name': 'OpenAI GPT-OSS 20B',
        'use_case': 'Quick queries, simple tasks',
        'strengths': ['Fast', 'Cost-effective', 'Good for simple tasks']
    }
}

def test_model_access(model_id, model_name):
    """Test if a model is accessible"""
    print(f"\n🧪 Testing {model_name}...")
    
    try:
        bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        body = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": "Respond with 'OK' if you can process this."}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 10,
                "temperature": 0.1
            }
        })
        
        response = bedrock.invoke_model(
            modelId=model_id,
            body=body
        )
        
        result = json.loads(response['body'].read())
        print(f"✅ {model_name} is accessible and working!")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print(f"❌ Access denied to {model_name}")
            print(f"   Request access in Bedrock console")
        else:
            print(f"❌ Error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def create_multi_model_orchestrator():
    """Create Lambda function that orchestrates multiple models"""
    
    lambda_code = '''
import json
import boto3
import os
from datetime import datetime

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# Model configuration
MODELS = {
    'nova_pro': 'amazon.nova-pro-v1:0',
    'gpt_oss_120b': 'openai.gpt-oss-120b-1:0',
    'gpt_oss_20b': 'openai.gpt-oss-20b-1:0'
}

def invoke_model(model_id, prompt, max_tokens=2000, temperature=0.7):
    """Invoke a Bedrock model"""
    try:
        body = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature
            }
        })
        
        response = bedrock.invoke_model(
            modelId=model_id,
            body=body
        )
        
        result = json.loads(response['body'].read())
        return result['output']['message']['content'][0]['text']
        
    except Exception as e:
        return f"Error invoking {model_id}: {str(e)}"

def multi_model_analysis(sequence_data, analysis_type):
    """
    Use multiple models for comprehensive analysis
    - Nova Pro: Primary deep analysis
    - GPT-OSS-120B: Secondary validation and literature context
    """
    
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'analysis_type': analysis_type,
        'models_used': []
    }
    
    # Step 1: Primary analysis with Nova Pro
    print("Running primary analysis with Nova Pro...")
    nova_prompt = f"""Analyze this genomic sequence data:

{sequence_data}

Analysis type: {analysis_type}

Provide:
1. Sequence characteristics
2. Potential mutations or variants
3. Clinical significance
4. Recommended follow-up tests"""
    
    nova_result = invoke_model(MODELS['nova_pro'], nova_prompt, max_tokens=2000)
    results['primary_analysis'] = {
        'model': 'Amazon Nova Pro',
        'result': nova_result
    }
    results['models_used'].append('nova_pro')
    
    # Step 2: Secondary validation with GPT-OSS-120B
    print("Running validation with GPT-OSS-120B...")
    gpt_prompt = f"""Review this genomic analysis and provide additional insights:

Original Data: {sequence_data[:500]}...

Primary Analysis: {nova_result[:1000]}...

Provide:
1. Validation of findings
2. Additional literature context
3. Alternative interpretations
4. Research recommendations"""
    
    gpt_result = invoke_model(MODELS['gpt_oss_120b'], gpt_prompt, max_tokens=1500)
    results['secondary_validation'] = {
        'model': 'OpenAI GPT-OSS 120B',
        'result': gpt_result
    }
    results['models_used'].append('gpt_oss_120b')
    
    # Step 3: Synthesize results
    synthesis_prompt = f"""Synthesize these two analyses into a comprehensive report:

Analysis 1 (Nova Pro): {nova_result[:800]}

Analysis 2 (GPT-OSS): {gpt_result[:800]}

Provide a unified, actionable summary."""
    
    synthesis = invoke_model(MODELS['gpt_oss_20b'], synthesis_prompt, max_tokens=1000)
    results['synthesis'] = {
        'model': 'OpenAI GPT-OSS 20B',
        'result': synthesis
    }
    results['models_used'].append('gpt_oss_20b')
    
    return results

def lambda_handler(event, context):
    """Lambda handler for multi-model genomics analysis"""
    
    try:
        # Parse input
        body = json.loads(event.get('body', '{}'))
        sequence_data = body.get('sequence', '')
        analysis_type = body.get('analysis_type', 'genomics')
        
        if not sequence_data:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'No sequence data provided'})
            }
        
        # Run multi-model analysis
        results = multi_model_analysis(sequence_data, analysis_type)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(results)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'message': 'Multi-model analysis failed'
            })
        }
'''
    
    return lambda_code

def deploy_multi_model_lambda():
    """Deploy the multi-model Lambda function"""
    print("\n📦 Creating multi-model Lambda function...")
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Create deployment package
    import zipfile
    import io
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('lambda_function.py', create_multi_model_orchestrator())
    
    zip_buffer.seek(0)
    
    function_name = 'biomerkin-multi-model-orchestrator'
    
    try:
        # Try to update existing function
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_buffer.read()
        )
        print(f"✅ Updated existing Lambda function: {function_name}")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        zip_buffer.seek(0)
        
        # Get IAM role (reuse existing)
        iam = boto3.client('iam')
        try:
            role = iam.get_role(RoleName='biomerkin-lambda-role')
            role_arn = role['Role']['Arn']
        except:
            print("❌ Lambda role not found. Please create it first.")
            return None
        
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_buffer.read()},
            Timeout=300,
            MemorySize=1024,
            Environment={
                'Variables': {
                    'PRIMARY_MODEL': 'amazon.nova-pro-v1:0',
                    'SECONDARY_MODEL': 'openai.gpt-oss-120b-1:0',
                    'QUICK_MODEL': 'openai.gpt-oss-20b-1:0'
                }
            }
        )
        print(f"✅ Created new Lambda function: {function_name}")
    
    return response

def create_usage_guide():
    """Create guide for using the multi-model system"""
    
    guide = """
# Multi-Model System Usage Guide

## 🎯 Model Strategy

### Amazon Nova Pro (Primary)
- **Use for:** Deep genomic analysis, complex reasoning
- **Strengths:** Medical knowledge, long context (300k tokens)
- **Model ID:** amazon.nova-pro-v1:0

### OpenAI GPT-OSS 120B (Secondary)
- **Use for:** Validation, literature review, alternative perspectives
- **Strengths:** Large parameter count, broad knowledge
- **Model ID:** openai.gpt-oss-120b-1:0

### OpenAI GPT-OSS 20B (Quick Tasks)
- **Use for:** Synthesis, summaries, quick queries
- **Strengths:** Fast, cost-effective
- **Model ID:** openai.gpt-oss-20b-1:0

## 📊 Analysis Workflow

1. **Primary Analysis** → Nova Pro analyzes the genomic data
2. **Validation** → GPT-OSS-120B validates and adds context
3. **Synthesis** → GPT-OSS-20B creates unified summary

## 🔧 API Usage

```python
import requests

response = requests.post(
    'YOUR_API_ENDPOINT/analyze',
    json={
        'sequence': 'ATCG...',
        'analysis_type': 'genomics'
    }
)

results = response.json()
print(results['primary_analysis'])  # Nova Pro results
print(results['secondary_validation'])  # GPT-OSS results
print(results['synthesis'])  # Combined summary
```

## 💰 Cost Optimization

- Use Nova Pro for complex analysis (higher quality)
- Use GPT-OSS-120B for validation (good balance)
- Use GPT-OSS-20B for simple tasks (most economical)

## 🎨 Model Selection Logic

```python
def select_model(task_complexity):
    if task_complexity == 'high':
        return 'amazon.nova-pro-v1:0'
    elif task_complexity == 'medium':
        return 'openai.gpt-oss-120b-1:0'
    else:
        return 'openai.gpt-oss-20b-1:0'
```
"""
    
    with open('MULTI_MODEL_USAGE_GUIDE.md', 'w') as f:
        f.write(guide)
    
    print("\n📖 Usage guide created: MULTI_MODEL_USAGE_GUIDE.md")

def main():
    print("🚀 Multi-Model System Deployment")
    print("="*60)
    print("\nModels to be configured:")
    for key, model in MODELS.items():
        print(f"\n{model['name']}:")
        print(f"  ID: {model['id']}")
        print(f"  Use: {model['use_case']}")
        print(f"  Strengths: {', '.join(model['strengths'])}")
    
    print("\n" + "="*60)
    
    # Test model access
    accessible_models = {}
    for key, model in MODELS.items():
        if test_model_access(model['id'], model['name']):
            accessible_models[key] = model
    
    print("\n" + "="*60)
    print(f"✅ {len(accessible_models)}/{len(MODELS)} models accessible")
    
    if len(accessible_models) >= 2:
        print("\n✅ Sufficient models available for multi-model setup!")
        
        # Deploy Lambda
        result = deploy_multi_model_lambda()
        
        if result:
            print("\n✅ Multi-model Lambda deployed successfully!")
            print(f"   Function ARN: {result.get('FunctionArn', 'N/A')}")
        
        # Create usage guide
        create_usage_guide()
        
        print("\n" + "="*60)
        print("🎉 MULTI-MODEL SYSTEM READY!")
        print("="*60)
        print("\nYour system now uses:")
        for key in accessible_models:
            print(f"  ✓ {accessible_models[key]['name']}")
        
        print("\nNext steps:")
        print("1. Review MULTI_MODEL_USAGE_GUIDE.md")
        print("2. Test the multi-model Lambda function")
        print("3. Update your frontend to use the new endpoint")
        
    else:
        print("\n⚠️  Not enough models accessible")
        print("   Request access to models in Bedrock console")

if __name__ == "__main__":
    main()
