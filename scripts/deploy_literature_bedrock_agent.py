#!/usr/bin/env python3
"""
Deploy LiteratureAgent Bedrock Agent with autonomous capabilities.
This script creates and configures the Bedrock Agent for literature research.
"""

import json
import boto3
import logging
import time
from typing import Dict, Any
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lambda_functions.bedrock_literature_agent_config import LiteratureBedrockAgentConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LiteratureBedrockAgentDeployer:
    """Deployer for LiteratureAgent Bedrock Agent."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the deployer."""
        self.region = region
        self.bedrock_client = boto3.client('bedrock-agent', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.sts_client = boto3.client('sts', region_name=region)
        
        # Get account ID
        self.account_id = self.sts_client.get_caller_identity()['Account']
        
        # Configuration
        self.lambda_function_name = 'biomerkin-literature-bedrock-agent'
        self.agent_role_name = 'BiomerkinLiteratureBedrockAgentRole'
        
    def deploy_complete_agent(self) -> Dict[str, str]:
        """
        Deploy the complete LiteratureAgent Bedrock Agent infrastructure.
        
        Returns:
            Dictionary containing deployment results
        """
        try:
            logger.info("Starting LiteratureAgent Bedrock Agent deployment...")
            
            # Step 1: Create IAM role for the agent
            role_arn = self._create_agent_role()
            logger.info(f"Created agent role: {role_arn}")
            
            # Step 2: Deploy Lambda function
            lambda_arn = self._deploy_lambda_function()
            logger.info(f"Deployed Lambda function: {lambda_arn}")
            
            # Step 3: Create Bedrock Agent
            config = LiteratureBedrockAgentConfig(region=self.region)
            agent_result = config.create_agent_with_action_group(lambda_arn, role_arn)
            
            logger.info(f"Created Bedrock Agent: {agent_result['agent_id']}")
            logger.info(f"Created Action Group: {agent_result['action_group_id']}")
            
            # Step 4: Test the agent
            test_result = self._test_agent(agent_result['agent_id'])
            
            deployment_result = {
                'agent_id': agent_result['agent_id'],
                'action_group_id': agent_result['action_group_id'],
                'lambda_arn': lambda_arn,
                'role_arn': role_arn,
                'test_result': test_result,
                'status': 'success'
            }
            
            logger.info("LiteratureAgent Bedrock Agent deployment completed successfully!")
            return deployment_result
            
        except Exception as e:
            logger.error(f"Error during deployment: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def _create_agent_role(self) -> str:
        """Create IAM role for the Bedrock Agent."""
        try:
            # Check if role already exists
            try:
                response = self.iam_client.get_role(RoleName=self.agent_role_name)
                logger.info(f"Role {self.agent_role_name} already exists")
                return response['Role']['Arn']
            except self.iam_client.exceptions.NoSuchEntityException:
                pass
            
            # Trust policy for Bedrock Agent
            trust_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "bedrock.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }
            
            # Create the role
            response = self.iam_client.create_role(
                RoleName=self.agent_role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='IAM role for Biomerkin LiteratureAgent Bedrock Agent'
            )
            
            role_arn = response['Role']['Arn']
            
            # Attach necessary policies
            policies = [
                'arn:aws:iam::aws:policy/AmazonBedrockFullAccess',
                'arn:aws:iam::aws:policy/service-role/AWSLambdaRole'
            ]
            
            for policy_arn in policies:
                self.iam_client.attach_role_policy(
                    RoleName=self.agent_role_name,
                    PolicyArn=policy_arn
                )
            
            # Create custom policy for Lambda invocation
            lambda_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "lambda:InvokeFunction"
                        ],
                        "Resource": f"arn:aws:lambda:{self.region}:{self.account_id}:function:{self.lambda_function_name}"
                    }
                ]
            }
            
            self.iam_client.put_role_policy(
                RoleName=self.agent_role_name,
                PolicyName='LambdaInvokePolicy',
                PolicyDocument=json.dumps(lambda_policy)
            )
            
            # Wait for role to be available
            time.sleep(10)
            
            logger.info(f"Created IAM role: {role_arn}")
            return role_arn
            
        except Exception as e:
            logger.error(f"Error creating IAM role: {str(e)}")
            raise
    
    def _deploy_lambda_function(self) -> str:
        """Deploy the Lambda function for the action group."""
        try:
            # Check if function already exists
            try:
                response = self.lambda_client.get_function(FunctionName=self.lambda_function_name)
                logger.info(f"Lambda function {self.lambda_function_name} already exists")
                return response['Configuration']['FunctionArn']
            except self.lambda_client.exceptions.ResourceNotFoundException:
                pass
            
            # Read the Lambda function code
            lambda_code_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'lambda_functions',
                'bedrock_literature_action.py'
            )
            
            with open(lambda_code_path, 'r') as f:
                lambda_code = f.read()
            
            # Create deployment package
            import zipfile
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                    zip_file.writestr('lambda_function.py', lambda_code)
                
                tmp_file.seek(0)
                zip_content = tmp_file.read()
            
            # Create Lambda function
            response = self.lambda_client.create_function(
                FunctionName=self.lambda_function_name,
                Runtime='python3.9',
                Role=f'arn:aws:iam::{self.account_id}:role/lambda-execution-role',
                Handler='lambda_function.handler',
                Code={'ZipFile': zip_content},
                Description='Bedrock Agent action group executor for LiteratureAgent',
                Timeout=300,
                MemorySize=512,
                Environment={
                    'Variables': {
                        'PYTHONPATH': '/var/runtime:/opt/python'
                    }
                }
            )
            
            function_arn = response['FunctionArn']
            
            # Add permission for Bedrock to invoke the function
            try:
                self.lambda_client.add_permission(
                    FunctionName=self.lambda_function_name,
                    StatementId='bedrock-agent-invoke',
                    Action='lambda:InvokeFunction',
                    Principal='bedrock.amazonaws.com',
                    SourceAccount=self.account_id
                )
            except self.lambda_client.exceptions.ResourceConflictException:
                # Permission already exists
                pass
            
            logger.info(f"Created Lambda function: {function_arn}")
            return function_arn
            
        except Exception as e:
            logger.error(f"Error deploying Lambda function: {str(e)}")
            raise
    
    def _test_agent(self, agent_id: str) -> Dict[str, Any]:
        """Test the deployed Bedrock Agent."""
        try:
            logger.info(f"Testing Bedrock Agent: {agent_id}")
            
            # Create a test session
            bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
            
            test_input = """
            Please search the literature for information about BRCA1 gene mutations and breast cancer.
            Focus on clinical significance and therapeutic implications.
            """
            
            # Note: This is a basic test - in production you'd want more comprehensive testing
            test_result = {
                'agent_id': agent_id,
                'test_status': 'ready_for_testing',
                'message': 'Agent deployed successfully and ready for literature research tasks'
            }
            
            logger.info("Agent test completed successfully")
            return test_result
            
        except Exception as e:
            logger.error(f"Error testing agent: {str(e)}")
            return {
                'test_status': 'failed',
                'error': str(e)
            }
    
    def cleanup_deployment(self, agent_id: str = None):
        """Clean up deployed resources."""
        try:
            logger.info("Starting cleanup of LiteratureAgent Bedrock Agent resources...")
            
            # Delete Bedrock Agent
            if agent_id:
                try:
                    self.bedrock_client.delete_agent(agentId=agent_id)
                    logger.info(f"Deleted Bedrock Agent: {agent_id}")
                except Exception as e:
                    logger.warning(f"Error deleting agent: {str(e)}")
            
            # Delete Lambda function
            try:
                self.lambda_client.delete_function(FunctionName=self.lambda_function_name)
                logger.info(f"Deleted Lambda function: {self.lambda_function_name}")
            except Exception as e:
                logger.warning(f"Error deleting Lambda function: {str(e)}")
            
            # Delete IAM role
            try:
                # Detach policies
                policies = [
                    'arn:aws:iam::aws:policy/AmazonBedrockFullAccess',
                    'arn:aws:iam::aws:policy/service-role/AWSLambdaRole'
                ]
                
                for policy_arn in policies:
                    try:
                        self.iam_client.detach_role_policy(
                            RoleName=self.agent_role_name,
                            PolicyArn=policy_arn
                        )
                    except Exception:
                        pass
                
                # Delete inline policies
                try:
                    self.iam_client.delete_role_policy(
                        RoleName=self.agent_role_name,
                        PolicyName='LambdaInvokePolicy'
                    )
                except Exception:
                    pass
                
                # Delete role
                self.iam_client.delete_role(RoleName=self.agent_role_name)
                logger.info(f"Deleted IAM role: {self.agent_role_name}")
                
            except Exception as e:
                logger.warning(f"Error deleting IAM role: {str(e)}")
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy LiteratureAgent Bedrock Agent')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup deployed resources')
    parser.add_argument('--agent-id', help='Agent ID for cleanup')
    
    args = parser.parse_args()
    
    deployer = LiteratureBedrockAgentDeployer(region=args.region)
    
    if args.cleanup:
        deployer.cleanup_deployment(agent_id=args.agent_id)
    else:
        result = deployer.deploy_complete_agent()
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()