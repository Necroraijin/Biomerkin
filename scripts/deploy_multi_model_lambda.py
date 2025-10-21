#!/usr/bin/env python3
"""
Deploy Multi-Model Lambda Function
Deploys Lambda that uses Nova Pro + GPT-OSS models
"""

import boto3
import zipfile
import io
import json
import time

def create_deployment_package():
    """Create Lambda deployment package"""
    print("📦 Creating deployment package...")
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add Lambda function
        with open('lambda_functions/multi_model_orchestrator.py', 'r') as f:
            zip_file.writestr('lambda_function.py', f.read())
    
    zip_buffer.seek(0)
    print("✅ Deployment package created")
    return zip_buffer.read()

def deploy_lambda():
    """Deploy or update Lambda function"""
    print("\n🚀 Deploying multi-model Lambda...")
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    iam = boto3.client('iam')
    
    function_name = 'biomerkin-multi-model-orchestrator'
    
    # Get IAM role
    try:
        role = iam.get_role(RoleName='biomerkin-lambda-role')
        role_arn = role['Role']['Arn']
        print(f"✅ Using IAM role: {role_arn}")
    except:
        print("❌ Lambda role 'biomerkin-lambda-role' not found")
        print("   Creating it now...")
        
        # Create role
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        
        role = iam.create_role(
            RoleName='biomerkin-lambda-role',
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        role_arn = role['Role']['Arn']
        
        # Attach policies
        iam.attach_role_policy(
            RoleName='biomerkin-lambda-role',
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        # Add Bedrock permissions
        bedrock_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": "*"
            }]
        }
        
        iam.put_role_policy(
            RoleName='biomerkin-lambda-role',
            PolicyName='BedrockAccess',
            PolicyDocument=json.dumps(bedrock_policy)
        )
        
        print("✅ Created IAM role with Bedrock permissions")
        print("   Waiting 10 seconds for role to propagate...")
        time.sleep(10)
    
    # Create deployment package
    zip_data = create_deployment_package()
    
    try:
        # Try to update existing function
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_data
        )
        print(f"✅ Updated existing Lambda: {function_name}")
        
        # Update configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name,
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
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        print(f"Creating new Lambda function: {function_name}")
        
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_data},
            Timeout=300,
            MemorySize=1024,
            Environment={
                'Variables': {
                    'PRIMARY_MODEL': 'amazon.nova-pro-v1:0',
                    'SECONDARY_MODEL': 'openai.gpt-oss-120b-1:0',
                    'QUICK_MODEL': 'openai.gpt-oss-20b-1:0'
                }
            },
            Description='Multi-model genomics analysis using Nova Pro + GPT-OSS'
        )
        print(f"✅ Created new Lambda: {function_name}")
    
    return response

def test_lambda():
    """Test the deployed Lambda"""
    print("\n🧪 Testing multi-model Lambda...")
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    test_payload = {
        'sequence': 'ATCGATCGATCGATCG',
        'analysis_type': 'genomics',
        'use_multi_model': True
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName='biomerkin-multi-model-orchestrator',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print("✅ Lambda test successful!")
            
            body = json.loads(result.get('body', '{}'))
            if 'models_used' in body:
                print(f"   Models used: {', '.join(body['models_used'])}")
                print(f"   Workflow: {body.get('workflow', 'unknown')}")
            
            return True
        else:
            print(f"❌ Lambda returned status: {response['StatusCode']}")
            print(f"   Response: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Lambda test failed: {str(e)}")
        return False

def create_api_gateway():
    """Create or update API Gateway endpoint"""
    print("\n🌐 Setting up API Gateway...")
    
    apigateway = boto3.client('apigateway', region_name='us-east-1')
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    api_name = 'biomerkin-multi-model-api'
    
    try:
        # Get existing APIs
        apis = apigateway.get_rest_apis()
        existing_api = next((api for api in apis['items'] if api['name'] == api_name), None)
        
        if existing_api:
            api_id = existing_api['id']
            print(f"✅ Using existing API: {api_id}")
        else:
            # Create new API
            api = apigateway.create_rest_api(
                name=api_name,
                description='Multi-model genomics analysis API',
                endpointConfiguration={'types': ['REGIONAL']}
            )
            api_id = api['id']
            print(f"✅ Created new API: {api_id}")
        
        # Get API endpoint
        api_endpoint = f"https://{api_id}.execute-api.us-east-1.amazonaws.com/prod"
        print(f"   Endpoint: {api_endpoint}")
        
        return api_endpoint
        
    except Exception as e:
        print(f"⚠️  API Gateway setup: {str(e)}")
        return None

def main():
    print("="*60)
    print("🚀 MULTI-MODEL LAMBDA DEPLOYMENT")
    print("="*60)
    print("\nModels to be used:")
    print("  1. Amazon Nova Pro (Primary analysis)")
    print("  2. OpenAI GPT-OSS 120B (Validation)")
    print("  3. OpenAI GPT-OSS 20B (Synthesis)")
    print("="*60)
    
    # Deploy Lambda
    result = deploy_lambda()
    
    if result:
        print(f"\n✅ Lambda ARN: {result['FunctionArn']}")
        
        # Test Lambda
        if test_lambda():
            print("\n✅ Multi-model system is working!")
            
            # Setup API Gateway
            api_endpoint = create_api_gateway()
            
            # Create summary
            print("\n" + "="*60)
            print("🎉 DEPLOYMENT COMPLETE!")
            print("="*60)
            print("\n📋 Summary:")
            print(f"   Lambda: biomerkin-multi-model-orchestrator")
            print(f"   Region: us-east-1")
            print(f"   Models: 3 (Nova Pro + 2x GPT-OSS)")
            
            if api_endpoint:
                print(f"   API: {api_endpoint}")
            
            print("\n📖 Usage:")
            print("   1. Call Lambda directly or via API Gateway")
            print("   2. Send genomic sequence data")
            print("   3. Receive multi-model analysis")
            
            print("\n💡 Next steps:")
            print("   1. Update frontend to use new endpoint")
            print("   2. Test with real genomic data")
            print("   3. Review MULTI_MODEL_USAGE_GUIDE.md")
            
            # Save configuration
            config = {
                'lambda_function': 'biomerkin-multi-model-orchestrator',
                'lambda_arn': result['FunctionArn'],
                'api_endpoint': api_endpoint,
                'models': {
                    'primary': 'amazon.nova-pro-v1:0',
                    'secondary': 'openai.gpt-oss-120b-1:0',
                    'quick': 'openai.gpt-oss-20b-1:0'
                },
                'region': 'us-east-1'
            }
            
            with open('multi_model_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            print("\n💾 Configuration saved to: multi_model_config.json")
            print("="*60)
        else:
            print("\n⚠️  Lambda deployed but test failed")
            print("   Check CloudWatch logs for details")
    else:
        print("\n❌ Deployment failed")

if __name__ == "__main__":
    main()
