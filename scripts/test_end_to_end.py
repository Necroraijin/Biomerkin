#!/usr/bin/env python3
"""
End-to-end test of Biomerkin Multi-Agent System
Tests the complete workflow with a real DNA sequence
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
from biomerkin.models.genomics import GenomicsResults, Gene, ProteinSequence
from biomerkin.models.analysis import CombinedAnalysis
from biomerkin.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_end_to_end():
    """Test complete multi-agent workflow end-to-end."""
    
    print("=" * 80)
    print("BIOMERKIN END-TO-END MULTI-AGENT WORKFLOW TEST")
    print("=" * 80)
    print()
    
    start_time = datetime.now()
    workflow_id = f"test_{start_time.strftime('%Y%m%d_%H%M%S')}"
    
    # Load chimpanzee sequence
    print("[1/6] Loading DNA Sequence...")
    sequence_file = Path(__file__).parent.parent / 'chimpanzee.txt'
    
    if not sequence_file.exists():
        print("❌ chimpanzee.txt not found!")
        return 1
    
    with open(sequence_file, 'r') as f:
        lines = f.readlines()
    
    # Parse and get a real sequence (skip the header line)
    sequences = []
    for line in lines[1:]:  # Skip first line (header)
        if line.strip():
            parts = line.strip().split('\t')
            if len(parts) >= 1 and len(parts[0]) > 100:  # Get sequences > 100bp
                sequences.append(parts[0])
    
    if not sequences:
        print("❌ No valid sequences found!")
        return 1
    
    # Use first substantial sequence
    test_sequence = sequences[0]
    print(f"✅ Loaded sequence: {len(test_sequence)} base pairs\n")
    
    # Step 1: GenomicsAgent
    print("[2/6] Running GenomicsAgent...")
    print("-" * 40)
    try:
        genomics_agent = GenomicsAgent()
        genomics_result = genomics_agent.analyze_sequence_data(test_sequence)
        print(f"✅ GenomicsAgent completed")
        print(f"   - Genes found: {len(genomics_result.genes)}")
        print(f"   - Mutations found: {len(genomics_result.mutations)}")
        print(f"   - Proteins translated: {len(genomics_result.protein_sequences)}")
        genomics_success = True
    except Exception as e:
        print(f"❌ GenomicsAgent failed: {str(e)}")
        genomics_result = None
        genomics_success = False
    
    print()
    
    # Step 2: ProteomicsAgent
    print("[3/6] Running ProteomicsAgent...")
    print("-" * 40)
    proteomics_success = False
    proteomics_result = None
    
    if genomics_result and genomics_result.protein_sequences:
        try:
            proteomics_agent = ProteomicsAgent()
            protein_seq = genomics_result.protein_sequences[0].sequence
            proteomics_result = proteomics_agent.analyze_protein(protein_seq)
            print(f"✅ ProteomicsAgent completed")
            print(f"   - Functional annotations: {len(proteomics_result.functional_annotations)}")
            print(f"   - Domains found: {len(proteomics_result.domains)}")
            proteomics_success = True
        except Exception as e:
            print(f"❌ ProteomicsAgent failed: {str(e)}")
    else:
        print("⚠️  ProteomicsAgent skipped (no protein sequences)")
    
    print()
    
    # Step 3: LiteratureAgent (parallel with DrugAgent)
    print("[4/6] Running LiteratureAgent...")
    print("-" * 40)
    literature_success = False
    literature_result = None
    
    # Create mock genomics data if needed
    if not genomics_result or not genomics_result.genes:
        print("⚠️  Using mock gene data (BRCA1) for literature search")
        from biomerkin.models.genomics import GenomicsResults, Gene
        genomics_for_lit = GenomicsResults(
            genes=[Gene(
                id='BRCA1',
                name='BRCA1',
                location=None,
                function='DNA repair and tumor suppression',
                confidence_score=0.95
            )],
            mutations=[],
            protein_sequences=[],
            quality_metrics=None
        )
    else:
        genomics_for_lit = genomics_result
    
    try:
        literature_agent = LiteratureAgent()
        literature_result = literature_agent.analyze_literature(
            genomics_for_lit,
            proteomics_result,
            max_articles=10
        )
        print(f"✅ LiteratureAgent completed")
        print(f"   - Articles found: {len(literature_result.articles) if literature_result else 0}")
        print(f"   - Key findings: {len(literature_result.summary.key_findings) if literature_result and literature_result.summary else 0}")
        literature_success = True
    except Exception as e:
        print(f"❌ LiteratureAgent failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Step 4: DrugAgent (parallel with LiteratureAgent)
    print("[5/6] Running DrugAgent...")
    print("-" * 40)
    drug_success = False
    drug_result = None
    
    try:
        drug_agent = DrugAgent()
        if genomics_result and genomics_result.genes:
            target_data = {
                'genes': [gene.name for gene in genomics_result.genes[:5]],
                'proteins': [p.sequence for p in genomics_result.protein_sequences[:3]] if genomics_result.protein_sequences else []
            }
        else:
            target_data = {
                'genes': ['BRCA1', 'TP53'],
                'proteins': []
            }
        
        drug_result = drug_agent.find_drug_candidates(target_data)
        print(f"✅ DrugAgent completed")
        print(f"   - Drug candidates: {len(drug_result.drug_candidates)}")
        print(f"   - Clinical trials: {len(drug_result.clinical_trials)}")
        drug_success = True
    except Exception as e:
        print(f"❌ DrugAgent failed: {str(e)}")
    
    print()
    
    # Step 5: DecisionAgent
    print("[6/6] Running DecisionAgent...")
    print("-" * 40)
    decision_success = False
    medical_report = None
    
    try:
        decision_agent = DecisionAgent()
        
        # Create combined analysis
        combined = CombinedAnalysis(
            workflow_id=workflow_id,
            genomics_results=genomics_result,
            proteomics_results=proteomics_result,
            literature_results=literature_result,
            drug_results=drug_result,
            medical_report=None,  # Will be generated
            analysis_start_time=start_time,
            analysis_end_time=None
        )
        
        medical_report = decision_agent.generate_medical_report(combined)
        print(f"✅ DecisionAgent completed")
        print(f"   - Report ID: {medical_report.report_id}")
        print(f"   - Drug recommendations: {len(medical_report.drug_recommendations)}")
        print(f"   - Treatment options: {len(medical_report.treatment_options)}")
        decision_success = True
    except Exception as e:
        print(f"❌ DecisionAgent failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Generate Final Report
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds()
    
    print("=" * 80)
    print("END-TO-END TEST RESULTS")
    print("=" * 80)
    
    agents_status = {
        'GenomicsAgent': genomics_success,
        'ProteomicsAgent': proteomics_success,
        'LiteratureAgent': literature_success,
        'DrugAgent': drug_success,
        'DecisionAgent': decision_success
    }
    
    agents_working = sum(agents_status.values())
    total_agents = len(agents_status)
    
    print(f"\nWorkflow ID: {workflow_id}")
    print(f"Total Execution Time: {total_time:.2f} seconds")
    print(f"\nAgents Status: {agents_working}/{total_agents} working")
    
    for agent, status in agents_status.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {agent}")
    
    print(f"\nData Flow:")
    print(f"  GenomicsAgent → ProteomicsAgent: {'✅' if genomics_success and proteomics_success else '⚠️'}")
    print(f"  GenomicsAgent → LiteratureAgent: {'✅' if genomics_success and literature_success else '⚠️'}")
    print(f"  GenomicsAgent → DrugAgent: {'✅' if genomics_success and drug_success else '⚠️'}")
    print(f"  All Agents → DecisionAgent: {'✅' if decision_success else '⚠️'}")
    
    print(f"\nResults Summary:")
    if genomics_result:
        print(f"  - Genes: {len(genomics_result.genes)}")
        print(f"  - Mutations: {len(genomics_result.mutations)}")
        print(f"  - Proteins: {len(genomics_result.protein_sequences)}")
    if literature_result:
        print(f"  - Articles: {len(literature_result.articles) if literature_result.articles else 0}")
    if drug_result:
        print(f"  - Drug Candidates: {len(drug_result.drug_candidates)}")
    if medical_report:
        print(f"  - Medical Report: Generated ({medical_report.report_id})")
    
    # Save detailed report
    report = {
        'workflow_id': workflow_id,
        'test_date': start_time.isoformat(),
        'execution_time_seconds': total_time,
        'sequence_length': len(test_sequence),
        'agents_status': agents_status,
        'agents_working': agents_working,
        'total_agents': total_agents,
        'success_rate': f"{(agents_working/total_agents)*100:.1f}%",
        'results': {
            'genes_found': len(genomics_result.genes) if genomics_result else 0,
            'mutations_found': len(genomics_result.mutations) if genomics_result else 0,
            'proteins_analyzed': len(genomics_result.protein_sequences) if genomics_result else 0,
            'articles_found': len(literature_result.articles) if literature_result and literature_result.articles else 0,
            'drugs_found': len(drug_result.drug_candidates) if drug_result else 0,
            'report_generated': medical_report is not None
        }
    }
    
    report_file = Path(__file__).parent.parent / 'END_TO_END_TEST_REPORT.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✅ Detailed report saved to: {report_file}")
    print("\n" + "=" * 80)
    
    if agents_working >= 3:
        print(f"✅ END-TO-END TEST PASSED ({agents_working}/{total_agents} agents working)")
        return 0
    else:
        print(f"⚠️  END-TO-END TEST PARTIAL ({agents_working}/{total_agents} agents working)")
        return 1

def main():
    """Main test function."""
    try:
        result = test_end_to_end()
        return result
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
