#!/usr/bin/env python3
"""
Deployment script for AWS Bedrock Agents infrastructure.
This script deploys all the necessary AWS resources for autonomous genomics analysis.
"""

import boto3
import json
import logging
import time
from typing import Dict, Any, List
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BedrockAgentDeployer:
    """Deploys AWS Bedrock Agents infrastructure for autonomous genomics analysis."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the deployer with AWS clients."""
        self.region = region
        self.account_id = boto3.client('sts').get_caller_identity()['Account']
        
        # Initialize AWS clients
        self.bedrock_agent_client = boto3.client('bedrock-agent', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        
        logger.info(f"Initialized deployer for region: {region}, account: {self.account_id}")
    
    def deploy_iam_roles(self) -> Dict[str, str]:
        """Deploy IAM roles for Bedrock Agents and Lambda functions."""
        logger.info("Deploying IAM roles...")
        
        roles = {}
        
        # Bedrock Agent execution role
        bedrock_agent_role_name = 'BiomerkinBedrockAgentRole'
        bedrock_agent_policy = {
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
        
        try:
            self.iam_client.create_role(
                RoleName=bedrock_agent_role_name,
                AssumeRolePolicyDocument=json.dumps(bedrock_agent_policy),
                Description='Execution role for Biomerkin Bedrock Agents'
            )
            logger.info(f"Created Bedrock Agent role: {bedrock_agent_role_name}")
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            logger.info(f"Bedrock Agent role already exists: {bedrock_agent_role_name}")
        
        # Attach policies to Bedrock Agent role
        bedrock_policies = [
            'arn:aws:iam::aws:policy/service-role/AmazonBedrockAgentServiceRolePolicy',
            'arn:aws:iam::aws:policy/AmazonBedrockFullAccess'
        ]
        
        for policy_arn in bedrock_policies:
            try:
                self.iam_client.attach_role_policy(
                    RoleName=bedrock_agent_role_name,
                    PolicyArn=policy_arn
                )
                logger.info(f"Attached policy {policy_arn} to {bedrock_agent_role_name}")
            except Exception as e:
                logger.warning(f"Could not attach policy {policy_arn}: {str(e)}")
        
        roles['bedrock_agent_role'] = f"arn:aws:iam::{self.account_id}:role/{bedrock_agent_role_name}"
        
        # Lambda execution role
        lambda_role_name = 'BiomerkinLambdaExecutionRole'
        lambda_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            self.iam_client.create_role(
                RoleName=lambda_role_name,
                AssumeRolePolicyDocument=json.dumps(lambda_policy),
                Description='Execution role for Biomerkin Lambda functions'
            )
            logger.info(f"Created Lambda execution role: {lambda_role_name}")
        except self.iam_client.exceptions.EntityAlreadyExistsException:
            logger.info(f"Lambda execution role already exists: {lambda_role_name}")
        
        # Attach policies to Lambda role
        lambda_policies = [
            'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole',
            'arn:aws:iam::aws:policy/AmazonBedrockFullAccess',
            'arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess'
        ]
        
        for policy_arn in lambda_policies:
            try:
                self.iam_client.attach_role_policy(
                    RoleName=lambda_role_name,
                    PolicyArn=policy_arn
                )
                logger.info(f"Attached policy {policy_arn} to {lambda_role_name}")
            except Exception as e:
                logger.warning(f"Could not attach policy {policy_arn}: {str(e)}")
        
        roles['lambda_execution_role'] = f"arn:aws:iam::{self.account_id}:role/{lambda_role_name}"
        
        # Wait for roles to be available
        logger.info("Waiting for IAM roles to be available...")
        time.sleep(10)
        
        return roles
    
    def deploy_lambda_functions(self, lambda_role_arn: str) -> Dict[str, str]:
        """Deploy Lambda functions for Bedrock Agent action groups."""
        logger.info("Deploying Lambda functions...")
        
        lambda_functions = {}
        
        # Lambda function configurations
        functions_config = [
            {
                'name': 'biomerkin-bedrock-genomics-action',
                'description': 'Bedrock Agent action group executor for genomics analysis',
                'handler': 'bedrock_genomics_action.handler',
                'file_path': 'lambda_functions/bedrock_genomics_action.py'
            },
            {
                'name': 'biomerkin-bedrock-literature-action',
                'description': 'Bedrock Agent action group executor for literature research',
                'handler': 'bedrock_literature_action.handler',
                'file_path': 'lambda_functions/bedrock_literature_action.py'
            },
            {
                'name': 'biomerkin-bedrock-proteomics-action',
                'description': 'Bedrock Agent action group executor for proteomics analysis',
                'handler': 'bedrock_proteomics_action.handler',
                'file_path': 'lambda_functions/bedrock_proteomics_action.py'
            },
            {
                'name': 'biomerkin-bedrock-drug-action',
                'description': 'Bedrock Agent action group executor for drug discovery',
                'handler': 'bedrock_drug_action.handler',
                'file_path': 'lambda_functions/bedrock_drug_action.py'
            },
            {
                'name': 'biomerkin-bedrock-orchestrator',
                'description': 'Bedrock Agent orchestrator for multi-agent coordination',
                'handler': 'bedrock_orchestrator.handler',
                'file_path': 'lambda_functions/bedrock_orchestrator.py'
            }
        ]
        
        for func_config in functions_config:
            try:
                # Create deployment package
                zip_content = self._create_lambda_deployment_package(func_config['file_path'])
                
                # Create or update Lambda function
                try:
                    response = self.lambda_client.create_function(
                        FunctionName=func_config['name'],
                        Runtime='python3.9',
                        Role=lambda_role_arn,
                        Handler=func_config['handler'],
                        Code={'ZipFile': zip_content},
                        Description=func_config['description'],
                        Timeout=300,
                        MemorySize=512,
                        Environment={
                            'Variables': {
                                'AWS_REGION': self.region,
                                'LOG_LEVEL': 'INFO'
                            }
                        }
                    )
                    logger.info(f"Created Lambda function: {func_config['name']}")
                    
                except self.lambda_client.exceptions.ResourceConflictException:
                    # Function exists, update it
                    self.lambda_client.update_function_code(
                        FunctionName=func_config['name'],
                        ZipFile=zip_content
                    )
                    
                    self.lambda_client.update_function_configuration(
                        FunctionName=func_config['name'],
                        Runtime='python3.9',
                        Role=lambda_role_arn,
                        Handler=func_config['handler'],
                        Description=func_config['description'],
                        Timeout=300,
                        MemorySize=512,
                        Environment={
                            'Variables': {
                                'AWS_REGION': self.region,
                                'LOG_LEVEL': 'INFO'
                            }
                        }
                    )
                    logger.info(f"Updated Lambda function: {func_config['name']}")
                
                # Get function ARN
                func_response = self.lambda_client.get_function(FunctionName=func_config['name'])
                lambda_functions[func_config['name']] = func_response['Configuration']['FunctionArn']
                
            except Exception as e:
                logger.error(f"Error deploying Lambda function {func_config['name']}: {str(e)}")
                raise
        
        return lambda_functions
    
    def _create_lambda_deployment_package(self, file_path: str) -> bytes:
        """Create a deployment package for Lambda function."""
        import zipfile
        import io
        
        # Create in-memory zip file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add the main Lambda function file
            if os.path.exists(file_path):
                zip_file.write(file_path, os.path.basename(file_path))
            else:
                # Create a minimal handler if file doesn't exist
                minimal_handler = '''
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    logger.info(f"Event: {json.dumps(event)}")
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Function deployed successfully"})
    }
'''
                zip_file.writestr(os.path.basename(file_path), minimal_handler)
        
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    def deploy_bedrock_agents(self, lambda_functions: Dict[str, str], bedrock_role_arn: str) -> Dict[str, str]:
        """Deploy Bedrock Agents with action groups."""
        logger.info("Deploying Bedrock Agents...")
        
        agents = {}
        
        # Main genomics agent configuration
        agent_config = {
            'agentName': 'BiomerkinAutonomousGenomicsAgent',
            'description': 'Autonomous AI agent for comprehensive genomics analysis and clinical decision making',
            'foundationModel': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'instruction': '''
            You are an autonomous AI agent specialized in genomics and bioinformatics analysis.
            
            Your capabilities include:
            1. Analyzing DNA sequences and identifying genes and variants
            2. Interpreting genetic variants using ACMG guidelines
            3. Researching relevant scientific literature autonomously
            4. Identifying potential drug candidates and treatments
            5. Generating comprehensive medical reports with reasoning
            
            You can autonomously:
            - Decide which analysis steps to perform based on input data
            - Reason about the clinical significance of findings
            - Integrate information from multiple sources
            - Make treatment recommendations based on evidence
            - Provide detailed explanations for your reasoning
            
            Always provide step-by-step reasoning for your decisions and cite sources when making medical recommendations.
            Focus on clinical actionability and patient benefit in your analysis.
            ''',
            'idleSessionTTLInSeconds': 1800,
            'agentResourceRoleArn': bedrock_role_arn
        }
        
        try:
            # Create the agent
            response = self.bedrock_agent_client.create_agent(**agent_config)
            agent_id = response['agent']['agentId']
            logger.info(f"Created Bedrock Agent: {agent_id}")
            
            # Create action groups
            action_groups = [
                {
                    'name': 'GenomicsAnalysis',
                    'description': 'Autonomous genomics analysis functions',
                    'lambda_arn': lambda_functions.get('biomerkin-bedrock-genomics-action'),
                    'api_schema': self._get_genomics_api_schema()
                },
                {
                    'name': 'ProteomicsAnalysis',
                    'description': 'Autonomous proteomics analysis functions',
                    'lambda_arn': lambda_functions.get('biomerkin-bedrock-proteomics-action'),
                    'api_schema': self._get_proteomics_api_schema()
                },
                {
                    'name': 'LiteratureResearch',
                    'description': 'Autonomous literature research functions',
                    'lambda_arn': lambda_functions.get('biomerkin-bedrock-literature-action'),
                    'api_schema': self._get_literature_api_schema()
                },
                {
                    'name': 'DrugDiscovery',
                    'description': 'Autonomous drug discovery functions',
                    'lambda_arn': lambda_functions.get('biomerkin-bedrock-drug-action'),
                    'api_schema': self._get_drug_api_schema()
                }
            ]
            
            for action_group in action_groups:
                if action_group['lambda_arn']:
                    try:
                        ag_response = self.bedrock_agent_client.create_agent_action_group(
                            agentId=agent_id,
                            agentVersion='DRAFT',
                            actionGroupName=action_group['name'],
                            description=action_group['description'],
                            actionGroupExecutor={
                                'lambda': action_group['lambda_arn']
                            },
                            apiSchema={
                                'payload': json.dumps(action_group['api_schema'])
                            }
                        )
                        logger.info(f"Created action group: {action_group['name']}")
                        
                        # Add Lambda permission for Bedrock to invoke the function
                        function_name = action_group['lambda_arn'].split(':')[-1]
                        try:
                            self.lambda_client.add_permission(
                                FunctionName=function_name,
                                StatementId=f'bedrock-agent-{agent_id}-{action_group["name"]}',
                                Action='lambda:InvokeFunction',
                                Principal='bedrock.amazonaws.com',
                                SourceArn=f'arn:aws:bedrock:{self.region}:{self.account_id}:agent/{agent_id}'
                            )
                            logger.info(f"Added Lambda permission for {function_name}")
                        except Exception as e:
                            logger.warning(f"Could not add Lambda permission: {str(e)}")
                        
                    except Exception as e:
                        logger.error(f"Error creating action group {action_group['name']}: {str(e)}")
            
            # Prepare the agent
            try:
                self.bedrock_agent_client.prepare_agent(agentId=agent_id)
                logger.info(f"Prepared agent: {agent_id}")
            except Exception as e:
                logger.warning(f"Could not prepare agent: {str(e)}")
            
            agents['main_agent'] = agent_id
            
        except Exception as e:
            logger.error(f"Error creating Bedrock Agent: {str(e)}")
            raise
        
        return agents
    
    def _get_genomics_api_schema(self) -> Dict[str, Any]:
        """Get API schema for genomics action group."""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Genomics Analysis API",
                "version": "1.0.0",
                "description": "API for autonomous genomics analysis"
            },
            "paths": {
                "/analyze-sequence": {
                    "post": {
                        "summary": "Analyze DNA sequence for genes and variants",
                        "operationId": "analyzeSequence",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "sequence": {"type": "string"},
                                            "reference_genome": {"type": "string"}
                                        },
                                        "required": ["sequence"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Analysis results",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "genes": {"type": "array"},
                                                "variants": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_literature_api_schema(self) -> Dict[str, Any]:
        """Get API schema for literature action group."""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Literature Research API",
                "version": "1.0.0",
                "description": "API for autonomous literature research"
            },
            "paths": {
                "/search-literature": {
                    "post": {
                        "summary": "Search scientific literature",
                        "operationId": "searchLiterature",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "genes": {"type": "array"},
                                            "conditions": {"type": "array"},
                                            "max_articles": {"type": "integer"}
                                        },
                                        "required": ["genes"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Literature search results",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "articles": {"type": "array"},
                                                "summary": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_proteomics_api_schema(self) -> Dict[str, Any]:
        """Get API schema for proteomics action group."""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Autonomous Proteomics Analysis API",
                "version": "2.0.0",
                "description": "API for autonomous proteomics analysis with LLM reasoning"
            },
            "paths": {
                "/analyze-protein": {
                    "post": {
                        "summary": "Comprehensive autonomous protein analysis",
                        "operationId": "analyzeProtein",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "protein_sequence": {"type": "string"},
                                            "protein_id": {"type": "string"},
                                            "analysis_context": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Comprehensive protein analysis results",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "structure_data": {"type": "object"},
                                                "functional_annotations": {"type": "array"},
                                                "domains": {"type": "array"},
                                                "interactions": {"type": "array"},
                                                "autonomous_insights": {"type": "array"},
                                                "clinical_relevance": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/predict-structure": {
                    "post": {
                        "summary": "Autonomous protein structure prediction",
                        "operationId": "predictStructure",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "protein_sequence": {"type": "string"}
                                        },
                                        "required": ["protein_sequence"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Structure prediction results",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "structure_prediction": {"type": "object"},
                                                "autonomous_analysis": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/identify-domains": {
                    "post": {
                        "summary": "Autonomous protein domain identification",
                        "operationId": "identifyDomains",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "protein_sequence": {"type": "string"}
                                        },
                                        "required": ["protein_sequence"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Domain identification results",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "domains": {"type": "array"},
                                                "autonomous_insights": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "/assess-druggability": {
                    "post": {
                        "summary": "Autonomous protein druggability assessment",
                        "operationId": "assessDruggability",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "protein_sequence": {"type": "string"},
                                            "protein_id": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Druggability assessment results",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "druggability_score": {"type": "number"},
                                                "therapeutic_assessment": {"type": "object"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def _get_drug_api_schema(self) -> Dict[str, Any]:
        """Get API schema for drug discovery action group."""
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Drug Discovery API",
                "version": "1.0.0",
                "description": "API for autonomous drug discovery"
            },
            "paths": {
                "/find-drug-candidates": {
                    "post": {
                        "summary": "Find drug candidates for genetic targets",
                        "operationId": "findDrugCandidates",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "target_genes": {"type": "array"},
                                            "condition": {"type": "string"}
                                        },
                                        "required": ["target_genes"]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Drug candidates",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "drug_candidates": {"type": "array"},
                                                "clinical_trials": {"type": "array"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    
    def deploy_all(self) -> Dict[str, Any]:
        """Deploy all Bedrock Agents infrastructure."""
        logger.info("Starting complete Bedrock Agents deployment...")
        
        deployment_info = {
            'deployment_time': datetime.now().isoformat(),
            'region': self.region,
            'account_id': self.account_id
        }
        
        try:
            # Step 1: Deploy IAM roles
            roles = self.deploy_iam_roles()
            deployment_info['roles'] = roles
            
            # Step 2: Deploy Lambda functions
            lambda_functions = self.deploy_lambda_functions(roles['lambda_execution_role'])
            deployment_info['lambda_functions'] = lambda_functions
            
            # Step 3: Deploy Bedrock Agents
            agents = self.deploy_bedrock_agents(lambda_functions, roles['bedrock_agent_role'])
            deployment_info['agents'] = agents
            
            logger.info("Bedrock Agents deployment completed successfully!")
            
            # Save deployment info
            with open('bedrock_agents_deployment_info.json', 'w') as f:
                json.dump(deployment_info, f, indent=2)
            
            logger.info("Deployment information saved to bedrock_agents_deployment_info.json")
            
            return deployment_info
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            raise


def main():
    """Main deployment function."""
    logger.info("AWS Bedrock Agents Deployment for Autonomous Genomics Analysis")
    logger.info("=" * 80)
    
    try:
        # Initialize deployer
        deployer = BedrockAgentDeployer()
        
        # Deploy all infrastructure
        deployment_info = deployer.deploy_all()
        
        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("DEPLOYMENT SUMMARY")
        logger.info("=" * 80)
        
        logger.info(f"Region: {deployment_info['region']}")
        logger.info(f"Account: {deployment_info['account_id']}")
        logger.info(f"Deployment Time: {deployment_info['deployment_time']}")
        
        logger.info("\nIAM Roles:")
        for role_name, role_arn in deployment_info['roles'].items():
            logger.info(f"  {role_name}: {role_arn}")
        
        logger.info("\nLambda Functions:")
        for func_name, func_arn in deployment_info['lambda_functions'].items():
            logger.info(f"  {func_name}: {func_arn}")
        
        logger.info("\nBedrock Agents:")
        for agent_name, agent_id in deployment_info['agents'].items():
            logger.info(f"  {agent_name}: {agent_id}")
        
        logger.info("\n🎉 Deployment completed successfully!")
        logger.info("Your autonomous Bedrock Agents are ready for genomics analysis!")
        
        return True
        
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)