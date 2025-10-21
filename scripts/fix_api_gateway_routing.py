#!/usr/bin/env python3
"""
Fix API Gateway Routing to Enhanced Orchestrator
Diagnoses and fixes the routing issue
"""

import boto3
import json
import time

def diagnose_api_gateway():
    """Diagnose the current API Gateway setup"""
    print("🔍 Diagnosing API Gateway...")
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    try:
        # Get API
        apis = apigateway.get_rest_apis()
        api = next((a for a in apis['items'] if '642v46sv19' in a['id']), None)
        
        if not api:
            print("❌ API not found")
            return None
        
        api_id = api['id']
        print(f"✅ Found API: {api_id} - {api['name']}")
        
        # Get resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        print(f"\n📋 Resources:")
        for resource in resources['items']:
            path = resource.get('path', '/')
            resource_id = resource['id']
            print(f"  - {path} (ID: {resource_id})")
            
            # Check methods
            if 'resourceMethods' in resource:
                for method in resource['resourceMethods']:
                    print(f"    └─ {method}")
                    
                    # Get integration
                    try:
                        integration = apigateway.get_integration(
                            restApiId=api_id,
                            resourceId=resource_id,
                            httpMethod=method
                        )
                        
                        if 'uri' in integration:
                            print(f"       URI: {integration['uri']}")
                        if 'type' in integration:
                            print(f"       Type: {integration['type']}")
                    except:
                        pass
        
        return api_id
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def add_lambda_permission():
    """Add permission for API Gateway to invoke Lambda"""
    print("\n🔐 Adding Lambda permissions...")
    
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    try:
        # Remove existing permission if any
        try:
            lambda_client.remove_permission(
                FunctionName='biomerkin-enhanced-orchestrator',
                StatementId='apigateway-invoke-permission'
            )
            print("  Removed old permission")
        except:
            pass
        
        # Add new permission
        lambda_client.add_permission(
            FunctionName='biomerkin-enhanced-orchestrator',
            StatementId='apigateway-invoke-permission',
            Action='lambda:InvokeFunction',
            Principal='apigateway.amazonaws.com',
            SourceArn='arn:aws:execute-api:ap-south-1:242201307639:642v46sv19/*/*/*'
        )
        print("✅ Added Lambda permission for API Gateway")
        return True
        
    except Exception as e:
        print(f"⚠️  Permission: {str(e)}")
        return False

def fix_api_gateway_integration(api_id):
    """Fix the API Gateway integration"""
    print(f"\n🔧 Fixing API Gateway integration...")
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    try:
        # Get resources
        resources = apigateway.get_resources(restApiId=api_id)
        
        # Find /analyze resource
        analyze_resource = next((r for r in resources['items'] if r.get('path') == '/analyze'), None)
        
        if not analyze_resource:
            print("❌ /analyze resource not found")
            return False
        
        resource_id = analyze_resource['id']
        print(f"✅ Found /analyze resource: {resource_id}")
        
        # Update POST integration
        lambda_arn = 'arn:aws:lambda:us-east-1:242201307639:function:biomerkin-enhanced-orchestrator'
        integration_uri = f'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
        
        print(f"  Updating POST integration...")
        print(f"  Target: {integration_uri}")
        
        try:
            # Delete existing integration
            apigateway.delete_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='POST'
            )
            print("  Deleted old integration")
        except:
            pass
        
        # Create new integration
        apigateway.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod='POST',
            type='AWS_PROXY',
            integrationHttpMethod='POST',
            uri=integration_uri,
            passthroughBehavior='WHEN_NO_MATCH',
            contentHandling='CONVERT_TO_TEXT'
        )
        print("✅ Created new integration")
        
        # Update integration response
        try:
            apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='POST',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            )
            print("✅ Updated integration response")
        except:
            pass
        
        # Update method response
        try:
            apigateway.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='POST',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Origin': True
                },
                responseModels={
                    'application/json': 'Empty'
                }
            )
            print("✅ Updated method response")
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def deploy_api(api_id):
    """Deploy the API changes"""
    print(f"\n🚀 Deploying API changes...")
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    try:
        response = apigateway.create_deployment(
            restApiId=api_id,
            stageName='prod',
            description='Fixed routing to enhanced orchestrator'
        )
        print(f"✅ Deployed to prod stage")
        print(f"   Deployment ID: {response['id']}")
        return True
        
    except Exception as e:
        print(f"❌ Deployment error: {str(e)}")
        return False

def test_api_endpoint(api_id):
    """Test the API endpoint"""
    print(f"\n🧪 Testing API endpoint...")
    
    import requests
    
    api_url = f"https://{api_id}.execute-api.ap-south-1.amazonaws.com/prod/analyze"
    
    print(f"  URL: {api_url}")
    
    try:
        response = requests.post(
            api_url,
            json={
                'sequence': 'ATCGATCGATCGATCG',
                'analysis_type': 'genomics',
                'use_multi_model': True
            },
            timeout=120
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ API endpoint is working!")
                print(f"   Models used: {data['analysis_results']['models_used']}")
                return True
            else:
                print(f"❌ API returned error: {data.get('message')}")
                return False
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏱️  Request timed out (analysis may still be running)")
        return False
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        return False

def main():
    print("="*60)
    print("🔧 API GATEWAY ROUTING FIX")
    print("="*60)
    
    # Step 1: Diagnose
    api_id = diagnose_api_gateway()
    
    if not api_id:
        print("\n❌ Cannot proceed without API ID")
        return
    
    # Step 2: Add Lambda permission
    add_lambda_permission()
    
    # Step 3: Fix integration
    if fix_api_gateway_integration(api_id):
        # Step 4: Deploy
        if deploy_api(api_id):
            # Wait for deployment
            print("\n⏳ Waiting for deployment to propagate...")
            time.sleep(5)
            
            # Step 5: Test
            if test_api_endpoint(api_id):
                print("\n" + "="*60)
                print("🎉 API GATEWAY ROUTING FIXED!")
                print("="*60)
                print(f"\n✅ Your API is now working:")
                print(f"   https://{api_id}.execute-api.ap-south-1.amazonaws.com/prod/analyze")
                print("\n📝 Test it:")
                print(f"   curl -X POST https://{api_id}.execute-api.ap-south-1.amazonaws.com/prod/analyze \\")
                print(f"     -H 'Content-Type: application/json' \\")
                print(f"     -d '{{\"sequence\":\"ATCGATCG\",\"use_multi_model\":true}}'")
                print("\n" + "="*60)
            else:
                print("\n⚠️  API deployed but test failed")
                print("   The Lambda works directly, so the issue may be:")
                print("   1. Deployment still propagating (wait 30 seconds)")
                print("   2. Lambda timeout (increase to 300 seconds)")
                print("   3. Try testing again in a moment")
        else:
            print("\n❌ Deployment failed")
    else:
        print("\n❌ Integration fix failed")

if __name__ == "__main__":
    main()
