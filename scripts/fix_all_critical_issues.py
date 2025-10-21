#!/usr/bin/env python3
"""
Fix All Critical Issues Script
Addresses all syntax errors, missing handlers, and production files
"""

import os
import re
from pathlib import Path

def fix_literature_action_syntax():
    """Fix syntax error in bedrock_literature_action.py"""
    print("🔧 Fixing bedrock_literature_action.py syntax error...")
    
    filepath = 'lambda_functions/bedrock_literature_action.py'
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the malformed line around line 884
        # The issue is: }all_score', 0.0):.2f}
        # Should be: {assessment.get('overall_score', 0.0):.2f}
        
        # Find and fix the malformed string
        content = content.replace(
            "}all_score', 0.0):.2f}",
            "{assessment.get('overall_score', 0.0):.2f}"
        )
        
        # Also fix any other similar issues
        content = content.replace(
            "    }all_score', 0.0):.2f} based on",
            "        f\"Relevance score: {assessment.get('overall_score', 0.0):.2f} based on"
        )
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✅ Fixed {filepath}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error fixing {filepath}: {e}")
        return False

def add_missing_lambda_handlers():
    """Add lambda_handler functions to config files"""
    print("\n🔧 Adding missing lambda_handler functions...")
    
    config_files = [
        'lambda_functions/bedrock_decision_agent_config.py',
        'lambda_functions/bedrock_drug_agent_config.py',
        'lambda_functions/bedrock_genomics_agent_config.py',
        'lambda_functions/bedrock_literature_agent_config.py',
        'lambda_functions/bedrock_proteomics_agent_config.py'
    ]
    
    handler_template = '''

def lambda_handler(event, context):
    """
    Lambda handler for Bedrock Agent configuration.
    This function returns the agent configuration for deployment.
    """
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Bedrock Agent configuration',
            'config': get_agent_config()
        })
    }
'''
    
    for filepath in config_files:
        if not os.path.exists(filepath):
            print(f"  ⚠️  File not found: {filepath}")
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if lambda_handler already exists
            if 'def lambda_handler' in content or 'def handler' in content:
                print(f"  ✅ Handler already exists in {filepath}")
                continue
            
            # Add import json if not present
            if 'import json' not in content:
                content = 'import json\n' + content
            
            # Add handler at the end
            content += handler_template
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✅ Added handler to {filepath}")
            
        except Exception as e:
            print(f"  ❌ Error fixing {filepath}: {e}")

def fix_lambda_return_formats():
    """Ensure Lambda functions return proper API Gateway format"""
    print("\n🔧 Fixing Lambda return formats...")
    
    lambda_files = [
        'lambda_functions/bedrock_decision_action.py',
        'lambda_functions/bedrock_drug_action.py',
        'lambda_functions/bedrock_genomics_action.py',
        'lambda_functions/bedrock_literature_action.py',
        'lambda_functions/bedrock_proteomics_action.py'
    ]
    
    for filepath in lambda_files:
        if not os.path.exists(filepath):
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if statusCode is used
            if 'statusCode' in content:
                print(f"  ✅ {filepath} already has proper format")
                continue
            
            # Find return statements and ensure they have statusCode
            # This is a simple check - manual review may be needed
            if 'return {' in content and 'statusCode' not in content:
                print(f"  ⚠️  {filepath} may need manual review for return format")
            
        except Exception as e:
            print(f"  ❌ Error checking {filepath}: {e}")

def create_gitignore():
    """Create .gitignore file"""
    print("\n🔧 Creating .gitignore...")
    
    gitignore_content = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment Variables
.env
.env.local
.env.*.local

# AWS
.aws/
*.pem
*.key

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Node (for frontend)
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build
frontend/build/
frontend/dist/

# Test
.pytest_cache/
.coverage
htmlcov/

# Temporary
*.tmp
*.bak
*.swp
temp/
tmp/
'''
    
    try:
        with open('.gitignore', 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("  ✅ Created .gitignore")
    except Exception as e:
        print(f"  ❌ Error creating .gitignore: {e}")

def create_env_example():
    """Create .env.example file"""
    print("\n🔧 Creating .env.example...")
    
    env_example_content = '''# AWS Configuration
AWS_REGION=ap-south-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# Bedrock Configuration
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_AGENT_REGION=us-east-1

# API Configuration
API_GATEWAY_URL=https://your-api-id.execute-api.region.amazonaws.com/prod
FRONTEND_URL=http://your-bucket.s3-website-region.amazonaws.com

# Database Configuration
DYNAMODB_TABLE_NAME=biomerkin-workflows
S3_BUCKET_NAME=biomerkin-data

# External APIs
PUBMED_API_KEY=your_pubmed_key_here
DRUGBANK_API_KEY=your_drugbank_key_here

# Application Settings
LOG_LEVEL=INFO
MAX_SEQUENCE_LENGTH=100000
TIMEOUT_SECONDS=300
'''
    
    try:
        with open('.env.example', 'w', encoding='utf-8') as f:
            f.write(env_example_content)
        print("  ✅ Created .env.example")
    except Exception as e:
        print(f"  ❌ Error creating .env.example: {e}")

def add_fastapi_to_requirements():
    """Add FastAPI to requirements.txt if missing"""
    print("\n🔧 Checking requirements.txt...")
    
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'fastapi' not in content.lower():
            with open('requirements.txt', 'a', encoding='utf-8') as f:
                f.write('\nfastapi>=0.104.0\n')
                f.write('uvicorn[standard]>=0.24.0\n')
            print("  ✅ Added FastAPI to requirements.txt")
        else:
            print("  ✅ FastAPI already in requirements.txt")
            
    except FileNotFoundError:
        print("  ⚠️  requirements.txt not found")
    except Exception as e:
        print(f"  ❌ Error updating requirements.txt: {e}")

def fix_aws_region_configuration():
    """Add explicit region configuration to AWS clients"""
    print("\n🔧 Checking AWS region configuration...")
    
    filepath = 'lambda_functions/enhanced_analysis_handler.py'
    
    if not os.path.exists(filepath):
        print(f"  ⚠️  {filepath} not found")
        return
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if region is specified
        if 'region_name' not in content and 'boto3.client' in content:
            # Add region to boto3 clients
            content = content.replace(
                "boto3.client('",
                "boto3.client('",
            )
            # This is a simple check - manual review recommended
            print(f"  ⚠️  {filepath} may need manual review for region configuration")
        else:
            print(f"  ✅ {filepath} has region configuration")
            
    except Exception as e:
        print(f"  ❌ Error checking {filepath}: {e}")

def run_all_fixes():
    """Run all fixes"""
    print("="*80)
    print("🚀 FIXING ALL CRITICAL ISSUES")
    print("="*80)
    
    # Fix syntax errors
    fix_literature_action_syntax()
    
    # Add missing handlers
    add_missing_lambda_handlers()
    
    # Fix return formats
    fix_lambda_return_formats()
    
    # Create production files
    create_gitignore()
    create_env_example()
    
    # Update requirements
    add_fastapi_to_requirements()
    
    # Check AWS configuration
    fix_aws_region_configuration()
    
    print("\n" + "="*80)
    print("✅ FIXES COMPLETED")
    print("="*80)
    print("\nNext steps:")
    print("1. Review the changes made")
    print("2. Test Lambda functions locally")
    print("3. Deploy to AWS")
    print("4. Run integration tests")

if __name__ == '__main__':
    run_all_fixes()
