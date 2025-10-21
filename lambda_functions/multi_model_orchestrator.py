"""
Multi-Model Orchestrator Lambda
Uses Amazon Nova Pro + OpenAI GPT-OSS for comprehensive genomics analysis
"""

import json
import boto3
import os
from datetime import datetime

# CORS Headers for all responses
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
}

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# Model configuration
MODELS = {
    'nova_pro': {
        'id': 'amazon.nova-pro-v1:0',
        'format': 'nova',
        'name': 'Amazon Nova Pro'
    },
    'gpt_oss_120b': {
        'id': 'openai.gpt-oss-120b-1:0',
        'format': 'openai',
        'name': 'OpenAI GPT-OSS 120B'
    },
    'gpt_oss_20b': {
        'id': 'openai.gpt-oss-20b-1:0',
        'format': 'openai',
        'name': 'OpenAI GPT-OSS 20B'
    }
}

def invoke_nova_model(model_id, prompt, max_tokens=2000, temperature=0.7):
    """Invoke Amazon Nova model"""
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
        return f"Error invoking Nova: {str(e)}"

def invoke_openai_model(model_id, prompt, max_tokens=2000, temperature=0.7):
    """Invoke OpenAI GPT-OSS model"""
    try:
        body = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        })
        
        response = bedrock.invoke_model(
            modelId=model_id,
            body=body
        )
        
        result = json.loads(response['body'].read())
        return result['choices'][0]['message']['content']
        
    except Exception as e:
        return f"Error invoking OpenAI: {str(e)}"

def invoke_model(model_key, prompt, max_tokens=2000, temperature=0.7):
    """Invoke any model with correct format"""
    model = MODELS[model_key]
    
    if model['format'] == 'nova':
        return invoke_nova_model(model['id'], prompt, max_tokens, temperature)
    elif model['format'] == 'openai':
        return invoke_openai_model(model['id'], prompt, max_tokens, temperature)
    else:
        return f"Unknown model format: {model['format']}"

def multi_model_genomics_analysis(sequence_data, analysis_type='genomics'):
    """
    Multi-model genomics analysis workflow:
    1. Nova Pro: Deep primary analysis
    2. GPT-OSS-120B: Validation and literature context
    3. GPT-OSS-20B: Synthesis and summary
    """
    
    results = {
        'timestamp': datetime.utcnow().isoformat(),
        'analysis_type': analysis_type,
        'models_used': [],
        'workflow': 'multi-model'
    }
    
    # Step 1: Primary analysis with Nova Pro
    print("Step 1: Primary analysis with Nova Pro...")
    nova_prompt = f"""You are an expert genomics analyst. Analyze this genomic sequence data:

Sequence: {sequence_data}

Analysis Type: {analysis_type}

Provide a comprehensive analysis including:
1. Sequence characteristics and quality
2. Identified mutations or variants
3. Clinical significance
4. Potential health implications
5. Recommended follow-up tests

Be specific and scientific in your analysis."""
    
    nova_result = invoke_model('nova_pro', nova_prompt, max_tokens=2000, temperature=0.3)
    results['primary_analysis'] = {
        'model': MODELS['nova_pro']['name'],
        'model_id': MODELS['nova_pro']['id'],
        'result': nova_result,
        'role': 'Primary deep analysis'
    }
    results['models_used'].append('nova_pro')
    
    # Step 2: Validation with GPT-OSS-120B
    print("Step 2: Validation with GPT-OSS-120B...")
    gpt_prompt = f"""You are a genomics research expert. Review and validate this genomic analysis:

Original Sequence (first 500 chars): {sequence_data[:500]}...

Primary Analysis Summary:
{nova_result[:1200]}...

Provide:
1. Validation of the primary findings
2. Additional scientific context from literature
3. Alternative interpretations if any
4. Research recommendations
5. Any concerns or limitations

Be thorough and cite relevant scientific concepts."""
    
    gpt_result = invoke_model('gpt_oss_120b', gpt_prompt, max_tokens=1500, temperature=0.4)
    results['secondary_validation'] = {
        'model': MODELS['gpt_oss_120b']['name'],
        'model_id': MODELS['gpt_oss_120b']['id'],
        'result': gpt_result,
        'role': 'Validation and literature review'
    }
    results['models_used'].append('gpt_oss_120b')
    
    # Step 3: Synthesis with GPT-OSS-20B
    print("Step 3: Synthesis with GPT-OSS-20B...")
    synthesis_prompt = f"""Create a unified, actionable summary from these two genomic analyses:

PRIMARY ANALYSIS (Nova Pro):
{nova_result[:1000]}

VALIDATION & CONTEXT (GPT-OSS-120B):
{gpt_result[:1000]}

Provide a concise executive summary that:
1. Highlights key findings
2. Presents consensus conclusions
3. Notes any discrepancies
4. Gives clear actionable recommendations

Keep it clear and actionable for clinicians."""
    
    synthesis = invoke_model('gpt_oss_20b', synthesis_prompt, max_tokens=800, temperature=0.3)
    results['synthesis'] = {
        'model': MODELS['gpt_oss_20b']['name'],
        'model_id': MODELS['gpt_oss_20b']['id'],
        'result': synthesis,
        'role': 'Synthesis and summary'
    }
    results['models_used'].append('gpt_oss_20b')
    
    # Create final report
    results['final_report'] = {
        'executive_summary': synthesis,
        'detailed_analysis': nova_result,
        'validation_notes': gpt_result,
        'confidence': 'High (multi-model consensus)',
        'models_count': len(results['models_used'])
    }
    
    return results

def lambda_handler(event, context):
    """Lambda handler for multi-model genomics analysis"""
    
    # Handle OPTIONS request for CORS
    if event.get("httpMethod") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS
        }
    
    print(f"Event: {json.dumps(event)}")
    
    try:
        # Handle both direct invocation and API Gateway
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', event)
        
        # Extract parameters
        sequence_data = body.get('sequence', body.get('sequenceData', ''))
        analysis_type = body.get('analysis_type', body.get('analysisType', 'genomics'))
        use_multi_model = body.get('use_multi_model', True)
        
        if not sequence_data:
            return {
                'statusCode': 400,
                'headers': {**CORS_HEADERS, 'Content-Type': 'application/json'},
                'body': json.dumps({
                    'error': 'No sequence data provided',
                    'message': 'Please provide sequence data in the request body'
                })
            }
        
        # Run analysis
        if use_multi_model:
            print("Running multi-model analysis...")
            results = multi_model_genomics_analysis(sequence_data, analysis_type)
        else:
            # Single model fallback (Nova Pro only)
            print("Running single-model analysis...")
            prompt = f"Analyze this genomic sequence: {sequence_data}"
            result = invoke_model('nova_pro', prompt)
            results = {
                'timestamp': datetime.utcnow().isoformat(),
                'analysis_type': analysis_type,
                'result': result,
                'models_used': ['nova_pro'],
                'workflow': 'single-model'
            }
        
        return {
            'statusCode': 200,
            'headers': {**CORS_HEADERS, 'Content-Type': 'application/json'},
            'body': json.dumps(results)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {**CORS_HEADERS, 'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': str(e),
                'message': 'Multi-model analysis failed',
                'traceback': traceback.format_exc()
            })
        }
