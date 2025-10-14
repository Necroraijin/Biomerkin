#!/usr/bin/env python3
"""
Deployment script for Biomerkin Hackathon submission.
Automates the complete deployment process for AWS.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
import boto3
from botocore.exceptions import ClientError


class BiomerkinDeployer:
    """Deployer for Biomerkin hackathon submission."""
    
    def __init__(self):
        """Initialize deployer."""
        self.region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        self.account_id = self._get_account_id()
        self.project_name = 'biomerkin-hackathon'
        
    def _get_account_id(self):
        """Get AWS account ID."""
        try:
            sts = boto3.client('sts')
            return sts.get_caller_identity()['Account']
        except Exception as e:
            print(f"❌ Error getting AWS account ID: {e}")
            sys.exit(1)
    
    def check_prerequisites(self):
        """Check if all prerequisites are met."""
        print("🔍 Checking prerequisites...")
        
        # Check AWS CLI
        try:
            subprocess.run(['aws', '--version'], check=True, capture_output=True)
            print("✅ AWS CLI installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ AWS CLI not found. Please install: https://aws.amazon.com/cli/")
            return False
        
        # Check CDK
        try:
            subprocess.run(['cdk', '--version'], check=True, capture_output=True)
            print("✅ AWS CDK installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ AWS CDK not found. Please install: npm install -g aws-cdk")
            return False
        
        # Check Node.js
        try:
            subprocess.run(['node', '--version'], check=True, capture_output=True)
            print("✅ Node.js installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Node.js not found. Please install: https://nodejs.org/")
            return False
        
        # Check Python
        try:
            subprocess.run(['python', '--version'], check=True, capture_output=True)
            print("✅ Python installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Python not found. Please install: https://python.org/")
            return False
        
        # Check AWS credentials
        try:
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            print(f"✅ AWS credentials configured (Account: {identity['Account']})")
        except Exception as e:
            print(f"❌ AWS credentials not configured: {e}")
            return False
        
        return True
    
    def bootstrap_cdk(self):
        """Bootstrap CDK if needed."""
        print("🚀 Bootstrapping CDK...")
        
        try:
            subprocess.run([
                'cdk', 'bootstrap', 
                f'aws://{self.account_id}/{self.region}'
            ], check=True, cwd='infrastructure')
            print("✅ CDK bootstrapped successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ CDK bootstrap failed: {e}")
            return False
        
        return True
    
    def install_dependencies(self):
        """Install all dependencies."""
        print("📦 Installing dependencies...")
        
        # Install Python dependencies
        try:
            subprocess.run(['pip', 'install', '-r', 'requirements.txt'], check=True)
            print("✅ Python dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Python dependencies installation failed: {e}")
            return False
        
        # Install Node.js dependencies
        try:
            subprocess.run(['npm', 'install'], check=True, cwd='frontend')
            print("✅ Node.js dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Node.js dependencies installation failed: {e}")
            return False
        
        # Install CDK dependencies
        try:
            subprocess.run(['npm', 'install'], check=True, cwd='infrastructure')
            print("✅ CDK dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ CDK dependencies installation failed: {e}")
            return False
        
        return True
    
    def deploy_infrastructure(self):
        """Deploy AWS infrastructure."""
        print("🏗️ Deploying infrastructure...")
        
        try:
            # Deploy all stacks
            subprocess.run([
                'cdk', 'deploy', '--all', '--require-approval', 'never'
            ], check=True, cwd='infrastructure')
            print("✅ Infrastructure deployed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Infrastructure deployment failed: {e}")
            return False
        
        return True
    
    def build_frontend(self):
        """Build and deploy frontend."""
        print("🎨 Building frontend...")
        
        try:
            # Build React app
            subprocess.run(['npm', 'run', 'build'], check=True, cwd='frontend')
            print("✅ Frontend built successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Frontend build failed: {e}")
            return False
        
        return True
    
    def deploy_frontend(self):
        """Deploy frontend to S3."""
        print("🌐 Deploying frontend...")
        
        try:
            # Get S3 bucket name from CDK outputs
            bucket_name = self._get_s3_bucket_name()
            if not bucket_name:
                print("❌ Could not find S3 bucket for frontend")
                return False
            
            # Upload to S3
            subprocess.run([
                'aws', 's3', 'sync', 
                'frontend/build/', 
                f's3://{bucket_name}/',
                '--delete'
            ], check=True)
            print(f"✅ Frontend deployed to S3: {bucket_name}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Frontend deployment failed: {e}")
            return False
        
        return True
    
    def _get_s3_bucket_name(self):
        """Get S3 bucket name from CDK outputs."""
        try:
            # This would typically read from CDK outputs
            # For now, return a placeholder
            return f"{self.project_name}-frontend-{self.account_id}"
        except Exception:
            return None
    
    def run_tests(self):
        """Run test suite."""
        print("🧪 Running tests...")
        
        try:
            # Run Python tests
            subprocess.run(['python', '-m', 'pytest', 'tests/'], check=True)
            print("✅ Python tests passed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Python tests failed: {e}")
            return False
        
        try:
            # Run frontend tests
            subprocess.run(['npm', 'test', '--', '--watchAll=false'], check=True, cwd='frontend')
            print("✅ Frontend tests passed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Frontend tests failed: {e}")
            return False
        
        return True
    
    def generate_deployment_info(self):
        """Generate deployment information."""
        print("📋 Generating deployment information...")
        
        deployment_info = {
            'project_name': self.project_name,
            'aws_account_id': self.account_id,
            'aws_region': self.region,
            'deployment_timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'endpoints': {
                'api_gateway': f'https://api.{self.project_name}.com',
                'frontend': f'https://{self.project_name}.com',
                'documentation': f'https://docs.{self.project_name}.com'
            },
            'services': [
                'Amazon Bedrock (Claude-3-Sonnet)',
                'AWS Lambda (5 agent functions)',
                'Amazon S3 (data storage)',
                'Amazon DynamoDB (workflow state)',
                'Amazon API Gateway (REST API)',
                'Amazon CloudWatch (monitoring)'
            ]
        }
        
        # Save deployment info
        with open('deployment_info.json', 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        print("✅ Deployment information saved to deployment_info.json")
        return deployment_info
    
    def deploy(self):
        """Run complete deployment process."""
        print("🚀 Starting Biomerkin Hackathon Deployment")
        print("=" * 50)
        
        steps = [
            ("Checking prerequisites", self.check_prerequisites),
            ("Installing dependencies", self.install_dependencies),
            ("Bootstrapping CDK", self.bootstrap_cdk),
            ("Deploying infrastructure", self.deploy_infrastructure),
            ("Building frontend", self.build_frontend),
            ("Deploying frontend", self.deploy_frontend),
            ("Running tests", self.run_tests),
            ("Generating deployment info", self.generate_deployment_info)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if not step_func():
                print(f"❌ Deployment failed at: {step_name}")
                sys.exit(1)
        
        print("\n🎉 Deployment completed successfully!")
        print("=" * 50)
        
        # Display deployment info
        deployment_info = self.generate_deployment_info()
        print("\n📊 Deployment Summary:")
        print(f"Project: {deployment_info['project_name']}")
        print(f"Account: {deployment_info['aws_account_id']}")
        print(f"Region: {deployment_info['aws_region']}")
        print(f"Frontend: {deployment_info['endpoints']['frontend']}")
        print(f"API: {deployment_info['endpoints']['api_gateway']}")
        
        print("\n🔗 Hackathon Submission Links:")
        print(f"Live Demo: {deployment_info['endpoints']['frontend']}")
        print(f"Source Code: https://github.com/your-username/biomerkin")
        print(f"Architecture: {deployment_info['endpoints']['documentation']}")


def main():
    """Main deployment function."""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
Biomerkin Hackathon Deployment Script

Usage:
    python scripts/deploy_hackathon.py

This script will:
1. Check prerequisites (AWS CLI, CDK, Node.js, Python)
2. Install all dependencies
3. Bootstrap CDK
4. Deploy AWS infrastructure
5. Build and deploy frontend
6. Run tests
7. Generate deployment information

Prerequisites:
- AWS Account with appropriate permissions
- AWS CLI configured
- Node.js 18+
- Python 3.11+
- AWS CDK CLI

Environment Variables:
- AWS_DEFAULT_REGION: AWS region (default: us-east-1)
        """)
        return
    
    deployer = BiomerkinDeployer()
    deployer.deploy()


if __name__ == "__main__":
    main()
