#!/usr/bin/env python3
"""
Environment management script for Biomerkin Multi-Agent System
Handles environment creation, configuration, and management
"""

import argparse
import boto3
import json
import logging
import sys
from typing import Dict, List, Optional
from pathlib import Path
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnvironmentManager:
    """Manages different deployment environments for Biomerkin"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.ssm = boto3.client('ssm', region_name=region)
        self.secrets = boto3.client('secretsmanager', region_name=region)
        
        # Environment configurations
        self.environments = {
            'dev': {
                'description': 'Development environment for testing',
                'instance_size': 'small',
                'monitoring': False,
                'backup': False,
                'multi_az': False,
                'auto_scaling': False
            },
            'staging': {
                'description': 'Staging environment for pre-production testing',
                'instance_size': 'medium',
                'monitoring': True,
                'backup': True,
                'multi_az': False,
                'auto_scaling': True
            },
            'prod': {
                'description': 'Production environment',
                'instance_size': 'large',
                'monitoring': True,
                'backup': True,
                'multi_az': True,
                'auto_scaling': True
            }
        }
    
    def create_environment_config(self, environment: str) -> Dict:
        """Create environment-specific configuration"""
        if environment not in self.environments:
            raise ValueError(f"Unknown environment: {environment}")
        
        config = self.environments[environment].copy()
        
        # Add environment-specific settings
        config.update({
            'environment_name': environment,
            'region': self.region,
            'stack_name': f'Biomerkin{environment.title()}',
            'api_name': f'biomerkin-api-{environment}',
            'lambda_prefix': f'biomerkin-{environment}',
            'table_prefix': f'biomerkin-{environment}',
            'bucket_prefix': f'biomerkin-{environment}'
        })
        
        return config
    
    def store_environment_config(self, environment: str, config: Dict) -> bool:
        """Store environment configuration in SSM Parameter Store"""
        try:
            parameter_name = f'/biomerkin/{environment}/config'
            
            self.ssm.put_parameter(
                Name=parameter_name,
                Value=json.dumps(config, indent=2),
                Type='String',
                Overwrite=True,
                Description=f'Configuration for Biomerkin {environment} environment'
            )
            
            logger.info(f"Environment configuration stored: {parameter_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store environment config: {str(e)}")
            return False
    
    def get_environment_config(self, environment: str) -> Optional[Dict]:
        """Retrieve environment configuration from SSM Parameter Store"""
        try:
            parameter_name = f'/biomerkin/{environment}/config'
            
            response = self.ssm.get_parameter(Name=parameter_name)
            config = json.loads(response['Parameter']['Value'])
            
            logger.info(f"Retrieved environment configuration: {parameter_name}")
            return config
            
        except self.ssm.exceptions.ParameterNotFound:
            logger.warning(f"Environment configuration not found: {parameter_name}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve environment config: {str(e)}")
            return None
    
    def create_environment_secrets(self, environment: str) -> bool:
        """Create environment-specific secrets"""
        try:
            secret_name = f'biomerkin/{environment}/api-keys'
            
            # Default secret structure
            secret_value = {
                'pubmed_api_key': 'your-pubmed-api-key',
                'drugbank_api_key': 'your-drugbank-api-key',
                'pdb_api_key': 'your-pdb-api-key',
                'bedrock_model_id': 'anthropic.claude-3-sonnet-20240229-v1:0'
            }
            
            try:
                # Try to create new secret
                self.secrets.create_secret(
                    Name=secret_name,
                    Description=f'API keys for Biomerkin {environment} environment',
                    SecretString=json.dumps(secret_value)
                )
                logger.info(f"Created new secret: {secret_name}")
                
            except self.secrets.exceptions.ResourceExistsException:
                # Update existing secret
                self.secrets.update_secret(
                    SecretId=secret_name,
                    SecretString=json.dumps(secret_value)
                )
                logger.info(f"Updated existing secret: {secret_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create environment secrets: {str(e)}")
            return False
    
    def list_environments(self) -> List[str]:
        """List all configured environments"""
        try:
            response = self.ssm.get_parameters_by_path(
                Path='/biomerkin/',
                Recursive=True
            )
            
            environments = set()
            for param in response['Parameters']:
                # Extract environment name from parameter path
                path_parts = param['Name'].split('/')
                if len(path_parts) >= 3:
                    environments.add(path_parts[2])
            
            return sorted(list(environments))
            
        except Exception as e:
            logger.error(f"Failed to list environments: {str(e)}")
            return []
    
    def validate_environment(self, environment: str) -> bool:
        """Validate environment configuration and resources"""
        logger.info(f"Validating {environment} environment...")
        
        try:
            # Check if configuration exists
            config = self.get_environment_config(environment)
            if not config:
                logger.error(f"No configuration found for {environment}")
                return False
            
            # Check if stack exists
            stack_name = config.get('stack_name')
            if stack_name:
                try:
                    response = self.cloudformation.describe_stacks(StackName=stack_name)
                    stack = response['Stacks'][0]
                    status = stack['StackStatus']
                    
                    if status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                        logger.info(f"Stack {stack_name} is in good state: {status}")
                    else:
                        logger.warning(f"Stack {stack_name} status: {status}")
                        
                except self.cloudformation.exceptions.ClientError:
                    logger.warning(f"Stack {stack_name} does not exist")
            
            # Check if secrets exist
            secret_name = f'biomerkin/{environment}/api-keys'
            try:
                self.secrets.describe_secret(SecretId=secret_name)
                logger.info(f"Secrets configured: {secret_name}")
            except self.secrets.exceptions.ResourceNotFoundException:
                logger.warning(f"Secrets not found: {secret_name}")
            
            logger.info(f"Environment {environment} validation completed")
            return True
            
        except Exception as e:
            logger.error(f"Environment validation failed: {str(e)}")
            return False
    
    def create_environment(self, environment: str) -> bool:
        """Create a new environment with all necessary resources"""
        logger.info(f"Creating {environment} environment...")
        
        try:
            # Create environment configuration
            config = self.create_environment_config(environment)
            
            # Store configuration
            if not self.store_environment_config(environment, config):
                return False
            
            # Create secrets
            if not self.create_environment_secrets(environment):
                return False
            
            logger.info(f"Environment {environment} created successfully")
            logger.info("Next steps:")
            logger.info(f"1. Update API keys in AWS Secrets Manager: biomerkin/{environment}/api-keys")
            logger.info(f"2. Deploy infrastructure: python scripts/deploy.py {environment}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create environment: {str(e)}")
            return False
    
    def delete_environment(self, environment: str, force: bool = False) -> bool:
        """Delete an environment and all its resources"""
        if environment == 'prod' and not force:
            logger.error("Cannot delete production environment without --force flag")
            return False
        
        logger.info(f"Deleting {environment} environment...")
        
        try:
            # Delete CloudFormation stack
            config = self.get_environment_config(environment)
            if config:
                stack_name = config.get('stack_name')
                if stack_name:
                    try:
                        self.cloudformation.delete_stack(StackName=stack_name)
                        logger.info(f"Initiated deletion of stack: {stack_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete stack: {str(e)}")
            
            # Delete secrets
            secret_name = f'biomerkin/{environment}/api-keys'
            try:
                self.secrets.delete_secret(
                    SecretId=secret_name,
                    ForceDeleteWithoutRecovery=True
                )
                logger.info(f"Deleted secret: {secret_name}")
            except Exception as e:
                logger.warning(f"Failed to delete secret: {str(e)}")
            
            # Delete SSM parameters
            try:
                parameter_name = f'/biomerkin/{environment}/config'
                self.ssm.delete_parameter(Name=parameter_name)
                logger.info(f"Deleted parameter: {parameter_name}")
            except Exception as e:
                logger.warning(f"Failed to delete parameter: {str(e)}")
            
            logger.info(f"Environment {environment} deletion initiated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete environment: {str(e)}")
            return False
    
    def export_environment_config(self, environment: str, output_file: str) -> bool:
        """Export environment configuration to file"""
        try:
            config = self.get_environment_config(environment)
            if not config:
                logger.error(f"No configuration found for {environment}")
                return False
            
            output_path = Path(output_file)
            
            if output_path.suffix.lower() == '.yaml':
                with open(output_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, indent=2)
            else:
                with open(output_path, 'w') as f:
                    json.dump(config, f, indent=2)
            
            logger.info(f"Configuration exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export configuration: {str(e)}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Manage Biomerkin environments')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create environment
    create_parser = subparsers.add_parser('create', help='Create new environment')
    create_parser.add_argument('environment', help='Environment name')
    
    # Delete environment
    delete_parser = subparsers.add_parser('delete', help='Delete environment')
    delete_parser.add_argument('environment', help='Environment name')
    delete_parser.add_argument('--force', action='store_true', help='Force deletion of production')
    
    # List environments
    subparsers.add_parser('list', help='List all environments')
    
    # Validate environment
    validate_parser = subparsers.add_parser('validate', help='Validate environment')
    validate_parser.add_argument('environment', help='Environment name')
    
    # Export configuration
    export_parser = subparsers.add_parser('export', help='Export environment configuration')
    export_parser.add_argument('environment', help='Environment name')
    export_parser.add_argument('output', help='Output file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return False
    
    manager = EnvironmentManager(args.region)
    
    if args.command == 'create':
        success = manager.create_environment(args.environment)
    elif args.command == 'delete':
        success = manager.delete_environment(args.environment, args.force)
    elif args.command == 'list':
        environments = manager.list_environments()
        print("Configured environments:")
        for env in environments:
            print(f"  - {env}")
        success = True
    elif args.command == 'validate':
        success = manager.validate_environment(args.environment)
    elif args.command == 'export':
        success = manager.export_environment_config(args.environment, args.output)
    else:
        parser.print_help()
        success = False
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)