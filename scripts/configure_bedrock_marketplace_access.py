#!/usr/bin/env python3
"""
Configure Bedrock Marketplace Access
This script helps configure AWS credentials for Bedrock marketplace models
"""

import boto3
import json
import os
from botocore.exceptions import ClientError

def test_bedrock_access():
    """Test if Bedrock is accessible with current credentials"""
    print("🔍 Testing Bedrock access...")
    
    try:
        bedrock = boto3.client('bedrock', region_name='us-east-1')
        models = bedrock.list_foundation_models()
        print(f"✅ Bedrock access confirmed! Found {len(models['modelSummaries'])} models")
        return True
    except Exception as e:
        print(f"❌ Bedrock access failed: {str(e)}")
        return False

def list_marketplace_models():
    """List all available marketplace models"""
    print("\n🔍 Checking for marketplace models...")
    
    try:
        bedrock = boto3.client('bedrock', region_name='us-east-1')
        response = bedrock.list_foundation_models()
        
        # Filter for potential marketplace/third-party models
        marketplace_providers = []
        all_providers = set()
        
        for model in response['modelSummaries']:
            provider = model.get('providerName', 'Unknown')
            all_providers.add(provider)
            
            # Check if it's a marketplace model (not standard AWS/Anthropic/etc)
            if provider not in ['Amazon', 'Anthropic', 'Meta', 'Cohere', 'AI21 Labs', 'Mistral AI']:
                marketplace_providers.append({
                    'modelId': model['modelId'],
                    'provider': provider,
                    'name': model.get('modelName', 'Unknown')
                })
        
        print(f"\n📊 All available providers: {', '.join(sorted(all_providers))}")
        
        if marketplace_providers:
            print(f"\n🎯 Found {len(marketplace_providers)} marketplace models:")
            for model in marketplace_providers:
                print(f"  - {model['provider']}: {model['name']} ({model['modelId']})")
        else:
            print("\n⚠️  No marketplace models found yet")
            print("   This could mean:")
            print("   1. Marketplace models need to be subscribed to first")
            print("   2. They may appear in SageMaker instead of Bedrock")
            print("   3. The John Snow Labs model might need separate activation")
        
        return marketplace_providers
        
    except Exception as e:
        print(f"❌ Error listing models: {str(e)}")
        return []

def check_sagemaker_marketplace():
    """Check SageMaker for marketplace models"""
    print("\n🔍 Checking SageMaker Marketplace...")
    
    try:
        sagemaker = boto3.client('sagemaker', region_name='us-east-1')
        
        # Try to list model packages
        response = sagemaker.list_model_packages(MaxResults=10)
        
        if response.get('ModelPackageSummaryList'):
            print(f"✅ Found {len(response['ModelPackageSummaryList'])} SageMaker model packages")
            for pkg in response['ModelPackageSummaryList'][:5]:
                print(f"  - {pkg.get('ModelPackageName', 'Unknown')}")
        else:
            print("ℹ️  No SageMaker model packages found")
            
    except Exception as e:
        print(f"⚠️  SageMaker check: {str(e)}")

def test_model_invocation(model_id='amazon.nova-pro-v1:0'):
    """Test invoking a model"""
    print(f"\n🧪 Testing model invocation: {model_id}")
    
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Simple test prompt
        body = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": "Say 'Hello' if you can read this."}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 50,
                "temperature": 0.7
            }
        })
        
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=body
        )
        
        result = json.loads(response['body'].read())
        print(f"✅ Model invocation successful!")
        print(f"   Response: {result.get('output', {}).get('message', {}).get('content', [{}])[0].get('text', 'No text')[:100]}")
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            print(f"❌ Access denied to {model_id}")
            print("   You may need to request access in the Bedrock console")
        else:
            print(f"❌ Error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def show_configuration_guide():
    """Show how to configure credentials"""
    print("\n" + "="*60)
    print("📋 HOW TO CONFIGURE YOUR BEDROCK API KEY")
    print("="*60)
    
    print("\n1️⃣  Configure AWS Credentials File:")
    print("   Location: ~/.aws/credentials")
    print("   Content:")
    print("   ```")
    print("   [default]")
    print("   aws_access_key_id = YOUR_ACCESS_KEY_ID")
    print("   aws_secret_access_key = YOUR_SECRET_ACCESS_KEY")
    print("   region = us-east-1")
    print("   ```")
    
    print("\n2️⃣  Or use Environment Variables:")
    print("   Windows (PowerShell):")
    print("   $env:AWS_ACCESS_KEY_ID='YOUR_KEY'")
    print("   $env:AWS_SECRET_ACCESS_KEY='YOUR_SECRET'")
    print("   $env:AWS_DEFAULT_REGION='us-east-1'")
    
    print("\n3️⃣  For Lambda Functions:")
    print("   - Go to AWS Console → Lambda → Your Function")
    print("   - Configuration → Environment Variables")
    print("   - Add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
    
    print("\n4️⃣  Test with:")
    print("   python scripts/configure_bedrock_marketplace_access.py")
    print("\n" + "="*60)

def main():
    print("🚀 Bedrock Marketplace Access Configuration\n")
    
    # Check if credentials are configured
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials:
            print(f"✅ AWS credentials found")
            print(f"   Access Key: {credentials.access_key[:8]}...")
            print(f"   Region: {session.region_name or 'us-east-1'}")
        else:
            print("❌ No AWS credentials found!")
            show_configuration_guide()
            return
            
    except Exception as e:
        print(f"❌ Error checking credentials: {str(e)}")
        show_configuration_guide()
        return
    
    # Run tests
    if test_bedrock_access():
        marketplace_models = list_marketplace_models()
        check_sagemaker_marketplace()
        test_model_invocation()
        
        print("\n" + "="*60)
        print("📝 NEXT STEPS FOR JOHN SNOW LABS MEDICAL LLM")
        print("="*60)
        print("\n1. Check AWS Marketplace:")
        print("   https://aws.amazon.com/marketplace/search/results?searchTerms=john+snow+labs")
        
        print("\n2. Subscribe to the model in AWS Marketplace")
        
        print("\n3. The model might appear in:")
        print("   - SageMaker JumpStart (not Bedrock)")
        print("   - Bedrock after subscription")
        
        print("\n4. Alternative: Use Amazon Nova Pro")
        print("   - Already available and working")
        print("   - Excellent for medical/genomics analysis")
        print("   - Model ID: amazon.nova-pro-v1:0")
        
        print("\n" + "="*60)
    else:
        show_configuration_guide()

if __name__ == "__main__":
    main()
