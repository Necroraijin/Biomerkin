#!/usr/bin/env python3
"""
Fix S3 public access settings for Biomerkin frontend deployment.
"""

import boto3
import json
import time

def fix_s3_public_access():
    """Fix S3 public access settings."""
    
    print("🔧 FIXING S3 PUBLIC ACCESS SETTINGS")
    print("="*40)
    
    try:
        s3_client = boto3.client('s3')
        
        # Find the biomerkin bucket
        response = s3_client.list_buckets()
        biomerkin_bucket = None
        
        for bucket in response['Buckets']:
            if 'biomerkin-frontend' in bucket['Name']:
                biomerkin_bucket = bucket['Name']
                break
        
        if not biomerkin_bucket:
            print("❌ No Biomerkin S3 bucket found")
            return False
        
        print(f"📦 Found bucket: {biomerkin_bucket}")
        
        # Remove block public access settings
        print("🔓 Removing block public access settings...")
        
        try:
            s3_client.put_public_access_block(
                Bucket=biomerkin_bucket,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': False,
                    'IgnorePublicAcls': False,
                    'BlockPublicPolicy': False,
                    'RestrictPublicBuckets': False
                }
            )
            print("✅ Removed block public access settings")
        except Exception as e:
            print(f"⚠️ Could not modify public access settings: {e}")
        
        # Wait a moment for settings to propagate
        print("⏳ Waiting for settings to propagate...")
        time.sleep(5)
        
        # Now set the bucket policy for website hosting
        print("🌐 Setting bucket policy for website hosting...")
        
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{biomerkin_bucket}/*"
                }
            ]
        }
        
        try:
            s3_client.put_bucket_policy(
                Bucket=biomerkin_bucket,
                Policy=json.dumps(bucket_policy)
            )
            print("✅ Set bucket policy successfully")
        except Exception as e:
            print(f"❌ Failed to set bucket policy: {e}")
            return False
        
        # Configure website hosting
        print("🏠 Configuring website hosting...")
        
        try:
            website_config = {
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'index.html'}
            }
            
            s3_client.put_bucket_website(
                Bucket=biomerkin_bucket,
                WebsiteConfiguration=website_config
            )
            print("✅ Configured website hosting")
        except Exception as e:
            print(f"⚠️ Website configuration warning: {e}")
        
        # Get website URL
        region = boto3.Session().region_name or 'us-east-1'
        website_url = f"http://{biomerkin_bucket}.s3-website-{region}.amazonaws.com"
        
        print(f"\n🎉 S3 BUCKET FIXED!")
        print(f"📦 Bucket: {biomerkin_bucket}")
        print(f"🌐 Website URL: {website_url}")
        
        return True, biomerkin_bucket, website_url
        
    except Exception as e:
        print(f"❌ Error fixing S3 settings: {e}")
        return False

def provide_manual_instructions():
    """Provide manual instructions for S3 setup."""
    
    print("\n📋 MANUAL S3 SETUP INSTRUCTIONS")
    print("="*35)
    
    print("If automatic fix failed, follow these steps:")
    
    print("\n1️⃣ GO TO S3 CONSOLE:")
    print("   https://console.aws.amazon.com/s3/")
    
    print("\n2️⃣ FIND YOUR BUCKET:")
    print("   • Look for bucket starting with 'biomerkin-frontend-'")
    print("   • Click on the bucket name")
    
    print("\n3️⃣ DISABLE BLOCK PUBLIC ACCESS:")
    print("   • Click 'Permissions' tab")
    print("   • Find 'Block public access' section")
    print("   • Click 'Edit'")
    print("   • Uncheck ALL 4 boxes")
    print("   • Click 'Save changes'")
    print("   • Type 'confirm' when prompted")
    
    print("\n4️⃣ ADD BUCKET POLICY:")
    print("   • Still in 'Permissions' tab")
    print("   • Find 'Bucket policy' section")
    print("   • Click 'Edit'")
    print("   • Paste this policy (replace BUCKET_NAME):")
    
    policy_template = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::BUCKET_NAME/*"
    }
  ]
}"""
    
    print(f"   {policy_template}")
    print("   • Click 'Save changes'")
    
    print("\n5️⃣ ENABLE WEBSITE HOSTING:")
    print("   • Click 'Properties' tab")
    print("   • Find 'Static website hosting'")
    print("   • Click 'Edit'")
    print("   • Select 'Enable'")
    print("   • Index document: index.html")
    print("   • Error document: index.html")
    print("   • Click 'Save changes'")

def main():
    """Main S3 fixing function."""
    
    result = fix_s3_public_access()
    
    if result and len(result) == 3:
        success, bucket_name, website_url = result
        
        if success:
            print("\n🎉 S3 SETUP COMPLETE!")
            print("Now you can continue with deployment:")
            print("   python scripts/deploy_biomerkin_to_aws.py")
            return True
    
    print("\n❌ AUTOMATIC FIX FAILED")
    provide_manual_instructions()
    return False

if __name__ == "__main__":
    main()