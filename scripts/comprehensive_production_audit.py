#!/usr/bin/env python3
"""
Comprehensive Production Audit Script for Biomerkin
Checks for errors, bugs, AWS integration, and production readiness
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import re

class ProductionAudit:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.successes = []
        self.aws_checks = []
        self.security_issues = []
        
    def log_issue(self, category: str, severity: str, message: str, file: str = None):
        """Log an issue found during audit"""
        issue = {
            'category': category,
            'severity': severity,
            'message': message,
            'file': file
        }
        if severity == 'CRITICAL':
            self.issues.append(issue)
        elif severity == 'WARNING':
            self.warnings.append(issue)
        else:
            self.successes.append(issue)
    
    def check_file_exists(self, filepath: str) -> bool:
        """Check if a file exists"""
        return Path(filepath).exists()
    
    def check_python_syntax(self, filepath: str) -> bool:
        """Check Python file for syntax errors"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                compile(f.read(), filepath, 'exec')
            return True
        except SyntaxError as e:
            self.log_issue('SYNTAX', 'CRITICAL', f'Syntax error: {e}', filepath)
            return False
        except Exception as e:
            self.log_issue('SYNTAX', 'WARNING', f'Could not parse: {e}', filepath)
            return False
    
    def check_imports(self, filepath: str) -> List[str]:
        """Extract and check imports from Python file"""
        missing_imports = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find all imports
            import_pattern = r'^(?:from\s+(\S+)\s+import|import\s+(\S+))'
            imports = re.findall(import_pattern, content, re.MULTILINE)
            
            # Check for AWS SDK
            has_boto3 = 'boto3' in content
            if 'bedrock' in content.lower() and not has_boto3:
                self.log_issue('IMPORTS', 'WARNING', 
                             'Uses Bedrock but boto3 not imported', filepath)
                
        except Exception as e:
            self.log_issue('IMPORTS', 'WARNING', f'Could not check imports: {e}', filepath)
        
        return missing_imports
    
    def check_aws_configuration(self, filepath: str):
        """Check for proper AWS configuration"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for hardcoded credentials (security issue)
            if re.search(r'aws_access_key_id\s*=\s*["\']AKIA', content):
                self.log_issue('SECURITY', 'CRITICAL',
                             'Hardcoded AWS credentials found!', filepath)
                self.security_issues.append(filepath)
            
            # Check for region configuration
            if 'boto3.client' in content or 'boto3.resource' in content:
                if 'region_name' not in content and 'AWS_REGION' not in content:
                    self.log_issue('AWS', 'WARNING',
                                 'AWS client without explicit region', filepath)
            
            # Check for proper error handling with AWS calls
            if 'boto3' in content:
                if 'ClientError' not in content and 'except' not in content:
                    self.log_issue('AWS', 'WARNING',
                                 'AWS calls without error handling', filepath)
                    
        except Exception as e:
            self.log_issue('AWS', 'WARNING', f'Could not check AWS config: {e}', filepath)
    
    def check_environment_variables(self, filepath: str):
        """Check for proper environment variable usage"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for os.environ usage without defaults
            env_pattern = r'os\.environ\[(["\'])([^"\']+)\1\]'
            env_vars = re.findall(env_pattern, content)
            
            for _, var_name in env_vars:
                # Check if there's a .get() alternative nearby
                if f'os.environ.get(\'{var_name}\'' not in content and \
                   f'os.environ.get("{var_name}"' not in content:
                    self.log_issue('CONFIG', 'WARNING',
                                 f'Environment variable {var_name} without default', filepath)
                    
        except Exception as e:
            pass
    
    def check_lambda_handler(self, filepath: str):
        """Check Lambda function structure"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for handler function
            if 'def lambda_handler' not in content and 'def handler' not in content:
                self.log_issue('LAMBDA', 'CRITICAL',
                             'No lambda_handler function found', filepath)
            
            # Check for proper return format
            if 'lambda_handler' in content or 'handler' in content:
                if 'statusCode' not in content:
                    self.log_issue('LAMBDA', 'WARNING',
                                 'Lambda handler may not return proper API Gateway format', filepath)
                    
        except Exception as e:
            pass
    
    def check_frontend_config(self):
        """Check frontend configuration"""
        print("\n🔍 Checking Frontend Configuration...")
        
        # Check package.json
        if self.check_file_exists('frontend/package.json'):
            try:
                with open('frontend/package.json', 'r') as f:
                    package = json.load(f)
                
                # Check for required dependencies
                deps = package.get('dependencies', {})
                required = ['react', 'axios']
                for dep in required:
                    if dep not in deps:
                        self.log_issue('FRONTEND', 'CRITICAL',
                                     f'Missing required dependency: {dep}', 'package.json')
                
                self.log_issue('FRONTEND', 'SUCCESS', 'package.json is valid', 'package.json')
            except Exception as e:
                self.log_issue('FRONTEND', 'CRITICAL', f'Invalid package.json: {e}', 'package.json')
        else:
            self.log_issue('FRONTEND', 'CRITICAL', 'package.json not found', 'frontend/')
        
        # Check API service configuration
        if self.check_file_exists('frontend/src/services/api.js'):
            with open('frontend/src/services/api.js', 'r') as f:
                content = f.read()
            
            # Check for environment variable usage
            if 'process.env.REACT_APP_API_URL' in content:
                self.log_issue('FRONTEND', 'SUCCESS',
                             'API URL uses environment variable', 'api.js')
            else:
                self.log_issue('FRONTEND', 'WARNING',
                             'API URL may be hardcoded', 'api.js')
    
    def check_aws_resources(self):
        """Check if AWS resources are properly configured"""
        print("\n🔍 Checking AWS Resource Configuration...")
        
        # Check for deployment scripts
        deployment_scripts = [
            'scripts/deploy_biomerkin_to_aws.py',
            'scripts/deploy_bedrock_agents.py',
            'scripts/deploy_full_bedrock_integration.py'
        ]
        
        for script in deployment_scripts:
            if self.check_file_exists(script):
                self.log_issue('AWS', 'SUCCESS', f'Deployment script exists', script)
                self.check_python_syntax(script)
                self.check_aws_configuration(script)
            else:
                self.log_issue('AWS', 'WARNING', f'Deployment script missing', script)
    
    def check_agent_implementations(self):
        """Check all agent implementations"""
        print("\n🔍 Checking Agent Implementations...")
        
        agents = [
            'biomerkin/agents/genomics_agent.py',
            'biomerkin/agents/proteomics_agent.py',
            'biomerkin/agents/literature_agent.py',
            'biomerkin/agents/drug_agent.py',
            'biomerkin/agents/decision_agent.py'
        ]
        
        for agent in agents:
            if self.check_file_exists(agent):
                self.log_issue('AGENTS', 'SUCCESS', f'Agent exists', agent)
                self.check_python_syntax(agent)
                self.check_imports(agent)
                self.check_aws_configuration(agent)
                self.check_environment_variables(agent)
            else:
                self.log_issue('AGENTS', 'CRITICAL', f'Agent missing', agent)
    
    def check_lambda_functions(self):
        """Check Lambda function implementations"""
        print("\n🔍 Checking Lambda Functions...")
        
        lambda_dir = Path('lambda_functions')
        if lambda_dir.exists():
            for lambda_file in lambda_dir.glob('*.py'):
                if lambda_file.name != '__init__.py':
                    filepath = str(lambda_file)
                    self.check_python_syntax(filepath)
                    self.check_lambda_handler(filepath)
                    self.check_aws_configuration(filepath)
                    self.check_environment_variables(filepath)
        else:
            self.log_issue('LAMBDA', 'CRITICAL', 'lambda_functions directory not found', 'lambda_functions/')
    
    def check_requirements(self):
        """Check requirements.txt for completeness"""
        print("\n🔍 Checking Requirements...")
        
        if self.check_file_exists('requirements.txt'):
            with open('requirements.txt', 'r') as f:
                requirements = f.read()
            
            essential_packages = [
                'boto3',
                'biopython',
                'requests',
                'fastapi'
            ]
            
            for package in essential_packages:
                if package.lower() in requirements.lower():
                    self.log_issue('REQUIREMENTS', 'SUCCESS',
                                 f'{package} is included', 'requirements.txt')
                else:
                    self.log_issue('REQUIREMENTS', 'WARNING',
                                 f'{package} may be missing', 'requirements.txt')
        else:
            self.log_issue('REQUIREMENTS', 'CRITICAL',
                         'requirements.txt not found', 'requirements.txt')
    
    def check_production_readiness(self):
        """Check overall production readiness"""
        print("\n🔍 Checking Production Readiness...")
        
        # Check for .env.example
        if self.check_file_exists('.env.example'):
            self.log_issue('PRODUCTION', 'SUCCESS', '.env.example exists', '.env.example')
        else:
            self.log_issue('PRODUCTION', 'WARNING', '.env.example missing', '.env.example')
        
        # Check for README
        if self.check_file_exists('README.md'):
            self.log_issue('PRODUCTION', 'SUCCESS', 'README.md exists', 'README.md')
        else:
            self.log_issue('PRODUCTION', 'WARNING', 'README.md missing', 'README.md')
        
        # Check for .gitignore
        if self.check_file_exists('.gitignore'):
            with open('.gitignore', 'r') as f:
                gitignore = f.read()
            
            if '.env' in gitignore:
                self.log_issue('PRODUCTION', 'SUCCESS', '.env in .gitignore', '.gitignore')
            else:
                self.log_issue('PRODUCTION', 'CRITICAL', '.env not in .gitignore', '.gitignore')
        else:
            self.log_issue('PRODUCTION', 'CRITICAL', '.gitignore missing', '.gitignore')
    
    def generate_report(self):
        """Generate comprehensive audit report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE PRODUCTION AUDIT REPORT")
        print("="*80)
        
        # Critical Issues
        if self.issues:
            print(f"\n🚨 CRITICAL ISSUES ({len(self.issues)}):")
            print("-" * 80)
            for issue in self.issues:
                print(f"  [{issue['category']}] {issue['message']}")
                if issue['file']:
                    print(f"    File: {issue['file']}")
        else:
            print("\n✅ No critical issues found!")
        
        # Warnings
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            print("-" * 80)
            for warning in self.warnings:
                print(f"  [{warning['category']}] {warning['message']}")
                if warning['file']:
                    print(f"    File: {warning['file']}")
        
        # Security Issues
        if self.security_issues:
            print(f"\n🔒 SECURITY ISSUES ({len(self.security_issues)}):")
            print("-" * 80)
            for file in self.security_issues:
                print(f"  ⚠️  {file}")
        
        # Successes
        print(f"\n✅ SUCCESSFUL CHECKS ({len(self.successes)}):")
        print("-" * 80)
        categories = {}
        for success in self.successes:
            cat = success['category']
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        for cat, count in categories.items():
            print(f"  {cat}: {count} checks passed")
        
        # Summary
        print("\n" + "="*80)
        print("📈 SUMMARY")
        print("="*80)
        print(f"  Critical Issues: {len(self.issues)}")
        print(f"  Warnings: {len(self.warnings)}")
        print(f"  Successful Checks: {len(self.successes)}")
        print(f"  Security Issues: {len(self.security_issues)}")
        
        # Production Readiness Score
        total_checks = len(self.issues) + len(self.warnings) + len(self.successes)
        if total_checks > 0:
            score = (len(self.successes) / total_checks) * 100
            print(f"\n  Production Readiness Score: {score:.1f}%")
            
            if score >= 90:
                print("  Status: ✅ READY FOR PRODUCTION")
            elif score >= 70:
                print("  Status: ⚠️  NEEDS MINOR FIXES")
            else:
                print("  Status: 🚨 NEEDS MAJOR FIXES")
        
        print("\n" + "="*80)
        
        # Save report to file
        self.save_report()
    
    def save_report(self):
        """Save audit report to file"""
        report = {
            'critical_issues': self.issues,
            'warnings': self.warnings,
            'successes': self.successes,
            'security_issues': self.security_issues,
            'summary': {
                'total_critical': len(self.issues),
                'total_warnings': len(self.warnings),
                'total_successes': len(self.successes),
                'total_security': len(self.security_issues)
            }
        }
        
        with open('PRODUCTION_AUDIT_REPORT.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n📄 Detailed report saved to: PRODUCTION_AUDIT_REPORT.json")
    
    def run_audit(self):
        """Run complete audit"""
        print("🚀 Starting Comprehensive Production Audit...")
        print("="*80)
        
        self.check_requirements()
        self.check_agent_implementations()
        self.check_lambda_functions()
        self.check_aws_resources()
        self.check_frontend_config()
        self.check_production_readiness()
        
        self.generate_report()

if __name__ == '__main__':
    auditor = ProductionAudit()
    auditor.run_audit()
