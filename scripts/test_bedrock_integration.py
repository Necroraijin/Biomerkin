#!/usr/bin/env python3
"""
Test if Bedrock integration is working
"""
import boto3
import json

def test_bedrock():
    """Test the Lambda with Bedrock"""
    print("Testing Bedrock Integration...")
    
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    # Test event
    test_event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "sequence_data": "ATCGATCGATCGATCGATCGATCG",
            "user_id": "test"
        }),
        "headers": {
            "Content-Type": "application/json"
        }
    }
    
    print("\nInvoking Lambda...")
    try:
        response = lambda_client.invoke(
            FunctionName='biomerkin-orchestrator',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_event)
        )
        
        payload = json.loads(response['Payload'].read())
        
        print(f"\nStatus Code: {response['StatusCode']}")
        
        if 'FunctionError' in response:
            print(f"ERROR: {response['FunctionError']}")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            return False
        
        # Check if response has Bedrock indicators
        if isinstance(payload, dict):
            body = json.loads(payload.get('body', '{}'))
            
            print(f"\nResponse Status: {payload.get('statusCode')}")
            print(f"Success: {body.get('success')}")
            print(f"Message: {body.get('message')}")
            
            if 'ai_model' in body:
                print(f"\nAI Model: {body['ai_model']}")
                print("BEDROCK INTEGRATION ACTIVE!")
                return True
            elif 'Bedrock' in body.get('message', ''):
                print("\nBEDROCK INTEGRATION ACTIVE!")
                return True
            else:
                print("\nWARNING: Response doesn't mention Bedrock")
                print("This might still be using mock data")
                return False
        
        return False
        
    except Exception as e:
        print(f"\nERROR: {e}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("TESTING BEDROCK INTEGRATION")
    print("="*60)
    
    if test_bedrock():
        print("\n" + "="*60)
        print("SUCCESS - BEDROCK IS ACTIVE!")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("BEDROCK NOT DETECTED")
        print("="*60)
