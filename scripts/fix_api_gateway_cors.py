#!/usr/bin/env python3
"""
Fix API Gateway CORS Configuration
Enables CORS at the API Gateway level for all routes
"""

import boto3
import json

# Initialize AWS clients
apigateway = boto3.client('apigateway', region_name='ap-south-1')

def find_api_gateway():
    """Find the Biomerkin API Gateway"""
    try:
        apis = apigateway.get_rest_apis()
        for api in apis['items']:
            if 'biomerkin' in api['name'].lower() or 'multi' in api['name'].lower():
                print(f"✅ Found API: {api['name']} (ID: {api['id']})")
                return api['id'], api['name']
        
        # If not found by name, list all APIs
        print("\n📋 Available APIs:")
        for api in apis['items']:
            print(f"   - {api['name']} (ID: {api['id']})")
        
        return None, None
    except Exception as e:
        print(f"❌ Error finding API Gateway: {str(e)}")
        return None, None

def get_resources(api_id):
    """Get all resources for the API"""
    try:
        resources = apigateway.get_resources(restApiId=api_id)
        return resources['items']
    except Exception as e:
        print(f"❌ Error getting resources: {str(e)}")
        return []

def enable_cors_for_resource(api_id, resource_id, resource_path):
    """Enable CORS for a specific resource"""
    try:
        # Check if OPTIONS method exists
        try:
            apigateway.get_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS'
            )
            print(f"   ℹ️  OPTIONS method already exists for {resource_path}")
        except apigateway.exceptions.NotFoundException:
            # Create OPTIONS method
            print(f"   📝 Creating OPTIONS method for {resource_path}")
            apigateway.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
        
        # Set up OPTIONS method response
        try:
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
        except Exception as e:
            if 'ConflictException' not in str(e):
                print(f"   ⚠️  Warning setting method response: {str(e)}")
        
        # Set up OPTIONS integration
        try:
            apigateway.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={
                    'application/json': '{"statusCode": 200}'
                }
            )
        except Exception as e:
            if 'ConflictException' not in str(e):
                print(f"   ⚠️  Warning setting integration: {str(e)}")
        
        # Set up OPTIONS integration response
        try:
            apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': "'*'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            )
        except Exception as e:
            if 'ConflictException' not in str(e):
                print(f"   ⚠️  Warning setting integration response: {str(e)}")
        
        print(f"   ✅ CORS enabled for {resource_path}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error enabling CORS for {resource_path}: {str(e)}")
        return False

def add_cors_to_existing_methods(api_id, resource_id, resource_path):
    """Add CORS headers to existing method responses"""
    methods = ['GET', 'POST', 'PUT', 'DELETE']
    
    for method in methods:
        try:
            # Check if method exists
            apigateway.get_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=method
            )
            
            # Add CORS headers to method response
            try:
                apigateway.put_method_response(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod=method,
                    statusCode='200',
                    responseParameters={
                        'method.response.header.Access-Control-Allow-Origin': True
                    }
                )
            except:
                pass
            
            # Add CORS headers to integration response
            try:
                apigateway.put_integration_response(
                    restApiId=api_id,
                    resourceId=resource_id,
                    httpMethod=method,
                    statusCode='200',
                    responseParameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'"
                    }
                )
            except:
                pass
                
        except apigateway.exceptions.NotFoundException:
            # Method doesn't exist, skip
            pass
        except Exception as e:
            pass

def deploy_api(api_id, stage_name='prod'):
    """Deploy the API to a stage"""
    try:
        print(f"\n🚀 Deploying API to stage: {stage_name}")
        apigateway.create_deployment(
            restApiId=api_id,
            stageName=stage_name,
            description='CORS configuration update'
        )
        print(f"✅ API deployed successfully")
        return True
    except Exception as e:
        print(f"❌ Error deploying API: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🔧 Fixing API Gateway CORS Configuration")
    print("=" * 60)
    
    # Find API Gateway
    api_id, api_name = find_api_gateway()
    if not api_id:
        print("\n❌ Could not find Biomerkin API Gateway")
        print("Please check your API Gateway configuration manually")
        return
    
    print(f"\n📦 Working with API: {api_name}")
    
    # Get all resources
    print("\n📋 Getting API resources...")
    resources = get_resources(api_id)
    
    if not resources:
        print("❌ No resources found")
        return
    
    print(f"✅ Found {len(resources)} resources")
    
    # Enable CORS for each resource
    print("\n🔧 Enabling CORS for all resources...")
    success_count = 0
    
    for resource in resources:
        resource_path = resource.get('path', '/')
        resource_id = resource['id']
        
        print(f"\n📍 Resource: {resource_path}")
        
        # Enable OPTIONS method
        if enable_cors_for_resource(api_id, resource_id, resource_path):
            success_count += 1
        
        # Add CORS to existing methods
        add_cors_to_existing_methods(api_id, resource_id, resource_path)
    
    print("\n" + "=" * 60)
    print(f"✅ CORS enabled for {success_count}/{len(resources)} resources")
    print("=" * 60)
    
    # Deploy API
    if deploy_api(api_id):
        print("\n🎉 API Gateway CORS configuration complete!")
        print("\n📝 CORS Headers Applied:")
        print("   - Access-Control-Allow-Origin: *")
        print("   - Access-Control-Allow-Headers: *")
        print("   - Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS")
        print("\n🧪 Test your React app now:")
        print("   http://biomerkin-frontend-20251018-013734.s3-website.ap-south-1.amazonaws.com")
    else:
        print("\n⚠️  CORS configured but deployment failed")
        print("You may need to deploy manually from AWS Console")

if __name__ == "__main__":
    main()
