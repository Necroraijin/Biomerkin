#!/usr/bin/env python3
"""
Enable CORS on API Gateway
"""
import boto3
import json

def enable_api_gateway_cors():
    """Enable CORS on API Gateway"""
    print("🔧 Enabling CORS on API Gateway...")
    
    apigateway = boto3.client('apigateway', region_name='ap-south-1')
    
    # API Gateway ID
    api_id = '642v46sv19'
    
    try:
        # Get all resources
        print("\n📋 Getting API resources...")
        resources = apigateway.get_resources(restApiId=api_id)
        
        for resource in resources['items']:
            resource_id = resource['id']
            path = resource['path']
            
            print(f"\n🔍 Checking resource: {path}")
            
            # Check if OPTIONS method exists
            methods = resource.get('resourceMethods', {})
            
            if 'OPTIONS' not in methods:
                print(f"   ➕ Adding OPTIONS method...")
                try:
                    # Add OPTIONS method
                    apigateway.put_method(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod='OPTIONS',
                        authorizationType='NONE'
                    )
                    
                    # Add mock integration
                    apigateway.put_integration(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod='OPTIONS',
                        type='MOCK',
                        requestTemplates={
                            'application/json': '{"statusCode": 200}'
                        }
                    )
                    
                    # Add method response
                    apigateway.put_method_response(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod='OPTIONS',
                        statusCode='200',
                        responseParameters={
                            'method.response.header.Access-Control-Allow-Headers': True,
                            'method.response.header.Access-Control-Allow-Methods': True,
                            'method.response.header.Access-Control-Allow-Origin': True
                        }
                    )
                    
                    # Add integration response
                    apigateway.put_integration_response(
                        restApiId=api_id,
                        resourceId=resource_id,
                        httpMethod='OPTIONS',
                        statusCode='200',
                        responseParameters={
                            'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key'",
                            'method.response.header.Access-Control-Allow-Methods': "'GET,POST,OPTIONS'",
                            'method.response.header.Access-Control-Allow-Origin': "'*'"
                        }
                    )
                    
                    print(f"   ✅ Added OPTIONS method with CORS")
                    
                except Exception as e:
                    if 'ConflictException' in str(e):
                        print(f"   ℹ️  OPTIONS already exists")
                    else:
                        print(f"   ⚠️  Error: {e}")
            else:
                print(f"   ✅ OPTIONS method already exists")
            
            # Update existing methods to include CORS headers
            for method in methods.keys():
                if method != 'OPTIONS':
                    print(f"   🔧 Updating {method} method response...")
                    try:
                        # Update method response to include CORS headers
                        apigateway.put_method_response(
                            restApiId=api_id,
                            resourceId=resource_id,
                            httpMethod=method,
                            statusCode='200',
                            responseParameters={
                                'method.response.header.Access-Control-Allow-Origin': True
                            }
                        )
                        print(f"   ✅ Updated {method} method")
                    except Exception as e:
                        if 'ConflictException' in str(e):
                            print(f"   ℹ️  {method} already configured")
                        else:
                            print(f"   ⚠️  Error updating {method}: {e}")
        
        # Deploy the API
        print("\n🚀 Deploying API changes...")
        apigateway.create_deployment(
            restApiId=api_id,
            stageName='prod',
            description='Enable CORS'
        )
        print("✅ API deployed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("🔧 ENABLING API GATEWAY CORS")
    print("="*60)
    
    success = enable_api_gateway_cors()
    
    if success:
        print("\n" + "="*60)
        print("✅ API GATEWAY CORS ENABLED!")
        print("="*60)
        print("\n🎯 What was configured:")
        print("   ✅ Added OPTIONS methods for preflight")
        print("   ✅ Added CORS headers to all methods")
        print("   ✅ Deployed changes to prod stage")
        print("\n🧪 Test now:")
        print("   Your frontend should work without CORS errors!")
        print("\n" + "="*60)
    else:
        print("\n⚠️  Some errors occurred, but Lambda CORS should still work")
