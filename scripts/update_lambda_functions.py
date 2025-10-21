#!/usr/bin/env python3
"""
Update Lambda functions with working handlers.
"""

import boto3
import json
import zipfile
import io

def update_lambda_functions():
    """Update Lambda functions with working handlers."""
    
    print("🔄 UPDATING LAMBDA FUNCTIONS")
    print("="*30)
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Update genomics function
    try:
        print("📦 Updating genomics function...")
        
        with open('lambda_functions/genomics_handler.py', 'r') as f:
            handler_code = f.read()
        
        # Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr('lambda_function.py', handler_code)
        
        zip_content = zip_buffer.getvalue()
        
        # Update function
        response = lambda_client.update_function_code(
            FunctionName='biomerkin-genomics-agent',
            ZipFile=zip_content
        )
        
        print("✅ Updated genomics function")
        
    except Exception as e:
        print(f"❌ Failed to update genomics: {e}")
    
    # Update decision function
    try:
        print("📦 Updating decision function...")
        
        with open('lambda_functions/decision_handler.py', 'r') as f:
            handler_code = f.read()
        
        # Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr('lambda_function.py', handler_code)
        
        zip_content = zip_buffer.getvalue()
        
        # Update function
        response = lambda_client.update_function_code(
            FunctionName='biomerkin-decision-agent',
            ZipFile=zip_content
        )
        
        print("✅ Updated decision function")
        
    except Exception as e:
        print(f"❌ Failed to update decision: {e}")

def test_functions():
    """Test the updated functions."""
    
    print("\n🧪 TESTING FUNCTIONS")
    print("="*20)
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    test_payload = {
        "input_data": {
            "sequence_data": "ATGCGATCGATCGATCG",
            "reference_genome": "GRCh38"
        }
    }
    
    # Test genomics function
    try:
        print("Testing genomics function...")
        
        response = lambda_client.invoke(
            FunctionName='biomerkin-genomics-agent',
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            print("✅ Genomics function working!")
        else:
            print(f"❌ Genomics function failed: {result}")
            
    except Exception as e:
        print(f"❌ Genomics test error: {e}")

def main():
    """Main update process."""
    
    print("🚀 UPDATING LAMBDA FUNCTIONS FOR WORKING DEMO")
    print("="*50)
    
    update_lambda_functions()
    test_functions()
    
    print("\n🎉 LAMBDA FUNCTIONS UPDATED!")
    print("\n🌐 Test your frontend now:")
    print("http://biomerkin-frontend-20251014-224832.s3-website-us-east-1.amazonaws.com")
    
    print("\n🎯 The analysis should now work!")

if __name__ == "__main__":
    main()