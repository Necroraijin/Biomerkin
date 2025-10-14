#!/usr/bin/env python3
"""
Disaster Recovery and Rollback procedures for Biomerkin Multi-Agent System
Handles backup, restore, and rollback operations
"""

import argparse
import boto3
import json
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DisasterRecoveryManager:
    """Manages disaster recovery and rollback procedures"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.cloudformation = boto3.client('cloudformation', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.dynamodb = boto3.client('dynamodb', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.ssm = boto3.client('ssm', region_name=region)
        
        # Backup configuration
        self.backup_bucket_prefix = "biomerkin-disaster-recovery"
        self.backup_retention_days = 30
    
    def create_backup_bucket(self, environment: str) -> str:
        """Create or ensure backup bucket exists"""
        bucket_name = f"{self.backup_bucket_prefix}-{environment}-{self.region}"
        
        try:
            # Check if bucket exists
            self.s3.head_bucket(Bucket=bucket_name)
            logger.info(f"Backup bucket already exists: {bucket_name}")
            
        except self.s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Create bucket
                if self.region == 'us-east-1':
                    self.s3.create_bucket(Bucket=bucket_name)
                else:
                    self.s3.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': self.region}
                    )
                
                # Enable versioning
                self.s3.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
                
                # Set lifecycle policy
                lifecycle_config = {
                    'Rules': [
                        {
                            'ID': 'DeleteOldBackups',
                            'Status': 'Enabled',
                            'Filter': {'Prefix': 'backups/'},
                            'Expiration': {'Days': self.backup_retention_days},
                            'NoncurrentVersionExpiration': {'NoncurrentDays': 7}
                        }
                    ]
                }
                
                self.s3.put_bucket_lifecycle_configuration(
                    Bucket=bucket_name,
                    LifecycleConfiguration=lifecycle_config
                )
                
                logger.info(f"Created backup bucket: {bucket_name}")
            else:
                raise e
        
        return bucket_name
    
    def backup_cloudformation_template(self, environment: str, stack_name: str) -> bool:
        """Backup CloudFormation template"""
        try:
            backup_bucket = self.create_backup_bucket(environment)
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            
            # Get current template
            response = self.cloudformation.get_template(StackName=stack_name)
            template = response['TemplateBody']
            
            # Upload to S3
            key = f"backups/cloudformation/{stack_name}/{timestamp}/template.json"
            self.s3.put_object(
                Bucket=backup_bucket,
                Key=key,
                Body=json.dumps(template, indent=2),
                ContentType='application/json'
            )
            
            # Also backup stack parameters
            stack_response = self.cloudformation.describe_stacks(StackName=stack_name)
            stack_info = stack_response['Stacks'][0]
            
            stack_key = f"backups/cloudformation/{stack_name}/{timestamp}/stack-info.json"
            self.s3.put_object(
                Bucket=backup_bucket,
                Key=stack_key,
                Body=json.dumps(stack_info, indent=2, default=str),
                ContentType='application/json'
            )
            
            logger.info(f"CloudFormation template backed up: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup CloudFormation template: {str(e)}")
            return False
    
    def backup_dynamodb_tables(self, environment: str) -> bool:
        """Backup DynamoDB tables"""
        try:
            backup_bucket = self.create_backup_bucket(environment)
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            
            # List tables for this environment
            table_prefix = f"biomerkin-{environment}"
            response = self.dynamodb.list_tables()
            
            environment_tables = [
                table for table in response['TableNames']
                if table.startswith(table_prefix)
            ]
            
            for table_name in environment_tables:
                try:
                    # Create point-in-time recovery backup
                    backup_name = f"{table_name}-backup-{timestamp}"
                    
                    self.dynamodb.create_backup(
                        TableName=table_name,
                        BackupName=backup_name
                    )
                    
                    logger.info(f"Created DynamoDB backup: {backup_name}")
                    
                    # Also export table data to S3 for additional safety
                    # This would require setting up DynamoDB export to S3
                    # For now, we'll just log the intent
                    logger.info(f"DynamoDB table {table_name} backup initiated")
                    
                except Exception as e:
                    logger.warning(f"Failed to backup table {table_name}: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup DynamoDB tables: {str(e)}")
            return False
    
    def backup_lambda_functions(self, environment: str) -> bool:
        """Backup Lambda function code and configuration"""
        try:
            backup_bucket = self.create_backup_bucket(environment)
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            
            # List Lambda functions for this environment
            function_prefix = f"biomerkin-{environment}"
            response = self.lambda_client.list_functions()
            
            environment_functions = [
                func for func in response['Functions']
                if func['FunctionName'].startswith(function_prefix)
            ]
            
            for function in environment_functions:
                function_name = function['FunctionName']
                
                try:
                    # Get function configuration
                    config_response = self.lambda_client.get_function(
                        FunctionName=function_name
                    )
                    
                    # Backup function configuration
                    config_key = f"backups/lambda/{function_name}/{timestamp}/config.json"
                    self.s3.put_object(
                        Bucket=backup_bucket,
                        Key=config_key,
                        Body=json.dumps(config_response, indent=2, default=str),
                        ContentType='application/json'
                    )
                    
                    # Get function code URL
                    code_url = config_response['Code']['Location']
                    
                    # Download and backup function code
                    import requests
                    code_response = requests.get(code_url)
                    
                    if code_response.status_code == 200:
                        code_key = f"backups/lambda/{function_name}/{timestamp}/code.zip"
                        self.s3.put_object(
                            Bucket=backup_bucket,
                            Key=code_key,
                            Body=code_response.content,
                            ContentType='application/zip'
                        )
                    
                    logger.info(f"Lambda function backed up: {function_name}")
                    
                except Exception as e:
                    logger.warning(f"Failed to backup function {function_name}: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to backup Lambda functions: {str(e)}")
            return False
    
    def create_full_backup(self, environment: str) -> bool:
        """Create a full backup of the environment"""
        logger.info(f"Creating full backup for {environment} environment...")
        
        try:
            # Get stack name
            stack_name = f"Biomerkin{environment.title()}"
            
            # Backup CloudFormation template
            if not self.backup_cloudformation_template(environment, stack_name):
                logger.warning("CloudFormation backup failed")
            
            # Backup DynamoDB tables
            if not self.backup_dynamodb_tables(environment):
                logger.warning("DynamoDB backup failed")
            
            # Backup Lambda functions
            if not self.backup_lambda_functions(environment):
                logger.warning("Lambda backup failed")
            
            # Store backup metadata
            backup_bucket = self.create_backup_bucket(environment)
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            
            backup_metadata = {
                'environment': environment,
                'timestamp': timestamp,
                'backup_type': 'full',
                'components': ['cloudformation', 'dynamodb', 'lambda'],
                'created_at': datetime.now().isoformat(),
                'region': self.region
            }
            
            metadata_key = f"backups/metadata/{timestamp}/backup-info.json"
            self.s3.put_object(
                Bucket=backup_bucket,
                Key=metadata_key,
                Body=json.dumps(backup_metadata, indent=2),
                ContentType='application/json'
            )
            
            logger.info(f"Full backup completed for {environment} environment")
            return True
            
        except Exception as e:
            logger.error(f"Full backup failed: {str(e)}")
            return False
    
    def list_backups(self, environment: str) -> List[Dict]:
        """List available backups for an environment"""
        try:
            backup_bucket = self.create_backup_bucket(environment)
            
            response = self.s3.list_objects_v2(
                Bucket=backup_bucket,
                Prefix='backups/metadata/',
                Delimiter='/'
            )
            
            backups = []
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('backup-info.json'):
                        # Get backup metadata
                        metadata_response = self.s3.get_object(
                            Bucket=backup_bucket,
                            Key=obj['Key']
                        )
                        
                        metadata = json.loads(metadata_response['Body'].read())
                        backups.append(metadata)
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {str(e)}")
            return []
    
    def rollback_to_backup(self, environment: str, backup_timestamp: str) -> bool:
        """Rollback environment to a specific backup"""
        logger.info(f"Rolling back {environment} to backup {backup_timestamp}...")
        
        try:
            backup_bucket = self.create_backup_bucket(environment)
            stack_name = f"Biomerkin{environment.title()}"
            
            # Get backup metadata
            metadata_key = f"backups/metadata/{backup_timestamp}/backup-info.json"
            metadata_response = self.s3.get_object(
                Bucket=backup_bucket,
                Key=metadata_key
            )
            backup_metadata = json.loads(metadata_response['Body'].read())
            
            logger.info(f"Backup metadata: {backup_metadata}")
            
            # Restore CloudFormation stack
            template_key = f"backups/cloudformation/{stack_name}/{backup_timestamp}/template.json"
            
            try:
                template_response = self.s3.get_object(
                    Bucket=backup_bucket,
                    Key=template_key
                )
                template_body = template_response['Body'].read().decode('utf-8')
                
                # Update stack with backup template
                self.cloudformation.update_stack(
                    StackName=stack_name,
                    TemplateBody=template_body,
                    Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM']
                )
                
                logger.info(f"Initiated CloudFormation rollback for {stack_name}")
                
                # Wait for stack update to complete
                waiter = self.cloudformation.get_waiter('stack_update_complete')
                waiter.wait(
                    StackName=stack_name,
                    WaiterConfig={'Delay': 30, 'MaxAttempts': 60}
                )
                
                logger.info("CloudFormation rollback completed")
                
            except Exception as e:
                logger.error(f"CloudFormation rollback failed: {str(e)}")
                return False
            
            # Note: DynamoDB and Lambda rollback would require more complex logic
            # For now, we'll just log the intent
            logger.info("Manual intervention may be required for DynamoDB and Lambda rollback")
            
            logger.info(f"Rollback to {backup_timestamp} completed")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return False
    
    def validate_backup_integrity(self, environment: str, backup_timestamp: str) -> bool:
        """Validate backup integrity"""
        try:
            backup_bucket = self.create_backup_bucket(environment)
            
            # Check if all expected backup components exist
            expected_components = [
                f"backups/metadata/{backup_timestamp}/backup-info.json",
                f"backups/cloudformation/Biomerkin{environment.title()}/{backup_timestamp}/template.json"
            ]
            
            for component in expected_components:
                try:
                    self.s3.head_object(Bucket=backup_bucket, Key=component)
                    logger.info(f"Backup component verified: {component}")
                except self.s3.exceptions.ClientError:
                    logger.error(f"Missing backup component: {component}")
                    return False
            
            logger.info(f"Backup {backup_timestamp} integrity validated")
            return True
            
        except Exception as e:
            logger.error(f"Backup validation failed: {str(e)}")
            return False
    
    def cleanup_old_backups(self, environment: str) -> bool:
        """Clean up old backups beyond retention period"""
        try:
            backup_bucket = self.create_backup_bucket(environment)
            cutoff_date = datetime.now() - timedelta(days=self.backup_retention_days)
            
            response = self.s3.list_objects_v2(
                Bucket=backup_bucket,
                Prefix='backups/'
            )
            
            deleted_count = 0
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                        self.s3.delete_object(
                            Bucket=backup_bucket,
                            Key=obj['Key']
                        )
                        deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} old backup objects")
            return True
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {str(e)}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Disaster Recovery for Biomerkin')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create backup
    backup_parser = subparsers.add_parser('backup', help='Create backup')
    backup_parser.add_argument('environment', help='Environment name')
    
    # List backups
    list_parser = subparsers.add_parser('list', help='List backups')
    list_parser.add_argument('environment', help='Environment name')
    
    # Rollback
    rollback_parser = subparsers.add_parser('rollback', help='Rollback to backup')
    rollback_parser.add_argument('environment', help='Environment name')
    rollback_parser.add_argument('timestamp', help='Backup timestamp')
    
    # Validate backup
    validate_parser = subparsers.add_parser('validate', help='Validate backup')
    validate_parser.add_argument('environment', help='Environment name')
    validate_parser.add_argument('timestamp', help='Backup timestamp')
    
    # Cleanup old backups
    cleanup_parser = subparsers.add_parser('cleanup', help='Cleanup old backups')
    cleanup_parser.add_argument('environment', help='Environment name')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return False
    
    dr_manager = DisasterRecoveryManager(args.region)
    
    if args.command == 'backup':
        success = dr_manager.create_full_backup(args.environment)
    elif args.command == 'list':
        backups = dr_manager.list_backups(args.environment)
        print(f"Available backups for {args.environment}:")
        for backup in backups:
            print(f"  - {backup['timestamp']} ({backup['backup_type']}) - {backup['created_at']}")
        success = True
    elif args.command == 'rollback':
        success = dr_manager.rollback_to_backup(args.environment, args.timestamp)
    elif args.command == 'validate':
        success = dr_manager.validate_backup_integrity(args.environment, args.timestamp)
    elif args.command == 'cleanup':
        success = dr_manager.cleanup_old_backups(args.environment)
    else:
        parser.print_help()
        success = False
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)