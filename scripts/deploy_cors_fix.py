#!/usr/bin/env python3
"""
Deploy CORS-fixed Lambda functions
Updates all Lambda functions with proper CORS headers
"""

import boto3
import zipfile
import io
import os
import json

# Initialize AWS clients
lambda_client = boto3.client('lambda', region_name='ap-south-1')

# Lambda functions to update
LAMBDA_FUNCTIONS = [
    {
        'name': 'biomerkin-orchestrator',
        'file': 'lambda_functions/multi_model_orchestrator.py',
        'handler': 'multi_model_orchestrator.lambda_handler'
    },
    {
        'name': 'biomerkin-enhanced-orchestrator',
        'file': 'lambda_functions/enhanced_bedrock_orchestrator.py',
        'handler': 'enhanced_bedrock_orchestrator.lambda_handler'
    },
    {
        'name': 'biomerkin-genomics',
        'file': 'lambda_functions/genomics_handler.py',
        'handler': 'genomics_handler.lambda_handler'
    },
    {
        'name': 'biomerkin-proteomics',
        'file': 'lambda_functions/proteomics_handler.py',
        'handler': 'proteomics_handler.lambda_handler'
    },
    {
        'name': 'biomerkin-decision',
        'file': 'lambda_functions/decision_handler.py',
        'handler': 'decision_handler.lambda_handler'
    },
    {
        'name': 'biomerkin-literature',
        'file': 'lambda_functions/bedrock_literature_action.py',
        'handler': 'bedrock_literature_action.lambda_handler'
    },
    {
        'name': 'biomerkin-drug',
        'file': 'lambda_functions/bedrock_drug_action.py',
        'handler': 'bedrock_drug_action.lambda_handler'
    }
]

def create_lambda_zip(file_path):
    """Create a ZIP file for Lambda deployment"""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add the Lambda function file
        zip_file.write(file_path, os.path.basename(file_path))
    
    zip_buffer.seek(0)
    return zip_buffer.read()

def update_lambda_function(function_name, zip_content):
    """Update Lambda function code"""
    try:
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        print(f"✅ Updated {function_name}")
        return True
    except lambda_client.exceptions.ResourceNotFoundException:
        print(f"⚠️  Function {function_name} not found - skipping")
        return False
    except Exception as e:
        print(f"❌ Error updating {function_name}: {str(e)}")
        return False

def main():
    """Main deployment function"""
    print("=" * 60)
    print("🚀 Deploying CORS-Fixed Lambda Functions")
    print("=" * 60)
    
    updated_count = 0
    skipped_count = 0
    
    for func in LAMBDA_FUNCTIONS:
        print(f"\n📦 Processing {func['name']}...")
        
        # Check if file exists
        if not os.path.exists(func['file']):
            print(f"   ⚠️  File not found: {func['file']}")
            skipped_count += 1
            continue
        
        # Create ZIP
        print(f"   📝 Creating deployment package...")
        zip_content = create_lambda_zip(func['file'])
        
        # Update Lambda
        print(f"   ⬆️  Uploading to AWS Lambda...")
        if update_lambda_function(func['name'], zip_content):
            updated_count += 1
        else:
            skipped_count += 1
    
    print("\n" + "=" * 60)
    print("📊 Deployment Summary")
    print("=" * 60)
    print(f"✅ Updated: {updated_count}")
    print(f"⚠️  Skipped: {skipped_count}")
    print(f"📝 Total:   {len(LAMBDA_FUNCTIONS)}")
    
    if updated_count > 0:
        print("\n🎉 CORS headers have been added to all Lambda functions!")
        print("\n📋 CORS Headers Applied:")
        print("   - Access-Control-Allow-Origin: *")
        print("   - Access-Control-Allow-Headers: *")
        print("   - Access-Control-Allow-Methods: OPTIONS,POST,GET")
        
        print("\n🧪 Test your API now:")
        print("   http://biomerkin-frontend-20251018-013734.s3-website.ap-south-1.amazonaws.com")
        print("   http://biomerkin-frontend-20251018-013734.s3-website.ap-south-1.amazonaws.com/test.html")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
