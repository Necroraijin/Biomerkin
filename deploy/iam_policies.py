"""
IAM roles and policies for Biomerkin multi-agent system with enhanced security.

This module implements least-privilege access principles, encryption requirements,
and comprehensive audit logging for all AWS resources.
"""
import boto3
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class IAMManager:
    def __init__(self):
        self.iam_client = boto3.client('iam')
    
    def create_lambda_execution_role(self, role_name: str) -> str:
        """Create IAM role for Lambda function execution"""
        trust_policy = {
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
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"Execution role for {role_name} Lambda function"
            )
            
            # Attach basic Lambda execution policy
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            
            return response['Role']['Arn']
        except Exception as e:
            print(f"Error creating role {role_name}: {e}")
            return None
    
    def create_bedrock_agent_role(self, role_name: str) -> str:
        """Create IAM role for Bedrock Agent"""
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
        
        bedrock_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "lambda:InvokeFunction"
                    ],
                    "Resource": "arn:aws:lambda:*:*:function:biomerkin-*"
                }
            ]
        }
        
        try:
            # Create role
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Execution role for Bedrock Agent"
            )
            
            # Create and attach custom policy
            policy_response = self.iam_client.create_policy(
                PolicyName=f"{role_name}-policy",
                PolicyDocument=json.dumps(bedrock_policy),
                Description="Policy for Bedrock Agent to invoke models and Lambda functions"
            )
            
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_response['Policy']['Arn']
            )
            
            return response['Role']['Arn']
        except Exception as e:
            print(f"Error creating Bedrock role {role_name}: {e}")
            return None
    
    def create_lambda_policies(self) -> Dict[str, str]:
        """Create specific policies for different Lambda functions with least-privilege access"""
        policies = {}
        
        # DynamoDB access policy with encryption requirements
        dynamodb_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan"
                    ],
                    "Resource": "arn:aws:dynamodb:*:*:table/biomerkin-*",
                    "Condition": {
                        "Bool": {
                            "dynamodb:EncryptedTable": "true"
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:DescribeTable"
                    ],
                    "Resource": "arn:aws:dynamodb:*:*:table/biomerkin-*"
                }
            ]
        }
        
        # S3 access policy with encryption requirements
        s3_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject"
                    ],
                    "Resource": "arn:aws:s3:::biomerkin-*/*",
                    "Condition": {
                        "StringEquals": {
                            "s3:x-amz-server-side-encryption": "AES256"
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:ListBucket",
                        "s3:GetBucketLocation"
                    ],
                    "Resource": "arn:aws:s3:::biomerkin-*"
                },
                {
                    "Effect": "Deny",
                    "Action": "s3:*",
                    "Resource": [
                        "arn:aws:s3:::biomerkin-*/*",
                        "arn:aws:s3:::biomerkin-*"
                    ],
                    "Condition": {
                        "Bool": {
                            "aws:SecureTransport": "false"
                        }
                    }
                }
            ]
        }
        
        # Bedrock access policy
        bedrock_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        # CloudWatch logs policy with audit logging
        cloudwatch_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams"
                    ],
                    "Resource": [
                        "arn:aws:logs:*:*:log-group:/biomerkin/*",
                        "arn:aws:logs:*:*:log-group:/aws/lambda/biomerkin-*"
                    ]
                }
            ]
        }
        
        # KMS access policy for encryption
        kms_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey*",
                        "kms:DescribeKey"
                    ],
                    "Resource": "arn:aws:kms:*:*:key/*",
                    "Condition": {
                        "StringEquals": {
                            "kms:ViaService": [
                                "s3.*.amazonaws.com",
                                "dynamodb.*.amazonaws.com"
                            ]
                        }
                    }
                }
            ]
        }
        
        # CloudTrail access policy for audit logging
        cloudtrail_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "cloudtrail:PutEvents"
                    ],
                    "Resource": "arn:aws:cloudtrail:*:*:trail/biomerkin-audit-trail"
                }
            ]
        }
        
        policy_definitions = {
            "BiomerkinDynamoDBPolicy": dynamodb_policy,
            "BiomerkinS3Policy": s3_policy,
            "BiomerkinBedrockPolicy": bedrock_policy,
            "BiomerkinCloudWatchPolicy": cloudwatch_policy,
            "BiomerkinKMSPolicy": kms_policy,
            "BiomerkinCloudTrailPolicy": cloudtrail_policy
        }
        
        for policy_name, policy_doc in policy_definitions.items():
            try:
                response = self.iam_client.create_policy(
                    PolicyName=policy_name,
                    PolicyDocument=json.dumps(policy_doc),
                    Description=f"Policy for Biomerkin {policy_name.replace('Biomerkin', '').replace('Policy', '')} access"
                )
                policies[policy_name] = response['Policy']['Arn']
            except Exception as e:
                print(f"Error creating policy {policy_name}: {e}")
        
        return policies
    
    def attach_policies_to_role(self, role_name: str, policy_arns: list):
        """Attach multiple policies to a role"""
        for policy_arn in policy_arns:
            try:
                self.iam_client.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn=policy_arn
                )
            except Exception as e:
                print(f"Error attaching policy {policy_arn} to role {role_name}: {e}")
    
    def create_security_boundary_policy(self) -> str:
        """Create a permissions boundary policy for additional security"""
        boundary_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:*",
                        "s3:*",
                        "bedrock:*",
                        "logs:*",
                        "kms:*",
                        "cloudtrail:*"
                    ],
                    "Resource": "*",
                    "Condition": {
                        "StringLike": {
                            "aws:RequestedRegion": ["us-east-1", "us-west-2"]
                        }
                    }
                },
                {
                    "Effect": "Deny",
                    "Action": [
                        "iam:*",
                        "organizations:*",
                        "account:*"
                    ],
                    "Resource": "*"
                }
            ]
        }
        
        try:
            response = self.iam_client.create_policy(
                PolicyName="BiomerkinSecurityBoundary",
                PolicyDocument=json.dumps(boundary_policy),
                Description="Security boundary policy for Biomerkin resources"
            )
            return response['Policy']['Arn']
        except Exception as e:
            print(f"Error creating security boundary policy: {e}")
            return None
    
    def create_audit_role(self) -> str:
        """Create IAM role for audit logging and monitoring"""
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": ["lambda.amazonaws.com", "cloudtrail.amazonaws.com"]
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        audit_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams"
                    ],
                    "Resource": "arn:aws:logs:*:*:log-group:/biomerkin/audit*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "cloudtrail:CreateTrail",
                        "cloudtrail:StartLogging",
                        "cloudtrail:StopLogging",
                        "cloudtrail:PutEvents"
                    ],
                    "Resource": "*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:PutObject",
                        "s3:GetBucketAcl"
                    ],
                    "Resource": [
                        "arn:aws:s3:::biomerkin-audit-logs",
                        "arn:aws:s3:::biomerkin-audit-logs/*"
                    ]
                }
            ]
        }
        
        try:
            # Create role
            role_response = self.iam_client.create_role(
                RoleName="biomerkin-audit-role",
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="Role for Biomerkin audit logging and monitoring"
            )
            
            # Create and attach policy
            policy_response = self.iam_client.create_policy(
                PolicyName="BiomerkinAuditPolicy",
                PolicyDocument=json.dumps(audit_policy),
                Description="Policy for Biomerkin audit operations"
            )
            
            self.iam_client.attach_role_policy(
                RoleName="biomerkin-audit-role",
                PolicyArn=policy_response['Policy']['Arn']
            )
            
            return role_response['Role']['Arn']
        except Exception as e:
            print(f"Error creating audit role: {e}")
            return None
    
    def enable_mfa_requirement(self, role_name: str):
        """Add MFA requirement to role (for human users)"""
        mfa_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Deny",
                    "Action": "*",
                    "Resource": "*",
                    "Condition": {
                        "BoolIfExists": {
                            "aws:MultiFactorAuthPresent": "false"
                        },
                        "NumericLessThan": {
                            "aws:MultiFactorAuthAge": "3600"
                        }
                    }
                }
            ]
        }
        
        try:
            policy_response = self.iam_client.create_policy(
                PolicyName=f"{role_name}-MFA-Policy",
                PolicyDocument=json.dumps(mfa_policy),
                Description=f"MFA requirement policy for {role_name}"
            )
            
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_response['Policy']['Arn']
            )
        except Exception as e:
            print(f"Error adding MFA requirement to {role_name}: {e}")
    
    def create_resource_based_policies(self) -> Dict[str, Any]:
        """Create resource-based policies for additional security"""
        policies = {}
        
        # S3 bucket policy
        s3_bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:*",
                    "Resource": [
                        "arn:aws:s3:::biomerkin-*",
                        "arn:aws:s3:::biomerkin-*/*"
                    ],
                    "Condition": {
                        "Bool": {
                            "aws:SecureTransport": "false"
                        }
                    }
                },
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "arn:aws:iam::*:role/biomerkin-*"
                    },
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject"
                    ],
                    "Resource": "arn:aws:s3:::biomerkin-*/*",
                    "Condition": {
                        "StringEquals": {
                            "s3:x-amz-server-side-encryption": "AES256"
                        }
                    }
                }
            ]
        }
        
        policies['s3_bucket_policy'] = s3_bucket_policy
        
        # DynamoDB resource policy
        dynamodb_resource_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": "arn:aws:iam::*:role/biomerkin-*"
                    },
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan"
                    ],
                    "Resource": "arn:aws:dynamodb:*:*:table/biomerkin-*"
                }
            ]
        }
        
        policies['dynamodb_resource_policy'] = dynamodb_resource_policy
        
        return policies

def setup_iam_infrastructure():
    """Set up all IAM roles and policies for the Biomerkin system with enhanced security"""
    iam_manager = IAMManager()
    
    # Create policies
    policies = iam_manager.create_lambda_policies()
    
    # Create security boundary policy
    boundary_policy_arn = iam_manager.create_security_boundary_policy()
    
    # Create audit role
    audit_role_arn = iam_manager.create_audit_role()
    
    # Create Lambda execution roles for each agent
    agent_roles = {}
    agents = ['orchestrator', 'genomics', 'proteomics', 'literature', 'drug', 'decision']
    
    for agent in agents:
        role_name = f"biomerkin-{agent}-lambda-role"
        role_arn = iam_manager.create_lambda_execution_role(role_name)
        if role_arn:
            agent_roles[agent] = role_arn
            
            # Attach relevant policies based on agent needs (least privilege)
            policies_to_attach = [
                policies.get('BiomerkinCloudWatchPolicy'),
                policies.get('BiomerkinKMSPolicy')
            ]
            
            # Agent-specific policies
            if agent == 'orchestrator':
                policies_to_attach.extend([
                    policies.get('BiomerkinDynamoDBPolicy'),
                    policies.get('BiomerkinS3Policy'),
                    policies.get('BiomerkinCloudTrailPolicy')
                ])
            elif agent in ['genomics', 'proteomics']:
                policies_to_attach.append(policies.get('BiomerkinDynamoDBPolicy'))
            elif agent in ['literature', 'decision']:
                policies_to_attach.extend([
                    policies.get('BiomerkinBedrockPolicy'),
                    policies.get('BiomerkinDynamoDBPolicy')
                ])
            elif agent == 'drug':
                policies_to_attach.append(policies.get('BiomerkinDynamoDBPolicy'))
            
            # Filter out None values
            policies_to_attach = [p for p in policies_to_attach if p]
            iam_manager.attach_policies_to_role(role_name, policies_to_attach)
    
    # Create Bedrock Agent role
    bedrock_role_arn = iam_manager.create_bedrock_agent_role("biomerkin-bedrock-agent-role")
    
    # Create resource-based policies
    resource_policies = iam_manager.create_resource_based_policies()
    
    return {
        'agent_roles': agent_roles,
        'bedrock_role': bedrock_role_arn,
        'audit_role': audit_role_arn,
        'policies': policies,
        'boundary_policy': boundary_policy_arn,
        'resource_policies': resource_policies
    }

if __name__ == "__main__":
    setup_iam_infrastructure()