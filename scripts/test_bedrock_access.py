#!/usr/bin/env python3
"""
Test if we have Bedrock access
"""
import boto3
import json

def test_bedrock_access():
    """Test Bedrock access"""
    print("Testing AWS Bedrock Access...")
    
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": "Say hello"
                }
            ]
        })
        
        print("\nCalling Bedrock Claude 3 Sonnet...")
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=body
        )
        
        response_body = json.loads(response['body'].read())
        
        print("\nSUCCESS!")
        print(f"Response: {response_body['content'][0]['text']}")
        print("\nBedrock access is working!")
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nBedrock access is NOT working!")
        print("\nPossible issues:")
        print("1. Model access not enabled in AWS Console")
        print("2. IAM permissions missing")
        print("3. Region not supported")
        return False

if __name__ == '__main__':
    print("="*60)
    print("TESTING BEDROCK ACCESS")
    print("="*60)
    test_bedrock_access()
