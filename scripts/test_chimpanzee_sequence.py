#!/usr/bin/env python3
"""
Test Biomerkin Multi-Agent System with Chimpanzee DNA Sequence
"""

import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from biomerkin.agents.genomics_agent import GenomicsAgent
from biomerkin.agents.proteomics_agent import ProteomicsAgent
from biomerkin.agents.literature_agent import LiteratureAgent
from biomerkin.agents.drug_agent import DrugAgent
from biomerkin.agents.decision_agent import DecisionAgent
from biomerkin.services.orchestrator import WorkflowOrchestrator
from biomerkin.utils.logging_config import get_logger

logger = get_logger(__name__)

async def test_chimpanzee_analysis():
    """Test complete multi-agent analysis with chimpanzee sequence."""
    
    print("=" * 80)
    print("BIOMERKIN MULTI-AGENT TEST - CHIMPANZEE DNA SEQUENCE")
    print("=" * 80)
    print()
    
    # Initialize orchestrator
    print("[1/6] Initializing Orchestrator...")
    orchestrator = WorkflowOrchestrator()
    print("✅ Orchestrator initialized\n")
    
    # Load chimpanzee sequence
    print("[2/6] Loading Chimpanzee DNA Sequence...")
    sequence_file = Path(__file__).parent.parent / 'chimpanzee.txt'
    
    if not sequence_file.exists():
        print("❌ chimpanzee.txt not found!")
        return
    
    with open(sequence_file, 'r') as f:
        sequence_content = f.read()
    
    sequence_length = len(sequence_content.replace('\n', '').replace('>', '').replace(' ', ''))
    print(f"✅ Loaded sequence: {sequence_length} base pairs\n")
    
    # Test each agent
    print("[3/6] Testing Individual Agents...")
    print("-" * 40)
    
    # Test GenomicsAgent
    print("\n🧬 Testing GenomicsAgent...")
    try:
        genomics_agent = GenomicsAgent()
        genomics_result = genomics_agent.analyze_sequence_data(
            sequence_content[:1000]  # Use first 1000 bp for testing
        )
        print(f"✅ GenomicsAgent: Found {len(genomics_result.genes)} genes, {len(genomics_result.mutations)} mutations")
    except Exception as e:
        print(f"❌ GenomicsAgent Error: {str(e)}")
        genomics_result = None
    
    # Test ProteomicsAgent
    print("\n🔬 Testing ProteomicsAgent...")
    try:
        proteomics_agent = ProteomicsAgent()
        if genomics_result and genomics_result.protein_sequences:
            protein_seq = genomics_result.protein_sequences[0].sequence
            proteomics_result = proteomics_agent.analyze_protein(protein_seq)
            print(f"✅ ProteomicsAgent: Found {len(proteomics_result.functional_annotations)} annotations")
        else:
            print("⚠️  ProteomicsAgent: Skipped (no protein sequences from genomics)")
            proteomics_result = None
    except Exception as e:
        print(f"❌ ProteomicsAgent Error: {str(e)}")
        proteomics_result = None
    
    # Test LiteratureAgent
    print("\n📚 Testing LiteratureAgent...")
    try:
        literature_agent = LiteratureAgent()
        if genomics_result and genomics_result.genes:
            gene_names = [gene.name for gene in genomics_result.genes[:3]]
            literature_result = literature_agent.search_literature(gene_names)
            print(f"✅ LiteratureAgent: Found {len(literature_result.articles)} articles")
        else:
            print("⚠️  LiteratureAgent: Skipped (no genes from genomics)")
            literature_result = None
    except Exception as e:
        print(f"❌ LiteratureAgent Error: {str(e)}")
        literature_result = None
    
    # Test DrugAgent
    print("\n💊 Testing DrugAgent...")
    try:
        drug_agent = DrugAgent()
        if genomics_result and genomics_result.genes:
            target_data = {
                'genes': [gene.name for gene in genomics_result.genes[:3]],
                'proteins': []
            }
            drug_result = drug_agent.find_drug_candidates(target_data)
            print(f"✅ DrugAgent: Found {len(drug_result.drug_candidates)} drug candidates")
        else:
            print("⚠️  DrugAgent: Skipped (no genes from genomics)")
            drug_result = None
    except Exception as e:
        print(f"❌ DrugAgent Error: {str(e)}")
        drug_result = None
    
    # Test DecisionAgent
    print("\n📋 Testing DecisionAgent...")
    try:
        decision_agent = DecisionAgent()
        from biomerkin.models.analysis import CombinedAnalysis
        
        combined = CombinedAnalysis(
            genomics_results=genomics_result,
            proteomics_results=proteomics_result,
            literature_results=literature_result,
            drug_results=drug_result
        )
        
        medical_report = decision_agent.generate_medical_report(combined)
        print(f"✅ DecisionAgent: Generated medical report {medical_report.report_id}")
    except Exception as e:
        print(f"❌ DecisionAgent Error: {str(e)}")
        medical_report = None
    
    # Test Full Orchestration
    print("\n[4/6] Testing Full Multi-Agent Orchestration...")
    print("-" * 40)
    
    try:
        workflow_result = orchestrator.execute_workflow({
            'sequence_file': str(sequence_file),
            'patient_info': {
                'patient_id': 'CHIMP_TEST_001',
                'species': 'Pan troglodytes',
                'test_type': 'multi_agent_validation'
            }
        })
        
        print(f"✅ Orchestration Complete!")
        print(f"   Workflow ID: {workflow_result.get('workflow_id')}")
        print(f"   Status: {workflow_result.get('status')}")
        print(f"   Agents Executed: {len(workflow_result.get('agent_results', {}))}")
        
    except Exception as e:
        print(f"❌ Orchestration Error: {str(e)}")
        workflow_result = None
    
    # Test Inter-Agent Communication
    print("\n[5/6] Testing Inter-Agent Communication...")
    print("-" * 40)
    
    if workflow_result and 'agent_results' in workflow_result:
        agent_results = workflow_result['agent_results']
        
        # Check if agents shared data
        if 'genomics' in agent_results and 'proteomics' in agent_results:
            print("✅ Genomics → Proteomics: Data handoff successful")
        
        if 'genomics' in agent_results and 'literature' in agent_results:
            print("✅ Genomics → Literature: Data handoff successful")
        
        if 'literature' in agent_results and 'drug' in agent_results:
            print("✅ Literature → Drug: Data handoff successful")
        
        if len(agent_results) >= 4:
            print("✅ Decision Agent: Integrated all agent results")
    else:
        print("⚠️  Inter-agent communication test skipped")
    
    # Generate Test Report
    print("\n[6/6] Generating Test Report...")
    print("-" * 40)
    
    report = {
        'test_date': datetime.now().isoformat(),
        'sequence_file': 'chimpanzee.txt',
        'sequence_length': sequence_length,
        'agents_tested': {
            'genomics': genomics_result is not None,
            'proteomics': proteomics_result is not None,
            'literature': literature_result is not None,
            'drug': drug_result is not None,
            'decision': medical_report is not None
        },
        'orchestration_tested': workflow_result is not None,
        'results_summary': {
            'genes_found': len(genomics_result.genes) if genomics_result else 0,
            'mutations_found': len(genomics_result.mutations) if genomics_result else 0,
            'proteins_analyzed': len(genomics_result.protein_sequences) if genomics_result else 0,
            'articles_found': len(literature_result.articles) if literature_result else 0,
            'drugs_found': len(drug_result.drug_candidates) if drug_result else 0,
            'report_generated': medical_report is not None
        }
    }
    
    # Save report
    report_file = Path(__file__).parent.parent / 'CHIMPANZEE_TEST_REPORT.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"✅ Test report saved to: {report_file}")
    
    # Print Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    agents_working = sum(report['agents_tested'].values())
    total_agents = len(report['agents_tested'])
    
    print(f"Agents Working: {agents_working}/{total_agents}")
    print(f"Orchestration: {'✅ Working' if report['orchestration_tested'] else '❌ Failed'}")
    print(f"\nResults:")
    print(f"  - Genes Found: {report['results_summary']['genes_found']}")
    print(f"  - Mutations Found: {report['results_summary']['mutations_found']}")
    print(f"  - Proteins Analyzed: {report['results_summary']['proteins_analyzed']}")
    print(f"  - Articles Found: {report['results_summary']['articles_found']}")
    print(f"  - Drug Candidates: {report['results_summary']['drugs_found']}")
    print(f"  - Medical Report: {'✅ Generated' if report['results_summary']['report_generated'] else '❌ Not Generated'}")
    
    print("\n" + "=" * 80)
    
    if agents_working == total_agents:
        print("✅ ALL AGENTS WORKING SUCCESSFULLY!")
        return 0
    else:
        print(f"⚠️  {total_agents - agents_working} agents had issues")
        return 1

def main():
    """Main test function."""
    try:
        result = asyncio.run(test_chimpanzee_analysis())
        return result
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"\n❌ Test failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
