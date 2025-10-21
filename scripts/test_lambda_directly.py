#!/usr/bin/env python3
"""
Test Lambda function directly
"""
import boto3
import json

def test_lambda():
    """Invoke Lambda function directly"""
    print("🧪 Testing Lambda Function Directly...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Test event
    test_event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "sequence_data": "ATCGATCGATCGATCG",
            "user_id": "test"
        }),
        "headers": {
            "Content-Type": "application/json",
            "Origin": "http://biomerkin-frontend-20251018-013734.s3-website-ap-south-1.amazonaws.com"
        }
    }
    
    print(f"\n📦 Invoking Lambda with test event...")
    
    try:
        response = lambda_client.invoke(
            FunctionName='biomerkin-orchestrator',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        # Read response
        payload = json.loads(response['Payload'].read())
        
        print(f"\n✅ Lambda Response:")
        print(f"   Status Code: {response['StatusCode']}")
        
        if 'FunctionError' in response:
            print(f"   ❌ Function Error: {response['FunctionError']}")
        
        print(f"\n📄 Payload:")
        print(json.dumps(payload, indent=2))
        
        # Check if response has CORS headers
        if isinstance(payload, dict) and 'headers' in payload:
            print(f"\n📋 Response Headers:")
            for key, value in payload.get('headers', {}).items():
                print(f"   {key}: {value}")
        
        return payload
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    result = test_lambda()
    
    if result:
        if result.get('statusCode') == 200:
            print("\n✅ Lambda is working correctly!")
        else:
            print(f"\n⚠️  Lambda returned status {result.get('statusCode')}")
