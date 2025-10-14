"""
Main AWS deployment orchestration script for Biomerkin multi-agent system
"""
import boto3
import json
import time
from typing import Dict, Any
from iam_policies import setup_iam_infrastructure
from lambda_deployment import deploy_all_lambda_functions
from api_gateway_setup import setup_api_gateway, create_api_documentation
from dynamodb_setup import setup_dynamodb_tables, create_dynamodb_client_utility
from s3_setup import setup_s3_infrastructure, create_s3_client_utility
from cloudwatch_setup import setup_cloudwatch_monitoring, create_custom_metrics_utility

class BiomerkinDeployment:
    def __init__(self, region='us-east-1', email_address=None, budget_limit=100.0):
        self.region = region
        self.email_address = email_address
        self.budget_limit = budget_limit
        self.deployment_results = {}
        
        # Get account ID
        sts_client = boto3.client('sts')
        self.account_id = sts_client.get_caller_identity()['Account']
        
        print(f"Starting Biomerkin deployment in region {region}")
        print(f"Account ID: {self.account_id}")
    
    def deploy_infrastructure(self) -> Dict[str, Any]:
        """Deploy complete AWS infrastructure for Biomerkin"""
        
        print("\n" + "="*60)
        print("BIOMERKIN AWS INFRASTRUCTURE DEPLOYMENT")
        print("="*60)
        
        # Step 1: Set up IAM roles and policies
        print("\n1. Setting up IAM roles and policies...")
        try:
            iam_results = setup_iam_infrastructure()
            self.deployment_results['iam'] = iam_results
            print("✓ IAM setup completed")
        except Exception as e:
            print(f"✗ IAM setup failed: {e}")
            return self.deployment_results
        
        # Step 2: Set up DynamoDB tables
        print("\n2. Setting up DynamoDB tables...")
        try:
            dynamodb_results = setup_dynamodb_tables()
            create_dynamodb_client_utility()
            self.deployment_results['dynamodb'] = dynamodb_results
            print("✓ DynamoDB setup completed")
        except Exception as e:
            print(f"✗ DynamoDB setup failed: {e}")
            return self.deployment_results
        
        # Step 3: Set up S3 buckets
        print("\n3. Setting up S3 buckets...")
        try:
            s3_results = setup_s3_infrastructure(self.account_id)
            create_s3_client_utility()
            self.deployment_results['s3'] = s3_results
            print("✓ S3 setup completed")
        except Exception as e:
            print(f"✗ S3 setup failed: {e}")
            return self.deployment_results
        
        # Step 4: Deploy Lambda functions
        print("\n4. Deploying Lambda functions...")
        try:
            if 'agent_roles' in iam_results:
                lambda_results = deploy_all_lambda_functions(iam_results['agent_roles'])
                self.deployment_results['lambda'] = lambda_results
                print("✓ Lambda deployment completed")
            else:
                print("✗ Cannot deploy Lambda functions - IAM roles not available")
                return self.deployment_results
        except Exception as e:
            print(f"✗ Lambda deployment failed: {e}")
            return self.deployment_results
        
        # Step 5: Set up API Gateway
        print("\n5. Setting up API Gateway...")
        try:
            if lambda_results:
                api_results = setup_api_gateway(lambda_results)
                create_api_documentation()
                self.deployment_results['api_gateway'] = api_results
                print("✓ API Gateway setup completed")
                if api_results:
                    print(f"API URL: {api_results['api_url']}")
            else:
                print("✗ Cannot set up API Gateway - Lambda functions not available")
                return self.deployment_results
        except Exception as e:
            print(f"✗ API Gateway setup failed: {e}")
            return self.deployment_results
        
        # Step 6: Set up CloudWatch monitoring
        print("\n6. Setting up CloudWatch monitoring...")
        try:
            cloudwatch_results = setup_cloudwatch_monitoring(
                self.email_address, self.budget_limit
            )
            create_custom_metrics_utility()
            self.deployment_results['cloudwatch'] = cloudwatch_results
            print("✓ CloudWatch setup completed")
        except Exception as e:
            print(f"✗ CloudWatch setup failed: {e}")
            return self.deployment_results
        
        # Step 7: Validate deployment
        print("\n7. Validating deployment...")
        validation_results = self.validate_deployment()
        self.deployment_results['validation'] = validation_results
        
        return self.deployment_results
    
    def validate_deployment(self) -> Dict[str, bool]:
        """Validate that all components are deployed correctly"""
        validation_results = {}
        
        # Validate Lambda functions
        lambda_client = boto3.client('lambda', region_name=self.region)
        expected_functions = [
            'biomerkin-orchestrator',
            'biomerkin-genomics',
            'biomerkin-proteomics',
            'biomerkin-literature',
            'biomerkin-drug',
            'biomerkin-decision'
        ]
        
        for function_name in expected_functions:
            try:
                lambda_client.get_function(FunctionName=function_name)
                validation_results[f"lambda_{function_name}"] = True
            except lambda_client.exceptions.ResourceNotFoundException:
                validation_results[f"lambda_{function_name}"] = False
        
        # Validate DynamoDB tables
        dynamodb_client = boto3.client('dynamodb', region_name=self.region)
        expected_tables = [
            'biomerkin-workflows',
            'biomerkin-analysis-results',
            'biomerkin-user-sessions',
            'biomerkin-audit-logs'
        ]
        
        for table_name in expected_tables:
            try:
                response = dynamodb_client.describe_table(TableName=table_name)
                validation_results[f"dynamodb_{table_name}"] = (
                    response['Table']['TableStatus'] == 'ACTIVE'
                )
            except dynamodb_client.exceptions.ResourceNotFoundException:
                validation_results[f"dynamodb_{table_name}"] = False
        
        # Validate S3 buckets
        s3_client = boto3.client('s3', region_name=self.region)
        expected_buckets = [
            'biomerkin-data',
            'biomerkin-results',
            'biomerkin-logs',
            'biomerkin-temp'
        ]
        
        for bucket_name in expected_buckets:
            try:
                s3_client.head_bucket(Bucket=bucket_name)
                validation_results[f"s3_{bucket_name}"] = True
            except s3_client.exceptions.NoSuchBucket:
                validation_results[f"s3_{bucket_name}"] = False
        
        # Validate API Gateway
        if 'api_gateway' in self.deployment_results and self.deployment_results['api_gateway']:
            api_id = self.deployment_results['api_gateway']['api_id']
            apigateway_client = boto3.client('apigateway', region_name=self.region)
            try:
                apigateway_client.get_rest_api(restApiId=api_id)
                validation_results['api_gateway'] = True
            except apigateway_client.exceptions.NotFoundException:
                validation_results['api_gateway'] = False
        else:
            validation_results['api_gateway'] = False
        
        return validation_results
    
    def generate_deployment_report(self) -> str:
        """Generate a comprehensive deployment report"""
        report = []
        report.append("BIOMERKIN DEPLOYMENT REPORT")
        report.append("=" * 50)
        report.append(f"Deployment Date: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append(f"AWS Region: {self.region}")
        report.append(f"Account ID: {self.account_id}")
        report.append("")
        
        # IAM Summary
        if 'iam' in self.deployment_results:
            report.append("IAM ROLES AND POLICIES:")
            iam_results = self.deployment_results['iam']
            if 'agent_roles' in iam_results:
                for agent, role_arn in iam_results['agent_roles'].items():
                    report.append(f"  ✓ {agent}: {role_arn}")
            if 'bedrock_role' in iam_results:
                report.append(f"  ✓ Bedrock Agent: {iam_results['bedrock_role']}")
            report.append("")
        
        # Lambda Summary
        if 'lambda' in self.deployment_results:
            report.append("LAMBDA FUNCTIONS:")
            for function_name, function_arn in self.deployment_results['lambda'].items():
                report.append(f"  ✓ {function_name}: {function_arn}")
            report.append("")
        
        # API Gateway Summary
        if 'api_gateway' in self.deployment_results and self.deployment_results['api_gateway']:
            api_info = self.deployment_results['api_gateway']
            report.append("API GATEWAY:")
            report.append(f"  ✓ API ID: {api_info['api_id']}")
            report.append(f"  ✓ API URL: {api_info['api_url']}")
            report.append("")
        
        # DynamoDB Summary
        if 'dynamodb' in self.deployment_results:
            report.append("DYNAMODB TABLES:")
            for table, success in self.deployment_results['dynamodb'].items():
                status = "✓" if success else "✗"
                report.append(f"  {status} biomerkin-{table}")
            report.append("")
        
        # S3 Summary
        if 's3' in self.deployment_results:
            report.append("S3 BUCKETS:")
            for bucket, success in self.deployment_results['s3'].items():
                status = "✓" if success else "✗"
                report.append(f"  {status} {bucket}")
            report.append("")
        
        # CloudWatch Summary
        if 'cloudwatch' in self.deployment_results:
            report.append("CLOUDWATCH MONITORING:")
            cw_results = self.deployment_results['cloudwatch']
            for component, success in cw_results.items():
                status = "✓" if success else "✗"
                report.append(f"  {status} {component}")
            report.append("")
        
        # Validation Summary
        if 'validation' in self.deployment_results:
            report.append("DEPLOYMENT VALIDATION:")
            validation_results = self.deployment_results['validation']
            passed = sum(1 for v in validation_results.values() if v)
            total = len(validation_results)
            report.append(f"  Validation Score: {passed}/{total}")
            
            for component, success in validation_results.items():
                status = "✓" if success else "✗"
                report.append(f"  {status} {component}")
            report.append("")
        
        # Cost Optimization Notes
        report.append("COST OPTIMIZATION FEATURES:")
        report.append("  ✓ Lambda functions with right-sized memory allocation")
        report.append("  ✓ DynamoDB on-demand billing mode")
        report.append("  ✓ S3 lifecycle policies for automatic archiving")
        report.append("  ✓ CloudWatch log retention policies")
        report.append(f"  ✓ Budget alerts set for ${self.budget_limit}/month")
        report.append("")
        
        # Next Steps
        report.append("NEXT STEPS:")
        report.append("  1. Test API endpoints using the provided OpenAPI specification")
        report.append("  2. Upload sample DNA sequences to test the workflow")
        report.append("  3. Monitor CloudWatch dashboard for system health")
        report.append("  4. Review cost optimization recommendations")
        report.append("")
        
        return "\n".join(report)
    
    def save_deployment_config(self, filename: str = 'biomerkin_deployment_config.json'):
        """Save deployment configuration for future reference"""
        config = {
            'deployment_timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'region': self.region,
            'account_id': self.account_id,
            'email_address': self.email_address,
            'budget_limit': self.budget_limit,
            'deployment_results': self.deployment_results
        }
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        print(f"Deployment configuration saved to {filename}")

def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Biomerkin AWS infrastructure')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--email', help='Email address for alerts')
    parser.add_argument('--budget', type=float, default=100.0, help='Monthly budget limit')
    parser.add_argument('--validate-only', action='store_true', help='Only validate existing deployment')
    
    args = parser.parse_args()
    
    deployment = BiomerkinDeployment(
        region=args.region,
        email_address=args.email,
        budget_limit=args.budget
    )
    
    if args.validate_only:
        print("Validating existing deployment...")
        validation_results = deployment.validate_deployment()
        deployment.deployment_results['validation'] = validation_results
    else:
        # Full deployment
        deployment.deploy_infrastructure()
    
    # Generate and display report
    report = deployment.generate_deployment_report()
    print("\n" + report)
    
    # Save configuration
    deployment.save_deployment_config()
    
    # Check if deployment was successful
    if 'validation' in deployment.deployment_results:
        validation_results = deployment.deployment_results['validation']
        failed_components = [k for k, v in validation_results.items() if not v]
        
        if failed_components:
            print(f"\n⚠️  Warning: {len(failed_components)} components failed validation:")
            for component in failed_components:
                print(f"   - {component}")
            return 1
        else:
            print("\n🎉 Deployment completed successfully! All components validated.")
            return 0
    else:
        print("\n❌ Deployment failed - validation not performed")
        return 1

if __name__ == "__main__":
    exit(main())