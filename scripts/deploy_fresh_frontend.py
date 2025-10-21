#!/usr/bin/env python3
"""
Deploy Fresh Frontend to S3
Creates a new bucket with proper configuration and deploys frontend
"""

import boto3
import json
import time
from datetime import datetime

def deploy_fresh_frontend():
    """Deploy frontend to a fresh S3 bucket"""
    
    # Create unique bucket name
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    bucket_name = f'biomerkin-frontend-{timestamp}'
    region = 'ap-south-1'
    
    print("="*80)
    print("🚀 DEPLOYING FRESH FRONTEND TO S3")
    print("="*80)
    print(f"\nBucket Name: {bucket_name}")
    print(f"Region: {region}")
    
    s3_client = boto3.client('s3', region_name=region)
    
    try:
        # Step 1: Create bucket
        print("\n📦 Step 1: Creating S3 bucket...")
        s3_client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={'LocationConstraint': region}
        )
        print(f"  ✅ Bucket created: {bucket_name}")
        
        # Step 2: Disable block public access
        print("\n🔓 Step 2: Configuring public access...")
        s3_client.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        )
        print("  ✅ Public access configured")
        
        # Step 3: Set bucket policy
        print("\n📜 Step 3: Setting bucket policy...")
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*"
            }]
        }
        
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        print("  ✅ Bucket policy set")
        
        # Step 4: Enable website hosting
        print("\n🌐 Step 4: Enabling website hosting...")
        s3_client.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'index.html'}
            }
        )
        print("  ✅ Website hosting enabled")
        
        # Step 5: Upload frontend files
        print("\n📤 Step 5: Uploading frontend files...")
        print("  Run this command to upload files:")
        print(f"\n  cd frontend/build")
        print(f"  aws s3 sync . s3://{bucket_name}/ --acl public-read")
        
        # Generate URLs
        print("\n" + "="*80)
        print("✅ DEPLOYMENT COMPLETE!")
        print("="*80)
        
        print(f"\n🌐 Your Frontend URLs:")
        print(f"\n  Primary URL:")
        print(f"  http://{bucket_name}.s3-website-{region}.amazonaws.com")
        
        print(f"\n  Alternative URL:")
        print(f"  http://{bucket_name}.s3-website.{region}.amazonaws.com")
        
        print(f"\n  Direct S3 URL:")
        print(f"  https://{bucket_name}.s3.{region}.amazonaws.com/index.html")
        
        print(f"\n📋 Next Steps:")
        print(f"  1. Build your frontend:")
        print(f"     cd frontend && npm run build")
        print(f"\n  2. Upload files:")
        print(f"     aws s3 sync build/ s3://{bucket_name}/ --acl public-read")
        print(f"\n  3. Access your site:")
        print(f"     http://{bucket_name}.s3-website-{region}.amazonaws.com")
        
        print("\n" + "="*80)
        
        # Save info to file
        with open('FRONTEND_DEPLOYMENT_INFO.txt', 'w') as f:
            f.write(f"Bucket Name: {bucket_name}\n")
            f.write(f"Region: {region}\n")
            f.write(f"Primary URL: http://{bucket_name}.s3-website-{region}.amazonaws.com\n")
            f.write(f"Alternative URL: http://{bucket_name}.s3-website.{region}.amazonaws.com\n")
            f.write(f"Direct URL: https://{bucket_name}.s3.{region}.amazonaws.com/index.html\n")
        
        print("📄 Deployment info saved to: FRONTEND_DEPLOYMENT_INFO.txt\n")
        
        return bucket_name
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

if __name__ == '__main__':
    deploy_fresh_frontend()
