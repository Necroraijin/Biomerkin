#!/usr/bin/env python3
"""
Redeploy Everything to US-East-1 Region
Fix the region mismatch by deploying all components to us-east-1
"""

import boto3
import json
import zipfile
import io
import time
from datetime import datetime

class USEast1Redeployer:
    def __init__(self):
        self.region = 'us-east-1'
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.apigateway_client = boto3.client('apigateway', region_name=self.region)
        self.iam_client = boto3.client('iam', region_name=self.region)
        self.bedrock_client = boto3.client('bedrock-runtime', region_name=self.region)
        
    def create_multi_model_orchestrator(self):
        """Create the main orchestrator Lambda function"""
        
        lambda_code = '''
"""
Multi-Model Orchestrator for US-East-1
Uses Amazon Nova Pro + OpenAI GPT-OSS for comprehensive genomics analysis
"""

import json
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# CORS Headers for all responses
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
}

# Use us-east-1 for Bedrock (same region as Lambda)
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
        logger.error(f"Nova model error: {str(e)}")
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
        logger.error(f"OpenAI model error: {str(e)}")
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
        'workflow': 'multi-model',
        'region': 'us-east-1'
    }
    
    # Step 1: Primary analysis with Nova Pro
    logger.info("Step 1: Primary analysis with Nova Pro...")
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
    logger.info("Step 2: Validation with GPT-OSS-120B...")
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
    logger.info("Step 3: Synthesis with GPT-OSS-20B...")
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
    
    logger.info(f"Event: {json.dumps(event)}")
    
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
            logger.info("Running multi-model analysis...")
            results = multi_model_genomics_analysis(sequence_data, analysis_type)
        else:
            # Single model fallback (Nova Pro only)
            logger.info("Running single-model analysis...")
            prompt = f"Analyze this genomic sequence: {sequence_data}"
            result = invoke_model('nova_pro', prompt)
            results = {
                'timestamp': datetime.utcnow().isoformat(),
                'analysis_type': analysis_type,
                'result': result,
                'models_used': ['nova_pro'],
                'workflow': 'single-model',
                'region': 'us-east-1'
            }
        
        return {
            'statusCode': 200,
            'headers': {**CORS_HEADERS, 'Content-Type': 'application/json'},
            'body': json.dumps(results)
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
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
'''
        
        return lambda_code

    def create_iam_role(self):
        """Create IAM role for Lambda functions"""
        role_name = 'biomerkin-lambda-role-us-east-1'
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Bedrock access policy
        bedrock_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            # Create role
            role_response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Biomerkin Lambda execution role for US-East-1'
            )
            
            # Attach basic execution policy
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            
            # Create and attach Bedrock policy
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName='BedrockAccess',
                PolicyDocument=json.dumps(bedrock_policy)
            )
            
            print(f"✅ Created IAM role: {role_name}")
            
            # Wait for role to be ready
            time.sleep(10)
            
            return role_response['Role']['Arn']
            
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            print(f"✅ IAM role already exists: {role_name}")
            return f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:role/{role_name}"
        except Exception as e:
            print(f"❌ Error creating IAM role: {e}")
            return None

    def deploy_lambda_function(self, function_name, role_arn):
        """Deploy Lambda function to US-East-1"""
        
        # Create deployment package
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('lambda_function.py', self.create_multi_model_orchestrator())
        
        zip_buffer.seek(0)
        zip_data = zip_buffer.read()
        
        try:
            # Try to create function
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_data},
                Description=f'Biomerkin {function_name} - Multi-model genomics analysis',
                Timeout=300,
                MemorySize=1024,
                Environment={
                    'Variables': {
                        'BEDROCK_REGION': 'us-east-1',
                        'LOG_LEVEL': 'INFO'
                    }
                }
            )
            print(f"✅ Created Lambda function: {function_name}")
            
        except self.lambda_client.exceptions.ResourceConflictException:
            # Function exists, update it
            self.lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_data
            )
            
            self.lambda_client.update_function_configuration(
                FunctionName=function_name,
                Timeout=300,
                MemorySize=1024,
                Environment={
                    'Variables': {
                        'BEDROCK_REGION': 'us-east-1',
                        'LOG_LEVEL': 'INFO'
                    }
                }
            )
            print(f"✅ Updated Lambda function: {function_name}")
        
        return True

    def create_api_gateway(self):
        """Create API Gateway in US-East-1"""
        
        try:
            # Create API Gateway
            api_response = self.apigateway_client.create_rest_api(
                name='biomerkin-api-us-east-1',
                description='Biomerkin Multi-Agent System API - US East 1',
                endpointConfiguration={
                    'types': ['REGIONAL']
                }
            )
            
            api_id = api_response['id']
            print(f"✅ Created API Gateway: {api_id}")
            
            # Get root resource
            resources = self.apigateway_client.get_resources(restApiId=api_id)
            root_resource_id = None
            for resource in resources['items']:
                if resource['path'] == '/':
                    root_resource_id = resource['id']
                    break
            
            if not root_resource_id:
                print("❌ Could not find root resource")
                return None
            
            # Create /analyze resource
            analyze_resource = self.apigateway_client.create_resource(
                restApiId=api_id,
                parentId=root_resource_id,
                pathPart='analyze'
            )
            analyze_resource_id = analyze_resource['id']
            print(f"✅ Created /analyze resource: {analyze_resource_id}")
            
            # Get Lambda function ARN
            lambda_arn = f"arn:aws:lambda:{self.region}:{boto3.client('sts').get_caller_identity()['Account']}:function:biomerkin-orchestrator"
            
            # Create POST method for /analyze
            self.apigateway_client.put_method(
                restApiId=api_id,
                resourceId=analyze_resource_id,
                httpMethod='POST',
                authorizationType='NONE'
            )
            
            # Create OPTIONS method for CORS
            self.apigateway_client.put_method(
                restApiId=api_id,
                resourceId=analyze_resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            # Create Lambda integration for POST
            self.apigateway_client.put_integration(
                restApiId=api_id,
                resourceId=analyze_resource_id,
                httpMethod='POST',
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
            )
            
            # Create MOCK integration for OPTIONS (CORS)
            self.apigateway_client.put_integration(
                restApiId=api_id,
                resourceId=analyze_resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={
                    'application/json': '{"statusCode": 200}'
                }
            )
            
            # Add CORS response headers for OPTIONS
            self.apigateway_client.put_method_response(
                restApiId=api_id,
                resourceId=analyze_resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': True,
                    'method.response.header.Access-Control-Allow-Headers': True,
                    'method.response.header.Access-Control-Allow-Methods': True
                }
            )
            
            self.apigateway_client.put_integration_response(
                restApiId=api_id,
                resourceId=analyze_resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                    'method.response.header.Access-Control-Allow-Headers': "'*'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
                }
            )
            
            # Deploy API
            deployment = self.apigateway_client.create_deployment(
                restApiId=api_id,
                stageName='prod',
                description='Production deployment for Biomerkin API'
            )
            
            print(f"✅ Deployed API to prod stage")
            
            # Add Lambda permission for API Gateway
            try:
                self.lambda_client.add_permission(
                    FunctionName='biomerkin-orchestrator',
                    StatementId='api-gateway-invoke',
                    Action='lambda:InvokeFunction',
                    Principal='apigateway.amazonaws.com',
                    SourceArn=f"arn:aws:execute-api:{self.region}:{boto3.client('sts').get_caller_identity()['Account']}:{api_id}/*/*"
                )
                print("✅ Added Lambda permission for API Gateway")
            except self.lambda_client.exceptions.ResourceConflictException:
                print("✅ Lambda permission already exists")
            
            api_url = f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod"
            print(f"✅ API URL: {api_url}")
            
            return api_url
            
        except Exception as e:
            print(f"❌ Error creating API Gateway: {e}")
            return None

    def test_deployment(self, api_url):
        """Test the deployment"""
        import requests
        
        print("\n🧪 Testing deployment...")
        
        test_data = {
            'sequence': 'ATCGATCGATCGATCG',
            'analysis_type': 'genomics'
        }
        
        try:
            response = requests.post(
                f"{api_url}/analyze",
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"✅ Test Status: {response.status_code}")
            print(f"✅ CORS Origin: {response.headers.get('Access-Control-Allow-Origin', 'MISSING')}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Analysis completed with {len(result.get('models_used', []))} models")
                return True
            else:
                print(f"⚠️  Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False

    def deploy_everything(self):
        """Deploy everything to US-East-1"""
        print("🚀 REDEPLOYING TO US-EAST-1")
        print("="*60)
        print("📍 Target Region: us-east-1")
        print("🎯 Components: Lambda + API Gateway + Bedrock")
        print("="*60)
        
        # Step 1: Create IAM role
        print("\n🔧 Step 1: Creating IAM role...")
        role_arn = self.create_iam_role()
        if not role_arn:
            print("❌ Failed to create IAM role")
            return None
        
        # Step 2: Deploy Lambda function
        print("\n🔧 Step 2: Deploying Lambda function...")
        if not self.deploy_lambda_function('biomerkin-orchestrator', role_arn):
            print("❌ Failed to deploy Lambda function")
            return None
        
        # Step 3: Create API Gateway
        print("\n🔧 Step 3: Creating API Gateway...")
        api_url = self.create_api_gateway()
        if not api_url:
            print("❌ Failed to create API Gateway")
            return None
        
        # Step 4: Test deployment
        print("\n🔧 Step 4: Testing deployment...")
        time.sleep(10)  # Wait for deployment to be ready
        
        if self.test_deployment(api_url):
            print("\n" + "="*60)
            print("🎉 DEPLOYMENT TO US-EAST-1 SUCCESSFUL!")
            print("="*60)
            print(f"✅ API URL: {api_url}")
            print(f"✅ Region: us-east-1")
            print(f"✅ CORS: Enabled")
            print(f"✅ Models: Nova Pro + GPT-OSS")
            print("\n🌐 Your new API endpoint:")
            print(f"   {api_url}/analyze")
            print("\n📝 Update your frontend to use this URL!")
            return api_url
        else:
            print("\n⚠️  Deployment completed but test failed")
            print("   The API might need a few more minutes to be ready")
            return api_url

def main():
    deployer = USEast1Redeployer()
    api_url = deployer.deploy_everything()
    
    if api_url:
        print(f"\n🎯 Next Steps:")
        print(f"1. Update frontend API URL to: {api_url}")
        print(f"2. Test your frontend application")
        print(f"3. The CORS issue should now be resolved!")

if __name__ == "__main__":
    main()
