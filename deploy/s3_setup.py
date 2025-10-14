"""
S3 setup for Biomerkin file storage with secure access
"""
import boto3
import json
from typing import Dict, Any

class S3Manager:
    def __init__(self, region='us-east-1'):
        self.s3_client = boto3.client('s3', region_name=region)
        self.region = region
    
    def create_bucket(self, bucket_name: str, enable_versioning: bool = True,
                     enable_encryption: bool = True) -> bool:
        """Create an S3 bucket with security configurations"""
        try:
            # Create bucket
            if self.region != 'us-east-1':
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            else:
                self.s3_client.create_bucket(Bucket=bucket_name)
            
            # Enable versioning
            if enable_versioning:
                self.s3_client.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
            
            # Enable server-side encryption
            if enable_encryption:
                self.s3_client.put_bucket_encryption(
                    Bucket=bucket_name,
                    ServerSideEncryptionConfiguration={
                        'Rules': [
                            {
                                'ApplyServerSideEncryptionByDefault': {
                                    'SSEAlgorithm': 'AES256'
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
            
            print(f"Bucket {bucket_name} created successfully")
            return True
            
        except self.s3_client.exceptions.BucketAlreadyExists:
            print(f"Bucket {bucket_name} already exists")
            return True
        except Exception as e:
            print(f"Error creating bucket {bucket_name}: {e}")
            return False
    
    def set_bucket_policy(self, bucket_name: str, policy: Dict[str, Any]) -> bool:
        """Set bucket policy for secure access"""
        try:
            self.s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(policy)
            )
            print(f"Bucket policy set for {bucket_name}")
            return True
        except Exception as e:
            print(f"Error setting bucket policy: {e}")
            return False
    
    def enable_lifecycle_policy(self, bucket_name: str) -> bool:
        """Enable lifecycle policy for cost optimization"""
        lifecycle_config = {
            'Rules': [
                {
                    'ID': 'BiomerkinDataLifecycle',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': ''},
                    'Transitions': [
                        {
                            'Days': 30,
                            'StorageClass': 'STANDARD_IA'
                        },
                        {
                            'Days': 90,
                            'StorageClass': 'GLACIER'
                        },
                        {
                            'Days': 365,
                            'StorageClass': 'DEEP_ARCHIVE'
                        }
                    ],
                    'Expiration': {
                        'Days': 2555  # 7 years retention
                    }
                },
                {
                    'ID': 'DeleteIncompleteMultipartUploads',
                    'Status': 'Enabled',
                    'Filter': {'Prefix': ''},
                    'AbortIncompleteMultipartUpload': {
                        'DaysAfterInitiation': 7
                    }
                }
            ]
        }
        
        try:
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=bucket_name,
                LifecycleConfiguration=lifecycle_config
            )
            print(f"Lifecycle policy enabled for {bucket_name}")
            return True
        except Exception as e:
            print(f"Error setting lifecycle policy: {e}")
            return False
    
    def enable_cloudtrail_logging(self, bucket_name: str) -> bool:
        """Enable CloudTrail logging for S3 access"""
        try:
            self.s3_client.put_bucket_logging(
                Bucket=bucket_name,
                BucketLoggingStatus={
                    'LoggingEnabled': {
                        'TargetBucket': f"{bucket_name}-access-logs",
                        'TargetPrefix': 'access-logs/'
                    }
                }
            )
            print(f"CloudTrail logging enabled for {bucket_name}")
            return True
        except Exception as e:
            print(f"Error enabling CloudTrail logging: {e}")
            return False

def create_bucket_policies(account_id: str) -> Dict[str, Dict[str, Any]]:
    """Create secure bucket policies for different use cases"""
    
    # Main data bucket policy
    data_bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowLambdaAccess",
                "Effect": "Allow",
                "Principal": {
                    "AWS": [
                        f"arn:aws:iam::{account_id}:role/biomerkin-*-lambda-role"
                    ]
                },
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject"
                ],
                "Resource": f"arn:aws:s3:::biomerkin-data/*"
            },
            {
                "Sid": "AllowLambdaListBucket",
                "Effect": "Allow",
                "Principal": {
                    "AWS": [
                        f"arn:aws:iam::{account_id}:role/biomerkin-*-lambda-role"
                    ]
                },
                "Action": "s3:ListBucket",
                "Resource": f"arn:aws:s3:::biomerkin-data"
            },
            {
                "Sid": "DenyInsecureConnections",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::biomerkin-data",
                    f"arn:aws:s3:::biomerkin-data/*"
                ],
                "Condition": {
                    "Bool": {
                        "aws:SecureTransport": "false"
                    }
                }
            }
        ]
    }
    
    # Results bucket policy (for processed results)
    results_bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowLambdaAccess",
                "Effect": "Allow",
                "Principal": {
                    "AWS": [
                        f"arn:aws:iam::{account_id}:role/biomerkin-*-lambda-role"
                    ]
                },
                "Action": [
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                "Resource": f"arn:aws:s3:::biomerkin-results/*"
            },
            {
                "Sid": "AllowCloudFrontAccess",
                "Effect": "Allow",
                "Principal": {
                    "AWS": f"arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity"
                },
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::biomerkin-results/*"
            },
            {
                "Sid": "DenyInsecureConnections",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": [
                    f"arn:aws:s3:::biomerkin-results",
                    f"arn:aws:s3:::biomerkin-results/*"
                ],
                "Condition": {
                    "Bool": {
                        "aws:SecureTransport": "false"
                    }
                }
            }
        ]
    }
    
    # Logs bucket policy
    logs_bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowCloudTrailLogs",
                "Effect": "Allow",
                "Principal": {
                    "Service": "cloudtrail.amazonaws.com"
                },
                "Action": "s3:PutObject",
                "Resource": f"arn:aws:s3:::biomerkin-logs/*",
                "Condition": {
                    "StringEquals": {
                        "s3:x-amz-acl": "bucket-owner-full-control"
                    }
                }
            },
            {
                "Sid": "AllowCloudTrailGetBucketAcl",
                "Effect": "Allow",
                "Principal": {
                    "Service": "cloudtrail.amazonaws.com"
                },
                "Action": "s3:GetBucketAcl",
                "Resource": f"arn:aws:s3:::biomerkin-logs"
            }
        ]
    }
    
    return {
        'data_bucket': data_bucket_policy,
        'results_bucket': results_bucket_policy,
        'logs_bucket': logs_bucket_policy
    }

def setup_s3_infrastructure(account_id: str) -> Dict[str, bool]:
    """Set up all S3 buckets for the Biomerkin system"""
    s3_manager = S3Manager()
    results = {}
    
    # Create buckets
    buckets_config = {
        'biomerkin-data': {
            'description': 'Main data storage for DNA sequences and intermediate results',
            'versioning': True,
            'encryption': True
        },
        'biomerkin-results': {
            'description': 'Processed results and reports',
            'versioning': True,
            'encryption': True
        },
        'biomerkin-logs': {
            'description': 'Access logs and audit trails',
            'versioning': False,
            'encryption': True
        },
        'biomerkin-temp': {
            'description': 'Temporary files and processing artifacts',
            'versioning': False,
            'encryption': True
        }
    }
    
    # Create buckets
    for bucket_name, config in buckets_config.items():
        print(f"Creating bucket: {bucket_name}")
        success = s3_manager.create_bucket(
            bucket_name=bucket_name,
            enable_versioning=config['versioning'],
            enable_encryption=config['encryption']
        )
        results[bucket_name] = success
        
        if success:
            # Enable lifecycle policy for cost optimization
            s3_manager.enable_lifecycle_policy(bucket_name)
    
    # Set bucket policies
    policies = create_bucket_policies(account_id)
    
    policy_mappings = {
        'biomerkin-data': policies['data_bucket'],
        'biomerkin-results': policies['results_bucket'],
        'biomerkin-logs': policies['logs_bucket']
    }
    
    for bucket_name, policy in policy_mappings.items():
        if results.get(bucket_name):
            s3_manager.set_bucket_policy(bucket_name, policy)
    
    return results

def create_s3_client_utility():
    """Create a utility class for S3 operations"""
    client_code = '''
"""
S3 client utility for Biomerkin file operations
"""
import boto3
import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError

class BiomerkinS3Client:
    def __init__(self, region='us-east-1'):
        self.s3_client = boto3.client('s3', region_name=region)
        self.region = region
        self.data_bucket = 'biomerkin-data'
        self.results_bucket = 'biomerkin-results'
        self.temp_bucket = 'biomerkin-temp'
    
    def upload_dna_sequence(self, workflow_id: str, sequence_data: str, 
                           filename: str = None) -> str:
        """Upload DNA sequence data to S3"""
        if not filename:
            filename = f"{workflow_id}/input/sequence.fasta"
        
        try:
            self.s3_client.put_object(
                Bucket=self.data_bucket,
                Key=filename,
                Body=sequence_data,
                ContentType='text/plain',
                Metadata={
                    'workflow_id': workflow_id,
                    'upload_time': datetime.utcnow().isoformat(),
                    'file_type': 'dna_sequence'
                }
            )
            return f"s3://{self.data_bucket}/{filename}"
        except Exception as e:
            print(f"Error uploading DNA sequence: {e}")
            return None
    
    def store_agent_results(self, workflow_id: str, agent_name: str, 
                           results: Dict[str, Any]) -> str:
        """Store agent results in S3"""
        filename = f"{workflow_id}/results/{agent_name}_results.json"
        
        try:
            self.s3_client.put_object(
                Bucket=self.results_bucket,
                Key=filename,
                Body=json.dumps(results, indent=2, default=str),
                ContentType='application/json',
                Metadata={
                    'workflow_id': workflow_id,
                    'agent_name': agent_name,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            return f"s3://{self.results_bucket}/{filename}"
        except Exception as e:
            print(f"Error storing agent results: {e}")
            return None
    
    def store_final_report(self, workflow_id: str, report_data: Dict[str, Any],
                          format_type: str = 'json') -> str:
        """Store final medical report"""
        if format_type == 'json':
            filename = f"{workflow_id}/reports/medical_report.json"
            body = json.dumps(report_data, indent=2, default=str)
            content_type = 'application/json'
        elif format_type == 'html':
            filename = f"{workflow_id}/reports/medical_report.html"
            body = report_data.get('html_content', '')
            content_type = 'text/html'
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
        
        try:
            self.s3_client.put_object(
                Bucket=self.results_bucket,
                Key=filename,
                Body=body,
                ContentType=content_type,
                Metadata={
                    'workflow_id': workflow_id,
                    'report_type': 'medical_report',
                    'format': format_type,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            return f"s3://{self.results_bucket}/{filename}"
        except Exception as e:
            print(f"Error storing final report: {e}")
            return None
    
    def get_file(self, bucket: str, key: str) -> Optional[str]:
        """Get file content from S3"""
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read().decode('utf-8')
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            print(f"Error getting file: {e}")
            return None
    
    def get_workflow_files(self, workflow_id: str) -> Dict[str, List[str]]:
        """Get all files associated with a workflow"""
        files = {'input': [], 'results': [], 'reports': []}
        
        buckets_to_check = [
            (self.data_bucket, 'input'),
            (self.results_bucket, 'results'),
            (self.results_bucket, 'reports')
        ]
        
        for bucket, file_type in buckets_to_check:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=bucket,
                    Prefix=f"{workflow_id}/{file_type}/"
                )
                
                for obj in response.get('Contents', []):
                    files[file_type].append(obj['Key'])
            except Exception as e:
                print(f"Error listing files in {bucket}: {e}")
        
        return files
    
    def generate_presigned_url(self, bucket: str, key: str, 
                              expiration: int = 3600) -> Optional[str]:
        """Generate a presigned URL for secure file access"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            print(f"Error generating presigned URL: {e}")
            return None
    
    def delete_workflow_files(self, workflow_id: str) -> bool:
        """Delete all files associated with a workflow"""
        try:
            # Get all files for the workflow
            files = self.get_workflow_files(workflow_id)
            
            # Delete from each bucket
            for bucket_name in [self.data_bucket, self.results_bucket]:
                objects_to_delete = []
                
                # Collect all objects to delete
                for file_type, file_list in files.items():
                    for file_key in file_list:
                        if file_key.startswith(f"{workflow_id}/"):
                            objects_to_delete.append({'Key': file_key})
                
                # Delete objects in batches
                if objects_to_delete:
                    self.s3_client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects_to_delete}
                    )
            
            return True
        except Exception as e:
            print(f"Error deleting workflow files: {e}")
            return False
    
    def get_storage_metrics(self) -> Dict[str, Any]:
        """Get storage usage metrics"""
        metrics = {}
        
        for bucket_name in [self.data_bucket, self.results_bucket, self.temp_bucket]:
            try:
                # Get bucket size using CloudWatch metrics would be more accurate
                # This is a simplified version
                response = self.s3_client.list_objects_v2(Bucket=bucket_name)
                
                total_size = 0
                object_count = 0
                
                for obj in response.get('Contents', []):
                    total_size += obj['Size']
                    object_count += 1
                
                metrics[bucket_name] = {
                    'total_size_bytes': total_size,
                    'object_count': object_count,
                    'total_size_mb': round(total_size / (1024 * 1024), 2)
                }
            except Exception as e:
                print(f"Error getting metrics for {bucket_name}: {e}")
                metrics[bucket_name] = {'error': str(e)}
        
        return metrics
'''
    
    os.makedirs('biomerkin/utils', exist_ok=True)
    with open('biomerkin/utils/s3_client.py', 'w') as f:
        f.write(client_code)

if __name__ == "__main__":
    # Get account ID
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()['Account']
    
    results = setup_s3_infrastructure(account_id)
    create_s3_client_utility()
    
    print("S3 setup results:")
    for bucket, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {bucket}")