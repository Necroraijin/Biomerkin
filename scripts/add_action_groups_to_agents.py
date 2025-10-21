#!/usr/bin/env python3
"""
Add action groups to existing Bedrock Agents
"""

import boto3
import json
import time
import sys

# Agent IDs from previous deployment
AGENT_IDS = {
    'genomics': 'SDWGWTUWUA',
    'literature': 'MHF7ORBPUQ',
    'drug': 'XPYDZJAGTR',
    'decision': '4GE0EVCGYG'
}

def create_simple_lambda_for_agent(lambda_client, iam_client, agent_name, account_id, region):
    """Create a simple Lambda function for the agent."""
    function_name = f"biomerkin-{agent_name}-action"
    
    # Simple Lambda code
    lambda_code = f'''
import json

def lambda_handler(event, context):
    """Handler for {agent_name} agent actions."""
    print(f"Event: {{json.dumps(event)}}")
    
    return {{
        'messageVersion': '1.0',
        'response': {{
            'actionGroup': event.get('actionGroup', ''),
            'apiPath': event.get('apiPath', ''),
            'httpMethod': 'POST',
            'httpStatusCode': 200,
            'responseBody': {{
                'application/json': {{
                    'body': json.dumps({{
                        'success': True,
                        'agent': '{agent_name}',
                        'message': 'Action completed successfully'
                    }})
                }}
            }}
        }}
    }}
'''
    
    # Create ZIP
    import zipfile
    import io
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr('lambda_function.py', lambda_code)
    zip_buffer.seek(0)
    
    # Create or get Lambda execution role
    role_name = f"{function_name}-role"
    
    try:
        role = iam_client.get_role(RoleName=role_name)
        role_arn = role['Role']['Arn']
        print(f"✅ Using existing role: {role_name}")
    except iam_client.exceptions.NoSuchEntityException:
        # Create role
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Service": "lambda.amazonaws.com"},
                "Action": "sts:AssumeRole"
            }]
        }
        
        role_response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        role_arn = role_response['Role']['Arn']
        
        # Attach policy
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        print(f"✅ Created role: {role_name}")
        print(f"⏳ Waiting 20 seconds for IAM propagation...")
        time.sleep(20)
    
    # Create or update Lambda
    try:
        lambda_client.get_function(FunctionName=function_name)
        # Update
        lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_buffer.read()
        )
        print(f"✅ Updated Lambda: {function_name}")
        response = lambda_client.get_function(FunctionName=function_name)
        function_arn = response['Configuration']['FunctionArn']
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create
        zip_buffer.seek(0)
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler='lambda_function.lambda_handler',
            Code={'ZipFile': zip_buffer.read()},
            Timeout=60,
            MemorySize=256
        )
        function_arn = response['FunctionArn']
        print(f"✅ Created Lambda: {function_name}")
    
    # Add Bedrock permission
    try:
        lambda_client.add_permission(
            FunctionName=function_name,
            StatementId=f'bedrock-invoke-{int(time.time())}',
            Action='lambda:InvokeFunction',
            Principal='bedrock.amazonaws.com',
            SourceArn=f"arn:aws:bedrock:{region}:{account_id}:agent/*"
        )
        print(f"✅ Added Bedrock permission")
    except lambda_client.exceptions.ResourceConflictException:
        print(f"⚠️  Permission already exists")
    
    return function_arn

def add_action_group_to_agent(bedrock_client, agent_id, agent_name, lambda_arn):
    """Add action group to Bedrock Agent."""
    action_group_name = f"{agent_name}-actions"
    
    # Complete OpenAPI schema
    api_schema = {
        "openapi": "3.0.0",
        "info": {
            "title": f"{agent_name.title()} API",
            "version": "1.0.0",
            "description": f"API for {agent_name} agent actions"
        },
        "paths": {
            "/execute": {
                "post": {
                    "summary": f"Execute {agent_name} action",
                    "description": f"Execute an action for the {agent_name} agent",
                    "operationId": f"execute{agent_name.title()}Action",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "action": {
                                            "type": "string",
                                            "description": "The action to execute"
                                        },
                                        "parameters": {
                                            "type": "object",
                                            "description": "Action parameters"
                                        }
                                    },
                                    "required": ["action"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {
                                                "type": "boolean"
                                            },
                                            "message": {
                                                "type": "string"
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
    }
    
    try:
        response = bedrock_client.create_agent_action_group(
            agentId=agent_id,
            agentVersion='DRAFT',
            actionGroupName=action_group_name,
            description=f"Action group for {agent_name} agent",
            actionGroupExecutor={
                'lambda': lambda_arn
            },
            apiSchema={
                'payload': json.dumps(api_schema)
            }
        )
        print(f"✅ Created action group: {action_group_name}")
        return response['agentActionGroup']['actionGroupId']
    except Exception as e:
        print(f"❌ Failed to create action group: {e}")
        return None

def prepare_agent(bedrock_client, agent_id, agent_name):
    """Prepare agent for use."""
    try:
        bedrock_client.prepare_agent(agentId=agent_id)
        print(f"✅ Prepared agent: {agent_name}")
        time.sleep(5)
    except Exception as e:
        print(f"⚠️  Failed to prepare agent: {e}")

def main():
    print("🚀 Adding Action Groups to Bedrock Agents")
    print("="*70)
    
    region = 'us-east-1'
    
    # Initialize clients
    bedrock_client = boto3.client('bedrock-agent', region_name=region)
    lambda_client = boto3.client('lambda', region_name=region)
    iam_client = boto3.client('iam', region_name=region)
    sts_client = boto3.client('sts', region_name=region)
    
    account_id = sts_client.get_caller_identity()['Account']
    
    success_count = 0
    
    for agent_name, agent_id in AGENT_IDS.items():
        print(f"\n{'='*70}")
        print(f"🤖 Processing {agent_name.title()}Agent (ID: {agent_id})")
        print(f"{'='*70}\n")
        
        try:
            # Create Lambda function
            lambda_arn = create_simple_lambda_for_agent(
                lambda_client, iam_client, agent_name, account_id, region
            )
            
            # Add action group
            action_group_id = add_action_group_to_agent(
                bedrock_client, agent_id, agent_name, lambda_arn
            )
            
            if action_group_id:
                # Prepare agent
                prepare_agent(bedrock_client, agent_id, agent_name)
                success_count += 1
                print(f"✅ {agent_name.title()}Agent fully configured!")
            
        except Exception as e:
            print(f"❌ Failed to configure {agent_name}: {e}")
    
    print(f"\n{'='*70}")
    print(f"🎉 CONFIGURATION COMPLETE")
    print(f"{'='*70}")
    print(f"\n✅ Successfully configured: {success_count}/{len(AGENT_IDS)} agents\n")
    
    if success_count == len(AGENT_IDS):
        print("🎯 All agents are ready to use!")
        print("\nNext steps:")
        print("1. Test agents: python scripts/test_autonomous_bedrock_agents.py")
        print("2. View in console: https://console.aws.amazon.com/bedrock/")
        return 0
    else:
        print("⚠️  Some agents failed to configure")
        return 1

if __name__ == "__main__":
    sys.exit(main())
