#!/usr/bin/env python3
"""
Deploy Bedrock Agent for DecisionAgent with autonomous medical decision-making capabilities.
This script creates and configures the Bedrock Agent for comprehensive medical report generation.
"""

import json
import boto3
import time
import logging
from typing import Dict, Any, Optional
import zipfile
import os
import sys

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lambda_functions.bedrock_decision_agent_config import DecisionBedrockAgentConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DecisionBedrockAgentDeployer:
    """Deployer for DecisionAgent Bedrock Agent."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the deployer."""
        self.region = region
        self.bedrock_client = boto3.client('bedrock-agent', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.config = DecisionBedrockAgentConfig(region)
        
        # Configuration
        self.agent_name = "biomerkin-decision-agent"
        self.lambda_function_name = "bedrock-decision-action"
        self.role_name = "BiomerkinDecisionBedrockAgentRole"
        
    def deploy_complete_agent(self) -> Dict[str, Any]:
        """Deploy the complete Bedrock Agent with all components."""
        try:
            logger.info("Starting DecisionAgent Bedrock Agent deployment...")
            
            # Step 1: Create IAM role
            role_arn = self.create_iam_role()
            logger.info(f"Created IAM role: {role_arn}")
            
            # Step 2: Create Lambda function
            lambda_arn = self.create_lambda_function()
            logger.info(f"Created Lambda function: {lambda_arn}")
            
            # Step 3: Create Bedrock Agent
            agent_response = self.create_bedrock_agent(role_arn)
            agent_id = agent_response['agent']['agentId']
            logger.info(f"Created Bedrock Agent: {agent_id}")
            
            # Step 4: Create action group
            action_group_response = self.create_action_group(agent_id, lambda_arn)
            logger.info(f"Created action group: {action_group_response['actionGroup']['actionGroupId']}")
            
            # Step 5: Prepare agent
            prepare_response = self.prepare_agent(agent_id)
            logger.info("Agent prepared successfully")
            
            # Step 6: Create alias
            alias_response = self.create_agent_alias(agent_id)
            logger.info(f"Created agent alias: {alias_response['agentAlias']['agentAliasId']}")
            
            deployment_info = {
                'agent_id': agent_id,
                'agent_name': self.agent_name,
                'agent_arn': agent_response['agent']['agentArn'],
                'alias_id': alias_response['agentAlias']['agentAliasId'],
                'lambda_function_arn': lambda_arn,
                'role_arn': role_arn,
                'region': self.region,
                'deployment_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'deployed'
            }
            
            # Save deployment info
            self.save_deployment_info(deployment_info)
            
            logger.info("DecisionAgent Bedrock Agent deployment completed successfully!")
            return deployment_info
            
        except Exception as e:
            logger.error(f"Error during deployment: {e}")
            raise
    
    def create_iam_role(self) -> str:
        """Create IAM role for the Bedrock Agent."""
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
        
        # Create role
        try:
            response = self.iam_client.create_role(
                RoleName=self.role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="IAM role for Biomerkin DecisionAgent Bedrock Agent"
            )
            role_arn = response['Role']['Arn']
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            response = self.iam_client.get_role(RoleName=self.role_name)
            role_arn = response['Role']['Arn']
            logger.info(f"Using existing IAM role: {role_arn}")
        
        # Attach policies
        policies = [
            "arn:aws:iam::aws:policy/service-role/AWSLambdaRole",
            "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
        ]
        
        for policy_arn in policies:
            try:
                self.iam_client.attach_role_policy(
                    RoleName=self.role_name,
                    PolicyArn=policy_arn
                )
            except Exception as e:
                logger.warning(f"Policy {policy_arn} may already be attached: {e}")
        
        # Create custom policy for Lambda invocation
        lambda_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:InvokeFunction"
                    ],
                    "Resource": f"arn:aws:lambda:{self.region}:*:function:{self.lambda_function_name}"
                }
            ]
        }
        
        try:
            self.iam_client.put_role_policy(
                RoleName=self.role_name,
                PolicyName="DecisionAgentLambdaInvokePolicy",
                PolicyDocument=json.dumps(lambda_policy)
            )
        except Exception as e:
            logger.warning(f"Lambda invoke policy may already exist: {e}")
        
        # Wait for role to be available
        time.sleep(10)
        
        return role_arn
    
    def create_lambda_function(self) -> str:
        """Create Lambda function for action group execution."""
        # Create deployment package
        zip_path = self.create_lambda_package()
        
        with open(zip_path, 'rb') as zip_file:
            zip_content = zip_file.read()
        
        function_config = {
            'FunctionName': self.lambda_function_name,
            'Runtime': 'python3.9',
            'Role': f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:role/{self.role_name}",
            'Handler': 'bedrock_decision_action.handler',
            'Code': {'ZipFile': zip_content},
            'Description': 'Bedrock Agent action executor for DecisionAgent medical decision-making',
            'Timeout': 300,
            'MemorySize': 1024,
            'Environment': {
                'Variables': {
                    'PYTHONPATH': '/opt/python:/var/runtime',
                    'AWS_DEFAULT_REGION': self.region
                }
            }
        }
        
        try:
            response = self.lambda_client.create_function(**function_config)
            lambda_arn = response['FunctionArn']
            logger.info(f"Created Lambda function: {lambda_arn}")
        except self.lambda_client.exceptions.ResourceConflictException:
            # Update existing function
            response = self.lambda_client.update_function_code(
                FunctionName=self.lambda_function_name,
                ZipFile=zip_content
            )
            lambda_arn = response['FunctionArn']
            logger.info(f"Updated existing Lambda function: {lambda_arn}")
        
        # Clean up zip file
        os.remove(zip_path)
        
        return lambda_arn
    
    def create_lambda_package(self) -> str:
        """Create Lambda deployment package."""
        zip_path = f"/tmp/{self.lambda_function_name}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add the action function
            action_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'lambda_functions',
                'bedrock_decision_action.py'
            )
            zip_file.write(action_file, 'bedrock_decision_action.py')
            
            # Add biomerkin modules (simplified - in practice, you'd include the full package)
            biomerkin_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'biomerkin'
            )
            
            if os.path.exists(biomerkin_dir):
                for root, dirs, files in os.walk(biomerkin_dir):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            arc_path = os.path.relpath(file_path, os.path.dirname(biomerkin_dir))
                            zip_file.write(file_path, arc_path)
        
        return zip_path
    
    def create_bedrock_agent(self, role_arn: str) -> Dict[str, Any]:
        """Create the Bedrock Agent."""
        try:
            response = self.config.create_bedrock_agent(
                agent_name=self.agent_name,
                role_arn=role_arn
            )
            return response
        except Exception as e:
            logger.error(f"Error creating Bedrock Agent: {e}")
            raise
    
    def create_action_group(self, agent_id: str, lambda_arn: str) -> Dict[str, Any]:
        """Create action group for the agent."""
        try:
            response = self.config.create_action_group(
                agent_id=agent_id,
                action_group_name="medical-decision-actions",
                lambda_function_arn=lambda_arn
            )
            return response
        except Exception as e:
            logger.error(f"Error creating action group: {e}")
            raise
    
    def prepare_agent(self, agent_id: str) -> Dict[str, Any]:
        """Prepare the agent for use."""
        try:
            response = self.config.prepare_agent(agent_id)
            
            # Wait for preparation to complete
            max_wait_time = 300  # 5 minutes
            wait_time = 0
            
            while wait_time < max_wait_time:
                try:
                    status_response = self.bedrock_client.get_agent(agentId=agent_id)
                    status = status_response['agent']['agentStatus']
                    
                    if status == 'PREPARED':
                        logger.info("Agent preparation completed")
                        break
                    elif status == 'FAILED':
                        raise Exception("Agent preparation failed")
                    
                    logger.info(f"Agent status: {status}, waiting...")
                    time.sleep(10)
                    wait_time += 10
                    
                except Exception as e:
                    logger.warning(f"Error checking agent status: {e}")
                    time.sleep(10)
                    wait_time += 10
            
            return response
        except Exception as e:
            logger.error(f"Error preparing agent: {e}")
            raise
    
    def create_agent_alias(self, agent_id: str) -> Dict[str, Any]:
        """Create an alias for the agent."""
        try:
            response = self.bedrock_client.create_agent_alias(
                agentId=agent_id,
                agentAliasName="production",
                description="Production alias for DecisionAgent Bedrock Agent"
            )
            return response
        except Exception as e:
            logger.error(f"Error creating agent alias: {e}")
            raise
    
    def save_deployment_info(self, deployment_info: Dict[str, Any]) -> None:
        """Save deployment information to file."""
        output_file = "decision_agent_deployment_info.json"
        
        with open(output_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        logger.info(f"Deployment information saved to {output_file}")
    
    def test_agent(self, agent_id: str, alias_id: str) -> Dict[str, Any]:
        """Test the deployed agent."""
        try:
            bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=self.region)
            
            test_input = {
                "patient_id": "TEST_001",
                "genomics_results": {
                    "genes": [
                        {
                            "id": "BRCA1",
                            "name": "BRCA1",
                            "function": "DNA repair tumor suppressor",
                            "confidence": 0.95
                        }
                    ],
                    "mutations": [
                        {
                            "gene_id": "BRCA1",
                            "position": 5382,
                            "reference": "C",
                            "alternate": "T",
                            "significance": "Pathogenic"
                        }
                    ]
                }
            }
            
            response = bedrock_runtime.invoke_agent(
                agentId=agent_id,
                agentAliasId=alias_id,
                sessionId="test-session-001",
                inputText=f"Generate a medical report for this patient data: {json.dumps(test_input)}"
            )
            
            logger.info("Agent test completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error testing agent: {e}")
            raise
    
    def cleanup_deployment(self, deployment_info: Dict[str, Any]) -> None:
        """Clean up deployed resources."""
        try:
            # Delete agent
            if 'agent_id' in deployment_info:
                try:
                    self.bedrock_client.delete_agent(
                        agentId=deployment_info['agent_id'],
                        skipResourceInUseCheck=True
                    )
                    logger.info(f"Deleted agent: {deployment_info['agent_id']}")
                except Exception as e:
                    logger.warning(f"Error deleting agent: {e}")
            
            # Delete Lambda function
            try:
                self.lambda_client.delete_function(
                    FunctionName=self.lambda_function_name
                )
                logger.info(f"Deleted Lambda function: {self.lambda_function_name}")
            except Exception as e:
                logger.warning(f"Error deleting Lambda function: {e}")
            
            # Delete IAM role
            try:
                # Detach policies
                policies = [
                    "arn:aws:iam::aws:policy/service-role/AWSLambdaRole",
                    "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
                ]
                
                for policy_arn in policies:
                    try:
                        self.iam_client.detach_role_policy(
                            RoleName=self.role_name,
                            PolicyArn=policy_arn
                        )
                    except Exception:
                        pass
                
                # Delete inline policy
                try:
                    self.iam_client.delete_role_policy(
                        RoleName=self.role_name,
                        PolicyName="DecisionAgentLambdaInvokePolicy"
                    )
                except Exception:
                    pass
                
                # Delete role
                self.iam_client.delete_role(RoleName=self.role_name)
                logger.info(f"Deleted IAM role: {self.role_name}")
                
            except Exception as e:
                logger.warning(f"Error deleting IAM role: {e}")
            
            logger.info("Cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy DecisionAgent Bedrock Agent')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--test', action='store_true', help='Test the deployed agent')
    parser.add_argument('--cleanup', action='store_true', help='Clean up deployed resources')
    
    args = parser.parse_args()
    
    deployer = DecisionBedrockAgentDeployer(region=args.region)
    
    if args.cleanup:
        # Load deployment info for cleanup
        try:
            with open('decision_agent_deployment_info.json', 'r') as f:
                deployment_info = json.load(f)
            deployer.cleanup_deployment(deployment_info)
        except FileNotFoundError:
            logger.error("No deployment info found for cleanup")
        return
    
    # Deploy the agent
    deployment_info = deployer.deploy_complete_agent()
    
    print("\n" + "="*80)
    print("DEPLOYMENT SUMMARY")
    print("="*80)
    print(f"Agent ID: {deployment_info['agent_id']}")
    print(f"Agent Name: {deployment_info['agent_name']}")
    print(f"Alias ID: {deployment_info['alias_id']}")
    print(f"Region: {deployment_info['region']}")
    print(f"Status: {deployment_info['status']}")
    print("="*80)
    
    if args.test:
        print("\nTesting deployed agent...")
        try:
            test_result = deployer.test_agent(
                deployment_info['agent_id'],
                deployment_info['alias_id']
            )
            print("Agent test completed successfully!")
        except Exception as e:
            print(f"Agent test failed: {e}")


if __name__ == "__main__":
    main()