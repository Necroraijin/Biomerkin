"""
Security infrastructure deployment for the Biomerkin multi-agent system.

This module deploys security-related AWS resources including KMS keys,
CloudTrail, security groups, and monitoring for compliance and audit logging.
"""

import boto3
import json
import time
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError

from .iam_policies import setup_iam_infrastructure


class SecurityInfrastructureDeployer:
    """Deploys security infrastructure for the Biomerkin system."""
    
    def __init__(self, region: str = 'us-east-1'):
        """
        Initialize the security infrastructure deployer.
        
        Args:
            region: AWS region for deployment
        """
        self.region = region
        self.kms_client = boto3.client('kms', region_name=region)
        self.cloudtrail_client = boto3.client('cloudtrail', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        self.logs_client = boto3.client('logs', region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)
        
        print(f"Initialized security deployer for region: {region}")
    
    def deploy_all_security_infrastructure(self) -> Dict[str, Any]:
        """Deploy all security infrastructure components."""
        print("Starting security infrastructure deployment...")
        
        results = {}
        
        try:
            # 1. Deploy KMS keys for encryption
            print("Deploying KMS encryption keys...")
            kms_results = self.deploy_kms_keys()
            results['kms'] = kms_results
            
            # 2. Deploy CloudTrail for audit logging
            print("Deploying CloudTrail for audit logging...")
            cloudtrail_results = self.deploy_cloudtrail(kms_results['audit_key_id'])
            results['cloudtrail'] = cloudtrail_results
            
            # 3. Deploy S3 buckets with encryption
            print("Deploying secure S3 buckets...")
            s3_results = self.deploy_secure_s3_buckets(kms_results['data_key_id'])
            results['s3'] = s3_results
            
            # 4. Deploy CloudWatch log groups
            print("Deploying CloudWatch log groups...")
            logs_results = self.deploy_cloudwatch_logs()
            results['logs'] = logs_results
            
            # 5. Deploy security monitoring
            print("Deploying security monitoring...")
            monitoring_results = self.deploy_security_monitoring()
            results['monitoring'] = monitoring_results
            
            # 6. Deploy IAM infrastructure
            print("Deploying IAM roles and policies...")
            iam_results = setup_iam_infrastructure()
            results['iam'] = iam_results
            
            # 7. Deploy VPC security groups (if needed)
            print("Deploying VPC security groups...")
            vpc_results = self.deploy_vpc_security_groups()
            results['vpc'] = vpc_results
            
            print("Security infrastructure deployment completed successfully!")
            return results
            
        except Exception as e:
            print(f"Security infrastructure deployment failed: {e}")
            raise
    
    def deploy_kms_keys(self) -> Dict[str, str]:
        """Deploy KMS keys for encryption."""
        keys = {}
        
        # Data encryption key
        data_key_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:root"
                    },
                    "Action": "kms:*",
                    "Resource": "*"
                },
                {
                    "Sid": "Allow Biomerkin services",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": [
                            f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:role/biomerkin-*"
                        ]
                    },
                    "Action": [
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            data_key_response = self.kms_client.create_key(
                Description="Biomerkin data encryption key",
                KeyUsage='ENCRYPT_DECRYPT',
                KeySpec='SYMMETRIC_DEFAULT',
                Policy=json.dumps(data_key_policy),
                Tags=[
                    {'TagKey': 'Project', 'TagValue': 'Biomerkin'},
                    {'TagKey': 'Purpose', 'TagValue': 'DataEncryption'},
                    {'TagKey': 'Environment', 'TagValue': 'Production'}
                ]
            )
            
            data_key_id = data_key_response['KeyMetadata']['KeyId']
            keys['data_key_id'] = data_key_id
            
            # Create alias for data key
            self.kms_client.create_alias(
                AliasName='alias/biomerkin-data-encryption',
                TargetKeyId=data_key_id
            )
            
            print(f"Created data encryption key: {data_key_id}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                print("Data encryption key already exists")
                # Get existing key
                aliases = self.kms_client.list_aliases()
                for alias in aliases['Aliases']:
                    if alias['AliasName'] == 'alias/biomerkin-data-encryption':
                        keys['data_key_id'] = alias['TargetKeyId']
                        break
            else:
                raise
        
        # Audit logging key
        audit_key_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:root"
                    },
                    "Action": "kms:*",
                    "Resource": "*"
                },
                {
                    "Sid": "Allow CloudTrail",
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "cloudtrail.amazonaws.com"
                    },
                    "Action": [
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            audit_key_response = self.kms_client.create_key(
                Description="Biomerkin audit logging encryption key",
                KeyUsage='ENCRYPT_DECRYPT',
                KeySpec='SYMMETRIC_DEFAULT',
                Policy=json.dumps(audit_key_policy),
                Tags=[
                    {'TagKey': 'Project', 'TagValue': 'Biomerkin'},
                    {'TagKey': 'Purpose', 'TagValue': 'AuditEncryption'},
                    {'TagKey': 'Environment', 'TagValue': 'Production'}
                ]
            )
            
            audit_key_id = audit_key_response['KeyMetadata']['KeyId']
            keys['audit_key_id'] = audit_key_id
            
            # Create alias for audit key
            self.kms_client.create_alias(
                AliasName='alias/biomerkin-audit-encryption',
                TargetKeyId=audit_key_id
            )
            
            print(f"Created audit encryption key: {audit_key_id}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                print("Audit encryption key already exists")
                # Get existing key
                aliases = self.kms_client.list_aliases()
                for alias in aliases['Aliases']:
                    if alias['AliasName'] == 'alias/biomerkin-audit-encryption':
                        keys['audit_key_id'] = alias['TargetKeyId']
                        break
            else:
                raise
        
        return keys
    
    def deploy_cloudtrail(self, kms_key_id: str) -> Dict[str, Any]:
        """Deploy CloudTrail for audit logging."""
        trail_name = "biomerkin-audit-trail"
        bucket_name = f"biomerkin-audit-logs-{boto3.client('sts').get_caller_identity()['Account']}-{self.region}"
        
        # Create S3 bucket for CloudTrail logs
        try:
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            # Enable versioning
            self.s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            
            # Enable encryption
            self.s3_client.put_bucket_encryption(
                Bucket=bucket_name,
                ServerSideEncryptionConfiguration={
                    'Rules': [
                        {
                            'ApplyServerSideEncryptionByDefault': {
                                'SSEAlgorithm': 'aws:kms',
                                'KMSMasterKeyID': kms_key_id
                            }
                        }
                    ]
                }
            )
            
            # Set bucket policy for CloudTrail
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AWSCloudTrailAclCheck",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "cloudtrail.amazonaws.com"
                        },
                        "Action": "s3:GetBucketAcl",
                        "Resource": f"arn:aws:s3:::{bucket_name}"
                    },
                    {
                        "Sid": "AWSCloudTrailWrite",
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "cloudtrail.amazonaws.com"
                        },
                        "Action": "s3:PutObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/*",
                        "Condition": {
                            "StringEquals": {
                                "s3:x-amz-acl": "bucket-owner-full-control"
                            }
                        }
                    }
                ]
            }
            
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            print(f"Created CloudTrail S3 bucket: {bucket_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                print(f"CloudTrail S3 bucket already exists: {bucket_name}")
            else:
                raise
        
        # Create CloudTrail
        try:
            trail_response = self.cloudtrail_client.create_trail(
                Name=trail_name,
                S3BucketName=bucket_name,
                IncludeGlobalServiceEvents=True,
                IsMultiRegionTrail=True,
                EnableLogFileValidation=True,
                KMSKeyId=kms_key_id,
                EventSelectors=[
                    {
                        'ReadWriteType': 'All',
                        'IncludeManagementEvents': True,
                        'DataResources': [
                            {
                                'Type': 'AWS::S3::Object',
                                'Values': ['arn:aws:s3:::biomerkin-*/*']
                            },
                            {
                                'Type': 'AWS::DynamoDB::Table',
                                'Values': ['arn:aws:dynamodb:*:*:table/biomerkin-*']
                            }
                        ]
                    }
                ],
                Tags=[
                    {'Key': 'Project', 'Value': 'Biomerkin'},
                    {'Key': 'Purpose', 'Value': 'AuditLogging'},
                    {'Key': 'Environment', 'Value': 'Production'}
                ]
            )
            
            # Start logging
            self.cloudtrail_client.start_logging(Name=trail_name)
            
            print(f"Created and started CloudTrail: {trail_name}")
            
            return {
                'trail_name': trail_name,
                'trail_arn': trail_response['TrailARN'],
                'bucket_name': bucket_name
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'TrailAlreadyExistsException':
                print(f"CloudTrail already exists: {trail_name}")
                # Get existing trail
                trails = self.cloudtrail_client.describe_trails(trailNameList=[trail_name])
                if trails['trailList']:
                    return {
                        'trail_name': trail_name,
                        'trail_arn': trails['trailList'][0]['TrailARN'],
                        'bucket_name': bucket_name
                    }
            else:
                raise
    
    def deploy_secure_s3_buckets(self, kms_key_id: str) -> Dict[str, str]:
        """Deploy S3 buckets with encryption and security policies."""
        account_id = boto3.client('sts').get_caller_identity()['Account']
        buckets = {}
        
        bucket_configs = [
            {
                'name': f'biomerkin-data-{account_id}-{self.region}',
                'purpose': 'data-storage'
            },
            {
                'name': f'biomerkin-results-{account_id}-{self.region}',
                'purpose': 'results-storage'
            },
            {
                'name': f'biomerkin-uploads-{account_id}-{self.region}',
                'purpose': 'file-uploads'
            }
        ]
        
        for bucket_config in bucket_configs:
            bucket_name = bucket_config['name']
            
            try:
                # Create bucket
                if self.region == 'us-east-1':
                    self.s3_client.create_bucket(Bucket=bucket_name)
                else:
                    self.s3_client.create_bucket(
                        Bucket=bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': self.region}
                    )
                
                # Enable versioning
                self.s3_client.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
                
                # Enable encryption
                self.s3_client.put_bucket_encryption(
                    Bucket=bucket_name,
                    ServerSideEncryptionConfiguration={
                        'Rules': [
                            {
                                'ApplyServerSideEncryptionByDefault': {
                                    'SSEAlgorithm': 'aws:kms',
                                    'KMSMasterKeyID': kms_key_id
                                }
                            }
                        ]
                    }
                )
                
                # Block public access
                self.s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True,
                        'RestrictPublicBuckets': True
                    }
                )
                
                # Set bucket policy
                bucket_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Deny",
                            "Principal": "*",
                            "Action": "s3:*",
                            "Resource": [
                                f"arn:aws:s3:::{bucket_name}",
                                f"arn:aws:s3:::{bucket_name}/*"
                            ],
                            "Condition": {
                                "Bool": {
                                    "aws:SecureTransport": "false"
                                }
                            }
                        }
                    ]
                }
                
                self.s3_client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=json.dumps(bucket_policy)
                )
                
                buckets[bucket_config['purpose']] = bucket_name
                print(f"Created secure S3 bucket: {bucket_name}")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                    buckets[bucket_config['purpose']] = bucket_name
                    print(f"S3 bucket already exists: {bucket_name}")
                else:
                    raise
        
        return buckets
    
    def deploy_cloudwatch_logs(self) -> Dict[str, str]:
        """Deploy CloudWatch log groups for security logging."""
        log_groups = {}
        
        log_group_configs = [
            {
                'name': '/biomerkin/audit',
                'retention_days': 2555,  # 7 years for compliance
                'purpose': 'audit-logs'
            },
            {
                'name': '/biomerkin/security',
                'retention_days': 365,
                'purpose': 'security-logs'
            },
            {
                'name': '/biomerkin/application',
                'retention_days': 90,
                'purpose': 'application-logs'
            },
            {
                'name': '/aws/lambda/biomerkin-security',
                'retention_days': 30,
                'purpose': 'lambda-security-logs'
            }
        ]
        
        for log_config in log_group_configs:
            log_group_name = log_config['name']
            
            try:
                self.logs_client.create_log_group(
                    logGroupName=log_group_name,
                    tags={
                        'Project': 'Biomerkin',
                        'Purpose': log_config['purpose'],
                        'Environment': 'Production'
                    }
                )
                
                # Set retention policy
                self.logs_client.put_retention_policy(
                    logGroupName=log_group_name,
                    retentionInDays=log_config['retention_days']
                )
                
                log_groups[log_config['purpose']] = log_group_name
                print(f"Created CloudWatch log group: {log_group_name}")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                    log_groups[log_config['purpose']] = log_group_name
                    print(f"CloudWatch log group already exists: {log_group_name}")
                else:
                    raise
        
        return log_groups
    
    def deploy_security_monitoring(self) -> Dict[str, str]:
        """Deploy security monitoring and alerting."""
        alarms = {}
        
        # Create CloudWatch alarms for security events
        alarm_configs = [
            {
                'name': 'BiomerkinUnauthorizedAccess',
                'description': 'Alert on unauthorized access attempts',
                'metric_name': 'UnauthorizedAccessAttempts',
                'namespace': 'Biomerkin/Security',
                'threshold': 5,
                'comparison': 'GreaterThanThreshold'
            },
            {
                'name': 'BiomerkinEncryptionFailures',
                'description': 'Alert on encryption failures',
                'metric_name': 'EncryptionFailures',
                'namespace': 'Biomerkin/Security',
                'threshold': 1,
                'comparison': 'GreaterThanOrEqualToThreshold'
            },
            {
                'name': 'BiomerkinAuditLogFailures',
                'description': 'Alert on audit log failures',
                'metric_name': 'AuditLogFailures',
                'namespace': 'Biomerkin/Security',
                'threshold': 1,
                'comparison': 'GreaterThanOrEqualToThreshold'
            }
        ]
        
        for alarm_config in alarm_configs:
            try:
                self.cloudwatch_client.put_metric_alarm(
                    AlarmName=alarm_config['name'],
                    AlarmDescription=alarm_config['description'],
                    MetricName=alarm_config['metric_name'],
                    Namespace=alarm_config['namespace'],
                    Statistic='Sum',
                    Period=300,  # 5 minutes
                    EvaluationPeriods=1,
                    Threshold=alarm_config['threshold'],
                    ComparisonOperator=alarm_config['comparison'],
                    Tags=[
                        {'Key': 'Project', 'Value': 'Biomerkin'},
                        {'Key': 'Purpose', 'Value': 'SecurityMonitoring'},
                        {'Key': 'Environment', 'Value': 'Production'}
                    ]
                )
                
                alarms[alarm_config['name']] = alarm_config['name']
                print(f"Created CloudWatch alarm: {alarm_config['name']}")
                
            except ClientError as e:
                print(f"Error creating alarm {alarm_config['name']}: {e}")
        
        return alarms
    
    def deploy_vpc_security_groups(self) -> Dict[str, str]:
        """Deploy VPC security groups for network security."""
        security_groups = {}
        
        try:
            # Get default VPC
            vpcs = self.ec2_client.describe_vpcs(
                Filters=[{'Name': 'is-default', 'Values': ['true']}]
            )
            
            if not vpcs['Vpcs']:
                print("No default VPC found, skipping security group creation")
                return security_groups
            
            vpc_id = vpcs['Vpcs'][0]['VpcId']
            
            # Create security group for Lambda functions
            try:
                sg_response = self.ec2_client.create_security_group(
                    GroupName='biomerkin-lambda-sg',
                    Description='Security group for Biomerkin Lambda functions',
                    VpcId=vpc_id,
                    TagSpecifications=[
                        {
                            'ResourceType': 'security-group',
                            'Tags': [
                                {'Key': 'Name', 'Value': 'biomerkin-lambda-sg'},
                                {'Key': 'Project', 'Value': 'Biomerkin'},
                                {'Key': 'Purpose', 'Value': 'LambdaSecurity'}
                            ]
                        }
                    ]
                )
                
                sg_id = sg_response['GroupId']
                
                # Add outbound rules for HTTPS only
                self.ec2_client.authorize_security_group_egress(
                    GroupId=sg_id,
                    IpPermissions=[
                        {
                            'IpProtocol': 'tcp',
                            'FromPort': 443,
                            'ToPort': 443,
                            'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTPS outbound'}]
                        }
                    ]
                )
                
                # Remove default outbound rule
                self.ec2_client.revoke_security_group_egress(
                    GroupId=sg_id,
                    IpPermissions=[
                        {
                            'IpProtocol': '-1',
                            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                        }
                    ]
                )
                
                security_groups['lambda-sg'] = sg_id
                print(f"Created Lambda security group: {sg_id}")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'InvalidGroup.Duplicate':
                    # Get existing security group
                    sgs = self.ec2_client.describe_security_groups(
                        Filters=[
                            {'Name': 'group-name', 'Values': ['biomerkin-lambda-sg']},
                            {'Name': 'vpc-id', 'Values': [vpc_id]}
                        ]
                    )
                    if sgs['SecurityGroups']:
                        security_groups['lambda-sg'] = sgs['SecurityGroups'][0]['GroupId']
                        print("Lambda security group already exists")
                else:
                    raise
                    
        except Exception as e:
            print(f"Error creating VPC security groups: {e}")
        
        return security_groups
    
    def validate_security_deployment(self) -> Dict[str, bool]:
        """Validate that security infrastructure is properly deployed."""
        validation_results = {}
        
        try:
            # Check KMS keys
            aliases = self.kms_client.list_aliases()
            data_key_exists = any(alias['AliasName'] == 'alias/biomerkin-data-encryption' for alias in aliases['Aliases'])
            audit_key_exists = any(alias['AliasName'] == 'alias/biomerkin-audit-encryption' for alias in aliases['Aliases'])
            
            validation_results['kms_data_key'] = data_key_exists
            validation_results['kms_audit_key'] = audit_key_exists
            
            # Check CloudTrail
            trails = self.cloudtrail_client.describe_trails(trailNameList=['biomerkin-audit-trail'])
            validation_results['cloudtrail'] = len(trails['trailList']) > 0
            
            # Check S3 buckets
            account_id = boto3.client('sts').get_caller_identity()['Account']
            bucket_name = f'biomerkin-data-{account_id}-{self.region}'
            
            try:
                self.s3_client.head_bucket(Bucket=bucket_name)
                validation_results['s3_buckets'] = True
            except ClientError:
                validation_results['s3_buckets'] = False
            
            # Check CloudWatch log groups
            try:
                self.logs_client.describe_log_groups(logGroupNamePrefix='/biomerkin/')
                validation_results['cloudwatch_logs'] = True
            except ClientError:
                validation_results['cloudwatch_logs'] = False
            
            print("Security infrastructure validation completed")
            return validation_results
            
        except Exception as e:
            print(f"Security validation failed: {e}")
            return {'validation_error': str(e)}


def deploy_security_infrastructure(region: str = 'us-east-1') -> Dict[str, Any]:
    """
    Deploy all security infrastructure for the Biomerkin system.
    
    Args:
        region: AWS region for deployment
        
    Returns:
        Dictionary containing deployment results
    """
    deployer = SecurityInfrastructureDeployer(region)
    return deployer.deploy_all_security_infrastructure()


def validate_security_infrastructure(region: str = 'us-east-1') -> Dict[str, bool]:
    """
    Validate security infrastructure deployment.
    
    Args:
        region: AWS region to validate
        
    Returns:
        Dictionary containing validation results
    """
    deployer = SecurityInfrastructureDeployer(region)
    return deployer.validate_security_deployment()


if __name__ == "__main__":
    import sys
    
    region = sys.argv[1] if len(sys.argv) > 1 else 'us-east-1'
    
    print(f"Deploying security infrastructure in region: {region}")
    results = deploy_security_infrastructure(region)
    
    print("\nDeployment Results:")
    for component, details in results.items():
        print(f"  {component}: {details}")
    
    print("\nValidating deployment...")
    validation = validate_security_infrastructure(region)
    
    print("\nValidation Results:")
    for check, passed in validation.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {check}: {status}")
    
    all_passed = all(validation.values()) if 'validation_error' not in validation else False
    print(f"\nOverall Status: {'✓ ALL CHECKS PASSED' if all_passed else '✗ SOME CHECKS FAILED'}")