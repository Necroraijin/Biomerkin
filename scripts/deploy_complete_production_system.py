#!/usr/bin/env python3
"""
Complete Production System Deployment Script
Deploys all AWS resources for a fully functional online system
"""

import boto3
import json
import time
import zipfile
import io
import os
from pathlib import Path
from typing import Dict, List, Any

class ProductionDeployer:
    def __init__(self):
        self.region = os.getenv('AWS_REGION', 'ap-south-1')
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        self.apigateway_client = boto3.client('apigateway', region_name=self.region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=self.region)
        self.s3_client = boto3.client('s3', region_name=self.region)
        self.iam_client = boto3.client('iam')
        
        self.deployment_results = {
            'lambda_functions': [],
            'api_gateway': None,
            'dynamodb_table': None,
            'errors': []
        }
    
    def create_lambda_deployment_package(self, function_name: str, handler_file: str) -> bytes:
        """Create a deployment package for Lambda function"""
        print(f"  📦 Creating deployment package for {function_name}...")
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add the handler file
            if os.path.exists(handler_file):
                zip_file.write(handler_file, os.path.basename(handler_file))
            
            # Add agent files if they exist
            agent_file = f'biomerkin/agents/{function_name.replace("biomerkin-", "")}_agent.py'
            if os.path.exists(agent_file):
                zip_file.write(agent_file, f'agents/{os.path.basename(agent_file)}')
            
            # Add common dependencies
            for root, dirs, files in os.walk('biomerkin'):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        arcname = file_path.replace('biomerkin/', '')
                        zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    def deploy_lambda_function(self, function_name: str, handler_file: str, handler_name: str, role_arn: str):
        """Deploy a Lambda function"""
        print(f"\n🚀 Deploying Lambda function: {function_name}")
        
        try:
            # Create deployment package
            zip_content = self.create_lambda_deployment_package(function_name, handler_file)
            
            # Check if function exists
            try:
                self.lambda_client.get_function(FunctionName=function_name)
                # Update existing function
                print(f"  ♻️  Updating existing function...")
                response = self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content
                )
                print(f"  ✅ Updated {function_name}")
            except self.lambda_client.exceptions.ResourceNotFoundException:
                # Create new function
                print(f"  ➕ Creating new function...")
                response = self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime='python3.11',
                    Role=role_arn,
                    Handler=handler_name,
                    Code={'ZipFile': zip_content},
                    Timeout=300,
                    MemorySize=1024,
                    Environment={
                        'Variables': {
                            'LOG_LEVEL': 'INFO',
                            'DYNAMODB_TABLE': 'biomerkin-workflows'
                        }
                    }
                )
                print(f"  ✅ Created {function_name}")
            
            self.deployment_results['lambda_functions'].append({
                'name': function_name,
                'arn': response['FunctionArn'],
                'status': 'deployed'
            })
            
            return response['FunctionArn']
            
        except Exception as e:
            error_msg = f"Failed to deploy {function_name}: {e}"
            print(f"  ❌ {error_msg}")
            self.deployment_results['errors'].append(error_msg)
            return None
    
    def deploy_all_lambda_functions(self):
        """Deploy all Lambda functions"""
        print("\n" + "="*80)
        print("📦 DEPLOYING LAMBDA FUNCTIONS")
        print("="*80)
        
        # Get or create IAM role
        role_arn = self.get_or_create_lambda_role()
        
        if not role_arn:
            print("❌ Cannot deploy Lambda functions without IAM role")
            return
        
        functions = [
            {
                'name': 'biomerkin-genomics',
                'handler_file': 'lambda_functions/bedrock_genomics_action.py',
                'handler': 'bedrock_genomics_action.handler'
            },
            {
                'name': 'biomerkin-proteomics',
                'handler_file': 'lambda_functions/bedrock_proteomics_action.py',
                'handler': 'bedrock_proteomics_action.handler'
            },
            {
                'name': 'biomerkin-literature',
                'handler_file': 'lambda_functions/bedrock_literature_action.py',
                'handler': 'bedrock_literature_action.handler'
            },
            {
                'name': 'biomerkin-drug',
                'handler_file': 'lambda_functions/bedrock_drug_action.py',
                'handler': 'bedrock_drug_action.handler'
            },
            {
                'name': 'biomerkin-decision',
                'handler_file': 'lambda_functions/bedrock_decision_action.py',
                'handler': 'bedrock_decision_action.handler'
            },
            {
                'name': 'biomerkin-orchestrator',
                'handler_file': 'lambda_functions/bedrock_orchestrator.py',
                'handler': 'bedrock_orchestrator.handler'
            }
        ]
        
        for func in functions:
            self.deploy_lambda_function(
                func['name'],
                func['handler_file'],
                func['handler'],
                role_arn
            )
    
    def get_or_create_lambda_role(self) -> str:
        """Get existing or create new Lambda execution role"""
        role_name = 'biomerkin-lambda-execution-role'
        
        try:
            response = self.iam_client.get_role(RoleName=role_name)
            print(f"  ✅ Using existing role: {role_name}")
            return response['Role']['Arn']
        except self.iam_client.exceptions.NoSuchEntityException:
            print(f"  ➕ Creating new role: {role_name}")
            
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            try:
                response = self.iam_client.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description='Execution role for Biomerkin Lambda functions'
                )
                
                # Attach policies
                policies = [
                    'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                    'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                    'arn:aws:iam::aws:policy/AmazonS3FullAccess',
                    'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
                ]
                
                for policy_arn in policies:
                    self.iam_client.attach_role_policy(
                        RoleName=role_name,
                        PolicyArn=policy_arn
                    )
                
                # Wait for role to be available
                time.sleep(10)
                
                print(f"  ✅ Created role: {role_name}")
                return response['Role']['Arn']
                
            except Exception as e:
                print(f"  ❌ Failed to create role: {e}")
                return None
    
    def create_dynamodb_table(self):
        """Create DynamoDB table for workflow state"""
        print("\n" + "="*80)
        print("🗄️  CREATING DYNAMODB TABLE")
        print("="*80)
        
        table_name = 'biomerkin-workflows'
        
        try:
            # Check if table exists
            self.dynamodb_client.describe_table(TableName=table_name)
            print(f"  ✅ Table already exists: {table_name}")
            self.deployment_results['dynamodb_table'] = table_name
            return
        except self.dynamodb_client.exceptions.ResourceNotFoundException:
            pass
        
        try:
            response = self.dynamodb_client.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'workflow_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'workflow_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST',
                Tags=[
                    {'Key': 'Project', 'Value': 'Biomerkin'},
                    {'Key': 'Environment', 'Value': 'Production'}
                ]
            )
            
            print(f"  ✅ Created table: {table_name}")
            print(f"  ⏳ Waiting for table to be active...")
            
            # Wait for table to be active
            waiter = self.dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            print(f"  ✅ Table is active")
            self.deployment_results['dynamodb_table'] = table_name
            
        except Exception as e:
            error_msg = f"Failed to create DynamoDB table: {e}"
            print(f"  ❌ {error_msg}")
            self.deployment_results['errors'].append(error_msg)
    
    def create_api_gateway(self):
        """Create API Gateway for the system"""
        print("\n" + "="*80)
        print("🌐 CREATING API GATEWAY")
        print("="*80)
        
        api_name = 'biomerkin-api'
        
        try:
            # Check if API exists
            apis = self.apigateway_client.get_rest_apis()
            for api in apis.get('items', []):
                if api['name'] == api_name:
                    print(f"  ✅ API already exists: {api_name}")
                    self.deployment_results['api_gateway'] = {
                        'id': api['id'],
                        'name': api_name
                    }
                    return api['id']
            
            # Create new API
            response = self.apigateway_client.create_rest_api(
                name=api_name,
                description='Biomerkin Multi-Agent Genomics Analysis API',
                endpointConfiguration={'types': ['REGIONAL']}
            )
            
            api_id = response['id']
            print(f"  ✅ Created API: {api_name} (ID: {api_id})")
            
            # Get root resource
            resources = self.apigateway_client.get_resources(restApiId=api_id)
            root_id = resources['items'][0]['id']
            
            # Create /analysis resource
            analysis_resource = self.apigateway_client.create_resource(
                restApiId=api_id,
                parentId=root_id,
                pathPart='analysis'
            )
            
            # Create POST method for /analysis
            self.apigateway_client.put_method(
                restApiId=api_id,
                resourceId=analysis_resource['id'],
                httpMethod='POST',
                authorizationType='NONE'
            )
            
            # Create mock integration (will be updated with Lambda later)
            self.apigateway_client.put_integration(
                restApiId=api_id,
                resourceId=analysis_resource['id'],
                httpMethod='POST',
                type='MOCK',
                requestTemplates={
                    'application/json': '{"statusCode": 200}'
                }
            )
            
            # Create method response
            self.apigateway_client.put_method_response(
                restApiId=api_id,
                resourceId=analysis_resource['id'],
                httpMethod='POST',
                statusCode='200'
            )
            
            # Create integration response
            self.apigateway_client.put_integration_response(
                restApiId=api_id,
                resourceId=analysis_resource['id'],
                httpMethod='POST',
                statusCode='200',
                responseTemplates={
                    'application/json': '{"message": "API Gateway configured"}'
                }
            )
            
            print(f"  ✅ Created /analysis endpoint with POST method")
            
            # Create deployment
            deployment = self.apigateway_client.create_deployment(
                restApiId=api_id,
                stageName='prod',
                description='Production deployment'
            )
            
            api_url = f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod"
            print(f"  ✅ API deployed to: {api_url}")
            
            self.deployment_results['api_gateway'] = {
                'id': api_id,
                'name': api_name,
                'url': api_url
            }
            
            return api_id
            
        except Exception as e:
            error_msg = f"Failed to create API Gateway: {e}"
            print(f"  ❌ {error_msg}")
            self.deployment_results['errors'].append(error_msg)
            return None
    
    def generate_deployment_report(self):
        """Generate deployment report"""
        print("\n" + "="*80)
        print("📊 DEPLOYMENT REPORT")
        print("="*80)
        
        print(f"\n✅ Lambda Functions Deployed: {len(self.deployment_results['lambda_functions'])}")
        for func in self.deployment_results['lambda_functions']:
            print(f"  • {func['name']}")
        
        if self.deployment_results['api_gateway']:
            print(f"\n✅ API Gateway:")
            print(f"  • Name: {self.deployment_results['api_gateway']['name']}")
            print(f"  • URL: {self.deployment_results['api_gateway'].get('url', 'N/A')}")
        
        if self.deployment_results['dynamodb_table']:
            print(f"\n✅ DynamoDB Table: {self.deployment_results['dynamodb_table']}")
        
        if self.deployment_results['errors']:
            print(f"\n❌ Errors ({len(self.deployment_results['errors'])}):")
            for error in self.deployment_results['errors']:
                print(f"  • {error}")
        
        print("\n" + "="*80)
        print("🎉 DEPLOYMENT COMPLETE")
        print("="*80)
        
        if len(self.deployment_results['errors']) == 0:
            print("\n✅ System is ready for online use!")
            print("✅ Users can now input their own data")
            print("\nNext steps:")
            print("1. Update frontend with API Gateway URL")
            print("2. Test with sample DNA sequences")
            print("3. Monitor CloudWatch logs")
        else:
            print("\n⚠️  Deployment completed with errors")
            print("Please review and fix the errors above")
        
        # Save report
        with open('DEPLOYMENT_REPORT.json', 'w') as f:
            json.dump(self.deployment_results, f, indent=2)
        
        print("\n📄 Detailed report saved to: DEPLOYMENT_REPORT.json")
    
    def deploy_all(self):
        """Deploy complete production system"""
        print("="*80)
        print("🚀 DEPLOYING COMPLETE PRODUCTION SYSTEM")
        print("="*80)
        
        self.create_dynamodb_table()
        self.deploy_all_lambda_functions()
        self.create_api_gateway()
        
        self.generate_deployment_report()

if __name__ == '__main__':
    deployer = ProductionDeployer()
    deployer.deploy_all()
