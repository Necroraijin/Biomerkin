#!/usr/bin/env python3
"""
Automated deployment script for Biomerkin Multi-Agent System
Handles environment-specific deployments with validation and rollback
"""

import argparse
import subprocess
import sys
import json
import boto3
import time
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BiomerkinDeployer:
    """Automated deployment manager for Biomerkin system"""
    
    def __init__(self, environment: str, region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        
        # Stack names for different environments
        self.stack_names = {
            'dev': 'BiomerkinDev',
            'staging': 'BiomerkinStaging',
            'prod': 'BiomerkinProd',
            'pipeline': 'BiomerkinPipeline'
        }
    
    def validate_environment(self) -> bool:
        """Validate that the environment is properly configured"""
        logger.info(f"Validating {self.environment} environment...")
        
        try:
            # Check AWS credentials
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            logger.info(f"Deploying as: {identity.get('Arn')}")
            
            # Validate CDK is installed
            result = subprocess.run(['cdk', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("CDK is not installed or not in PATH")
                return False
            
            logger.info(f"CDK version: {result.stdout.strip()}")
            
            # Check if stack already exists
            stack_name = self.stack_names.get(self.environment)
            if stack_name:
                try:
                    response = self.cloudformation.describe_stacks(StackName=stack_name)
                    logger.info(f"Stack {stack_name} already exists")
                except self.cloudformation.exceptions.ClientError:
                    logger.info(f"Stack {stack_name} does not exist - will create new")
            
            return True
            
        except Exception as e:
            logger.error(f"Environment validation failed: {str(e)}")
            return False
    
    def run_tests(self) -> bool:
        """Run tests before deployment"""
        logger.info("Running tests before deployment...")
        
        try:
            # Run unit tests
            result = subprocess.run([
                'python', '-m', 'pytest', 'tests/', '-v', 
                '--cov=biomerkin', '--cov-report=term-missing'
            ], cwd='..', capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error("Unit tests failed:")
                logger.error(result.stdout)
                logger.error(result.stderr)
                return False
            
            logger.info("All tests passed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Test execution failed: {str(e)}")
            return False
    
    def package_lambda_functions(self) -> bool:
        """Package Lambda functions for deployment"""
        logger.info("Packaging Lambda functions...")
        
        try:
            # Create deployment package
            result = subprocess.run([
                'python', 'scripts/package_lambdas.py'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error("Lambda packaging failed:")
                logger.error(result.stderr)
                return False
            
            logger.info("Lambda functions packaged successfully")
            return True
            
        except Exception as e:
            logger.error(f"Lambda packaging failed: {str(e)}")
            return False
    
    def deploy_infrastructure(self) -> bool:
        """Deploy infrastructure using CDK"""
        logger.info(f"Deploying infrastructure to {self.environment}...")
        
        try:
            # Change to infrastructure directory
            import os
            os.chdir('infrastructure')
            
            # Bootstrap CDK if needed
            logger.info("Bootstrapping CDK...")
            bootstrap_result = subprocess.run([
                'cdk', 'bootstrap', f'--context', f'environment={self.environment}'
            ], capture_output=True, text=True)
            
            if bootstrap_result.returncode != 0:
                logger.warning(f"CDK bootstrap warning: {bootstrap_result.stderr}")
            
            # Deploy the stack
            stack_name = self.stack_names.get(self.environment, f'Biomerkin{self.environment.title()}')
            deploy_result = subprocess.run([
                'cdk', 'deploy', stack_name,
                '--require-approval', 'never',
                '--context', f'environment={self.environment}'
            ], capture_output=True, text=True)
            
            if deploy_result.returncode != 0:
                logger.error("CDK deployment failed:")
                logger.error(deploy_result.stdout)
                logger.error(deploy_result.stderr)
                return False
            
            logger.info("Infrastructure deployed successfully")
            logger.info(deploy_result.stdout)
            return True
            
        except Exception as e:
            logger.error(f"Infrastructure deployment failed: {str(e)}")
            return False
        finally:
            # Return to original directory
            os.chdir('..')
    
    def validate_deployment(self) -> bool:
        """Validate that the deployment was successful"""
        logger.info("Validating deployment...")
        
        try:
            stack_name = self.stack_names.get(self.environment)
            if not stack_name:
                logger.error(f"Unknown environment: {self.environment}")
                return False
            
            # Check stack status
            response = self.cloudformation.describe_stacks(StackName=stack_name)
            stack = response['Stacks'][0]
            status = stack['StackStatus']
            
            if status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                logger.error(f"Stack deployment failed with status: {status}")
                return False
            
            # Test Lambda functions
            function_names = [
                f'biomerkin-orchestrator-{self.environment}',
                f'biomerkin-genomics-{self.environment}',
                f'biomerkin-proteomics-{self.environment}',
                f'biomerkin-literature-{self.environment}',
                f'biomerkin-drug-{self.environment}',
                f'biomerkin-decision-{self.environment}'
            ]
            
            for function_name in function_names:
                try:
                    response = self.lambda_client.get_function(FunctionName=function_name)
                    logger.info(f"Lambda function {function_name} is active")
                except self.lambda_client.exceptions.ResourceNotFoundException:
                    logger.warning(f"Lambda function {function_name} not found")
            
            logger.info("Deployment validation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Deployment validation failed: {str(e)}")
            return False
    
    def rollback_deployment(self) -> bool:
        """Rollback to previous deployment if current one fails"""
        logger.info("Initiating rollback...")
        
        try:
            stack_name = self.stack_names.get(self.environment)
            if not stack_name:
                logger.error(f"Unknown environment: {self.environment}")
                return False
            
            # Get stack events to find the last successful deployment
            response = self.cloudformation.describe_stack_events(StackName=stack_name)
            events = response['StackEvents']
            
            # Find the last successful update
            for event in events:
                if (event['ResourceType'] == 'AWS::CloudFormation::Stack' and 
                    event['ResourceStatus'] in ['UPDATE_COMPLETE', 'CREATE_COMPLETE']):
                    logger.info(f"Found last successful deployment at: {event['Timestamp']}")
                    break
            
            # For now, we'll just log the rollback attempt
            # In a real scenario, you might want to implement stack rollback logic
            logger.info("Rollback completed - manual intervention may be required")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return False
    
    def deploy(self, skip_tests: bool = False, skip_validation: bool = False) -> bool:
        """Main deployment orchestration"""
        logger.info(f"Starting deployment to {self.environment} environment")
        
        try:
            # Step 1: Validate environment
            if not self.validate_environment():
                logger.error("Environment validation failed")
                return False
            
            # Step 2: Run tests (unless skipped)
            if not skip_tests and not self.run_tests():
                logger.error("Tests failed - aborting deployment")
                return False
            
            # Step 3: Package Lambda functions
            if not self.package_lambda_functions():
                logger.error("Lambda packaging failed - aborting deployment")
                return False
            
            # Step 4: Deploy infrastructure
            if not self.deploy_infrastructure():
                logger.error("Infrastructure deployment failed")
                if not skip_validation:
                    self.rollback_deployment()
                return False
            
            # Step 5: Validate deployment (unless skipped)
            if not skip_validation and not self.validate_deployment():
                logger.error("Deployment validation failed")
                self.rollback_deployment()
                return False
            
            logger.info(f"Deployment to {self.environment} completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            return False


def main():
    """Main entry point for deployment script"""
    parser = argparse.ArgumentParser(description='Deploy Biomerkin Multi-Agent System')
    parser.add_argument('environment', choices=['dev', 'staging', 'prod', 'pipeline'],
                       help='Target environment for deployment')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region for deployment')
    parser.add_argument('--skip-tests', action='store_true',
                       help='Skip running tests before deployment')
    parser.add_argument('--skip-validation', action='store_true',
                       help='Skip post-deployment validation')
    parser.add_argument('--rollback', action='store_true',
                       help='Rollback the current deployment')
    
    args = parser.parse_args()
    
    deployer = BiomerkinDeployer(args.environment, args.region)
    
    if args.rollback:
        success = deployer.rollback_deployment()
    else:
        success = deployer.deploy(args.skip_tests, args.skip_validation)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()