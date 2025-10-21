#!/usr/bin/env python3
"""
Final API Gateway Fix
Comprehensive fix for all API Gateway issues
"""

import boto3
import json
import time

def fix_api_gateway_completely():
    """Complete API Gateway fix"""
    print("🔧 Comprehensive API Gateway Fix\n")
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    lambda_client = boto3.client('lambda', region_name='ap-south-1')
    
    api_id = '642v46sv19'
    
    try:
        # Get resources
        resources = apigateway.get_resources(restApiId=api_id)
        analyze_resource = next((r for r in resources['items'] if r.get('path') == '/analyze'), None)
        
        if not analyze_resource:
            print("❌ /analyze not found")
            return False
        
        resource_id = analyze_resource['id']
        print(f"✅ Found /analyze: {resource_id}")
        
        # Ensure Lambda permission exists
        print("\n1️⃣  Setting Lambda permissions...")
        try:
            lambda_client.remove_permission(
                FunctionName='biomerkin-enhanced-orchestrator',
                StatementId='apigateway-prod-invoke'
            )
        except:
            pass
        
        lambda_client.add_permission(
            FunctionName='biomerkin-enhanced-orchestrator',
            StatementId='apigateway-prod-invoke',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn=f'arn:aws:execute-api:ap-south-1:242201307639:{api_id}/prod/POST/analyze'
        )
        print("   ✅ Lambda permission added")
        
        # Fix POST method
        print("\n2️⃣  Fixing POST method...")
        try:
            apigateway.delete_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='POST'
            )
            print("   Deleted old POST method")
        except:
            pass
        
        # Create POST method
        apigateway.put_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            authorizationType='NONE',
            apiKeyRequired=False
        )
        print("   ✅ Created POST method")
        
        # Add method response
        apigateway.put_method_response(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            statusCode='200',
            responseParameters={
                'method.response.header.Access-Control-Allow-Origin': True,
                'method.response.header.Access-Control-Allow-Headers': True,
                'method.response.header.Access-Control-Allow-Methods': True
            },
            responseModels={'application/json': 'Empty'}
        )
        print("   ✅ Added method response")
        
        # Create integration
        print("\n3️⃣  Creating Lambda integration...")
        lambda_arn = 'arn:aws:lambda:ap-south-1:242201307639:function:biomerkin-enhanced-orchestrator'
        integration_uri = f'arn:aws:apigateway:ap-south-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=integration_uri,
            passthroughBehavior='WHEN_NO_MATCH'
        )
        print(f"   ✅ Integration created")
        print(f"   URI: {integration_uri}")
        
        # Fix OPTIONS for CORS
        print("\n4️⃣  Fixing CORS (OPTIONS)...")
        try:
            # Update OPTIONS integration
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={
                    'application/json': '{"statusCode": 200}'
                }
            )
            
            apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,OPTIONS'",
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                },
                responseTemplates={
                    'application/json': ''
                }
            )
            print("   ✅ CORS configured")
        except Exception as e:
            print(f"   ⚠️  CORS: {str(e)}")
        
        # Deploy
        print("\n5️⃣  Deploying to prod...")
        deployment = apigateway.create_deployment(
            restApiId=api_id,
            stageName='prod',
            description='Complete API Gateway fix with Lambda in ap-south-1'
        )
        print(f"   ✅ Deployed (ID: {deployment['id']})")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_with_retries():
    """Test API with retries"""
    print("\n6️⃣  Testing API (with retries)...")
    
    import requests
    
    api_url = "https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod/analyze"
    
    for attempt in range(3):
        try:
            print(f"\n   Attempt {attempt + 1}/3...")
            response = requests.post(
                api_url,
                json={
                    'sequence': 'ATCGATCGATCGATCG',
                    'analysis_type': 'genomics',
                    'use_multi_model': True
                },
                timeout=120
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("   ✅ SUCCESS!")
                    print(f"   Models: {data['analysis_results']['models_used']}")
                    return True
                else:
                    print(f"   ❌ Error: {data.get('message')}")
            else:
                print(f"   Response: {response.text[:200]}")
            
            if attempt < 2:
                print("   Waiting 10 seconds before retry...")
                time.sleep(10)
                
        except Exception as e:
            print(f"   ❌ {str(e)}")
            if attempt < 2:
                time.sleep(10)
    
    return False

def main():
    print("="*60)
    print("🚀 FINAL API GATEWAY FIX")
    print("="*60)
    
    if fix_api_gateway_completely():
        print("\n⏳ Waiting for deployment to propagate (15 seconds)...")
        time.sleep(15)
        
        if test_with_retries():
            print("\n" + "="*60)
            print("🎉 API GATEWAY IS NOW WORKING!")
            print("="*60)
            print("\n✅ Your API endpoint:")
            print("   https://642v46sv19.execute-api.ap-south-1.amazonaws.com/prod/analyze")
            print("\n📝 Test it:")
            print("   python scripts/test_complete_system.py")
            print("\n💻 Frontend is ready to use!")
            print("="*60)
        else:
            print("\n⚠️  API configured but test failed")
            print("\nℹ️  The Lambda works directly in ap-south-1")
            print("   Try testing again in 30 seconds")
            print("   Or use direct Lambda invocation for now")
    else:
        print("\n❌ Fix failed")

if __name__ == "__main__":
    main()
