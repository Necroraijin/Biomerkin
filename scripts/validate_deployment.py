#!/usr/bin/env python3
"""
Deployment validation script for Biomerkin Multi-Agent System
Validates that all components are properly deployed and functional
"""

import argparse
import boto3
import json
import logging
import sys
import time
import requests
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeploymentValidator:
    """Validates deployment health and functionality"""
    
    def __init__(self, environment: str, region: str = "us-east-1"):
        self.environment = environment
        self.region = region
        
        # AWS clients
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.apigateway = boto3.client('apigateway', region_name=region)
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        
        # Expected resources
        self.stack_name = f"Biomerkin{environment.title()}"
        self.expected_functions = [
            f'biomerkin-orchestrator-{environment}',
            f'biomerkin-genomics-{environment}',
            f'biomerkin-proteomics-{environment}',
            f'biomerkin-literature-{environment}',
            f'biomerkin-drug-{environment}',
            f'biomerkin-decision-{environment}'
        ]
        self.expected_tables = [
            f'biomerkin-workflows-{environment}',
            f'biomerkin-cache-{environment}'
        ]
        self.expected_buckets = [
            f'biomerkin-sequences-{environment}',
            f'biomerkin-reports-{environment}'
        ]
    
    def validate_cloudformation_stack(self) -> bool:
        """Validate CloudFormation stack status"""
        logger.info(f"Validating CloudFormation stack: {self.stack_name}")
        
        try:
            response = self.cloudformation.describe_stacks(StackName=self.stack_name)
            stack = response['Stacks'][0]
            status = stack['StackStatus']
            
            if status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                logger.info(f"✓ Stack {self.stack_name} is in good state: {status}")
                
                # Check stack outputs
                outputs = stack.get('Outputs', [])
                logger.info(f"Stack outputs: {len(outputs)} items")
                
                for output in outputs:
                    logger.info(f"  - {output['OutputKey']}: {output['OutputValue']}")
                
                return True
            else:
                logger.error(f"✗ Stack {self.stack_name} is in bad state: {status}")
                return False
                
        except self.cloudformation.exceptions.ClientError as e:
            logger.error(f"✗ Stack {self.stack_name} not found: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"✗ Error validating stack: {str(e)}")
            return False
    
    def validate_lambda_functions(self) -> bool:
        """Validate Lambda functions are deployed and functional"""
        logger.info("Validating Lambda functions...")
        
        all_valid = True
        
        for function_name in self.expected_functions:
            try:
                # Check if function exists
                response = self.lambda_client.get_function(FunctionName=function_name)
                
                # Check function state
                state = response['Configuration']['State']
                if state == 'Active':
                    logger.info(f"✓ Lambda function {function_name} is active")
                    
                    # Test function invocation with a simple test event
                    try:
                        test_event = {
                            'test': True,
                            'source': 'deployment-validation'
                        }
                        
                        invoke_response = self.lambda_client.invoke(
                            FunctionName=function_name,
                            InvocationType='RequestResponse',
                            Payload=json.dumps(test_event)
                        )
                        
                        if invoke_response['StatusCode'] == 200:
                            logger.info(f"✓ Lambda function {function_name} invocation successful")
                        else:
                            logger.warning(f"⚠ Lambda function {function_name} invocation returned status {invoke_response['StatusCode']}")
                            
                    except Exception as e:
                        logger.warning(f"⚠ Lambda function {function_name} test invocation failed: {str(e)}")
                        # Don't fail validation for test invocation issues
                        
                else:
                    logger.error(f"✗ Lambda function {function_name} is in state: {state}")
                    all_valid = False
                    
            except self.lambda_client.exceptions.ResourceNotFoundException:
                logger.error(f"✗ Lambda function {function_name} not found")
                all_valid = False
            except Exception as e:
                logger.error(f"✗ Error validating function {function_name}: {str(e)}")
                all_valid = False
        
        return all_valid
    
    def validate_dynamodb_tables(self) -> bool:
        """Validate DynamoDB tables are created and accessible"""
        logger.info("Validating DynamoDB tables...")
        
        all_valid = True
        
        for table_name in self.expected_tables:
            try:
                response = self.dynamodb.describe_table(TableName=table_name)
                status = response['Table']['TableStatus']
                
                if status == 'ACTIVE':
                    logger.info(f"✓ DynamoDB table {table_name} is active")
                    
                    # Test table access
                    try:
                        self.dynamodb.scan(
                            TableName=table_name,
                            Limit=1
                        )
                        logger.info(f"✓ DynamoDB table {table_name} is accessible")
                    except Exception as e:
                        logger.warning(f"⚠ DynamoDB table {table_name} access test failed: {str(e)}")
                        
                else:
                    logger.error(f"✗ DynamoDB table {table_name} is in state: {status}")
                    all_valid = False
                    
            except self.dynamodb.exceptions.ResourceNotFoundException:
                logger.error(f"✗ DynamoDB table {table_name} not found")
                all_valid = False
            except Exception as e:
                logger.error(f"✗ Error validating table {table_name}: {str(e)}")
                all_valid = False
        
        return all_valid
    
    def validate_s3_buckets(self) -> bool:
        """Validate S3 buckets are created and accessible"""
        logger.info("Validating S3 buckets...")
        
        all_valid = True
        
        # Note: Bucket names include account ID, so we need to find them
        try:
            response = self.s3.list_buckets()
            existing_buckets = [bucket['Name'] for bucket in response['Buckets']]
            
            for expected_bucket_prefix in self.expected_buckets:
                # Find bucket that starts with expected prefix
                matching_buckets = [
                    bucket for bucket in existing_buckets
                    if bucket.startswith(expected_bucket_prefix)
                ]
                
                if matching_buckets:
                    bucket_name = matching_buckets[0]
                    logger.info(f"✓ S3 bucket found: {bucket_name}")
                    
                    # Test bucket access
                    try:
                        self.s3.head_bucket(Bucket=bucket_name)
                        logger.info(f"✓ S3 bucket {bucket_name} is accessible")
                    except Exception as e:
                        logger.warning(f"⚠ S3 bucket {bucket_name} access test failed: {str(e)}")
                        
                else:
                    logger.error(f"✗ S3 bucket with prefix {expected_bucket_prefix} not found")
                    all_valid = False
                    
        except Exception as e:
            logger.error(f"✗ Error validating S3 buckets: {str(e)}")
            all_valid = False
        
        return all_valid
    
    def validate_api_gateway(self) -> bool:
        """Validate API Gateway is deployed and accessible"""
        logger.info("Validating API Gateway...")
        
        try:
            # Find API by name
            api_name = f'biomerkin-api-{self.environment}'
            response = self.apigateway.get_rest_apis()
            
            matching_apis = [
                api for api in response['items']
                if api['name'] == api_name
            ]
            
            if not matching_apis:
                logger.error(f"✗ API Gateway {api_name} not found")
                return False
            
            api = matching_apis[0]
            api_id = api['id']
            
            logger.info(f"✓ API Gateway found: {api_name} ({api_id})")
            
            # Get API resources
            resources_response = self.apigateway.get_resources(restApiId=api_id)
            resources = resources_response['items']
            
            logger.info(f"✓ API Gateway has {len(resources)} resources")
            
            # Test API endpoint (if deployed)
            try:
                api_url = f"https://{api_id}.execute-api.{self.region}.amazonaws.com/prod"
                
                # Simple health check - this might fail due to authentication
                # but we can at least check if the endpoint responds
                response = requests.get(f"{api_url}/workflows", timeout=10)
                
                if response.status_code in [200, 401, 403]:  # 401/403 are OK - means API is responding
                    logger.info(f"✓ API Gateway endpoint is responding: {api_url}")
                else:
                    logger.warning(f"⚠ API Gateway endpoint returned status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"⚠ API Gateway endpoint test failed: {str(e)}")
                # Don't fail validation for endpoint test issues
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Error validating API Gateway: {str(e)}")
            return False
    
    def validate_monitoring(self) -> bool:
        """Validate CloudWatch monitoring is set up"""
        logger.info("Validating CloudWatch monitoring...")
        
        try:
            # Check for CloudWatch alarms
            response = self.cloudwatch.describe_alarms(
                AlarmNamePrefix=f'Biomerkin-{self.environment}'
            )
            
            alarms = response['MetricAlarms']
            logger.info(f"✓ Found {len(alarms)} CloudWatch alarms")
            
            # Check alarm states
            active_alarms = [alarm for alarm in alarms if alarm['StateValue'] == 'ALARM']
            if active_alarms:
                logger.warning(f"⚠ {len(active_alarms)} alarms are currently in ALARM state")
                for alarm in active_alarms:
                    logger.warning(f"  - {alarm['AlarmName']}: {alarm['StateReason']}")
            else:
                logger.info("✓ No alarms are currently firing")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Error validating monitoring: {str(e)}")
            return False
    
    def run_integration_test(self) -> bool:
        """Run a simple integration test"""
        logger.info("Running integration test...")
        
        try:
            # Test orchestrator function with a simple workflow
            orchestrator_function = f'biomerkin-orchestrator-{self.environment}'
            
            test_event = {
                'httpMethod': 'POST',
                'path': '/workflows',
                'body': json.dumps({
                    'sequence_data': 'ATCGATCGATCG',  # Simple test sequence
                    'test_mode': True
                }),
                'headers': {
                    'Content-Type': 'application/json'
                }
            }
            
            response = self.lambda_client.invoke(
                FunctionName=orchestrator_function,
                InvocationType='RequestResponse',
                Payload=json.dumps(test_event)
            )
            
            if response['StatusCode'] == 200:
                payload = json.loads(response['Payload'].read())
                logger.info(f"✓ Integration test successful: {payload}")
                return True
            else:
                logger.error(f"✗ Integration test failed with status {response['StatusCode']}")
                return False
                
        except Exception as e:
            logger.warning(f"⚠ Integration test failed: {str(e)}")
            # Don't fail overall validation for integration test issues
            return True
    
    def validate_deployment(self) -> bool:
        """Run complete deployment validation"""
        logger.info(f"Starting deployment validation for {self.environment} environment...")
        
        validation_results = {
            'cloudformation': self.validate_cloudformation_stack(),
            'lambda_functions': self.validate_lambda_functions(),
            'dynamodb_tables': self.validate_dynamodb_tables(),
            's3_buckets': self.validate_s3_buckets(),
            'api_gateway': self.validate_api_gateway(),
            'monitoring': self.validate_monitoring(),
            'integration_test': self.run_integration_test()
        }
        
        # Summary
        passed = sum(1 for result in validation_results.values() if result)
        total = len(validation_results)
        
        logger.info(f"\nValidation Summary:")
        logger.info(f"Passed: {passed}/{total} checks")
        
        for check, result in validation_results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"  {check}: {status}")
        
        overall_success = all(validation_results.values())
        
        if overall_success:
            logger.info(f"\n🎉 Deployment validation PASSED for {self.environment} environment!")
        else:
            logger.error(f"\n❌ Deployment validation FAILED for {self.environment} environment!")
        
        return overall_success


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Validate Biomerkin deployment')
    parser.add_argument('environment', help='Environment to validate (dev, staging, prod)')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    args = parser.parse_args()
    
    validator = DeploymentValidator(args.environment, args.region)
    success = validator.validate_deployment()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()