#!/usr/bin/env python3
"""
Automated AWS deployment script for Biomerkin.
Perfect for beginners - handles everything automatically!
"""

import boto3
import json
import time
import zipfile
import os
import sys
from pathlib import Path
from datetime import datetime
import subprocess

class BiomerkinAWSDeployer:
    """Automated AWS deployment for Biomerkin system."""
    
    def __init__(self):
        self.region = 'us-east-1'
        self.project_name = 'biomerkin'
        self.deployment_id = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        # AWS clients
        self.lambda_client = None
        self.apigateway_client = None
        self.dynamodb_client = None
        self.s3_client = None
        self.iam_client = None
        self.bedrock_client = None
        
        # Deployment results
        self.deployment_results = {
            'timestamp': datetime.now().isoformat(),
            'resources_created': [],
            'endpoints': {},
            'errors': []
        }
    
    def print_step(self, step_num, title, description=""):
        """Print deployment step with formatting."""
        print(f"\n{'='*60}")
        print(f"🚀 STEP {step_num}: {title}")
        print(f"{'='*60}")
        if description:
            print(f"📋 {description}")
        print()
    
    def check_aws_setup(self):
        """Check if AWS is properly configured."""
        self.print_step(1, "Checking AWS Setup", "Verifying your AWS credentials and permissions")
        
        try:
            # Test AWS credentials
            sts_client = boto3.client('sts', region_name=self.region)
            identity = sts_client.get_caller_identity()
            
            print(f"✅ AWS Account ID: {identity['Account']}")
            print(f"✅ User/Role: {identity['Arn']}")
            print(f"✅ Region: {self.region}")
            
            # Initialize AWS clients
            self.lambda_client = boto3.client('lambda', region_name=self.region)
            self.apigateway_client = boto3.client('apigateway', region_name=self.region)
            self.dynamodb_client = boto3.client('dynamodb', region_name=self.region)
            self.s3_client = boto3.client('s3', region_name=self.region)
            self.iam_client = boto3.client('iam', region_name=self.region)
            
            try:
                self.bedrock_client = boto3.client('bedrock-runtime', region_name=self.region)
                print("✅ Bedrock access configured")
            except Exception as e:
                print(f"⚠️ Bedrock access issue: {e}")
                print("   You may need to request Bedrock access in AWS Console")
            
            return True
            
        except Exception as e:
            print(f"❌ AWS Setup Error: {e}")
            print("\n🔧 TROUBLESHOOTING:")
            print("1. Run: aws configure")
            print("2. Enter your Access Key ID and Secret Access Key")
            print("3. Set region to: us-east-1")
            return False
    
    def create_iam_role(self):
        """Create IAM role for Lambda functions."""
        self.print_step(2, "Creating IAM Role", "Setting up permissions for Lambda functions")
        
        role_name = f"{self.project_name}-lambda-role"
        
        # Trust policy for Lambda
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
            # Check if role exists
            try:
                role = self.iam_client.get_role(RoleName=role_name)
                print(f"✅ IAM Role already exists: {role_name}")
                return role['Role']['Arn']
            except self.iam_client.exceptions.NoSuchEntityException:
                pass
            
            # Create role
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"Lambda execution role for {self.project_name}"
            )
            
            role_arn = response['Role']['Arn']
            print(f"✅ Created IAM Role: {role_name}")
            
            # Attach policies
            policies = [
                'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
                'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess',
                'arn:aws:iam::aws:policy/AmazonS3FullAccess'
            ]
            
            for policy_arn in policies:
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
                print(f"✅ Attached policy: {policy_arn.split('/')[-1]}")
            
            # Create custom Bedrock policy
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
                self.iam_client.create_policy(
                    PolicyName=f"{self.project_name}-bedrock-policy",
                    PolicyDocument=json.dumps(bedrock_policy),
                    Description="Bedrock access for Biomerkin"
                )
                
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:policy/{self.project_name}-bedrock-policy"
                )
                print("✅ Created and attached Bedrock policy")
            except Exception as e:
                print(f"⚠️ Bedrock policy creation failed: {e}")
            
            # Wait for role to be ready
            print("⏳ Waiting for IAM role to be ready...")
            time.sleep(10)
            
            self.deployment_results['resources_created'].append(f"IAM Role: {role_name}")
            return role_arn
            
        except Exception as e:
            print(f"❌ IAM Role creation failed: {e}")
            self.deployment_results['errors'].append(f"IAM Role: {e}")
            return None
    
    def create_dynamodb_table(self):
        """Create DynamoDB table for workflow state."""
        self.print_step(3, "Creating DynamoDB Table", "Setting up database for workflow management")
        
        table_name = f"{self.project_name}-workflows"
        
        try:
            # Check if table exists
            try:
                response = self.dynamodb_client.describe_table(TableName=table_name)
                print(f"✅ DynamoDB table already exists: {table_name}")
                return table_name
            except self.dynamodb_client.exceptions.ResourceNotFoundException:
                pass
            
            # Create table
            response = self.dynamodb_client.create_table(
                TableName=table_name,
                KeySchema=[
                    {'AttributeName': 'workflow_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'workflow_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'N'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            print(f"✅ Created DynamoDB table: {table_name}")
            
            # Wait for table to be ready
            print("⏳ Waiting for table to be active...")
            waiter = self.dynamodb_client.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            
            self.deployment_results['resources_created'].append(f"DynamoDB Table: {table_name}")
            return table_name
            
        except Exception as e:
            print(f"❌ DynamoDB table creation failed: {e}")
            self.deployment_results['errors'].append(f"DynamoDB: {e}")
            return None
    
    def create_s3_bucket(self):
        """Create S3 bucket for frontend hosting."""
        self.print_step(4, "Creating S3 Bucket", "Setting up storage for frontend and data")
        
        bucket_name = f"{self.project_name}-frontend-{self.deployment_id}"
        
        try:
            # Create bucket
            if self.region == 'us-east-1':
                # us-east-1 doesn't need LocationConstraint
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            print(f"✅ Created S3 bucket: {bucket_name}")
            
            # Configure for static website hosting
            website_config = {
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'index.html'}
            }
            
            self.s3_client.put_bucket_website(
                Bucket=bucket_name,
                WebsiteConfiguration=website_config
            )
            
            # Remove block public access settings first
            try:
                self.s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': False,
                        'IgnorePublicAcls': False,
                        'BlockPublicPolicy': False,
                        'RestrictPublicBuckets': False
                    }
                )
                print("✅ Removed block public access settings")
                
                # Wait for settings to propagate
                time.sleep(3)
                
            except Exception as e:
                print(f"⚠️ Could not modify public access settings: {e}")
            
            # Make bucket public for website hosting
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/*"
                    }
                ]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            print("✅ Configured S3 bucket for website hosting")
            
            website_url = f"http://{bucket_name}.s3-website-{self.region}.amazonaws.com"
            self.deployment_results['endpoints']['frontend'] = website_url
            self.deployment_results['resources_created'].append(f"S3 Bucket: {bucket_name}")
            
            return bucket_name, website_url
            
        except Exception as e:
            print(f"❌ S3 bucket creation failed: {e}")
            self.deployment_results['errors'].append(f"S3: {e}")
            return None, None
    
    def package_lambda_function(self, agent_name):
        """Package Lambda function code."""
        print(f"📦 Packaging {agent_name} Lambda function...")
        
        # Create temporary directory for packaging
        package_dir = Path(f"temp_lambda_{agent_name}")
        package_dir.mkdir(exist_ok=True)
        
        try:
            # Copy agent code
            agent_file = Path(f"biomerkin/agents/{agent_name}_agent.py")
            if agent_file.exists():
                import shutil
                shutil.copy2(agent_file, package_dir / "lambda_function.py")
                
                # Copy dependencies
                for dep_dir in ['biomerkin/models', 'biomerkin/utils']:
                    if Path(dep_dir).exists():
                        shutil.copytree(dep_dir, package_dir / dep_dir, dirs_exist_ok=True)
                
                # Create simple lambda handler
                handler_code = f'''
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from {agent_name}_agent import {agent_name.title()}Agent

def lambda_handler(event, context):
    """Lambda handler for {agent_name} agent."""
    try:
        agent = {agent_name.title()}Agent()
        result = agent.execute(event.get('input_data', {{}}))
        
        return {{
            'statusCode': 200,
            'body': result,
            'headers': {{
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }}
        }}
    except Exception as e:
        return {{
            'statusCode': 500,
            'body': {{'error': str(e)}},
            'headers': {{
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }}
        }}
'''
                
                with open(package_dir / "lambda_function.py", 'w') as f:
                    f.write(handler_code)
                
                # Create ZIP file
                zip_path = f"{agent_name}_lambda.zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(package_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, package_dir)
                            zipf.write(file_path, arcname)
                
                print(f"✅ Packaged {agent_name} Lambda function")
                
                # Cleanup
                shutil.rmtree(package_dir)
                
                return zip_path
            else:
                print(f"⚠️ Agent file not found: {agent_file}")
                return None
                
        except Exception as e:
            print(f"❌ Failed to package {agent_name}: {e}")
            return None
    
    def deploy_lambda_functions(self, role_arn):
        """Deploy Lambda functions for all agents."""
        self.print_step(5, "Deploying Lambda Functions", "Creating serverless functions for each AI agent")
        
        agents = ['genomics', 'proteomics', 'literature', 'drug', 'decision']
        lambda_arns = {}
        
        for agent in agents:
            try:
                print(f"\n🚀 Deploying {agent.title()}Agent...")
                
                function_name = f"{self.project_name}-{agent}-agent"
                
                # Package function
                zip_path = self.package_lambda_function(agent)
                if not zip_path:
                    continue
                
                # Read ZIP file
                with open(zip_path, 'rb') as f:
                    zip_content = f.read()
                
                # Check if function exists
                try:
                    self.lambda_client.get_function(FunctionName=function_name)
                    # Update existing function
                    response = self.lambda_client.update_function_code(
                        FunctionName=function_name,
                        ZipFile=zip_content
                    )
                    print(f"✅ Updated existing Lambda function: {function_name}")
                except self.lambda_client.exceptions.ResourceNotFoundException:
                    # Create new function
                    response = self.lambda_client.create_function(
                        FunctionName=function_name,
                        Runtime='python3.9',
                        Role=role_arn,
                        Handler='lambda_function.lambda_handler',
                        Code={'ZipFile': zip_content},
                        Description=f"Biomerkin {agent.title()} Agent",
                        Timeout=300,  # 5 minutes
                        MemorySize=1024,
                        Environment={
                            'Variables': {
                                'AGENT_TYPE': agent,
                                'BIOMERKIN_REGION': self.region
                            }
                        }
                    )
                    print(f"✅ Created Lambda function: {function_name}")
                
                lambda_arns[agent] = response['FunctionArn']
                self.deployment_results['resources_created'].append(f"Lambda Function: {function_name}")
                
                # Cleanup ZIP file
                os.remove(zip_path)
                
            except Exception as e:
                print(f"❌ Failed to deploy {agent} Lambda: {e}")
                self.deployment_results['errors'].append(f"Lambda {agent}: {e}")
        
        return lambda_arns
    
    def create_api_gateway(self, lambda_arns):
        """Create API Gateway for REST endpoints."""
        self.print_step(6, "Creating API Gateway", "Setting up REST API endpoints")
        
        api_name = f"{self.project_name}-api"
        
        try:
            # Create REST API
            response = self.apigateway_client.create_rest_api(
                name=api_name,
                description="Biomerkin Multi-Agent Genomics API",
                endpointConfiguration={'types': ['REGIONAL']}
            )
            
            api_id = response['id']
            print(f"✅ Created API Gateway: {api_name}")
            
            # Get root resource
            resources = self.apigateway_client.get_resources(restApiId=api_id)
            root_id = None
            for resource in resources['items']:
                if resource['path'] == '/':
                    root_id = resource['id']
                    break
            
            # Create resources and methods for each agent
            for agent, lambda_arn in lambda_arns.items():
                try:
                    # Create resource
                    resource_response = self.apigateway_client.create_resource(
                        restApiId=api_id,
                        parentId=root_id,
                        pathPart=agent
                    )
                    
                    resource_id = resource_response['id']
                    
                    # Create POST method
                    self.apigateway_client.put_method(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod='POST',
                        authorizationType='NONE'
                    )
                    
                    # Set up Lambda integration
                    lambda_uri = f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
                    
                    self.apigateway_client.put_integration(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod='POST',
                        type='AWS_PROXY',
                        integrationHttpMethod='POST',
                        uri=lambda_uri
                    )
                    
                    print(f"✅ Created endpoint: /{agent}")
                    
                except Exception as e:
                    print(f"⚠️ Failed to create endpoint for {agent}: {e}")
            
            # Deploy API
            deployment_response = self.apigateway_client.create_deployment(
                restApiId=api_id,
                stageName='prod',
                description='Production deployment'
            )
            
            api_url = f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod"
            self.deployment_results['endpoints']['api'] = api_url
            self.deployment_results['resources_created'].append(f"API Gateway: {api_name}")
            
            print(f"✅ API deployed at: {api_url}")
            
            return api_id, api_url
            
        except Exception as e:
            print(f"❌ API Gateway creation failed: {e}")
            self.deployment_results['errors'].append(f"API Gateway: {e}")
            return None, None
    
    def deploy_frontend(self, bucket_name):
        """Deploy frontend to S3."""
        self.print_step(7, "Deploying Frontend", "Uploading React application to S3")
        
        try:
            frontend_dir = Path("frontend/build")
            
            if not frontend_dir.exists():
                print("⚠️ Frontend build not found. Building now...")
                
                # Build frontend
                result = subprocess.run(
                    ["npm", "run", "build"],
                    cwd="frontend",
                    capture_output=True,
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"❌ Frontend build failed: {result.stderr}")
                    return False
                
                print("✅ Frontend built successfully")
            
            # Upload files to S3
            uploaded_files = 0
            for root, dirs, files in os.walk(frontend_dir):
                for file in files:
                    local_path = os.path.join(root, file)
                    s3_path = os.path.relpath(local_path, frontend_dir)
                    
                    # Determine content type
                    content_type = 'text/html'
                    if file.endswith('.js'):
                        content_type = 'application/javascript'
                    elif file.endswith('.css'):
                        content_type = 'text/css'
                    elif file.endswith('.json'):
                        content_type = 'application/json'
                    elif file.endswith('.png'):
                        content_type = 'image/png'
                    elif file.endswith('.jpg') or file.endswith('.jpeg'):
                        content_type = 'image/jpeg'
                    
                    self.s3_client.upload_file(
                        local_path,
                        bucket_name,
                        s3_path,
                        ExtraArgs={'ContentType': content_type}
                    )
                    
                    uploaded_files += 1
            
            print(f"✅ Uploaded {uploaded_files} files to S3")
            return True
            
        except Exception as e:
            print(f"❌ Frontend deployment failed: {e}")
            self.deployment_results['errors'].append(f"Frontend: {e}")
            return False
    
    def test_deployment(self):
        """Test the deployed system."""
        self.print_step(8, "Testing Deployment", "Verifying all components are working")
        
        try:
            # Test API endpoints
            api_url = self.deployment_results['endpoints'].get('api')
            if api_url:
                import requests
                
                # Test a simple endpoint
                test_url = f"{api_url}/genomics"
                test_data = {
                    "input_data": {
                        "sequence_data": "ATGCGATCGATCG",
                        "reference_genome": "GRCh38"
                    }
                }
                
                try:
                    response = requests.post(test_url, json=test_data, timeout=30)
                    if response.status_code == 200:
                        print("✅ API endpoint test passed")
                    else:
                        print(f"⚠️ API endpoint returned status: {response.status_code}")
                except Exception as e:
                    print(f"⚠️ API endpoint test failed: {e}")
            
            # Test frontend
            frontend_url = self.deployment_results['endpoints'].get('frontend')
            if frontend_url:
                try:
                    response = requests.get(frontend_url, timeout=10)
                    if response.status_code == 200:
                        print("✅ Frontend test passed")
                    else:
                        print(f"⚠️ Frontend returned status: {response.status_code}")
                except Exception as e:
                    print(f"⚠️ Frontend test failed: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Deployment testing failed: {e}")
            return False
    
    def generate_deployment_report(self):
        """Generate final deployment report."""
        self.print_step(9, "Deployment Complete!", "Your Biomerkin system is now live on AWS")
        
        print("🎉 DEPLOYMENT SUCCESSFUL!")
        print("\n📋 DEPLOYMENT SUMMARY:")
        print(f"   • Resources Created: {len(self.deployment_results['resources_created'])}")
        print(f"   • Errors: {len(self.deployment_results['errors'])}")
        
        print("\n🌐 YOUR LIVE URLS:")
        for name, url in self.deployment_results['endpoints'].items():
            print(f"   • {name.title()}: {url}")
        
        print("\n📦 RESOURCES CREATED:")
        for resource in self.deployment_results['resources_created']:
            print(f"   ✅ {resource}")
        
        if self.deployment_results['errors']:
            print("\n⚠️ ERRORS ENCOUNTERED:")
            for error in self.deployment_results['errors']:
                print(f"   ❌ {error}")
        
        # Save deployment info
        with open(f"deployment_info_{self.deployment_id}.json", 'w') as f:
            json.dump(self.deployment_results, f, indent=2)
        
        print(f"\n📄 Deployment details saved to: deployment_info_{self.deployment_id}.json")
        
        print("\n🎯 NEXT STEPS:")
        print("1. Test your demo scenarios:")
        print("   python demo/judge_demo_runner.py --aws-mode")
        print("\n2. Share your frontend URL with hackathon judges")
        print("\n3. Use CloudWatch to monitor your system:")
        print("   https://console.aws.amazon.com/cloudwatch/")
        
        return True
    
    def deploy(self):
        """Run complete deployment process."""
        print("🚀 BIOMERKIN AWS DEPLOYMENT STARTING")
        print("="*60)
        print("This will deploy your entire system to AWS automatically!")
        print("Estimated time: 15-20 minutes")
        print()
        
        # Step-by-step deployment
        if not self.check_aws_setup():
            return False
        
        role_arn = self.create_iam_role()
        if not role_arn:
            return False
        
        table_name = self.create_dynamodb_table()
        if not table_name:
            return False
        
        bucket_name, website_url = self.create_s3_bucket()
        if not bucket_name:
            return False
        
        lambda_arns = self.deploy_lambda_functions(role_arn)
        if not lambda_arns:
            return False
        
        api_id, api_url = self.create_api_gateway(lambda_arns)
        if not api_id:
            return False
        
        if not self.deploy_frontend(bucket_name):
            return False
        
        self.test_deployment()
        
        return self.generate_deployment_report()


def main():
    """Main deployment function."""
    deployer = BiomerkinAWSDeployer()
    
    try:
        success = deployer.deploy()
        
        if success:
            print("\n🎉 DEPLOYMENT SUCCESSFUL!")
            print("Your Biomerkin system is now live on AWS!")
            return 0
        else:
            print("\n❌ DEPLOYMENT FAILED!")
            print("Check the errors above and try again.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️ Deployment cancelled by user")
        return 1
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)