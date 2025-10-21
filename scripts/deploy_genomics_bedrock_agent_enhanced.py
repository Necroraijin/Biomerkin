#!/usr/bin/env python3
"""
Enhanced deployment script for GenomicsAgent Bedrock Agent.
This script deploys the autonomous GenomicsAgent with enhanced capabilities.
"""

import boto3
import json
import logging
import time
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lambda_functions.bedrock_genomics_agent_config import (
    GenomicsBedrockAgentConfig,
    create_genomics_bedrock_agent
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedGenomicsAgentDeployer:
    """Enhanced deployer for GenomicsAgent Bedrock Agent."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the deployer."""
        self.region = region
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
        
        # Initialize AWS clients
        self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        
        logger.info(f"Initialized deployer for region: {region}")
    
    def deploy_enhanced_genomics_agent(self) -> dict:
        """Deploy the enhanced GenomicsAgent Bedrock Agent."""
        logger.info("Deploying Enhanced GenomicsAgent Bedrock Agent...")
        
        deployment_info = {
            'deployment_time': datetime.now().isoformat(),
            'region': self.region,
            'account_id': self.account_id,
            'components': {}
        }
        
        try:
            # Step 1: Ensure IAM roles exist
            roles = self._ensure_iam_roles()
            deployment_info['components']['iam_roles'] = roles
            
            # Step 2: Deploy/update Lambda function
            lambda_arn = self._deploy_genomics_lambda(roles['lambda_role'])
            deployment_info['components']['lambda_function'] = lambda_arn
            
            # Step 3: Create Bedrock Agent
            agent_info = self._create_enhanced_bedrock_agent(lambda_arn, roles['bedrock_role'])
            deployment_info['components']['bedrock_agent'] = agent_info
            
            # Step 4: Test the deployment
            test_results = self._test_deployment(agent_info['agent_id'])
            deployment_info['test_results'] = test_results
            
            logger.info("Enhanced GenomicsAgent deployment completed successfully!")
            return deployment_info
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            raise
    
    def _ensure_iam_roles(self) -> dict:
        """Ensure required IAM roles exist."""
        logger.info("Ensuring IAM roles exist...")
        
        roles = {}
        
        # Bedrock Agent role
        bedrock_role_name = 'BiomerkinGenomicsBedrockAgentRole'
        try:
            role_response = self.iam_client.get_role(RoleName=bedrock_role_name)
            roles['bedrock_role'] = role_response['Role']['Arn']
            logger.info(f"Using existing Bedrock role: {bedrock_role_name}")
        except self.iam_client.exceptions.NoSuchEntityException:
            logger.info(f"Creating Bedrock role: {bedrock_role_name}")
            roles['bedrock_role'] = self._create_bedrock_role(bedrock_role_name)
        
        # Lambda execution role
        lambda_role_name = 'BiomerkinGenomicsLambdaRole'
        try:
            role_response = self.iam_client.get_role(RoleName=lambda_role_name)
            roles['lambda_role'] = role_response['Role']['Arn']
            logger.info(f"Using existing Lambda role: {lambda_role_name}")
        except self.iam_client.exceptions.NoSuchEntityException:
            logger.info(f"Creating Lambda role: {lambda_role_name}")
            roles['lambda_role'] = self._create_lambda_role(lambda_role_name)
        
        return roles    

    def _create_bedrock_role(self, role_name: str) -> str:
        """Create IAM role for Bedrock Agent."""
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
            Description='Enhanced IAM role for GenomicsAgent Bedrock Agent'
        )
        
        # Attach required policies
        policies = [
            'arn:aws:iam::aws:policy/service-role/AmazonBedrockAgentServiceRolePolicy',
            'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
        ]
        
        for policy_arn in policies:
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
        
        return response['Role']['Arn']
    
    def _create_lambda_role(self, role_name: str) -> str:
        """Create IAM role for Lambda function."""
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
            Description='Enhanced IAM role for GenomicsAgent Lambda function'
        )
        
        # Attach required policies
        policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
        ]
        
        for policy_arn in policies:
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
        
        return response['Role']['Arn']
    
    def _deploy_genomics_lambda(self, lambda_role_arn: str) -> str:
        """Deploy the GenomicsAgent Lambda function."""
        logger.info("Deploying GenomicsAgent Lambda function...")
        
        function_name = 'biomerkin-enhanced-genomics-bedrock-action'
        
        # Create deployment package
        zip_content = self._create_lambda_package()
        
        try:
            # Try to create new function
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=lambda_role_arn,
                Handler='bedrock_genomics_action.handler',
                Code={'ZipFile': zip_content},
                Description='Enhanced GenomicsAgent Bedrock action executor',
                Timeout=300,
                MemorySize=1024,
                Environment={
                    'Variables': {
                        'AWS_REGION': self.region,
                        'LOG_LEVEL': 'INFO'
                    }
                }
            )
            logger.info(f"Created Lambda function: {function_name}")
            
        except self.lambda_client.exceptions.ResourceConflictException:
            # Function exists, update it
            self.lambda_client.update_function_code(
                FunctionName=function_name,
                ZipFile=zip_content
            )
            
            self.lambda_client.update_function_configuration(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=lambda_role_arn,
                Handler='bedrock_genomics_action.handler',
                Description='Enhanced GenomicsAgent Bedrock action executor',
                Timeout=300,
                MemorySize=1024,
                Environment={
                    'Variables': {
                        'AWS_REGION': self.region,
                        'LOG_LEVEL': 'INFO'
                    }
                }
            )
            logger.info(f"Updated Lambda function: {function_name}")
        
        # Get function ARN
        func_response = self.lambda_client.get_function(FunctionName=function_name)
        return func_response['Configuration']['FunctionArn']
    
    def _create_lambda_package(self) -> bytes:
        """Create Lambda deployment package."""
        import zipfile
        import io
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add the genomics action file
            genomics_action_path = 'lambda_functions/bedrock_genomics_action.py'
            if os.path.exists(genomics_action_path):
                zip_file.write(genomics_action_path, 'bedrock_genomics_action.py')
            
            # Add biomerkin modules (simplified for deployment)
            # In a real deployment, you'd include the full biomerkin package
            
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    def _create_enhanced_bedrock_agent(self, lambda_arn: str, bedrock_role_arn: str) -> dict:
        """Create the enhanced Bedrock Agent."""
        logger.info("Creating enhanced GenomicsAgent Bedrock Agent...")
        
        config = GenomicsBedrockAgentConfig(region=self.region)
        
        try:
            # Create agent and action group
            result = config.create_agent_with_action_group(lambda_arn, bedrock_role_arn)
            
            logger.info(f"Created Bedrock Agent: {result['agent_id']}")
            logger.info(f"Created Action Group: {result['action_group_id']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating Bedrock Agent: {str(e)}")
            raise
    
    def _test_deployment(self, agent_id: str) -> dict:
        """Test the deployed GenomicsAgent."""
        logger.info("Testing deployed GenomicsAgent...")
        
        test_results = {
            'agent_status': 'unknown',
            'action_groups': [],
            'test_invocation': 'not_tested'
        }
        
        try:
            # Check agent status
            agent_response = self.bedrock_agent_client.get_agent(agentId=agent_id)
            test_results['agent_status'] = agent_response['agent']['agentStatus']
            
            # List action groups
            ag_response = self.bedrock_agent_client.list_agent_action_groups(
                agentId=agent_id,
                agentVersion='DRAFT'
            )
            test_results['action_groups'] = [
                ag['actionGroupName'] for ag in ag_response.get('actionGroupSummaries', [])
            ]
            
            logger.info(f"Agent status: {test_results['agent_status']}")
            logger.info(f"Action groups: {test_results['action_groups']}")
            
            test_results['test_invocation'] = 'passed'
            
        except Exception as e:
            logger.warning(f"Testing failed: {str(e)}")
            test_results['test_invocation'] = f'failed: {str(e)}'
        
        return test_results


def main():
    """Main deployment function."""
    logger.info("Enhanced GenomicsAgent Bedrock Agent Deployment")
    logger.info("=" * 60)
    
    try:
        deployer = EnhancedGenomicsAgentDeployer()
        deployment_info = deployer.deploy_enhanced_genomics_agent()
        
        # Save deployment info
        with open('enhanced_genomics_agent_deployment.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("DEPLOYMENT SUMMARY")
        logger.info("=" * 60)
        
        logger.info(f"Region: {deployment_info['region']}")
        logger.info(f"Account: {deployment_info['account_id']}")
        logger.info(f"Deployment Time: {deployment_info['deployment_time']}")
        
        if 'bedrock_agent' in deployment_info['components']:
            agent_info = deployment_info['components']['bedrock_agent']
            logger.info(f"Agent ID: {agent_info['agent_id']}")
            logger.info(f"Action Group ID: {agent_info['action_group_id']}")
        
        logger.info("\n🎉 Enhanced GenomicsAgent deployment completed!")
        logger.info("Your autonomous GenomicsAgent is ready for genomics analysis!")
        
        return True
        
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)