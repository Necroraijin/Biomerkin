#!/usr/bin/env python3
"""
Deployment script for Enhanced Bedrock Agent Orchestration components.
This script deploys the enhanced orchestration service and Lambda functions
with all necessary AWS resources and configurations.
"""

import json
import boto3
import logging
import time
import zipfile
import os
import sys
from typing import Dict, Any, List
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from biomerkin.utils.logging_config import get_logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)


class EnhancedOrchestrationDeployer:
    """
    Deployer for enhanced Bedrock Agent orchestration components.
    
    This class handles the deployment of:
    1. Enhanced orchestration Lambda function
    2. IAM roles and policies for orchestration
    3. DynamoDB tables for orchestration state
    4. CloudWatch log groups and metrics
    5. API Gateway endpoints for orchestration
    """
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the deployer."""
        self.region = region
        self.logger = get_logger(__name__)
        
        # Initialize AWS clients
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.dynamodb_client = boto3.client('dynamodb', region_name=region)
        self.logs_client = boto3.client('logs', region_name=region)
        self.apigateway_client = boto3.client('apigateway', region_name=region)
        self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=region)
        
        # Deployment configuration
        self.function_name = 'biomerkin-enhanced-orchestrator'
        self.role_name = 'BiomerkinEnhancedOrchestrationRole'
        self.table_name = 'BiomerkinOrchestrationState'
        self.log_group_name = f'/aws/lambda/{self.function_name}'
        
        # Get account ID
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
    
    def deploy_all_components(self) -> Dict[str, Any]:
        """Deploy all enhanced orchestration components."""
        deployment_results = {
            'deployment_id': f"enhanced_orchestration_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'region': self.region,
            'account_id': self.account_id,
            'components': {}
        }
        
        try:
            self.logger.info("Starting enhanced orchestration deployment...")
            
            # Step 1: Create IAM role and policies
            self.logger.info("Creating IAM role and policies...")
            iam_result = self._create_iam_resources()
            deployment_results['components']['iam'] = iam_result
            
            # Step 2: Create DynamoDB table for orchestration state
            self.logger.info("Creating DynamoDB table...")
            dynamodb_result = self._create_dynamodb_table()
            deployment_results['components']['dynamodb'] = dynamodb_result
            
            # Step 3: Create CloudWatch log group
            self.logger.info("Creating CloudWatch log group...")
            logs_result = self._create_log_group()
            deployment_results['components']['logs'] = logs_result
            
            # Step 4: Package and deploy Lambda function
            self.logger.info("Packaging and deploying Lambda function...")
            lambda_result = self._deploy_lambda_function(iam_result['role_arn'])
            deployment_results['components']['lambda'] = lambda_result
            
            # Step 5: Create API Gateway endpoints
            self.logger.info("Creating API Gateway endpoints...")
            api_result = self._create_api_gateway()
            deployment_results['components']['api_gateway'] = api_result
            
            # Step 6: Configure Bedrock Agent permissions
            self.logger.info("Configuring Bedrock Agent permissions...")
            bedrock_result = self._configure_bedrock_permissions()
            deployment_results['components']['bedrock'] = bedrock_result
            
            # Step 7: Test deployment
            self.logger.info("Testing deployment...")
            test_result = self._test_deployment()
            deployment_results['components']['test'] = test_result
            
            deployment_results['success'] = True
            deployment_results['message'] = 'Enhanced orchestration deployment completed successfully'
            
            self.logger.info("Enhanced orchestration deployment completed successfully!")
            return deployment_results
            
        except Exception as e:
            self.logger.error(f"Error during deployment: {str(e)}")
            deployment_results['success'] = False
            deployment_results['error'] = str(e)
            return deployment_results
    
    def _create_iam_resources(self) -> Dict[str, Any]:
        """Create IAM role and policies for enhanced orchestration."""
        try:
            # Trust policy for Lambda and Bedrock Agents
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": [
                                "lambda.amazonaws.com",
                                "bedrock.amazonaws.com"
                            ]
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            # Enhanced orchestration policy
            orchestration_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
                        ],
                        "Resource": f"arn:aws:logs:{self.region}:{self.account_id}:*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "bedrock:InvokeModel",
                            "bedrock:InvokeModelWithResponseStream"
                        ],
                        "Resource": "*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "bedrock-agent:InvokeAgent",
                            "bedrock-agent:CreateAgent",
                            "bedrock-agent:GetAgent",
                            "bedrock-agent:ListAgents",
                            "bedrock-agent:UpdateAgent",
                            "bedrock-agent:PrepareAgent",
                            "bedrock-agent:CreateAgentActionGroup",
                            "bedrock-agent:GetAgentActionGroup",
                            "bedrock-agent:ListAgentActionGroups"
                        ],
                        "Resource": "*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "dynamodb:GetItem",
                            "dynamodb:PutItem",
                            "dynamodb:UpdateItem",
                            "dynamodb:DeleteItem",
                            "dynamodb:Query",
                            "dynamodb:Scan"
                        ],
                        "Resource": f"arn:aws:dynamodb:{self.region}:{self.account_id}:table/{self.table_name}"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "lambda:InvokeFunction"
                        ],
                        "Resource": f"arn:aws:lambda:{self.region}:{self.account_id}:function:biomerkin-*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "cloudwatch:PutMetricData",
                            "cloudwatch:GetMetricStatistics"
                        ],
                        "Resource": "*"
                    }
                ]
            }
            
            # Create role
            try:
                self.iam_client.create_role(
                    RoleName=self.role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description='Enhanced orchestration role for Biomerkin multi-agent workflows'
                )
                self.logger.info(f"Created IAM role: {self.role_name}")
            except self.iam_client.exceptions.EntityAlreadyExistsException:
                self.logger.info(f"IAM role {self.role_name} already exists")
            
            # Create and attach policy
            policy_name = f"{self.role_name}Policy"
            policy_arn = f"arn:aws:iam::{self.account_id}:policy/{policy_name}"
            
            try:
                self.iam_client.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(orchestration_policy),
                    Description='Policy for enhanced Bedrock Agent orchestration'
                )
                self.logger.info(f"Created IAM policy: {policy_name}")
            except self.iam_client.exceptions.EntityAlreadyExistsException:
                self.logger.info(f"IAM policy {policy_name} already exists")
            
            # Attach policy to role
            self.iam_client.attach_role_policy(
                RoleName=self.role_name,
                PolicyArn=policy_arn
            )
            
            # Wait for role to be available
            time.sleep(10)
            
            role_arn = f"arn:aws:iam::{self.account_id}:role/{self.role_name}"
            
            return {
                'success': True,
                'role_name': self.role_name,
                'role_arn': role_arn,
                'policy_name': policy_name,
                'policy_arn': policy_arn
            }
            
        except Exception as e:
            self.logger.error(f"Error creating IAM resources: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_dynamodb_table(self) -> Dict[str, Any]:
        """Create DynamoDB table for orchestration state management."""
        try:
            table_definition = {
                'TableName': self.table_name,
                'KeySchema': [
                    {
                        'AttributeName': 'session_id',
                        'KeyType': 'HASH'
                    }
                ],
                'AttributeDefinitions': [
                    {
                        'AttributeName': 'session_id',
                        'AttributeType': 'S'
                    }
                ],
                'BillingMode': 'PAY_PER_REQUEST',
                'Tags': [
                    {
                        'Key': 'Project',
                        'Value': 'Biomerkin'
                    },
                    {
                        'Key': 'Component',
                        'Value': 'EnhancedOrchestration'
                    }
                ]
            }
            
            try:
                response = self.dynamodb_client.create_table(**table_definition)
                self.logger.info(f"Created DynamoDB table: {self.table_name}")
                
                # Wait for table to be active
                waiter = self.dynamodb_client.get_waiter('table_exists')
                waiter.wait(TableName=self.table_name)
                
                return {
                    'success': True,
                    'table_name': self.table_name,
                    'table_arn': response['TableDescription']['TableArn']
                }
                
            except self.dynamodb_client.exceptions.ResourceInUseException:
                self.logger.info(f"DynamoDB table {self.table_name} already exists")
                
                # Get existing table info
                response = self.dynamodb_client.describe_table(TableName=self.table_name)
                
                return {
                    'success': True,
                    'table_name': self.table_name,
                    'table_arn': response['Table']['TableArn'],
                    'already_exists': True
                }
                
        except Exception as e:
            self.logger.error(f"Error creating DynamoDB table: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_log_group(self) -> Dict[str, Any]:
        """Create CloudWatch log group for orchestration logging."""
        try:
            try:
                self.logs_client.create_log_group(
                    logGroupName=self.log_group_name,
                    tags={
                        'Project': 'Biomerkin',
                        'Component': 'EnhancedOrchestration'
                    }
                )
                self.logger.info(f"Created CloudWatch log group: {self.log_group_name}")
                
            except self.logs_client.exceptions.ResourceAlreadyExistsException:
                self.logger.info(f"CloudWatch log group {self.log_group_name} already exists")
            
            # Set retention policy
            self.logs_client.put_retention_policy(
                logGroupName=self.log_group_name,
                retentionInDays=30
            )
            
            return {
                'success': True,
                'log_group_name': self.log_group_name,
                'log_group_arn': f"arn:aws:logs:{self.region}:{self.account_id}:log-group:{self.log_group_name}"
            }
            
        except Exception as e:
            self.logger.error(f"Error creating log group: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _deploy_lambda_function(self, role_arn: str) -> Dict[str, Any]:
        """Package and deploy the enhanced orchestration Lambda function."""
        try:
            # Create deployment package
            package_path = self._create_deployment_package()
            
            # Lambda function configuration
            function_config = {
                'FunctionName': self.function_name,
                'Runtime': 'python3.9',
                'Role': role_arn,
                'Handler': 'enhanced_bedrock_orchestrator.handler',
                'Code': {
                    'ZipFile': open(package_path, 'rb').read()
                },
                'Description': 'Enhanced Bedrock Agent orchestration for autonomous multi-agent workflows',
                'Timeout': 900,  # 15 minutes
                'MemorySize': 1024,
                'Environment': {
                    'Variables': {
                        'ORCHESTRATION_TABLE_NAME': self.table_name,
                        'AWS_REGION': self.region,
                        'LOG_LEVEL': 'INFO'
                    }
                },
                'Tags': {
                    'Project': 'Biomerkin',
                    'Component': 'EnhancedOrchestration'
                }
            }
            
            try:
                # Create function
                response = self.lambda_client.create_function(**function_config)
                self.logger.info(f"Created Lambda function: {self.function_name}")
                
            except self.lambda_client.exceptions.ResourceConflictException:
                # Update existing function
                self.logger.info(f"Lambda function {self.function_name} already exists, updating...")
                
                # Update function code
                self.lambda_client.update_function_code(
                    FunctionName=self.function_name,
                    ZipFile=open(package_path, 'rb').read()
                )
                
                # Update function configuration
                config_update = function_config.copy()
                del config_update['Code']
                del config_update['FunctionName']
                
                response = self.lambda_client.update_function_configuration(
                    FunctionName=self.function_name,
                    **config_update
                )
            
            # Clean up deployment package
            os.remove(package_path)
            
            return {
                'success': True,
                'function_name': self.function_name,
                'function_arn': response['FunctionArn'],
                'version': response['Version']
            }
            
        except Exception as e:
            self.logger.error(f"Error deploying Lambda function: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_deployment_package(self) -> str:
        """Create deployment package for Lambda function."""
        package_path = '/tmp/enhanced_orchestration_package.zip'
        
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add Lambda function code
            lambda_file = 'lambda_functions/enhanced_bedrock_orchestrator.py'
            if os.path.exists(lambda_file):
                zip_file.write(lambda_file, 'enhanced_bedrock_orchestrator.py')
            
            # Add biomerkin package
            biomerkin_dir = 'biomerkin'
            if os.path.exists(biomerkin_dir):
                for root, dirs, files in os.walk(biomerkin_dir):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            arc_path = os.path.join('biomerkin', os.path.relpath(file_path, biomerkin_dir))
                            zip_file.write(file_path, arc_path)
        
        return package_path
    
    def _create_api_gateway(self) -> Dict[str, Any]:
        """Create API Gateway endpoints for orchestration."""
        try:
            # Create REST API
            api_name = 'biomerkin-enhanced-orchestration-api'
            
            try:
                api_response = self.apigateway_client.create_rest_api(
                    name=api_name,
                    description='Enhanced orchestration API for Biomerkin multi-agent workflows',
                    tags={
                        'Project': 'Biomerkin',
                        'Component': 'EnhancedOrchestration'
                    }
                )
                api_id = api_response['id']
                self.logger.info(f"Created API Gateway: {api_name}")
                
            except Exception as e:
                # Try to find existing API
                apis = self.apigateway_client.get_rest_apis()
                api_id = None
                for api in apis['items']:
                    if api['name'] == api_name:
                        api_id = api['id']
                        break
                
                if not api_id:
                    raise e
                
                self.logger.info(f"Using existing API Gateway: {api_name}")
            
            # Get root resource
            resources = self.apigateway_client.get_resources(restApiId=api_id)
            root_resource_id = None
            for resource in resources['items']:
                if resource['path'] == '/':
                    root_resource_id = resource['id']
                    break
            
            # Create orchestration resource
            try:
                orchestration_resource = self.apigateway_client.create_resource(
                    restApiId=api_id,
                    parentId=root_resource_id,
                    pathPart='orchestrate'
                )
                orchestration_resource_id = orchestration_resource['id']
                
            except Exception:
                # Resource might already exist
                resources = self.apigateway_client.get_resources(restApiId=api_id)
                orchestration_resource_id = None
                for resource in resources['items']:
                    if resource.get('pathPart') == 'orchestrate':
                        orchestration_resource_id = resource['id']
                        break
                
                if not orchestration_resource_id:
                    raise
            
            # Create POST method
            try:
                self.apigateway_client.put_method(
                    restApiId=api_id,
                    resourceId=orchestration_resource_id,
                    httpMethod='POST',
                    authorizationType='NONE'
                )
                
                # Create integration
                lambda_arn = f"arn:aws:lambda:{self.region}:{self.account_id}:function:{self.function_name}"
                integration_uri = f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations"
                
                self.apigateway_client.put_integration(
                    restApiId=api_id,
                    resourceId=orchestration_resource_id,
                    httpMethod='POST',
                    type='AWS_PROXY',
                    integrationHttpMethod='POST',
                    uri=integration_uri
                )
                
            except Exception as e:
                self.logger.warning(f"Method/integration might already exist: {str(e)}")
            
            # Deploy API
            deployment = self.apigateway_client.create_deployment(
                restApiId=api_id,
                stageName='prod',
                description='Enhanced orchestration API deployment'
            )
            
            api_url = f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod/orchestrate"
            
            return {
                'success': True,
                'api_id': api_id,
                'api_name': api_name,
                'api_url': api_url,
                'deployment_id': deployment['id']
            }
            
        except Exception as e:
            self.logger.error(f"Error creating API Gateway: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _configure_bedrock_permissions(self) -> Dict[str, Any]:
        """Configure Bedrock Agent permissions for orchestration."""
        try:
            # Add Lambda invoke permission for API Gateway
            try:
                self.lambda_client.add_permission(
                    FunctionName=self.function_name,
                    StatementId='AllowAPIGatewayInvoke',
                    Action='lambda:InvokeFunction',
                    Principal='apigateway.amazonaws.com'
                )
                self.logger.info("Added API Gateway invoke permission to Lambda function")
                
            except Exception as e:
                self.logger.warning(f"Permission might already exist: {str(e)}")
            
            return {
                'success': True,
                'permissions_configured': True
            }
            
        except Exception as e:
            self.logger.error(f"Error configuring Bedrock permissions: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _test_deployment(self) -> Dict[str, Any]:
        """Test the deployed orchestration components."""
        try:
            # Test Lambda function
            test_event = {
                'dna_sequence': 'ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG',
                'patient_info': {
                    'patient_id': 'DEPLOYMENT_TEST_001',
                    'age': 45,
                    'deployment_test': True
                },
                'orchestration_type': 'autonomous_comprehensive'
            }
            
            try:
                response = self.lambda_client.invoke(
                    FunctionName=self.function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(test_event)
                )
                
                payload = json.loads(response['Payload'].read())
                
                if response['StatusCode'] == 200:
                    self.logger.info("Lambda function test successful")
                    test_success = True
                else:
                    self.logger.warning(f"Lambda function test returned status: {response['StatusCode']}")
                    test_success = False
                
            except Exception as e:
                self.logger.warning(f"Lambda function test failed: {str(e)}")
                test_success = False
            
            return {
                'success': test_success,
                'lambda_test': test_success,
                'test_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error testing deployment: {str(e)}")
            return {'success': False, 'error': str(e)}


def main():
    """Main deployment function."""
    logger.info("Starting Enhanced Bedrock Orchestration Deployment")
    
    try:
        # Initialize deployer
        deployer = EnhancedOrchestrationDeployer()
        
        # Deploy all components
        deployment_result = deployer.deploy_all_components()
        
        # Print deployment summary
        logger.info("\n" + "=" * 80)
        logger.info("DEPLOYMENT SUMMARY")
        logger.info("=" * 80)
        
        if deployment_result['success']:
            logger.info("✅ Enhanced orchestration deployment completed successfully!")
            
            components = deployment_result['components']
            
            logger.info("\nDeployed Components:")
            for component_name, component_result in components.items():
                if component_result.get('success', False):
                    logger.info(f"  ✅ {component_name.upper()}")
                else:
                    logger.info(f"  ❌ {component_name.upper()}: {component_result.get('error', 'Unknown error')}")
            
            # Print key information
            if 'lambda' in components and components['lambda'].get('success'):
                logger.info(f"\nLambda Function: {components['lambda']['function_name']}")
                logger.info(f"Function ARN: {components['lambda']['function_arn']}")
            
            if 'api_gateway' in components and components['api_gateway'].get('success'):
                logger.info(f"\nAPI Gateway URL: {components['api_gateway']['api_url']}")
            
            if 'dynamodb' in components and components['dynamodb'].get('success'):
                logger.info(f"\nDynamoDB Table: {components['dynamodb']['table_name']}")
            
            logger.info("\n🎉 Enhanced orchestration is ready for use!")
            
        else:
            logger.error("❌ Enhanced orchestration deployment failed!")
            logger.error(f"Error: {deployment_result.get('error', 'Unknown error')}")
        
        # Save deployment results
        deployment_file = f"enhanced_orchestration_deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(deployment_file, 'w') as f:
            json.dump(deployment_result, f, indent=2, default=str)
        
        logger.info(f"\nDeployment results saved to: {deployment_file}")
        
        return deployment_result['success']
        
    except Exception as e:
        logger.error(f"Deployment failed with error: {str(e)}")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nDeployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)