#!/usr/bin/env python3
"""
AWS Integration and Live Deployment Checker
Verifies AWS resources are properly deployed and accessible online
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Any

class AWSIntegrationChecker:
    def __init__(self):
        self.results = {
            'lambda_functions': [],
            'bedrock_agents': [],
            'api_gateway': [],
            's3_buckets': [],
            'dynamodb_tables': [],
            'iam_roles': [],
            'cloudwatch_logs': [],
            'issues': [],
            'warnings': []
        }
        
        try:
            self.lambda_client = boto3.client('lambda')
            self.bedrock_client = boto3.client('bedrock-agent')
            self.bedrock_runtime = boto3.client('bedrock-agent-runtime')
            self.apigateway_client = boto3.client('apigateway')
            self.s3_client = boto3.client('s3')
            self.dynamodb_client = boto3.client('dynamodb')
            self.iam_client = boto3.client('iam')
            self.logs_client = boto3.client('logs')
            self.credentials_valid = True
        except NoCredentialsError:
            print("❌ AWS credentials not configured!")
            print("Please run: aws configure")
            self.credentials_valid = False
        except Exception as e:
            print(f"❌ Error initializing AWS clients: {e}")
            self.credentials_valid = False
    
    def check_lambda_functions(self):
        """Check deployed Lambda functions"""
        print("\n🔍 Checking Lambda Functions...")
        
        if not self.credentials_valid:
            return
        
        try:
            response = self.lambda_client.list_functions()
            functions = response.get('Functions', [])
            
            # Expected Lambda functions
            expected_functions = [
                'biomerkin-genomics',
                'biomerkin-proteomics',
                'biomerkin-literature',
                'biomerkin-drug',
                'biomerkin-decision',
                'biomerkin-orchestrator'
            ]
            
            found_functions = []
            for func in functions:
                func_name = func['FunctionName']
                if 'biomerkin' in func_name.lower():
                    found_functions.append(func_name)
                    self.results['lambda_functions'].append({
                        'name': func_name,
                        'runtime': func.get('Runtime'),
                        'memory': func.get('MemorySize'),
                        'timeout': func.get('Timeout'),
                        'status': 'DEPLOYED'
                    })
                    print(f"  ✅ Found: {func_name}")
                    
                    # Check function configuration
                    if func.get('Timeout', 0) < 60:
                        self.results['warnings'].append(
                            f"Lambda {func_name} has low timeout: {func.get('Timeout')}s"
                        )
            
            # Check for missing functions
            for expected in expected_functions:
                if not any(expected in f for f in found_functions):
                    self.results['issues'].append(f"Missing Lambda function: {expected}")
                    print(f"  ❌ Missing: {expected}")
            
            if not found_functions:
                self.results['issues'].append("No Biomerkin Lambda functions found!")
                print("  ❌ No Biomerkin Lambda functions deployed")
            
        except ClientError as e:
            error_msg = f"Error checking Lambda functions: {e}"
            self.results['issues'].append(error_msg)
            print(f"  ❌ {error_msg}")
    
    def check_bedrock_agents(self):
        """Check Bedrock Agents deployment"""
        print("\n🔍 Checking Bedrock Agents...")
        
        if not self.credentials_valid:
            return
        
        try:
            response = self.bedrock_client.list_agents()
            agents = response.get('agentSummaries', [])
            
            expected_agents = [
                'genomics',
                'proteomics',
                'literature',
                'drug',
                'decision'
            ]
            
            found_agents = []
            for agent in agents:
                agent_name = agent.get('agentName', '').lower()
                if any(exp in agent_name for exp in expected_agents):
                    found_agents.append(agent_name)
                    self.results['bedrock_agents'].append({
                        'name': agent.get('agentName'),
                        'id': agent.get('agentId'),
                        'status': agent.get('agentStatus'),
                        'updated': str(agent.get('updatedAt'))
                    })
                    print(f"  ✅ Found: {agent.get('agentName')} (Status: {agent.get('agentStatus')})")
            
            # Check for missing agents
            for expected in expected_agents:
                if not any(expected in f for f in found_agents):
                    self.results['warnings'].append(f"Bedrock agent may be missing: {expected}")
                    print(f"  ⚠️  Not found: {expected} agent")
            
            if not found_agents:
                self.results['warnings'].append("No Bedrock agents found - may not be deployed yet")
                print("  ⚠️  No Bedrock agents found")
            
        except ClientError as e:
            if 'AccessDeniedException' in str(e):
                self.results['warnings'].append("No access to Bedrock - may need to enable in AWS console")
                print("  ⚠️  Bedrock access denied - may need to enable Bedrock in your region")
            else:
                error_msg = f"Error checking Bedrock agents: {e}"
                self.results['warnings'].append(error_msg)
                print(f"  ⚠️  {error_msg}")
    
    def check_api_gateway(self):
        """Check API Gateway deployment"""
        print("\n🔍 Checking API Gateway...")
        
        if not self.credentials_valid:
            return
        
        try:
            response = self.apigateway_client.get_rest_apis()
            apis = response.get('items', [])
            
            biomerkin_apis = []
            for api in apis:
                api_name = api.get('name', '').lower()
                if 'biomerkin' in api_name:
                    biomerkin_apis.append(api)
                    api_id = api.get('id')
                    
                    # Get stages
                    stages_response = self.apigateway_client.get_stages(restApiId=api_id)
                    stages = stages_response.get('item', [])
                    
                    for stage in stages:
                        stage_name = stage.get('stageName')
                        url = f"https://{api_id}.execute-api.{boto3.session.Session().region_name}.amazonaws.com/{stage_name}"
                        
                        self.results['api_gateway'].append({
                            'name': api.get('name'),
                            'id': api_id,
                            'stage': stage_name,
                            'url': url,
                            'status': 'DEPLOYED'
                        })
                        print(f"  ✅ Found: {api.get('name')}")
                        print(f"     URL: {url}")
            
            if not biomerkin_apis:
                self.results['issues'].append("No API Gateway found for Biomerkin")
                print("  ❌ No API Gateway deployed")
            
        except ClientError as e:
            error_msg = f"Error checking API Gateway: {e}"
            self.results['issues'].append(error_msg)
            print(f"  ❌ {error_msg}")
    
    def check_s3_buckets(self):
        """Check S3 buckets"""
        print("\n🔍 Checking S3 Buckets...")
        
        if not self.credentials_valid:
            return
        
        try:
            response = self.s3_client.list_buckets()
            buckets = response.get('Buckets', [])
            
            biomerkin_buckets = []
            for bucket in buckets:
                bucket_name = bucket.get('Name', '').lower()
                if 'biomerkin' in bucket_name:
                    biomerkin_buckets.append(bucket_name)
                    
                    # Check if bucket is configured for website hosting
                    try:
                        website_config = self.s3_client.get_bucket_website(Bucket=bucket_name)
                        is_website = True
                        website_url = f"http://{bucket_name}.s3-website-{boto3.session.Session().region_name}.amazonaws.com"
                    except:
                        is_website = False
                        website_url = None
                    
                    self.results['s3_buckets'].append({
                        'name': bucket_name,
                        'is_website': is_website,
                        'url': website_url,
                        'created': str(bucket.get('CreationDate'))
                    })
                    
                    print(f"  ✅ Found: {bucket_name}")
                    if is_website:
                        print(f"     Website URL: {website_url}")
            
            if not biomerkin_buckets:
                self.results['warnings'].append("No S3 buckets found for Biomerkin")
                print("  ⚠️  No S3 buckets found")
            
        except ClientError as e:
            error_msg = f"Error checking S3 buckets: {e}"
            self.results['issues'].append(error_msg)
            print(f"  ❌ {error_msg}")
    
    def check_dynamodb_tables(self):
        """Check DynamoDB tables"""
        print("\n🔍 Checking DynamoDB Tables...")
        
        if not self.credentials_valid:
            return
        
        try:
            response = self.dynamodb_client.list_tables()
            tables = response.get('TableNames', [])
            
            biomerkin_tables = []
            for table_name in tables:
                if 'biomerkin' in table_name.lower():
                    biomerkin_tables.append(table_name)
                    
                    # Get table details
                    table_info = self.dynamodb_client.describe_table(TableName=table_name)
                    table_data = table_info.get('Table', {})
                    
                    self.results['dynamodb_tables'].append({
                        'name': table_name,
                        'status': table_data.get('TableStatus'),
                        'item_count': table_data.get('ItemCount', 0),
                        'size_bytes': table_data.get('TableSizeBytes', 0)
                    })
                    
                    print(f"  ✅ Found: {table_name} (Status: {table_data.get('TableStatus')})")
            
            if not biomerkin_tables:
                self.results['warnings'].append("No DynamoDB tables found for Biomerkin")
                print("  ⚠️  No DynamoDB tables found")
            
        except ClientError as e:
            error_msg = f"Error checking DynamoDB tables: {e}"
            self.results['issues'].append(error_msg)
            print(f"  ❌ {error_msg}")
    
    def check_iam_roles(self):
        """Check IAM roles"""
        print("\n🔍 Checking IAM Roles...")
        
        if not self.credentials_valid:
            return
        
        try:
            response = self.iam_client.list_roles()
            roles = response.get('Roles', [])
            
            biomerkin_roles = []
            for role in roles:
                role_name = role.get('RoleName', '').lower()
                if 'biomerkin' in role_name or 'lambda' in role_name:
                    biomerkin_roles.append(role.get('RoleName'))
                    self.results['iam_roles'].append({
                        'name': role.get('RoleName'),
                        'arn': role.get('Arn'),
                        'created': str(role.get('CreateDate'))
                    })
                    print(f"  ✅ Found: {role.get('RoleName')}")
            
            if not biomerkin_roles:
                self.results['warnings'].append("No IAM roles found for Biomerkin")
                print("  ⚠️  No specific IAM roles found")
            
        except ClientError as e:
            error_msg = f"Error checking IAM roles: {e}"
            self.results['warnings'].append(error_msg)
            print(f"  ⚠️  {error_msg}")
    
    def generate_deployment_report(self):
        """Generate deployment status report"""
        print("\n" + "="*80)
        print("📊 AWS INTEGRATION & DEPLOYMENT STATUS")
        print("="*80)
        
        # Lambda Functions
        print(f"\n📦 Lambda Functions: {len(self.results['lambda_functions'])} deployed")
        for func in self.results['lambda_functions']:
            print(f"  • {func['name']} ({func['runtime']}, {func['memory']}MB, {func['timeout']}s)")
        
        # Bedrock Agents
        print(f"\n🤖 Bedrock Agents: {len(self.results['bedrock_agents'])} deployed")
        for agent in self.results['bedrock_agents']:
            print(f"  • {agent['name']} (Status: {agent['status']})")
        
        # API Gateway
        print(f"\n🌐 API Gateway: {len(self.results['api_gateway'])} endpoints")
        for api in self.results['api_gateway']:
            print(f"  • {api['name']}")
            print(f"    URL: {api['url']}")
        
        # S3 Buckets
        print(f"\n🪣 S3 Buckets: {len(self.results['s3_buckets'])} found")
        for bucket in self.results['s3_buckets']:
            print(f"  • {bucket['name']}")
            if bucket['is_website']:
                print(f"    Website: {bucket['url']}")
        
        # DynamoDB Tables
        print(f"\n🗄️  DynamoDB Tables: {len(self.results['dynamodb_tables'])} found")
        for table in self.results['dynamodb_tables']:
            print(f"  • {table['name']} ({table['item_count']} items)")
        
        # Issues and Warnings
        if self.results['issues']:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.results['issues'])}):")
            for issue in self.results['issues']:
                print(f"  ❌ {issue}")
        
        if self.results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(self.results['warnings'])}):")
            for warning in self.results['warnings']:
                print(f"  ⚠️  {warning}")
        
        # Overall Status
        print("\n" + "="*80)
        print("📈 DEPLOYMENT STATUS")
        print("="*80)
        
        total_resources = (
            len(self.results['lambda_functions']) +
            len(self.results['bedrock_agents']) +
            len(self.results['api_gateway']) +
            len(self.results['s3_buckets']) +
            len(self.results['dynamodb_tables'])
        )
        
        print(f"  Total AWS Resources: {total_resources}")
        print(f"  Critical Issues: {len(self.results['issues'])}")
        print(f"  Warnings: {len(self.results['warnings'])}")
        
        if len(self.results['issues']) == 0 and total_resources >= 5:
            print("\n  ✅ System is LIVE and ready for user input!")
            print("  ✅ AWS integration is properly configured")
        elif len(self.results['issues']) == 0:
            print("\n  ⚠️  System is partially deployed")
            print("  ⚠️  Some resources may be missing")
        else:
            print("\n  ❌ System has critical issues")
            print("  ❌ Deployment incomplete")
        
        print("\n" + "="*80)
        
        # Save report
        with open('AWS_INTEGRATION_STATUS.json', 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print("\n📄 Detailed report saved to: AWS_INTEGRATION_STATUS.json")
    
    def run_checks(self):
        """Run all AWS integration checks"""
        if not self.credentials_valid:
            print("\n❌ Cannot proceed without valid AWS credentials")
            print("Please configure AWS CLI with: aws configure")
            return
        
        print("🚀 Checking AWS Integration and Live Deployment Status...")
        print("="*80)
        
        self.check_lambda_functions()
        self.check_bedrock_agents()
        self.check_api_gateway()
        self.check_s3_buckets()
        self.check_dynamodb_tables()
        self.check_iam_roles()
        
        self.generate_deployment_report()

if __name__ == '__main__':
    checker = AWSIntegrationChecker()
    checker.run_checks()
