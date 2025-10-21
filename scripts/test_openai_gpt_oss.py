#!/usr/bin/env python3
"""
Test OpenAI GPT-OSS models with correct API format
"""

import boto3
import json

def test_openai_format():
    """Test OpenAI GPT-OSS with correct format"""
    
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    
    models_to_test = [
        'openai.gpt-oss-120b-1:0',
        'openai.gpt-oss-20b-1:0'
    ]
    
    for model_id in models_to_test:
        print(f"\n🧪 Testing {model_id}...")
        
        # Try OpenAI-style format
        try:
            body = json.dumps({
                "messages": [
                    {
                        "role": "user",
                        "content": "Say 'Hello' if you can read this."
                    }
                ],
                "max_tokens": 50,
                "temperature": 0.7
            })
            
            response = bedrock.invoke_model(
                modelId=model_id,
                body=body
            )
            
            result = json.loads(response['body'].read())
            print(f"✅ {model_id} works!")
            print(f"   Response: {json.dumps(result, indent=2)[:200]}")
            
        except Exception as e:
            print(f"❌ Format 1 failed: {str(e)[:150]}")
            
            # Try alternative format
            try:
                body = json.dumps({
                    "prompt": "Say 'Hello' if you can read this.",
                    "max_tokens": 50,
                    "temperature": 0.7
                })
                
                response = bedrock.invoke_model(
                    modelId=model_id,
                    body=body
                )
                
                result = json.loads(response['body'].read())
                print(f"✅ {model_id} works with prompt format!")
                print(f"   Response: {json.dumps(result, indent=2)[:200]}")
                
            except Exception as e2:
                print(f"❌ Format 2 also failed: {str(e2)[:150]}")

if __name__ == "__main__":
    test_openai_format()
