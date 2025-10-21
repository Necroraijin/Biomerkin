#!/usr/bin/env python3
"""
Test Amazon Nova Pro access
"""
import boto3
import json

def test_nova():
    """Test Nova Pro"""
    print("Testing Amazon Nova Pro...")
    
    try:
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        body = json.dumps({
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": "Say hello"}]
                }
            ],
            "inferenceConfig": {
                "max_new_tokens": 100,
                "temperature": 0.7
            }
        })
        
        print("\nCalling Amazon Nova Pro...")
        response = bedrock_runtime.invoke_model(
            modelId='amazon.nova-pro-v1:0',
            body=body
        )
        
        response_body = json.loads(response['body'].read())
        
        print("\nSUCCESS!")
        print(f"Response: {response_body}")
        print("\nNova Pro access is working!")
        return True
        
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == '__main__':
    test_nova()
