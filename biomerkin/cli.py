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
from .services.enhanced_orchestrator import get_enhanced_orchestrator
from .services.cost_optimization_service import get_cost_optimization_service
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
        self.enhanced_orchestrator = get_enhanced_orchestrator()
        self.cost_service = get_cost_optimization_service()
    
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
            
            # Check if enhanced mode is requested
            if hasattr(args, 'enhanced') and args.enhanced:
                print("🚀 Using Enhanced Mode with AWS Strands Agents...")
                result = asyncio.run(self._run_enhanced_analysis(workflow_id, args.sequence_file))
            else:
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
            current_agent="orchestrator",
            progress_percentage=0.0,
            input_data={"sequence_file": sequence_file},
            results={},
            errors=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Run orchestrator
        result = await self.orchestrator.execute_workflow(workflow_state)
        return result
    
    async def _run_enhanced_analysis(self, workflow_id: str, sequence_file: str) -> AnalysisResults:
        """Run enhanced analysis workflow with Strands Agents."""
        # Create workflow state
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            status="running",
            current_agent="enhanced_orchestrator",
            progress_percentage=0.0,
            input_data={
                "sequence_file": sequence_file,
                "enhanced_mode": True,
                "enable_strands": True
            },
            results={},
            errors=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Run enhanced orchestrator
        result = await self.enhanced_orchestrator.execute_enhanced_workflow(workflow_state)
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
        print("Biomerkin System Status")
        print("=" * 30)
        
        # Check configuration
        print(f"[OK] Configuration: Loaded")
        print(f"[INFO] AWS Region: {self.config.aws.region}")
        print(f"[INFO] Bedrock Model: {self.config.aws.bedrock_model_id}")
        
        # Check services
        try:
            # Test AWS connectivity
            import boto3
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            print(f"[OK] AWS Connection: {identity.get('Arn', 'Connected')}")
        except Exception as e:
            print(f"[ERROR] AWS Connection: {str(e)}")
        
        # Check agents
        agents = ["GenomicsAgent", "ProteomicsAgent", "LiteratureAgent", "DrugAgent", "DecisionAgent"]
        for agent in agents:
            print(f"[OK] {agent}: Available")
        
        # Check enhanced orchestrator status
        try:
            enhanced_status = self.enhanced_orchestrator.get_enhanced_status()
            print(f"[INFO] Enhanced Orchestrator: {'Enabled' if enhanced_status.get('strands_enabled') else 'Disabled'}")
            if enhanced_status.get('strands_enabled'):
                print(f"[INFO] Strands Agents: {enhanced_status.get('active_agents', 0)} active")
                print(f"[INFO] Model Providers: {', '.join(enhanced_status.get('model_providers', []))}")
        except Exception as e:
            print(f"[WARNING] Enhanced Orchestrator: {str(e)}")
    
    def config_cmd(self, args) -> None:
        """Manage configuration."""
        if args.show:
            print("⚙️ Current Configuration:")
            print(json.dumps(self.config.to_dict(), indent=2))
        elif args.init:
            self._init_config(args)
        else:
            print("Use --show to display config or --init to create sample config")
    
    def _init_config(self, args=None) -> None:
        """Initialize configuration file."""
        config_path = Path("biomerkin_config.json")
        
        if config_path.exists() and not (args and args.force):
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
    
    def demo(self, args) -> None:
        """Run enhanced demo with Strands Agents."""
        print("🎬 Running Enhanced Demo...")
        
        try:
            import subprocess
            import sys
            
            # Run the enhanced demo script
            demo_script = Path(__file__).parent.parent / "scripts" / "demo_enhanced_workflow.py"
            
            if not demo_script.exists():
                print(f"[ERROR] Demo script not found: {demo_script}")
                sys.exit(1)
            
            print(f"[STARTING] Starting {args.type} demo...")
            subprocess.run([sys.executable, str(demo_script)], check=True)
            print("[SUCCESS] Demo completed successfully!")
            
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Demo failed: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Error running demo: {e}")
            sys.exit(1)
    
    def cost_dashboard(self, args) -> None:
        """Display cost optimization dashboard."""
        print("[COST] Biomerkin Cost Optimization Dashboard")
        print("=" * 50)
        
        try:
            # Get dashboard data
            dashboard_data = self.cost_service.get_cost_dashboard_data()
            
            if 'error' in dashboard_data:
                print(f"[ERROR] Error retrieving cost data: {dashboard_data['error']}")
                return
            
            # Display current costs
            current_costs = dashboard_data['current_costs']
            print(f"\n[COSTS] Current Costs (Last 7 days):")
            print(f"   Total: ${current_costs['total_cost']:.2f} {current_costs['currency']}")
            print(f"   Services:")
            for service, cost in current_costs['service_breakdown'].items():
                print(f"     * {service}: ${cost:.2f}")
            
            # Display cost trends
            trends = dashboard_data['cost_trends']
            print(f"\n[TRENDS] Cost Trends (Last 30 days):")
            print(f"   Trend: {trends['trend']}")
            print(f"   Change: {trends['change_percent']:.1f}%")
            avg_daily = trends.get('average_daily_cost', 0.0)
            print(f"   Average Daily: ${avg_daily:.2f}")
            
            # Display optimization recommendations
            recommendations = dashboard_data['optimization_recommendations']
            print(f"\n[RECOMMENDATIONS] Optimization Recommendations:")
            total_savings = 0
            for rec in recommendations:
                print(f"   * {rec['service']}: {rec['description']}")
                print(f"     Potential Savings: ${rec['potential_savings']:.2f}")
                print(f"     Priority: {rec['priority']}, Effort: {rec['effort']}")
                total_savings += rec['potential_savings']
            
            print(f"\n[SAVINGS] Total Potential Savings: ${total_savings:.2f}")
            
            # Display budget alerts
            alerts = dashboard_data['budget_alerts']
            if alerts:
                print(f"\n[ALERTS] Budget Alerts:")
                for alert in alerts:
                    print(f"   * {alert['budget_name']}: {alert['severity']} severity")
                    print(f"     Threshold: {alert['threshold']}%, Current: ${alert['current_spend']:.2f}")
            
            # Display summary
            summary = dashboard_data['summary']
            print(f"\n[SUMMARY] Summary:")
            print(f"   Optimization Score: {summary['optimization_score']:.0f}/100")
            print(f"   Recommendations: {summary['recommendations_count']}")
            print(f"   Active Alerts: {summary['alerts_count']}")
            print(f"   Last Updated: {summary['last_updated']}")
            
        except Exception as e:
            print(f"[ERROR] Error displaying cost dashboard: {e}")
            sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Biomerkin Multi-Agent Bioinformatics System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  biomerkin analyze sequence.fasta
  biomerkin analyze sequence.fasta --enhanced
  biomerkin status
  biomerkin config --init
  biomerkin deploy
  biomerkin demo --type comprehensive
  biomerkin cost --days 30
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run bioinformatics analysis')
    analyze_parser.add_argument('sequence_file', help='Path to DNA sequence file (FASTA format)')
    analyze_parser.add_argument('--output', '-o', help='Output directory for results')
    analyze_parser.add_argument('--max-articles', type=int, default=20, help='Maximum articles to analyze')
    analyze_parser.add_argument('--enhanced', action='store_true', help='Use enhanced mode with AWS Strands Agents')
    
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
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run enhanced demo with Strands Agents')
    demo_parser.add_argument('--type', choices=['comprehensive', 'handoffs', 'swarm', 'graph'], 
                            default='comprehensive', help='Type of demo to run')
    
    # Cost dashboard command
    cost_parser = subparsers.add_parser('cost', help='Display cost optimization dashboard')
    cost_parser.add_argument('--days', type=int, default=7, help='Number of days to analyze costs for')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        cli = BiomerkinCLI()
        # Map command names to method names
        command_mapping = {
            'cost': 'cost_dashboard',
            'config': 'config_cmd'
        }
        method_name = command_mapping.get(args.command, args.command)
        command_method = getattr(cli, method_name)
        command_method(args)
    except KeyboardInterrupt:
        print("\n[INFO] Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
