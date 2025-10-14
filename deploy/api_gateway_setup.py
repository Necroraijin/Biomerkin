"""
API Gateway setup for Biomerkin multi-agent system
"""
import boto3
import json
from typing import Dict, Any

class APIGatewayManager:
    def __init__(self, region='us-east-1'):
        self.apigateway_client = boto3.client('apigateway', region_name=region)
        self.region = region
    
    def create_rest_api(self, api_name: str, description: str) -> str:
        """Create a REST API"""
        try:
            response = self.apigateway_client.create_rest_api(
                name=api_name,
                description=description,
                endpointConfiguration={
                    'types': ['REGIONAL']
                }
            )
            return response['id']
        except Exception as e:
            print(f"Error creating REST API: {e}")
            return None
    
    def get_root_resource_id(self, api_id: str) -> str:
        """Get the root resource ID for the API"""
        try:
            response = self.apigateway_client.get_resources(restApiId=api_id)
            for resource in response['items']:
                if resource['path'] == '/':
                    return resource['id']
        except Exception as e:
            print(f"Error getting root resource: {e}")
        return None
    
    def create_resource(self, api_id: str, parent_id: str, path_part: str) -> str:
        """Create a resource under the parent resource"""
        try:
            response = self.apigateway_client.create_resource(
                restApiId=api_id,
                parentId=parent_id,
                pathPart=path_part
            )
            return response['id']
        except Exception as e:
            print(f"Error creating resource {path_part}: {e}")
            return None
    
    def create_method(self, api_id: str, resource_id: str, http_method: str,
                     authorization_type: str = 'NONE') -> bool:
        """Create a method for a resource"""
        try:
            self.apigateway_client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                authorizationType=authorization_type,
                requestParameters={
                    'method.request.header.Content-Type': False
                }
            )
            return True
        except Exception as e:
            print(f"Error creating method {http_method}: {e}")
            return False
    
    def create_integration(self, api_id: str, resource_id: str, http_method: str,
                          lambda_function_arn: str) -> bool:
        """Create Lambda integration for a method"""
        try:
            integration_uri = f"arn:aws:apigateway:{self.region}:lambda:path/2015-03-31/functions/{lambda_function_arn}/invocations"
            
            self.apigateway_client.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                type='AWS_PROXY',
                integrationHttpMethod='POST',
                uri=integration_uri
            )
            return True
        except Exception as e:
            print(f"Error creating integration: {e}")
            return False
    
    def add_cors_support(self, api_id: str, resource_id: str) -> bool:
        """Add CORS support to a resource"""
        try:
            # Create OPTIONS method
            self.apigateway_client.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                authorizationType='NONE'
            )
            
            # Create mock integration for OPTIONS
            self.apigateway_client.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                type='MOCK',
                requestTemplates={
                    'application/json': '{"statusCode": 200}'
                }
            )
            
            # Set up method response for OPTIONS
            self.apigateway_client.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': False,
                    'method.response.header.Access-Control-Allow-Methods': False,
                    'method.response.header.Access-Control-Allow-Origin': False
                }
            )
            
            # Set up integration response for OPTIONS
            self.apigateway_client.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod='OPTIONS',
                statusCode='200',
                responseParameters={
                    'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
                    'method.response.header.Access-Control-Allow-Origin': "'*'"
                }
            )
            
            return True
        except Exception as e:
            print(f"Error adding CORS support: {e}")
            return False
    
    def create_deployment(self, api_id: str, stage_name: str) -> str:
        """Create a deployment for the API"""
        try:
            response = self.apigateway_client.create_deployment(
                restApiId=api_id,
                stageName=stage_name,
                description=f"Deployment for {stage_name} stage"
            )
            return response['id']
        except Exception as e:
            print(f"Error creating deployment: {e}")
            return None
    
    def add_lambda_permission(self, lambda_function_name: str, api_id: str, 
                             account_id: str) -> bool:
        """Add permission for API Gateway to invoke Lambda function"""
        lambda_client = boto3.client('lambda', region_name=self.region)
        
        try:
            source_arn = f"arn:aws:execute-api:{self.region}:{account_id}:{api_id}/*/*"
            
            lambda_client.add_permission(
                FunctionName=lambda_function_name,
                StatementId=f"apigateway-invoke-{api_id}",
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=source_arn
            )
            return True
        except Exception as e:
            print(f"Error adding Lambda permission: {e}")
            return False

def setup_api_gateway(lambda_function_arns: Dict[str, str]) -> Dict[str, Any]:
    """Set up complete API Gateway for Biomerkin system"""
    api_manager = APIGatewayManager()
    
    # Create REST API
    api_id = api_manager.create_rest_api(
        api_name="biomerkin-api",
        description="REST API for Biomerkin multi-agent bioinformatics system"
    )
    
    if not api_id:
        return None
    
    # Get root resource ID
    root_resource_id = api_manager.get_root_resource_id(api_id)
    
    # API structure
    api_structure = {
        'workflows': {
            'methods': ['POST', 'GET'],
            'lambda_function': 'biomerkin-orchestrator',
            'sub_resources': {
                '{workflow_id}': {
                    'methods': ['GET'],
                    'lambda_function': 'biomerkin-orchestrator'
                },
                '{workflow_id}/results': {
                    'methods': ['GET'],
                    'lambda_function': 'biomerkin-orchestrator'
                }
            }
        },
        'analysis': {
            'sub_resources': {
                'genomics': {
                    'methods': ['POST'],
                    'lambda_function': 'biomerkin-genomics'
                },
                'proteomics': {
                    'methods': ['POST'],
                    'lambda_function': 'biomerkin-proteomics'
                },
                'literature': {
                    'methods': ['POST'],
                    'lambda_function': 'biomerkin-literature'
                },
                'drug': {
                    'methods': ['POST'],
                    'lambda_function': 'biomerkin-drug'
                },
                'decision': {
                    'methods': ['POST'],
                    'lambda_function': 'biomerkin-decision'
                }
            }
        }
    }
    
    # Get account ID for Lambda permissions
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()['Account']
    
    def create_resource_structure(parent_id: str, structure: dict, path_prefix: str = ""):
        """Recursively create API Gateway resource structure"""
        for resource_name, config in structure.items():
            # Create resource
            resource_id = api_manager.create_resource(api_id, parent_id, resource_name)
            if not resource_id:
                continue
            
            current_path = f"{path_prefix}/{resource_name}"
            
            # Create methods for this resource
            if 'methods' in config:
                lambda_function_name = config['lambda_function']
                lambda_function_arn = lambda_function_arns.get(lambda_function_name)
                
                if lambda_function_arn:
                    for method in config['methods']:
                        # Create method
                        api_manager.create_method(api_id, resource_id, method)
                        
                        # Create integration
                        api_manager.create_integration(
                            api_id, resource_id, method, lambda_function_arn
                        )
                    
                    # Add Lambda permission
                    api_manager.add_lambda_permission(
                        lambda_function_name, api_id, account_id
                    )
            
            # Add CORS support
            api_manager.add_cors_support(api_id, resource_id)
            
            # Create sub-resources recursively
            if 'sub_resources' in config:
                create_resource_structure(
                    resource_id, config['sub_resources'], current_path
                )
    
    # Create the resource structure
    create_resource_structure(root_resource_id, api_structure)
    
    # Create deployment
    deployment_id = api_manager.create_deployment(api_id, 'prod')
    
    # Get API endpoint URL
    api_url = f"https://{api_id}.execute-api.{api_manager.region}.amazonaws.com/prod"
    
    return {
        'api_id': api_id,
        'deployment_id': deployment_id,
        'api_url': api_url,
        'region': api_manager.region
    }

def create_api_documentation():
    """Create OpenAPI specification for the Biomerkin API"""
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Biomerkin Multi-Agent API",
            "description": "REST API for bioinformatics analysis using multiple AI agents",
            "version": "1.0.0"
        },
        "servers": [
            {
                "url": "https://api.biomerkin.com/prod",
                "description": "Production server"
            }
        ],
        "paths": {
            "/workflows": {
                "post": {
                    "summary": "Start a new analysis workflow",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "dna_sequence": {
                                            "type": "string",
                                            "description": "DNA sequence in FASTA format"
                                        }
                                    },
                                    "required": ["dna_sequence"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Workflow started successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "workflow_id": {
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/workflows/{workflow_id}": {
                "get": {
                    "summary": "Get workflow status",
                    "parameters": [
                        {
                            "name": "workflow_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Workflow status",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "workflow_id": {"type": "string"},
                                            "status": {"type": "string"},
                                            "progress_percentage": {"type": "number"},
                                            "current_agent": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/workflows/{workflow_id}/results": {
                "get": {
                    "summary": "Get workflow results",
                    "parameters": [
                        {
                            "name": "workflow_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Analysis results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "genomics_results": {"type": "object"},
                                            "proteomics_results": {"type": "object"},
                                            "literature_summary": {"type": "object"},
                                            "drug_candidates": {"type": "array"},
                                            "medical_report": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Write OpenAPI spec to file
    with open('deploy/biomerkin_api_spec.json', 'w') as f:
        json.dump(openapi_spec, f, indent=2)
    
    return openapi_spec

if __name__ == "__main__":
    # Example usage
    lambda_arns = {
        'biomerkin-orchestrator': 'arn:aws:lambda:us-east-1:123456789012:function:biomerkin-orchestrator',
        'biomerkin-genomics': 'arn:aws:lambda:us-east-1:123456789012:function:biomerkin-genomics',
        'biomerkin-proteomics': 'arn:aws:lambda:us-east-1:123456789012:function:biomerkin-proteomics',
        'biomerkin-literature': 'arn:aws:lambda:us-east-1:123456789012:function:biomerkin-literature',
        'biomerkin-drug': 'arn:aws:lambda:us-east-1:123456789012:function:biomerkin-drug',
        'biomerkin-decision': 'arn:aws:lambda:us-east-1:123456789012:function:biomerkin-decision'
    }
    
    api_info = setup_api_gateway(lambda_arns)
    create_api_documentation()
    
    if api_info:
        print(f"API Gateway created successfully: {api_info['api_url']}")