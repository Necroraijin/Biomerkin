#!/usr/bin/env python3
"""
Deploy Bedrock Agent for DrugAgent with autonomous capabilities.
This script creates and configures the DrugAgent Bedrock Agent with enhanced
autonomous reasoning and LLM integration for drug discovery and clinical analysis.
"""

import json
import boto3
import logging
import time
import sys
import os
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lambda_functions.bedrock_drug_agent_config import DrugBedrockAgentConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DrugBedrockAgentDeployer:
    """Deployer for DrugAgent Bedrock Agent."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the deployer."""
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.bedrock_client = boto3.client('bedrock-agent', region_name=region)
        self.config = DrugBedrockAgentConfig(region=region)
        
    def deploy_complete_agent(self) -> Dict[str, str]:
        """
        Deploy the complete DrugAgent Bedrock Agent infrastructure.
        
        Returns:
            Dictionary containing deployment information
        """
        try:
            logger.info("Starting DrugAgent Bedrock Agent deployment...")
            
            # Step 1: Create or update Lambda function
            lambda_arn = self._deploy_lambda_function()
            logger.info(f"Lambda function deployed: {lambda_arn}")
            
            # Step 2: Create or get IAM role
            role_arn = self._create_bedrock_agent_role()
            logger.info(f"IAM role ready: {role_arn}")
            
            # Step 3: Create Bedrock Agent with action group
            agent_info = self.config.create_agent_with_action_group(lambda_arn, role_arn)
            logger.info(f"Bedrock Agent created: {agent_info}")
            
            # Step 4: Test the agent
            test_result = self._test_agent(agent_info['agent_id'])
            logger.info(f"Agent test result: {test_result}")
            
            deployment_info = {
                'agent_id': agent_info['agent_id'],
                'action_group_id': agent_info['action_group_id'],
                'lambda_arn': lambda_arn,
                'role_arn': role_arn,
                'region': self.region,
                'status': 'deployed',
                'test_result': test_result
            }
            
            # Save deployment info
            self._save_deployment_info(deployment_info)
            
            logger.info("DrugAgent Bedrock Agent deployment completed successfully!")
            return deployment_info
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            raise
    
    def _deploy_lambda_function(self) -> str:
        """Deploy or update the Lambda function for DrugAgent actions."""
        function_name = 'biomerkin-drug-bedrock-action'
        
        try:
            # Check if function exists
            try:
                response = self.lambda_client.get_function(FunctionName=function_name)
                logger.info(f"Lambda function {function_name} already exists, updating...")
                
                # Update function code
                with open('lambda_functions/bedrock_drug_action.py', 'rb') as f:
                    zip_content = self._create_lambda_zip()
                
                self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content
                )
                
                # Update configuration
                self.lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Runtime='python3.9',
                    Handler='bedrock_drug_action.handler',
                    Timeout=300,
                    MemorySize=512,
                    Environment={
                        'Variables': {
                            'PYTHONPATH': '/opt/python:/var/runtime',
                            'LOG_LEVEL': 'INFO'
                        }
                    }
                )
                
                return response['Configuration']['FunctionArn']
                
            except self.lambda_client.exceptions.ResourceNotFoundException:
                logger.info(f"Creating new Lambda function {function_name}...")
                
                # Create new function
                zip_content = self._create_lambda_zip()
                
                response = self.lambda_client.create_function(
                    FunctionName=function_name,
                    Runtime='python3.9',
                    Role=self._get_lambda_execution_role(),
                    Handler='bedrock_drug_action.handler',
                    Code={'ZipFile': zip_content},
                    Description='Bedrock Agent action executor for DrugAgent with autonomous capabilities',
                    Timeout=300,
                    MemorySize=512,
                    Environment={
                        'Variables': {
                            'PYTHONPATH': '/opt/python:/var/runtime',
                            'LOG_LEVEL': 'INFO'
                        }
                    },
                    Tags={
                        'Project': 'Biomerkin',
                        'Component': 'DrugAgent',
                        'Type': 'BedrockAction'
                    }
                )
                
                return response['FunctionArn']
                
        except Exception as e:
            logger.error(f"Error deploying Lambda function: {str(e)}")
            raise
    
    def _create_lambda_zip(self) -> bytes:
        """Create ZIP file for Lambda deployment."""
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add the main handler file
            zip_file.write('lambda_functions/bedrock_drug_action.py', 'bedrock_drug_action.py')
            
            # Add biomerkin package files
            import os
            for root, dirs, files in os.walk('biomerkin'):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        arcname = file_path.replace('\\', '/')
                        zip_file.write(file_path, arcname)
        
        return zip_buffer.getvalue()
    
    def _get_lambda_execution_role(self) -> str:
        """Get or create Lambda execution role."""
        role_name = 'BiomerkinDrugLambdaExecutionRole'
        
        try:
            response = self.iam_client.get_role(RoleName=role_name)
            return response['Role']['Arn']
        except self.iam_client.exceptions.NoSuchEntityException:
            # Create the role
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
            
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Execution role for Biomerkin DrugAgent Lambda functions'
            )
            
            # Attach basic execution policy
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            
            # Wait for role to be ready
            time.sleep(10)
            
            return response['Role']['Arn']
    
    def _create_bedrock_agent_role(self) -> str:
        """Create or get IAM role for Bedrock Agent."""
        role_name = 'BiomerkinDrugBedrockAgentRole'
        
        try:
            response = self.iam_client.get_role(RoleName=role_name)
            return response['Role']['Arn']
        except self.iam_client.exceptions.NoSuchEntityException:
            # Create the role
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "bedrock.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Service role for Biomerkin DrugAgent Bedrock Agent'
            )
            
            # Create and attach policy for Bedrock Agent
            policy_document = {
                "Version": "2012-10-17",
                "Statement": [
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
                            "lambda:InvokeFunction"
                        ],
                        "Resource": "*"
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "logs:CreateLogGroup",
                            "logs:CreateLogStream",
                            "logs:PutLogEvents"
                        ],
                        "Resource": "*"
                    }
                ]
            }
            
            policy_name = f"{role_name}Policy"
            self.iam_client.create_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            
            # Wait for role to be ready
            time.sleep(10)
            
            return response['Role']['Arn']
    
    def _test_agent(self, agent_id: str) -> Dict[str, Any]:
        """Test the deployed Bedrock Agent."""
        try:
            # Simple test to verify agent is accessible
            response = self.bedrock_client.get_agent(agentId=agent_id)
            
            agent_status = response['agent']['agentStatus']
            
            return {
                'agent_accessible': True,
                'agent_status': agent_status,
                'test_timestamp': time.time()
            }
            
        except Exception as e:
            logger.warning(f"Agent test failed: {str(e)}")
            return {
                'agent_accessible': False,
                'error': str(e),
                'test_timestamp': time.time()
            }
    
    def _save_deployment_info(self, deployment_info: Dict[str, Any]):
        """Save deployment information to file."""
        filename = f"drug_agent_bedrock_deployment_info_{int(time.time())}.json"
        
        with open(filename, 'w') as f:
            json.dump(deployment_info, f, indent=2, default=str)
        
        logger.info(f"Deployment info saved to {filename}")


def main():
    """Main deployment function."""
    try:
        deployer = DrugBedrockAgentDeployer()
        deployment_info = deployer.deploy_complete_agent()
        
        print("\n" + "="*60)
        print("DRUGAGENT BEDROCK AGENT DEPLOYMENT SUCCESSFUL!")
        print("="*60)
        print(f"Agent ID: {deployment_info['agent_id']}")
        print(f"Action Group ID: {deployment_info['action_group_id']}")
        print(f"Lambda ARN: {deployment_info['lambda_arn']}")
        print(f"Region: {deployment_info['region']}")
        print(f"Status: {deployment_info['status']}")
        print("="*60)
        
        return deployment_info
        
    except Exception as e:
        print(f"\nDeployment failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()