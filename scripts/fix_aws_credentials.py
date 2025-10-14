#!/usr/bin/env python3
"""
Fix AWS credentials configuration issues.
"""

import os
import boto3
from pathlib import Path

def diagnose_aws_credentials():
    """Diagnose AWS credentials issues."""
    
    print("🔍 DIAGNOSING AWS CREDENTIALS ISSUE")
    print("="*50)
    
    # Check if AWS CLI is installed
    try:
        import subprocess
        result = subprocess.run(['aws', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ AWS CLI is installed")
            print(f"   Version: {result.stdout.strip()}")
        else:
            print("❌ AWS CLI not found")
            return False
    except FileNotFoundError:
        print("❌ AWS CLI not installed")
        return False
    
    # Check credentials file
    aws_dir = Path.home() / '.aws'
    credentials_file = aws_dir / 'credentials'
    config_file = aws_dir / 'config'
    
    print(f"\n📁 Checking AWS configuration files:")
    print(f"   AWS directory: {aws_dir}")
    print(f"   Credentials file: {credentials_file} - {'✅ EXISTS' if credentials_file.exists() else '❌ MISSING'}")
    print(f"   Config file: {config_file} - {'✅ EXISTS' if config_file.exists() else '❌ MISSING'}")
    
    # Check environment variables
    print(f"\n🌍 Checking environment variables:")
    env_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION']
    
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            # Mask the secret key for security
            if 'SECRET' in var:
                masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '*' * len(value)
                print(f"   {var}: {masked_value}")
            else:
                print(f"   {var}: {value}")
        else:
            print(f"   {var}: ❌ NOT SET")
    
    # Try to read credentials file
    if credentials_file.exists():
        print(f"\n📄 Credentials file content:")
        try:
            with open(credentials_file, 'r') as f:
                content = f.read()
                
            # Mask sensitive data
            lines = content.split('\n')
            for line in lines:
                if 'aws_secret_access_key' in line.lower():
                    parts = line.split('=')
                    if len(parts) == 2:
                        key = parts[1].strip()
                        masked = key[:4] + '*' * (len(key) - 8) + key[-4:] if len(key) > 8 else '*' * len(key)
                        print(f"   aws_secret_access_key = {masked}")
                else:
                    print(f"   {line}")
                    
        except Exception as e:
            print(f"   ❌ Error reading credentials: {e}")
    
    return True

def fix_aws_credentials():
    """Interactive AWS credentials setup."""
    
    print("\n🔧 FIXING AWS CREDENTIALS")
    print("="*30)
    
    print("Let's set up your AWS credentials step by step.")
    print("\n📋 You'll need:")
    print("1. AWS Access Key ID (starts with AKIA...)")
    print("2. AWS Secret Access Key (long random string)")
    print("3. Default region (recommend: us-east-1)")
    
    print("\n🔑 If you don't have these keys:")
    print("1. Go to: https://console.aws.amazon.com")
    print("2. Click your name (top right) → Security credentials")
    print("3. Scroll to 'Access keys' → Create access key")
    print("4. Choose 'CLI' → Create")
    print("5. Copy both keys immediately!")
    
    # Get user input
    print("\n" + "="*50)
    access_key = input("Enter your AWS Access Key ID: ").strip()
    
    if not access_key:
        print("❌ Access Key ID is required")
        return False
    
    if not access_key.startswith('AKIA'):
        print("⚠️ Warning: Access Key ID should start with 'AKIA'")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            return False
    
    secret_key = input("Enter your AWS Secret Access Key: ").strip()
    
    if not secret_key:
        print("❌ Secret Access Key is required")
        return False
    
    if len(secret_key) < 20:
        print("⚠️ Warning: Secret Access Key seems too short")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            return False
    
    region = input("Enter default region (press Enter for us-east-1): ").strip()
    if not region:
        region = 'us-east-1'
    
    # Create AWS directory
    aws_dir = Path.home() / '.aws'
    aws_dir.mkdir(exist_ok=True)
    
    # Write credentials file
    credentials_content = f"""[default]
aws_access_key_id = {access_key}
aws_secret_access_key = {secret_key}
"""
    
    credentials_file = aws_dir / 'credentials'
    with open(credentials_file, 'w') as f:
        f.write(credentials_content)
    
    # Write config file
    config_content = f"""[default]
region = {region}
output = json
"""
    
    config_file = aws_dir / 'config'
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print(f"\n✅ AWS credentials saved to: {credentials_file}")
    print(f"✅ AWS config saved to: {config_file}")
    
    # Test the credentials
    print(f"\n🧪 Testing credentials...")
    
    try:
        sts_client = boto3.client('sts', region_name=region)
        identity = sts_client.get_caller_identity()
        
        print("✅ SUCCESS! Credentials are working")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User/Role: {identity['Arn']}")
        print(f"   Region: {region}")
        
        return True
        
    except Exception as e:
        print(f"❌ Credentials test failed: {e}")
        
        if "SignatureDoesNotMatch" in str(e):
            print("\n🔧 TROUBLESHOOTING:")
            print("1. Double-check your Secret Access Key")
            print("2. Make sure there are no extra spaces")
            print("3. Verify the keys are from the same AWS account")
            print("4. Try creating new access keys")
        
        return False

def alternative_setup_methods():
    """Show alternative credential setup methods."""
    
    print("\n🔄 ALTERNATIVE SETUP METHODS")
    print("="*35)
    
    print("If the interactive setup didn't work, try these:")
    
    print("\n1️⃣ AWS CLI Configure Command:")
    print("   aws configure")
    print("   (Enter your keys when prompted)")
    
    print("\n2️⃣ Environment Variables (Windows):")
    print("   set AWS_ACCESS_KEY_ID=your_access_key")
    print("   set AWS_SECRET_ACCESS_KEY=your_secret_key")
    print("   set AWS_DEFAULT_REGION=us-east-1")
    
    print("\n3️⃣ Manual File Creation:")
    aws_dir = Path.home() / '.aws'
    print(f"   Create file: {aws_dir / 'credentials'}")
    print("   Content:")
    print("   [default]")
    print("   aws_access_key_id = YOUR_ACCESS_KEY")
    print("   aws_secret_access_key = YOUR_SECRET_KEY")
    
    print(f"\n   Create file: {aws_dir / 'config'}")
    print("   Content:")
    print("   [default]")
    print("   region = us-east-1")
    print("   output = json")

def main():
    """Main credential fixing function."""
    
    # First, diagnose the issue
    if not diagnose_aws_credentials():
        return False
    
    print("\n" + "="*60)
    choice = input("Would you like to fix your AWS credentials now? (y/n): ").strip().lower()
    
    if choice == 'y':
        success = fix_aws_credentials()
        
        if success:
            print("\n🎉 AWS CREDENTIALS FIXED!")
            print("You can now run the deployment script:")
            print("   python scripts/deploy_biomerkin_to_aws.py")
        else:
            print("\n❌ Credential setup failed")
            alternative_setup_methods()
        
        return success
    else:
        alternative_setup_methods()
        return False

if __name__ == "__main__":
    main()