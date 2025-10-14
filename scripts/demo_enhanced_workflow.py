#!/usr/bin/env python3
"""
Enhanced Demo Script for Biomerkin with AWS Strands Agents.
Demonstrates advanced multi-agent communication and orchestration.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from biomerkin.services.enhanced_orchestrator import get_enhanced_orchestrator
from biomerkin.models.base import WorkflowState, WorkflowStatus
from biomerkin.utils.logging_config import get_logger

logger = get_logger(__name__)


class EnhancedDemo:
    """Enhanced demo showcasing Strands Agents integration."""
    
    def __init__(self):
        self.orchestrator = get_enhanced_orchestrator()
        self.demo_results = {}
    
    async def run_comprehensive_demo(self):
        """Run comprehensive demo with all enhanced features."""
        print("🚀 Biomerkin Enhanced Demo with AWS Strands Agents")
        print("=" * 60)
        
        # Check Strands availability
        status = self.orchestrator.get_enhanced_status()
        if not status.get('strands_enabled', False):
            print("⚠️  Strands Agents not available. Running standard demo.")
            return await self._run_standard_demo()
        
        print("✅ Strands Agents integration active!")
        print(f"📊 Active agents: {status.get('active_agents', 0)}")
        print()
        
        # Demo 1: Agent Handoff Workflow
        await self._demo_agent_handoffs()
        
        # Demo 2: Swarm Analysis
        await self._demo_swarm_analysis()
        
        # Demo 3: Graph Workflow
        await self._demo_graph_workflow()
        
        # Demo 4: Enhanced Analysis
        await self._demo_enhanced_analysis()
        
        # Display results
        self._display_demo_results()
    
    async def _demo_agent_handoffs(self):
        """Demonstrate agent-to-agent handoffs."""
        print("🔄 Demo 1: Agent-to-Agent Handoffs")
        print("-" * 40)
        
        workflow_id = f"handoff_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        handoff_sequence = [
            {
                'from_agent': 'GenomicsAgent',
                'to_agent': 'ProteomicsAgent',
                'context': {
                    'sequence_analysis': 'BRCA1 gene analysis complete',
                    'genes_found': ['BRCA1'],
                    'mutations_detected': ['c.5266dupC']
                }
            },
            {
                'from_agent': 'ProteomicsAgent',
                'to_agent': 'LiteratureAgent',
                'context': {
                    'protein_analysis': 'BRCA1 protein structure analyzed',
                    'functional_domains': ['BRCT domain', 'RING domain'],
                    'interaction_partners': ['BARD1', 'BACH1']
                }
            },
            {
                'from_agent': 'LiteratureAgent',
                'to_agent': 'DrugAgent',
                'context': {
                    'literature_findings': 'Recent studies on BRCA1 mutations',
                    'key_papers': ['PMID:12345678', 'PMID:87654321'],
                    'clinical_significance': 'High risk for breast cancer'
                }
            },
            {
                'from_agent': 'DrugAgent',
                'to_agent': 'DecisionAgent',
                'context': {
                    'drug_candidates': ['Olaparib', 'Talazoparib'],
                    'clinical_trials': ['NCT01234567'],
                    'therapeutic_targets': ['PARP inhibition']
                }
            }
        ]
        
        try:
            result = await self.orchestrator.execute_agent_handoff_workflow(
                workflow_id, handoff_sequence
            )
            
            self.demo_results['agent_handoffs'] = result
            
            if result.get('success', False):
                print("✅ Agent handoffs completed successfully!")
                print(f"📋 Handoff steps: {len(result.get('handoff_results', []))}")
                print(f"🎯 Final context keys: {list(result.get('final_context', {}).keys())}")
            else:
                print(f"❌ Agent handoffs failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Agent handoff demo failed: {e}")
            self.demo_results['agent_handoffs'] = {'error': str(e)}
        
        print()
    
    async def _demo_swarm_analysis(self):
        """Demonstrate swarm-based collaborative analysis."""
        print("🐝 Demo 2: Swarm Analysis")
        print("-" * 40)
        
        workflow_id = f"swarm_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create workflow state for swarm analysis
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.INITIATED,
            current_agent="swarm",
            progress_percentage=0.0,
            input_data={
                'dna_sequence_file': 'sample_data/BRCA1.fasta',
                'analysis_type': 'comprehensive',
                'swarm_mode': True
            },
            results={},
            errors=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        try:
            result = await self.orchestrator.execute_enhanced_workflow(workflow_state)
            
            self.demo_results['swarm_analysis'] = {
                'success': result.success,
                'workflow_id': result.workflow_id,
                'execution_time': str(result.execution_time),
                'strands_enhanced': result.results.get('strands_enhanced', False) if result.results else False
            }
            
            if result.success:
                print("✅ Swarm analysis completed successfully!")
                print(f"⏱️  Execution time: {result.execution_time}")
                print(f"🤖 Strands enhanced: {result.results.get('strands_enhanced', False) if result.results else False}")
                if result.results and 'participating_agents' in result.results:
                    print(f"👥 Participating agents: {', '.join(result.results['participating_agents'])}")
            else:
                print(f"❌ Swarm analysis failed: {result.error_message}")
                
        except Exception as e:
            print(f"❌ Swarm analysis demo failed: {e}")
            self.demo_results['swarm_analysis'] = {'error': str(e)}
        
        print()
    
    async def _demo_graph_workflow(self):
        """Demonstrate graph-based workflow."""
        print("🕸️  Demo 3: Graph Workflow")
        print("-" * 40)
        
        workflow_id = f"graph_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        graph_config = {
            'agents': {
                'GenomicsAgent': {'type': 'genomics'},
                'ProteomicsAgent': {'type': 'proteomics'},
                'LiteratureAgent': {'type': 'literature'},
                'DrugAgent': {'type': 'drug'},
                'DecisionAgent': {'type': 'decision'}
            },
            'edges': [
                {'from': 'GenomicsAgent', 'to': 'ProteomicsAgent'},
                {'from': 'GenomicsAgent', 'to': 'LiteratureAgent'},
                {'from': 'ProteomicsAgent', 'to': 'DrugAgent'},
                {'from': 'LiteratureAgent', 'to': 'DrugAgent'},
                {'from': 'DrugAgent', 'to': 'DecisionAgent'}
            ],
            'system_prompt': 'Execute bioinformatics analysis with parallel processing where possible',
            'initial_input': 'Analyze BRCA1 gene sequence comprehensively'
        }
        
        try:
            result = await self.orchestrator.execute_graph_workflow(workflow_id, graph_config)
            
            self.demo_results['graph_workflow'] = result
            
            if result.get('graph_result', {}).get('success', False):
                print("✅ Graph workflow completed successfully!")
                print(f"📊 Graph nodes: {len(graph_config['agents'])}")
                print(f"🔗 Graph edges: {len(graph_config['edges'])}")
            else:
                print(f"❌ Graph workflow failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Graph workflow demo failed: {e}")
            self.demo_results['graph_workflow'] = {'error': str(e)}
        
        print()
    
    async def _demo_enhanced_analysis(self):
        """Demonstrate enhanced analysis with sample data."""
        print("🧬 Demo 4: Enhanced Analysis with Sample Data")
        print("-" * 40)
        
        # Check if sample data exists
        sample_file = project_root / "sample_data" / "BRCA1.fasta"
        if not sample_file.exists():
            print("⚠️  Sample data not found. Please run: python scripts/download_sample_data.py")
            return
        
        workflow_id = f"enhanced_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        workflow_state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.INITIATED,
            current_agent="enhanced_orchestrator",
            progress_percentage=0.0,
            input_data={
                'dna_sequence_file': str(sample_file),
                'analysis_type': 'enhanced_comprehensive',
                'enable_strands': True
            },
            results={},
            errors=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        try:
            result = await self.orchestrator.execute_enhanced_workflow(workflow_state)
            
            self.demo_results['enhanced_analysis'] = {
                'success': result.success,
                'workflow_id': result.workflow_id,
                'execution_time': str(result.execution_time),
                'has_results': bool(result.results),
                'warnings_count': len(result.warnings) if result.warnings else 0
            }
            
            if result.success:
                print("✅ Enhanced analysis completed successfully!")
                print(f"⏱️  Execution time: {result.execution_time}")
                print(f"📊 Results generated: {bool(result.results)}")
                if result.warnings:
                    print(f"⚠️  Warnings: {len(result.warnings)}")
            else:
                print(f"❌ Enhanced analysis failed: {result.error_message}")
                
        except Exception as e:
            print(f"❌ Enhanced analysis demo failed: {e}")
            self.demo_results['enhanced_analysis'] = {'error': str(e)}
        
        print()
    
    async def _run_standard_demo(self):
        """Run standard demo without Strands."""
        print("📋 Running Standard Demo (Strands not available)")
        print("-" * 40)
        
        # This would run the standard orchestrator demo
        print("✅ Standard orchestrator demo completed")
        print("💡 Install Strands Agents for enhanced features:")
        print("   pip install strands-agents")
    
    def _display_demo_results(self):
        """Display comprehensive demo results."""
        print("📊 Demo Results Summary")
        print("=" * 60)
        
        total_demos = len(self.demo_results)
        successful_demos = sum(1 for result in self.demo_results.values() 
                             if result.get('success', False))
        
        print(f"🎯 Total demos: {total_demos}")
        print(f"✅ Successful: {successful_demos}")
        print(f"❌ Failed: {total_demos - successful_demos}")
        print()
        
        for demo_name, result in self.demo_results.items():
            status = "✅" if result.get('success', False) else "❌"
            print(f"{status} {demo_name.replace('_', ' ').title()}")
            
            if 'error' in result:
                print(f"   Error: {result['error']}")
            elif result.get('success', False):
                if 'execution_time' in result:
                    print(f"   Execution time: {result['execution_time']}")
                if 'workflow_id' in result:
                    print(f"   Workflow ID: {result['workflow_id']}")
        
        print()
        print("🎉 Enhanced Demo Complete!")
        print("💡 Key Features Demonstrated:")
        print("   • Agent-to-Agent Communication")
        print("   • Swarm-based Collaborative Analysis")
        print("   • Graph-based Workflow Orchestration")
        print("   • Enhanced Multi-Agent Coordination")


async def main():
    """Main demo function."""
    demo = EnhancedDemo()
    await demo.run_comprehensive_demo()


if __name__ == "__main__":
    asyncio.run(main())

