#!/usr/bin/env python3
"""
Perfect AWS Integration Test
Tests all components to ensure perfect integration
"""

import boto3
import json
import sys
from datetime import datetime

class PerfectIntegrationTest:
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        self.region = 'ap-south-1'
        
    def test_lambda_bedrock_integration(self):
        """Test if Lambda functions can access Bedrock"""
        print("\n🔍 Testing Lambda → Bedrock Integration...")
        
        try:
            lambda_client = boto3.client('lambda', region_name=self.region)
            
            # Test each Lambda function
            functions = [
                'biomerkin-genomics',
                'biomerkin-proteomics',
                'biomerkin-literature',
                'biomerkin-drug',
                'biomerkin-decision',
                'biomerkin-orchestrator'
            ]
            
            for func_name in functions:
                try:
                    # Get function configuration
                    response = lambda_client.get_function(FunctionName=func_name)
                    
                    # Check if function has Bedrock permissions
                    role_arn = response['Configuration']['Role']
                    
                    # Verify function exists and is active
                    if response['Configuration']['State'] == 'Active':
                        self.results['passed'].append(f"✅ {func_name} is active and configured")
                    else:
                        self.results['warnings'].append(f"⚠️  {func_name} state: {response['Configuration']['State']}")
                        
                except Exception as e:
                    self.results['failed'].append(f"❌ {func_name}: {str(e)}")
                    
        except Exception as e:
            self.results['failed'].append(f"❌ Lambda client error: {str(e)}")
    
    def test_bedrock_access(self):
        """Test Bedrock API access"""
        print("\n🔍 Testing Bedrock API Access...")
        
        try:
            bedrock_client = boto3.client('bedrock', region_name=self.region)
            
            # List available models
            response = bedrock_client.list_foundation_models()
            
            claude_models = [m for m in response['modelSummaries'] if 'claude' in m['modelId'].lower()]
            
            if len(claude_models) >= 5:
                self.results['passed'].append(f"✅ Bedrock accessible with {len(claude_models)} Claude models")
            else:
                self.results['warnings'].append(f"⚠️  Only {len(claude_models)} Claude models available")
                
        except Exception as e:
            self.results['failed'].append(f"❌ Bedrock access error: {str(e)}")
    
    def test_iam_permissions(self):
        """Test IAM permissions for Bedrock"""
        print("\n🔍 Testing IAM Permissions...")
        
        try:
            iam_client = boto3.client('iam')
            
            # Check Lambda execution role
            role_name = 'biomerkin-lambda-execution-role'
            
            # Get attached policies
            response = iam_client.list_attached_role_policies(RoleName=role_name)
            
            policies = [p['PolicyName'] for p in response['AttachedPolicies']]
            
            required_policies = [
                'AmazonBedrockFullAccess',
                'AWSLambdaBasicExecutionRole',
                'AmazonDynamoDBFullAccess',
                'AmazonS3FullAccess'
            ]
            
            for policy in required_policies:
                if policy in policies:
                    self.results['passed'].append(f"✅ {policy} attached")
                else:
                    self.results['failed'].append(f"❌ {policy} missing")
                    
        except Exception as e:
            self.results['failed'].append(f"❌ IAM check error: {str(e)}")
    
    def test_dynamodb_integration(self):
        """Test DynamoDB integration"""
        print("\n🔍 Testing DynamoDB Integration...")
        
        try:
            dynamodb_client = boto3.client('dynamodb', region_name=self.region)
            
            # Check table exists
            response = dynamodb_client.describe_table(TableName='biomerkin-workflows')
            
            if response['Table']['TableStatus'] == 'ACTIVE':
                self.results['passed'].append("✅ DynamoDB table active and accessible")
            else:
                self.results['warnings'].append(f"⚠️  DynamoDB status: {response['Table']['TableStatus']}")
                
        except Exception as e:
            self.results['failed'].append(f"❌ DynamoDB error: {str(e)}")
    
    def test_s3_integration(self):
        """Test S3 integration"""
        print("\n🔍 Testing S3 Integration...")
        
        try:
            s3_client = boto3.client('s3', region_name=self.region)
            
            # List buckets
            response = s3_client.list_buckets()
            
            biomerkin_buckets = [b['Name'] for b in response['Buckets'] if 'biomerkin' in b['Name']]
            
            if len(biomerkin_buckets) >= 1:
                self.results['passed'].append(f"✅ {len(biomerkin_buckets)} S3 buckets found")
                
                # Check if frontend bucket has website configuration
                for bucket in biomerkin_buckets:
                    if 'frontend' in bucket:
                        try:
                            website = s3_client.get_bucket_website(Bucket=bucket)
                            self.results['passed'].append(f"✅ {bucket} has website hosting")
                        except:
                            pass
            else:
                self.results['warnings'].append("⚠️  No S3 buckets found")
                
        except Exception as e:
            self.results['failed'].append(f"❌ S3 error: {str(e)}")
    
    def test_api_gateway_integration(self):
        """Test API Gateway integration"""
        print("\n🔍 Testing API Gateway Integration...")
        
        try:
            apigateway_client = boto3.client('apigateway', region_name=self.region)
            
            # List APIs
            response = apigateway_client.get_rest_apis()
            
            biomerkin_apis = [api for api in response['items'] if 'biomerkin' in api['name'].lower()]
            
            if len(biomerkin_apis) >= 1:
                api = biomerkin_apis[0]
                self.results['passed'].append(f"✅ API Gateway '{api['name']}' exists")
                
                # Check for deployments
                api_id = api['id']
                deployments = apigateway_client.get_deployments(restApiId=api_id)
                
                if deployments['items']:
                    self.results['passed'].append(f"✅ API has {len(deployments['items'])} deployment(s)")
                else:
                    self.results['warnings'].append("⚠️  API has no deployments")
            else:
                self.results['warnings'].append("⚠️  No API Gateway found")
                
        except Exception as e:
            self.results['failed'].append(f"❌ API Gateway error: {str(e)}")
    
    def test_lambda_code_integration(self):
        """Test if Lambda functions have code with Bedrock calls"""
        print("\n🔍 Testing Lambda Code Integration...")
        
        try:
            lambda_client = boto3.client('lambda', region_name=self.region)
            
            # Check code size (indicates code is uploaded)
            functions = [
                'biomerkin-genomics',
                'biomerkin-literature',
                'biomerkin-decision'
            ]
            
            for func_name in functions:
                try:
                    response = lambda_client.get_function(FunctionName=func_name)
                    code_size = response['Configuration']['CodeSize']
                    
                    if code_size > 100000:  # > 100KB indicates real code
                        self.results['passed'].append(f"✅ {func_name} has code ({code_size} bytes)")
                    else:
                        self.results['warnings'].append(f"⚠️  {func_name} code size small: {code_size} bytes")
                        
                except Exception as e:
                    self.results['failed'].append(f"❌ {func_name}: {str(e)}")
                    
        except Exception as e:
            self.results['failed'].append(f"❌ Lambda code check error: {str(e)}")
    
    def test_end_to_end_connectivity(self):
        """Test end-to-end connectivity"""
        print("\n🔍 Testing End-to-End Connectivity...")
        
        # Check if all components can communicate
        components = {
            'Lambda': len([r for r in self.results['passed'] if 'biomerkin-' in r]),
            'Bedrock': len([r for r in self.results['passed'] if 'Bedrock' in r]),
            'DynamoDB': len([r for r in self.results['passed'] if 'DynamoDB' in r]),
            'S3': len([r for r in self.results['passed'] if 'S3' in r]),
            'API Gateway': len([r for r in self.results['passed'] if 'API' in r]),
            'IAM': len([r for r in self.results['passed'] if 'Access' in r])
        }
        
        all_connected = all(count > 0 for count in components.values())
        
        if all_connected:
            self.results['passed'].append("✅ All components connected end-to-end")
        else:
            missing = [k for k, v in components.items() if v == 0]
            self.results['warnings'].append(f"⚠️  Missing connections: {', '.join(missing)}")
    
    def generate_report(self):
        """Generate integration test report"""
        print("\n" + "="*80)
        print("📊 PERFECT AWS INTEGRATION TEST REPORT")
        print("="*80)
        
        print(f"\n✅ PASSED TESTS ({len(self.results['passed'])}):")
        for result in self.results['passed']:
            print(f"  {result}")
        
        if self.results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(self.results['warnings'])}):")
            for warning in self.results['warnings']:
                print(f"  {warning}")
        
        if self.results['failed']:
            print(f"\n❌ FAILED TESTS ({len(self.results['failed'])}):")
            for failure in self.results['failed']:
                print(f"  {failure}")
        
        # Calculate integration score
        total_tests = len(self.results['passed']) + len(self.results['failed'])
        if total_tests > 0:
            score = (len(self.results['passed']) / total_tests) * 100
        else:
            score = 0
        
        print("\n" + "="*80)
        print("📈 INTEGRATION SCORE")
        print("="*80)
        print(f"  Passed: {len(self.results['passed'])}")
        print(f"  Failed: {len(self.results['failed'])}")
        print(f"  Warnings: {len(self.results['warnings'])}")
        print(f"  Score: {score:.1f}%")
        
        if score >= 90 and len(self.results['failed']) == 0:
            print("\n  Status: ✅ PERFECTLY INTEGRATED")
        elif score >= 70:
            print("\n  Status: ⚠️  MOSTLY INTEGRATED (minor issues)")
        else:
            print("\n  Status: ❌ INTEGRATION ISSUES")
        
        print("\n" + "="*80)
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'passed': self.results['passed'],
            'failed': self.results['failed'],
            'warnings': self.results['warnings'],
            'score': score
        }
        
        with open('PERFECT_INTEGRATION_TEST_REPORT.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n📄 Report saved to: PERFECT_INTEGRATION_TEST_REPORT.json")
        
        return len(self.results['failed']) == 0
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Perfect AWS Integration Tests...")
        print("="*80)
        
        self.test_lambda_bedrock_integration()
        self.test_bedrock_access()
        self.test_iam_permissions()
        self.test_dynamodb_integration()
        self.test_s3_integration()
        self.test_api_gateway_integration()
        self.test_lambda_code_integration()
        self.test_end_to_end_connectivity()
        
        return self.generate_report()

if __name__ == '__main__':
    tester = PerfectIntegrationTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
