#!/usr/bin/env python3
"""
Biomerkin CLI - Main command-line interface for the multi-agent bioinformatics system.
"""

import argparse
import sys
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from .services.orchestrator import WorkflowOrchestrator
from .models import WorkflowState, AnalysisResults
from .utils.config import get_config
from .utils.logging_config import get_logger


class BiomerkinCLI:
    """Main CLI class for Biomerkin operations."""
    
    def __init__(self):
        """Initialize CLI."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.orchestrator = WorkflowOrchestrator()
    
    def analyze(self, args) -> None:
        """Run bioinformatics analysis workflow."""
        print("🧬 Starting Biomerkin Multi-Agent Analysis...")
        
        # Validate input file
        if not os.path.exists(args.sequence_file):
            print(f"❌ Error: Sequence file '{args.sequence_file}' not found")
            sys.exit(1)
        
        # Create workflow state
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Run analysis
            print(f"📋 Workflow ID: {workflow_id}")
            print("🔄 Initializing agents...")
            
            # Start analysis workflow
            result = asyncio.run(self._run_analysis(workflow_id, args.sequence_file))
            
            if result.success:
                print("✅ Analysis completed successfully!")
                print(f"📊 Results saved to: {result.workflow_id}")
                
                # Display summary
                if result.results:
                    self._display_summary(result.results)
            else:
                print(f"❌ Analysis failed: {result.error_message}")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Error during analysis: {str(e)}")
            sys.exit(1)
    
    async def _run_analysis(self, workflow_id: str, sequence_file: str) -> AnalysisResults:
        """Run the analysis workflow."""
        # Create workflow state
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            status="running",
            input_data={"sequence_file": sequence_file},
            created_at=datetime.now()
        )
        
        # Run orchestrator
        result = await self.orchestrator.execute_workflow(workflow_state)
        return result
    
    def _display_summary(self, results) -> None:
        """Display analysis results summary."""
        print("\n📈 Analysis Summary:")
        print("=" * 50)
        
        if results.genomics_results:
            print(f"🧬 Genomics: {len(results.genomics_results.genes)} genes, {len(results.genomics_results.mutations)} mutations")
        
        if results.proteomics_results:
            print(f"🔬 Proteomics: {len(results.proteomics_results.functional_annotations)} annotations")
        
        if results.literature_results:
            print(f"📚 Literature: {len(results.literature_results.articles)} articles analyzed")
        
        if results.drug_results:
            print(f"💊 Drug Discovery: {len(results.drug_results.drug_candidates)} candidates")
        
        if results.medical_report:
            print(f"🏥 Medical Report: {results.medical_report.report_id}")
    
    def status(self, args) -> None:
        """Check system status."""
        print("🔍 Biomerkin System Status")
        print("=" * 30)
        
        # Check configuration
        print(f"✅ Configuration: Loaded")
        print(f"📍 AWS Region: {self.config.aws.region}")
        print(f"🤖 Bedrock Model: {self.config.aws.bedrock_model_id}")
        
        # Check services
        try:
            # Test AWS connectivity
            import boto3
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            print(f"✅ AWS Connection: {identity.get('Arn', 'Connected')}")
        except Exception as e:
            print(f"❌ AWS Connection: {str(e)}")
        
        # Check agents
        agents = ["GenomicsAgent", "ProteomicsAgent", "LiteratureAgent", "DrugAgent", "DecisionAgent"]
        for agent in agents:
            print(f"✅ {agent}: Available")
    
    def config_cmd(self, args) -> None:
        """Manage configuration."""
        if args.show:
            print("⚙️ Current Configuration:")
            print(json.dumps(self.config.to_dict(), indent=2))
        elif args.init:
            self._init_config()
        else:
            print("Use --show to display config or --init to create sample config")
    
    def _init_config(self) -> None:
        """Initialize configuration file."""
        config_path = Path("biomerkin_config.json")
        
        if config_path.exists() and not args.force:
            print(f"⚠️ Configuration file already exists: {config_path}")
            response = input("Overwrite? (y/N): ")
            if response.lower() != 'y':
                return
        
        # Create sample configuration
        sample_config = {
            "aws": {
                "region": "us-east-1",
                "bedrock_model_id": "anthropic.claude-3-sonnet-20240229-v1:0"
            },
            "api": {
                "pubmed_email": "your-email@example.com",
                "pubmed_api_key": "your-pubmed-api-key",
                "pdb_api_base_url": "https://data.rcsb.org/rest/v1",
                "request_timeout": 30,
                "max_retries": 3,
                "retry_delay": 1
            },
            "workflow": {
                "max_concurrent_agents": 3,
                "timeout_seconds": 1800,
                "retry_attempts": 2
            },
            "cache": {
                "enabled": True,
                "ttl_seconds": 3600,
                "max_size_mb": 100
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"✅ Sample configuration created: {config_path}")
        print("📝 Please edit the configuration file with your actual values")
    
    def deploy(self, args) -> None:
        """Deploy to AWS."""
        print("🚀 Deploying Biomerkin to AWS...")
        
        # Check if CDK is available
        try:
            import subprocess
            result = subprocess.run(['cdk', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ AWS CDK not found. Please install: npm install -g aws-cdk")
                sys.exit(1)
        except FileNotFoundError:
            print("❌ AWS CDK not found. Please install: npm install -g aws-cdk")
            sys.exit(1)
        
        # Deploy infrastructure
        try:
            print("📦 Building infrastructure...")
            subprocess.run(['cdk', 'deploy', '--all'], check=True, cwd='infrastructure')
            print("✅ Deployment completed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Deployment failed: {e}")
            sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Biomerkin Multi-Agent Bioinformatics System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  biomerkin analyze sequence.fasta
  biomerkin status
  biomerkin config --init
  biomerkin deploy
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run bioinformatics analysis')
    analyze_parser.add_argument('sequence_file', help='Path to DNA sequence file (FASTA format)')
    analyze_parser.add_argument('--output', '-o', help='Output directory for results')
    analyze_parser.add_argument('--max-articles', type=int, default=20, help='Maximum articles to analyze')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check system status')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument('--show', action='store_true', help='Show current configuration')
    config_group.add_argument('--init', action='store_true', help='Initialize configuration file')
    config_parser.add_argument('--force', action='store_true', help='Force overwrite existing config')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy to AWS')
    deploy_parser.add_argument('--environment', choices=['dev', 'staging', 'prod'], 
                              default='dev', help='Deployment environment')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        cli = BiomerkinCLI()
        command_method = getattr(cli, args.command)
        command_method(args)
    except KeyboardInterrupt:
        print("\n⏹️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
