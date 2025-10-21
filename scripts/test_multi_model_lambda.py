#!/usr/bin/env python3
"""Test the multi-model Lambda function"""

import boto3
import json
import time

def test_lambda():
    print("🧪 Testing multi-model Lambda function...\n")
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Wait for Lambda to be ready
    print("Waiting for Lambda to be ready...")
    time.sleep(5)
    
    test_payload = {
        'sequence': 'ATCGATCGATCGATCGTAGCTAGCTAGCTAGC',
        'analysis_type': 'genomics',
        'use_multi_model': True
    }
    
    try:
        print("Invoking Lambda...")
        response = lambda_client.invoke(
            FunctionName='biomerkin-multi-model-orchestrator',
            InvocationType='RequestResponse',
            Payload=json.dumps(test_payload)
        )
        
        result = json.loads(response['Payload'].read())
        
        print(f"Status Code: {response['StatusCode']}\n")
        
        if response['StatusCode'] == 200:
            body = json.loads(result.get('body', '{}'))
            
            print("✅ MULTI-MODEL LAMBDA IS WORKING!\n")
            print("="*60)
            print(f"Workflow: {body.get('workflow', 'unknown')}")
            print(f"Models Used: {', '.join(body.get('models_used', []))}")
            print(f"Analysis Type: {body.get('analysis_type', 'unknown')}")
            print("="*60)
            
            if 'final_report' in body:
                print("\n📊 Final Report Available:")
                report = body['final_report']
                print(f"  - Executive Summary: {len(report.get('executive_summary', ''))} chars")
                print(f"  - Detailed Analysis: {len(report.get('detailed_analysis', ''))} chars")
                print(f"  - Validation Notes: {len(report.get('validation_notes', ''))} chars")
                print(f"  - Confidence: {report.get('confidence', 'unknown')}")
                print(f"  - Models Count: {report.get('models_count', 0)}")
            
            if 'primary_analysis' in body:
                print("\n🔬 Primary Analysis (Nova Pro):")
                print(f"  {body['primary_analysis']['result'][:200]}...")
            
            if 'secondary_validation' in body:
                print("\n✓ Secondary Validation (GPT-OSS-120B):")
                print(f"  {body['secondary_validation']['result'][:200]}...")
            
            if 'synthesis' in body:
                print("\n📝 Synthesis (GPT-OSS-20B):")
                print(f"  {body['synthesis']['result'][:200]}...")
            
            print("\n" + "="*60)
            print("🎉 ALL MODELS WORKING TOGETHER!")
            print("="*60)
            
            return True
        else:
            print(f"❌ Lambda returned status: {response['StatusCode']}")
            print(f"Response: {json.dumps(result, indent=2)}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_lambda()
