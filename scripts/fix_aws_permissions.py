#!/usr/bin/env python3
"""
Fix AWS IAM permissions for Biomerkin deployment.
"""

import boto3
import json
from datetime import datetime

def check_current_permissions():
    """Check what permissions the current user has."""
    
    print("🔍 CHECKING YOUR AWS PERMISSIONS")
    print("="*40)
    
    try:
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        
        print(f"✅ Current User: {identity['Arn']}")
        print(f"✅ Account ID: {identity['Account']}")
        
        # Extract username
        arn_parts = identity['Arn'].split('/')
        username = arn_parts[-1] if len(arn_parts) > 1 else "unknown"
        
        return username, identity['Account']
        
    except Exception as e:
        print(f"❌ Error checking identity: {e}")
        return None, None

def test_required_permissions():
    """Test if user has required permissions."""
    
    print("\n🧪 TESTING REQUIRED PERMISSIONS")
    print("="*35)
    
    # List of services we need to test
    test_cases = [
        ("IAM", "iam", "list_roles", {}),
        ("Lambda", "lambda", "list_functions", {}),
        ("API Gateway", "apigateway", "get_rest_apis", {}),
        ("DynamoDB", "dynamodb", "list_tables", {}),
        ("S3", "s3", "list_buckets", {}),
    ]
    
    permissions_ok = True
    
    for service_name, service, method, params in test_cases:
        try:
            client = boto3.client(service)
            getattr(client, method)(**params)
            print(f"   ✅ {service_name}: Can access")
        except Exception as e:
            print(f"   ❌ {service_name}: {e}")
            permissions_ok = False
    
    return permissions_ok

def create_policy_for_user(username):
    """Create the required IAM policy for deployment."""
    
    print(f"\n📋 CREATING DEPLOYMENT POLICY FOR USER: {username}")
    print("="*50)
    
    # Comprehensive policy for Biomerkin deployment
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    # IAM permissions
                    "iam:GetRole",
                    "iam:CreateRole",
                    "iam:AttachRolePolicy",
                    "iam:CreatePolicy",
                    "iam:GetPolicy",
                    "iam:ListRoles",
                    "iam:ListPolicies",
                    "iam:PassRole",
                    
                    # Lambda permissions
                    "lambda:CreateFunction",
                    "lambda:UpdateFunctionCode",
                    "lambda:UpdateFunctionConfiguration",
                    "lambda:GetFunction",
                    "lambda:ListFunctions",
                    "lambda:InvokeFunction",
                    "lambda:AddPermission",
                    
                    # API Gateway permissions
                    "apigateway:*",
                    
                    # DynamoDB permissions
                    "dynamodb:CreateTable",
                    "dynamodb:DescribeTable",
                    "dynamodb:ListTables",
                    "dynamodb:PutItem",
                    "dynamodb:GetItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                    
                    # S3 permissions
                    "s3:CreateBucket",
                    "s3:ListBucket",
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:PutBucketPolicy",
                    "s3:PutBucketWebsite",
                    "s3:GetBucketLocation",
                    "s3:ListAllMyBuckets",
                    
                    # Bedrock permissions
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                    "bedrock:ListFoundationModels",
                    
                    # CloudWatch permissions
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogGroups",
                    "logs:DescribeLogStreams",
                    
                    # STS permissions
                    "sts:GetCallerIdentity"
                ],
                "Resource": "*"
            }
        ]
    }
    
    try:
        iam_client = boto3.client('iam')
        
        policy_name = f"BiomerkinDeploymentPolicy-{datetime.now().strftime('%Y%m%d')}"
        
        # Create the policy
        response = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document),
            Description="Comprehensive permissions for Biomerkin deployment"
        )
        
        policy_arn = response['Policy']['Arn']
        print(f"✅ Created policy: {policy_name}")
        
        # Attach policy to user
        iam_client.attach_user_policy(
            UserName=username,
            PolicyArn=policy_arn
        )
        
        print(f"✅ Attached policy to user: {username}")
        
        return True, policy_arn
        
    except Exception as e:
        print(f"❌ Failed to create/attach policy: {e}")
        return False, None

def provide_manual_instructions(username, account_id):
    """Provide manual instructions for adding permissions."""
    
    print(f"\n📋 MANUAL PERMISSION SETUP INSTRUCTIONS")
    print("="*45)
    
    print("Since automatic policy creation failed, please follow these steps:")
    
    print(f"\n1️⃣ GO TO AWS IAM CONSOLE:")
    print(f"   https://console.aws.amazon.com/iam/")
    
    print(f"\n2️⃣ FIND YOUR USER:")
    print(f"   • Click 'Users' in the left sidebar")
    print(f"   • Find and click on user: {username}")
    
    print(f"\n3️⃣ ADD ADMINISTRATOR ACCESS (EASIEST):")
    print(f"   • Click 'Add permissions' button")
    print(f"   • Select 'Attach policies directly'")
    print(f"   • Search for 'AdministratorAccess'")
    print(f"   • Check the box next to 'AdministratorAccess'")
    print(f"   • Click 'Add permissions'")
    
    print(f"\n⚠️ SECURITY NOTE:")
    print(f"   AdministratorAccess gives full permissions - perfect for hackathons!")
    print(f"   For production, you'd want more restricted permissions.")
    
    print(f"\n4️⃣ ALTERNATIVE - ATTACH SPECIFIC POLICIES:")
    print(f"   Instead of AdministratorAccess, attach these policies:")
    print(f"   • IAMFullAccess")
    print(f"   • AWSLambdaFullAccess") 
    print(f"   • AmazonAPIGatewayAdministrator")
    print(f"   • AmazonDynamoDBFullAccess")
    print(f"   • AmazonS3FullAccess")
    
    print(f"\n5️⃣ TEST YOUR PERMISSIONS:")
    print(f"   python scripts/fix_aws_permissions.py")

def main():
    """Main permission fixing function."""
    
    # Check current user
    username, account_id = check_current_permissions()
    
    if not username:
        print("❌ Cannot determine current user")
        return False
    
    # Test current permissions
    permissions_ok = test_required_permissions()
    
    if permissions_ok:
        print("\n🎉 ALL PERMISSIONS ARE WORKING!")
        print("You can now run the deployment:")
        print("   python scripts/deploy_biomerkin_to_aws.py")
        return True
    
    print(f"\n🔧 ATTEMPTING TO FIX PERMISSIONS...")
    
    # Try to create and attach policy
    success, policy_arn = create_policy_for_user(username)
    
    if success:
        print(f"\n✅ PERMISSIONS FIXED!")
        print(f"Policy created: {policy_arn}")
        print(f"\n⏳ Wait 30 seconds for permissions to propagate, then run:")
        print(f"   python scripts/deploy_biomerkin_to_aws.py")
        return True
    else:
        print(f"\n❌ AUTOMATIC FIX FAILED")
        provide_manual_instructions(username, account_id)
        return False

if __name__ == "__main__":
    main()