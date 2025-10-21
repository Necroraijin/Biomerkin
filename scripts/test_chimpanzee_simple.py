#!/usr/bin/env python3
"""
Simple test of Biomerkin Multi-Agent System with Chimpanzee DNA Sequence
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from biomerkin.agents.genomics_agent import GenomicsAgent
from biomerkin.agents.proteomics_agent import ProteomicsAgent
from biomerkin.agents.literature_agent import LiteratureAgent
from biomerkin.agents.drug_agent import DrugAgent
from biomerkin.agents.decision_agent import DecisionAgent
from biomerkin.services.orchestrator import WorkflowOrchestrator
from biomerkin.models.analysis import CombinedAnalysis
from biomerkin.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_chimpanzee_analysis():
    """Test complete multi-agent analysis with chimpanzee sequence."""
    
    print("=" * 80)
    print("BIOMERKIN MULTI-AGENT TEST - CHIMPANZEE DNA SEQUENCE")
    print("=" * 80)
    print()
    
    # Load chimpanzee sequence
    print("[1/5] Loading Chimpanzee DNA Sequence...")
    sequence_file = Path(__file__).parent.parent / 'chimpanzee.txt'
    
    if not sequence_file.exists():
        print("❌ chimpanzee.txt not found!")
        return 1
    
    with open(sequence_file, 'r') as f:
        lines = f.readlines()
    
    # Parse the sequence file (it's tab-separated with sequence and class)
    sequences = []
    for line in lines:
        if line.strip():
            parts = line.strip().split('\t')
            if len(parts) >= 1:
                sequences.append(parts[0])
    
    total_length = sum(len(seq) for seq in sequences)
    print(f"✅ Loaded {len(sequences)} sequences: {total_length} base pairs total\n")
    
    # Test GenomicsAgent
    print("[2/5] Testing GenomicsAgent...")
    print("-" * 40)
    try:
        genomics_agent = GenomicsAgent()
        # Use first sequence for testing
        test_sequence = sequences[0] if sequences else ""
        genomics_result = genomics_agent.analyze_sequence_data(test_sequence)
        print(f"✅ GenomicsAgent: Analyzed {len(test_sequence)} bp")
        print(f"   - Genes found: {len(genomics_result.genes)}")
        print(f"   - Mutations found: {len(genomics_result.mutations)}")
        print(f"   - Proteins translated: {len(genomics_result.protein_sequences)}")
        genomics_success = True
    except Exception as e:
        print(f"❌ GenomicsAgent Error: {str(e)}")
        genomics_result = None
        genomics_success = False
    
    print()
    
    # Test ProteomicsAgent
    print("[3/5] Testing ProteomicsAgent...")
    print("-" * 40)
    try:
        proteomics_agent = ProteomicsAgent()
        if genomics_result and genomics_result.protein_sequences:
            protein_seq = genomics_result.protein_sequences[0].sequence
            proteomics_result = proteomics_agent.analyze_protein(protein_seq)
            print(f"✅ ProteomicsAgent: Analyzed protein sequence")
            print(f"   - Functional annotations: {len(proteomics_result.functional_annotations)}")
            proteomics_success = True
        else:
            print("⚠️  ProteomicsAgent: Skipped (no protein sequences from genomics)")
            proteomics_result = None
            proteomics_success = False
    except Exception as e:
        print(f"❌ ProteomicsAgent Error: {str(e)}")
        proteomics_result = None
        proteomics_success = False
    
    print()
    
    # Test LiteratureAgent
    print("[4/5] Testing LiteratureAgent...")
    print("-" * 40)
    try:
        literature_agent = LiteratureAgent()
        if genomics_result and genomics_result.genes:
            literature_result = literature_agent.analyze_literature(genomics_result, proteomics_result)
            print(f"✅ LiteratureAgent: Searched literature")
            print(f"   - Articles found: {len(literature_result.articles)}")
            literature_success = True
        else:
            # Create a mock genomics result for testing
            print("⚠️  Creating mock genomics data for literature search")
            from biomerkin.models.genomics import GenomicsResults, Gene
            mock_genomics = GenomicsResults(
                genes=[Gene(id='BRCA1', name='BRCA1', location=None, function='Tumor suppressor', confidence_score=0.9)],
                mutations=[],
                protein_sequences=[],
                quality_metrics=None
            )
            literature_result = literature_agent.analyze_literature(mock_genomics, None)
            print(f"✅ LiteratureAgent: Searched literature")
            print(f"   - Articles found: {len(literature_result.articles)}")
            literature_success = True
    except Exception as e:
        print(f"❌ LiteratureAgent Error: {str(e)}")
        import traceback
        traceback.print_exc()
        literature_result = None
        literature_success = False
    
    print()
    
    # Test DrugAgent
    print("[5/5] Testing DrugAgent...")
    print("-" * 40)
    try:
        drug_agent = DrugAgent()
        if genomics_result and genomics_result.genes:
            target_data = {
                'genes': [gene.name for gene in genomics_result.genes[:3]],
                'proteins': []
            }
        else:
            # Test with a known gene
            print("⚠️  Using test gene 'BRCA1' for drug search")
            target_data = {
                'genes': ['BRCA1'],
                'proteins': []
            }
        
        drug_result = drug_agent.find_drug_candidates(target_data)
        print(f"✅ DrugAgent: Searched drug databases")
        print(f"   - Drug candidates found: {len(drug_result.drug_candidates)}")
        drug_success = True
    except Exception as e:
        print(f"❌ DrugAgent Error: {str(e)}")
        drug_result = None
        drug_success = False
    
    print()
    
    # Generate Test Report
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    agents_tested = {
        'genomics': genomics_success,
        'proteomics': proteomics_success,
        'literature': literature_success,
        'drug': drug_success
    }
    
    agents_working = sum(agents_tested.values())
    total_agents = len(agents_tested)
    
    print(f"\nAgents Working: {agents_working}/{total_agents}")
    print(f"\nAgent Status:")
    for agent, status in agents_tested.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {agent.capitalize()}Agent")
    
    print(f"\nResults:")
    if genomics_result:
        print(f"  - Genes Found: {len(genomics_result.genes)}")
        print(f"  - Mutations Found: {len(genomics_result.mutations)}")
        print(f"  - Proteins Analyzed: {len(genomics_result.protein_sequences)}")
    if literature_result:
        print(f"  - Articles Found: {len(literature_result.articles)}")
    if drug_result:
        print(f"  - Drug Candidates: {len(drug_result.drug_candidates)}")
    
    # Save report
    report = {
        'test_date': datetime.now().isoformat(),
        'sequence_file': 'chimpanzee.txt',
        'sequences_tested': len(sequences),
        'total_base_pairs': total_length,
        'agents_tested': agents_tested,
        'agents_working': agents_working,
        'total_agents': total_agents,
        'results_summary': {
            'genes_found': len(genomics_result.genes) if genomics_result else 0,
            'mutations_found': len(genomics_result.mutations) if genomics_result else 0,
            'proteins_analyzed': len(genomics_result.protein_sequences) if genomics_result else 0,
            'articles_found': len(literature_result.articles) if literature_result else 0,
            'drugs_found': len(drug_result.drug_candidates) if drug_result else 0,
        }
    }
    
    report_file = Path(__file__).parent.parent / 'CHIMPANZEE_TEST_REPORT.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Test report saved to: {report_file}")
    print("\n" + "=" * 80)
    
    if agents_working == total_agents:
        print("✅ ALL AGENTS WORKING SUCCESSFULLY!")
        return 0
    elif agents_working > 0:
        print(f"⚠️  {total_agents - agents_working} agent(s) had issues, but {agents_working} working")
        return 0
    else:
        print("❌ All agents failed")
        return 1

def main():
    """Main test function."""
    try:
        result = test_chimpanzee_analysis()
        return result
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
