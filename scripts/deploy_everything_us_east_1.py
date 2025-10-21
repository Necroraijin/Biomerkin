#!/usr/bin/env python3
"""
Deploy Complete Biomerkin System to us-east-1
Creates API Gateway + Lambda in us-east-1 where Bedrock models are available
"""

import boto3
import json
import zipfile
import io
import os
import time

# Target region where Bedrock models are available
REGION = 'us-east-1'

# Initialize AWS clients
lambda_client = boto3.client('lambda', region_name=REGION)
apigateway = boto3.client('apigateway', region_name=REGION)
iam = boto3.client('iam')

def create_lambda_role():
    """Create IAM role for Lambda functions"""
    role_name = 'biomerkin-lambda-role-us-east-1'
    
    try:
        # Check if role exists
        role = iam.get_role(RoleName=role_name)
        print(f"✅ IAM Role already exists: {role_name}")
        return role['Role']['Arn']
    except iam.exceptions.NoSuchEntityException:
        pass
    
    print(f"📝 Creating IAM role: {role_name}")
    
    # Trust policy
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    # Create role
    role = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(trust_policy),
        Description='Role for Biomerkin Lambda functions in us-east-1'
    )
    
    # Attach policies
    policies = [
        'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
        'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
    ]
    
    for policy_arn in policies:
        iam.attach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
    
    print(f"✅ IAM Role created: {role_name}")
    print("⏳ Waiting 10 seconds for role to propagate...")
    time.sleep(10)
    
    return role['Role']['Arn']

def create_lambda_zip(file_path):
    """Create a ZIP file for Lambda deployment"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(file_path, os.path.basename(file_path))
    
    zip_buffer.seek(0)
    return zip_buffer.read()

def create_or_update_lambda(function_name, file_path, handler, role_arn):
    """Create or update Lambda function"""
    try:
        # Check if function exists
        lambda_client.get_function(FunctionName=function_name)
        
        # Update existing function
        print(f"   📝 Updating existing function: {function_name}")
        zip_content = create_lambda_zip(file_path)
        
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        # Update configuration
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Handler=handler,
            Runtime='python3.11',
            Timeout=300,
            MemorySize=512
        )
        
        print(f"   ✅ Updated: {function_name}")
        return function_name
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function
        print(f"   📝 Creating new function: {function_name}")
        zip_content = create_lambda_zip(file_path)
        
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler=handler,
            Code={'ZipFile': zip_content},
            Timeout=300,
            MemorySize=512
        )
        
        print(f"   ✅ Created: {function_name}")
        return response['FunctionName']

def create_api_gateway():
    """Create API Gateway"""
    api_name = 'biomerkin-api-us-east-1'
    
    # Check if API exists
    apis = apigateway.get_rest_apis()
    for api in apis['items']:
        if api['name'] == api_name:
            print(f"✅ API Gateway already exists: {api_name} (ID: {api['id']})")
            return api['id']
    
    print(f"📝 Creating API Gateway: {api_name}")
    
    api = apigateway.create_rest_api(
        name=api_name,
        description='Biomerkin Multi-Model Genomics Analysis API in us-east-1',
        endpointConfiguration={'types': ['REGIONAL']}
    )
    
    print(f"✅ API Gateway created: {api_name} (ID: {api['id']})")
    return api['id']

def get_root_resource(api_id):
    """Get root resource ID"""
    resources = apigateway.get_resources(restApiId=api_id)
    for resource in resources['items']:
        if resource['path'] == '/':
            return resource['id']
    return None

def create_resource(api_id, parent_id, path_part):
    """Create API resource"""
    try:
        resources = apigateway.get_resources(restApiId=api_id)
        for resource in resources['items']:
            if resource.get('pathPart') == path_part:
                print(f"   ℹ️  Resource already exists: /{path_part}")
                return resource['id']
        
        resource = apigateway.create_resource(
            restApiId=api_id,
            parentId=parent_id,
            pathPart=path_part
        )
        print(f"   ✅ Created resource: /{path_part}")
        return resource['id']
    except Exception as e:
        print(f"   ⚠️  Error creating resource: {str(e)}")
        return None

def setup_method(api_id, resource_id, http_method, lambda_function_name):
    """Setup API Gateway method"""
    try:
        # Create method
        try:
            apigateway.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                authorizationType='NONE'
            )
        except:
            pass
        
        # Get Lambda ARN
        account_id = boto3.client('sts').get_caller_identity()['Account']
        lambda_arn = f"arn:aws:lambda:{REGION}:{account_id}:function:{lambda_function_name}"
        
        # Setup integration
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=http_method,
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=f"arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
        )
        
        # Add Lambda permission
        try:
            lambda_client.add_permission(
                FunctionName=lambda_function_name,
                StatementId=f'apigateway-{api_id}-{http_method}',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f"arn:aws:execute-api:{REGION}:{account_id}:{api_id}/*/*"
            )
        except:
            pass  # Permission might already exist
        
        print(f"   ✅ Setup {http_method} method")
        
    except Exception as e:
        print(f"   ⚠️  Error setting up method: {str(e)}")

def setup_cors(api_id, resource_id):
    """Setup CORS for resource"""
    try:
        # OPTIONS method
        apigateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            authorizationType='NONE'
        )
        
        # OPTIONS method response
        apigateway.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': True,
                'method.response.header.Access-Control-Allow-Methods': True,
                'method.response.header.Access-Control-Allow-Origin': True
            }
        )
        
        # OPTIONS integration
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            type='MOCK',
            requestTemplates={'application/json': '{"statusCode": 200}'}
        )
        
        # OPTIONS integration response
        apigateway.put_integration_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='OPTIONS',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Headers': "'*'",
                'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
                'method.response.header.Access-Control-Allow-Origin': "'*'"
            }
        )
        
        print(f"   ✅ CORS enabled")
        
    except Exception as e:
        print(f"   ⚠️  CORS setup warning: {str(e)}")

def deploy_api(api_id, stage_name='prod'):
    """Deploy API to stage"""
    try:
        apigateway.create_deployment(
            restApiId=api_id,
            stageName=stage_name,
            description='Initial deployment to us-east-1'
        )
        print(f"✅ API deployed to stage: {stage_name}")
        return True
    except Exception as e:
        print(f"❌ Error deploying API: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("🚀 Deploying Complete Biomerkin System to us-east-1")
    print("=" * 70)
    
    # Step 1: Create IAM Role
    print("\n📋 Step 1: Creating IAM Role")
    role_arn = create_lambda_role()
    
    # Step 2: Create Lambda Function
    print("\n📋 Step 2: Creating Lambda Function")
    function_name = 'biomerkin-multi-model-us-east-1'
    file_path = 'lambda_functions/multi_model_orchestrator.py'
    handler = 'multi_model_orchestrator.lambda_handler'
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    lambda_name = create_or_update_lambda(function_name, file_path, handler, role_arn)
    
    # Step 3: Create API Gateway
    print("\n📋 Step 3: Creating API Gateway")
    api_id = create_api_gateway()
    
    # Step 4: Setup API Resources
    print("\n📋 Step 4: Setting up API Resources")
    root_id = get_root_resource(api_id)
    
    # Create /analyze resource
    analyze_id = create_resource(api_id, root_id, 'analyze')
    
    if analyze_id:
        # Setup POST method
        setup_method(api_id, analyze_id, 'POST', lambda_name)
        
        # Setup CORS
        setup_cors(api_id, analyze_id)
    
    # Step 5: Deploy API
    print("\n📋 Step 5: Deploying API")
    if deploy_api(api_id):
        # Get API URL
        account_id = boto3.client('sts').get_caller_identity()['Account']
        api_url = f"https://{api_id}.execute-api.{REGION}.amazonaws.com/prod"
        
        print("\n" + "=" * 70)
        print("🎉 Deployment Complete!")
        print("=" * 70)
        print(f"\n📍 API Endpoint:")
        print(f"   {api_url}/analyze")
        print(f"\n📝 Update your frontend .env file:")
        print(f"   REACT_APP_API_URL={api_url}")
        print(f"\n🧪 Test with curl:")
        print(f'''   curl -X POST {api_url}/analyze \\
     -H "Content-Type: application/json" \\
     -d '{{"sequence":"ATCGATCG","analysis_type":"genomics","use_multi_model":true}}' ''')
        print("\n" + "=" * 70)
    else:
        print("\n❌ Deployment failed")

if __name__ == "__main__":
    main()
