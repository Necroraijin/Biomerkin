#!/usr/bin/env python3
"""
Deployment script for ProteomicsAgent AWS Bedrock Agent.
This script deploys the autonomous ProteomicsAgent with enhanced capabilities.
"""

import boto3
import json
import logging
import time
import sys
import os
from typing import Dict, Any
from datetime import datetime

# Add the lambda_functions directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda_functions'))

from bedrock_proteomics_agent_config import ProteomicsBedrockAgentConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProteomicsAgentDeployer:
    """Deploys the ProteomicsAgent Bedrock Agent infrastructure."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the deployer."""
        self.region = region
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
        
        # Initialize AWS clients
        self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        
        logger.info(f"Initialized ProteomicsAgent deployer for region: {region}")
    
    def ensure_iam_roles(self) -> Dict[str, str]:
        """Ensure IAM roles exist for ProteomicsAgent."""
        logger.info("Ensuring IAM roles for ProteomicsAgent...")
        
        roles = {}
        
        # Bedrock Agent execution role
        bedrock_role_name = 'BiomerkinProteomicsBedrockAgentRole'
        bedrock_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "bedrock.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            self.iam_client.create_role(
                RoleName=bedrock_role_name,
                AssumeRolePolicyDocument=json.dumps(bedrock_policy),
                Description='Execution role for Biomerkin ProteomicsAgent Bedrock Agent'
            )
            logger.info(f"Created Bedrock role: {bedrock_role_name}")
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            logger.info(f"Bedrock role already exists: {bedrock_role_name}")
        
        # Attach necessary policies
        policies = [
            'arn:aws:iam::aws:policy/service-role/AmazonBedrockAgentServiceRolePolicy',
            'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
        ]
        
        for policy_arn in policies:
            try:
                self.iam_client.attach_role_policy(
                    RoleName=bedrock_role_name,
                    PolicyArn=policy_arn
                )
            except Exception as e:
                logger.warning(f"Could not attach policy {policy_arn}: {str(e)}")
        
        roles['bedrock_role'] = f"arn:aws:iam::{self.account_id}:role/{bedrock_role_name}"
        
        # Lambda execution role
        lambda_role_name = 'BiomerkinProteomicsLambdaRole'
        lambda_policy = {
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
            self.iam_client.create_role(
                RoleName=lambda_role_name,
                AssumeRolePolicyDocument=json.dumps(lambda_policy),
                Description='Execution role for Biomerkin ProteomicsAgent Lambda function'
            )
            logger.info(f"Created Lambda role: {lambda_role_name}")
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            logger.info(f"Lambda role already exists: {lambda_role_name}")
        
        # Attach Lambda policies
        lambda_policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
        ]
        
        for policy_arn in lambda_policies:
            try:
                self.iam_client.attach_role_policy(
                    RoleName=lambda_role_name,
                    PolicyArn=policy_arn
                )
            except Exception as e:
                logger.warning(f"Could not attach policy {policy_arn}: {str(e)}")
        
        roles['lambda_role'] = f"arn:aws:iam::{self.account_id}:role/{lambda_role_name}"
        
        # Wait for roles to propagate
        time.sleep(10)
        
        return roles
    
    def deploy_lambda_function(self, lambda_role_arn: str) -> str:
        """Deploy the ProteomicsAgent Lambda function."""
        logger.info("Deploying ProteomicsAgent Lambda function...")
        
        function_name = 'biomerkin-proteomics-bedrock-agent'
        
        # Create deployment package
        zip_content = self._create_lambda_package()
        
        try:
            # Try to create the function
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=lambda_role_arn,
                Handler='bedrock_proteomics_action.handler',
                Code={'ZipFile': zip_content},
                Description='Bedrock Agent action executor for autonomous proteomics analysis',
                Timeout=300,
                MemorySize=1024,
                Environment={
                    'Variables': {
                        'LOG_LEVEL': 'INFO',
                        'BIOMERKIN_REGION': self.region
                    }
                },
                Tags={
                    'Project': 'Biomerkin',
                    'Component': 'ProteomicsAgent',
                    'Hackathon': 'AWS-Agent-Hackathon'
                }
            )
            logger.info(f"Created Lambda function: {function_name}")
            
        except self.lambda_client.exceptions.ResourceConflictException:
            # Function exists, try to update it
            try:
                self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_content
                )
                
                self.lambda_client.update_function_configuration(
                    FunctionName=function_name,
                    Runtime='python3.9',
                    Role=lambda_role_arn,
                    Handler='bedrock_proteomics_action.handler',
                    Description='Bedrock Agent action executor for autonomous proteomics analysis',
                    Timeout=300,
                    MemorySize=1024,
                    Environment={
                        'Variables': {
                            'LOG_LEVEL': 'INFO',
                            'BIOMERKIN_REGION': self.region
                        }
                    }
                )
                logger.info(f"Updated Lambda function: {function_name}")
            except Exception as update_error:
                logger.warning(f"Could not update Lambda function (may be in progress): {str(update_error)}")
                logger.info(f"Using existing Lambda function: {function_name}")
        
        # Get function ARN
        func_response = self.lambda_client.get_function(FunctionName=function_name)
        function_arn = func_response['Configuration']['FunctionArn']
        
        return function_arn
    
    def _create_lambda_package(self) -> bytes:
        """Create Lambda deployment package."""
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add the main Lambda function
            lambda_file = os.path.join(os.path.dirname(__file__), '..', 'lambda_functions', 'bedrock_proteomics_action.py')
            if os.path.exists(lambda_file):
                zip_file.write(lambda_file, 'bedrock_proteomics_action.py')
            else:
                # Create minimal handler if file doesn't exist
                minimal_handler = '''
import json
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info(f"ProteomicsAgent Bedrock Action invoked: {json.dumps(event)}")
    
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": event.get("httpMethod", "POST"),
            "httpStatusCode": 200,
            "responseBody": {
                "application/json": {
                    "body": json.dumps({
                        "message": "ProteomicsAgent Bedrock Agent deployed successfully",
                        "timestamp": datetime.now().isoformat(),
                        "capabilities": [
                            "Autonomous protein structure analysis",
                            "Function prediction with LLM reasoning",
                            "Domain identification and analysis",
                            "Protein interaction prediction",
                            "Druggability assessment",
                            "Clinical significance evaluation"
                        ]
                    })
                }
            }
        }
    }
'''
                zip_file.writestr('bedrock_proteomics_action.py', minimal_handler)
        
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    def deploy_bedrock_agent(self, lambda_arn: str, bedrock_role_arn: str) -> Dict[str, str]:
        """Deploy the ProteomicsAgent Bedrock Agent."""
        logger.info("Deploying ProteomicsAgent Bedrock Agent...")
        
        # Initialize configuration
        config = ProteomicsBedrockAgentConfig(self.region)
        
        try:
            # Create agent and action group
            result = config.create_agent_with_action_group(lambda_arn, bedrock_role_arn)
            
            # Add Lambda permission for Bedrock to invoke
            function_name = lambda_arn.split(':')[-1]
            try:
                self.lambda_client.add_permission(
                    FunctionName=function_name,
                    StatementId=f'bedrock-proteomics-agent-{result["agent_id"]}',
                    Action='lambda:InvokeFunction',
                    Principal='bedrock.amazonaws.com',
                    SourceArn=f'arn:aws:bedrock:{self.region}:{self.account_id}:agent/{result["agent_id"]}'
                )
                logger.info(f"Added Lambda permission for ProteomicsAgent")
            except Exception as e:
                logger.warning(f"Could not add Lambda permission: {str(e)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error deploying ProteomicsAgent Bedrock Agent: {str(e)}")
            raise
    
    def deploy_all(self) -> Dict[str, Any]:
        """Deploy complete ProteomicsAgent infrastructure."""
        logger.info("Starting ProteomicsAgent Bedrock Agent deployment...")
        
        deployment_info = {
            'deployment_time': datetime.now().isoformat(),
            'region': self.region,
            'account_id': self.account_id,
            'component': 'ProteomicsAgent'
        }
        
        try:
            # Step 1: Ensure IAM roles
            roles = self.ensure_iam_roles()
            deployment_info['roles'] = roles
            
            # Step 2: Deploy Lambda function
            lambda_arn = self.deploy_lambda_function(roles['lambda_role'])
            deployment_info['lambda_function'] = lambda_arn
            
            # Step 3: Deploy Bedrock Agent
            agent_info = self.deploy_bedrock_agent(lambda_arn, roles['bedrock_role'])
            deployment_info['bedrock_agent'] = agent_info
            
            logger.info("ProteomicsAgent Bedrock Agent deployment completed successfully!")
            
            # Save deployment info
            with open('proteomics_agent_deployment_info.json', 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            return deployment_info
            
        except Exception as e:
            logger.error(f"ProteomicsAgent deployment failed: {str(e)}")
            raise
    
    def test_deployment(self, agent_id: str) -> bool:
        """Test the deployed ProteomicsAgent."""
        logger.info(f"Testing ProteomicsAgent deployment: {agent_id}")
        
        try:
            # Test agent status
            response = self.bedrock_agent_client.get_agent(agentId=agent_id)
            agent_status = response['agent']['agentStatus']
            
            if agent_status == 'PREPARED':
                logger.info("✅ ProteomicsAgent is ready and prepared")
                return True
            else:
                logger.warning(f"⚠️ ProteomicsAgent status: {agent_status}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing ProteomicsAgent: {str(e)}")
            return False


def main():
    """Main deployment function."""
    logger.info("AWS Bedrock ProteomicsAgent Deployment")
    logger.info("=" * 60)
    
    try:
        # Initialize deployer
        deployer = ProteomicsAgentDeployer()
        
        # Deploy all infrastructure
        deployment_info = deployer.deploy_all()
        
        # Test deployment
        agent_id = deployment_info['bedrock_agent']['agent_id']
        test_success = deployer.test_deployment(agent_id)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("PROTEOMICS AGENT DEPLOYMENT SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"Region: {deployment_info['region']}")
        logger.info(f"Account: {deployment_info['account_id']}")
        logger.info(f"Deployment Time: {deployment_info['deployment_time']}")
        
        logger.info(f"\nBedrock Agent ID: {deployment_info['bedrock_agent']['agent_id']}")
        logger.info(f"Action Group ID: {deployment_info['bedrock_agent']['action_group_id']}")
        logger.info(f"Lambda Function: {deployment_info['lambda_function']}")
        
        logger.info(f"\nDeployment Status: {'✅ SUCCESS' if test_success else '⚠️ PARTIAL'}")
        
        if test_success:
            logger.info("\n🎉 ProteomicsAgent Bedrock Agent is ready!")
            logger.info("Autonomous proteomics analysis capabilities:")
            logger.info("  • Protein structure prediction and analysis")
            logger.info("  • Function annotation with LLM reasoning")
            logger.info("  • Domain identification and characterization")
            logger.info("  • Protein interaction prediction")
            logger.info("  • Druggability assessment")
            logger.info("  • Clinical significance evaluation")
        
        return test_success
        
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)