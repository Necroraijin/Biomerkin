#!/usr/bin/env python3
"""
Fix Cross-Region Lambda Issue
API Gateway is in ap-south-1 but Lambda is in us-east-1
We need to either move Lambda or create a proxy
"""

import boto3
import json
import zipfile
import io
import time

def create_lambda_in_same_region():
    """Create the enhanced orchestrator in ap-south-1 (same as API Gateway)"""
    print("🚀 Creating Lambda in ap-south-1 (same region as API Gateway)...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    iam = boto3.client('iam')
    
    # Get the Lambda code from us-east-1
    us_lambda = boto3.client('lambda', region_name='us-east-1')
    
    try:
        # Get function code
        response = us_lambda.get_function(FunctionName='biomerkin-enhanced-orchestrator')
        code_location = response['Code']['Location']
        
        print(f"  Fetching code from us-east-1...")
        
        # Download code
        import requests
        code_response = requests.get(code_location)
        code_zip = code_response.content
        
        print(f"  Code downloaded: {len(code_zip)} bytes")
        
        # Get IAM role
        try:
            role = iam.get_role(RoleName='biomerkin-lambda-role')
            role_arn = role['Role']['Arn']
        except:
            print("  Creating IAM role...")
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
            
            print("  Waiting for role to propagate...")
            time.sleep(10)
        
        # Create function in ap-south-1
        function_name = 'biomerkin-enhanced-orchestrator'
        
        try:
            # Try to update if exists
            lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=code_zip
            )
            print(f"✅ Updated Lambda in ap-south-1")
        except lambda_client.exceptions.ResourceNotFoundException:
            # Create new
            lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.11',
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': code_zip},
                Timeout=300,
                MemorySize=1024,
                Environment={
                    'Variables': {
                        'MULTI_MODEL_ENABLED': 'true',
                        'PRIMARY_MODEL': 'amazon.nova-pro-v1:0',
                        'SECONDARY_MODEL': 'openai.gpt-oss-120b-1:0',
                        'QUICK_MODEL': 'openai.gpt-oss-20b-1:0',
                        'BEDROCK_REGION': 'us-east-1'
                    }
                },
                Description='Enhanced orchestrator with multi-model support (ap-south-1)'
            )
            print(f"✅ Created Lambda in ap-south-1")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def update_api_gateway_integration():
    """Update API Gateway to use the ap-south-1 Lambda"""
    print("\n🔧 Updating API Gateway integration...")
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    try:
        api_id = '642v46sv19'
        
        # Get resources
        resources = apigateway.get_resources(restApiId=api_id)
        analyze_resource = next((r for r in resources['items'] if r.get('path') == '/analyze'), None)
        
        if not analyze_resource:
            print("❌ /analyze resource not found")
            return False
        
        resource_id = analyze_resource['id']
        
        # Add Lambda permission
        try:
            lambda_client.remove_permission(
                FunctionName='biomerkin-enhanced-orchestrator',
                StatementId='apigateway-invoke'
            )
        except:
            pass
        
        lambda_client.add_permission(
            FunctionName='biomerkin-enhanced-orchestrator',
            StatementId='apigateway-invoke',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f'arn:aws:execute-api:ap-south-1:242201307639:{api_id}/*/*/*'
        )
        print("  Added Lambda permission")
        
        # Update integration to use ap-south-1 Lambda
        lambda_arn = 'arn:aws:lambda:ap-south-1:242201307639:function:biomerkin-enhanced-orchestrator'
        integration_uri = f'arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        
        # Delete old integration
        try:
            apigateway.delete_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='POST'
            )
        except:
            pass
        
        # Create new integration
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=integration_uri
        )
        print("✅ Updated integration to ap-south-1 Lambda")
        
        # Deploy
        apigateway.create_deployment(
            restApiId=api_id,
            stageName='prod',
            description='Fixed cross-region Lambda issue'
        )
        print("✅ Deployed API changes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api():
    """Test the API"""
    print("\n🧪 Testing API...")
    
    import requests
    
    api_url = "https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod/analyze"
    
    try:
        print(f"  Sending request to {api_url}")
        response = requests.post(
            api_url,
            json={
                'sequence': 'ATCGATCGATCGATCG',
                'analysis_type': 'genomics',
                'use_multi_model': True
            },
            timeout=120
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ API IS WORKING!")
                print(f"   Models: {data['analysis_results']['models_used']}")
                print(f"   Workflow: {data['analysis_results']['workflow']}")
                return True
            else:
                print(f"❌ Error: {data.get('message')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"   {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def main():
    print("="*60)
    print("🔧 FIXING CROSS-REGION LAMBDA ISSUE")
    print("="*60)
    print("\nProblem: API Gateway (ap-south-1) → Lambda (us-east-1)")
    print("Solution: Create Lambda in ap-south-1")
    print("="*60)
    
    # Step 1: Create Lambda in ap-south-1
    if create_lambda_in_same_region():
        print("\n⏳ Waiting for Lambda to be ready...")
        time.sleep(5)
        
        # Step 2: Update API Gateway
        if update_api_gateway_integration():
            print("\n⏳ Waiting for deployment...")
            time.sleep(5)
            
            # Step 3: Test
            if test_api():
                print("\n" + "="*60)
                print("🎉 API GATEWAY ROUTING FIXED!")
                print("="*60)
                print("\n✅ Your API is now fully operational:")
                print("   https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod/analyze")
                print("\n📝 Test command:")
                print("   python scripts/test_complete_system.py")
                print("\n💻 Frontend can now use the API!")
                print("="*60)
            else:
                print("\n⚠️  API deployed but test failed")
                print("   Wait 30 seconds and try: python scripts/test_complete_system.py")
        else:
            print("\n❌ API Gateway update failed")
    else:
        print("\n❌ Lambda creation failed")

if __name__ == "__main__":
    main()
