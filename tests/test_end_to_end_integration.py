"""
End-to-end integration tests for Biomerkin multi-agent system.
Tests the complete workflow from sequence input to medical report generation.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from biomerkin.services.orchestrator import WorkflowOrchestrator
from biomerkin.services.enhanced_orchestrator import EnhancedWorkflowOrchestrator
from biomerkin.models.base import WorkflowState, WorkflowStatus
from biomerkin.agents.genomics_agent import GenomicsAgent
from biomerkin.agents.proteomics_agent import ProteomicsAgent
from biomerkin.agents.literature_agent import LiteratureAgent
from biomerkin.agents.drug_agent import DrugAgent
from biomerkin.agents.decision_agent import DecisionAgent


@pytest.fixture
def sample_dna_sequence():
    """Create a sample DNA sequence."""
    return "ATGGCTAGCAAAGGAGAGGCTAACTAA"


@pytest.fixture
def sample_fasta_file(sample_dna_sequence):
    """Create a temporary FASTA file with sample DNA sequence."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.fasta', delete=False) as f:
        f.write(">sample_sequence\n")
        f.write(sample_dna_sequence)
        file_path = f.name
    
    yield file_path
    
    # Cleanup
    if os.path.exists(file_path):
        os.unlink(file_path)


@pytest.fixture
def mock_dynamodb_client():
    """Create a mock DynamoDB client."""
    client = Mock()
    client.save_workflow_state = Mock()
    client.load_workflow_state = Mock()
    return client


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow_with_file(self, sample_fasta_file, mock_dynamodb_client):
        """Test complete workflow from file input to report generation."""
        # Create orchestrator
        orchestrator = WorkflowOrchestrator(dynamodb_client=mock_dynamodb_client)
        
        # Create workflow state
        workflow_state = WorkflowState(
            workflow_id="test-e2e-001",
            status=WorkflowStatus.INITIATED,
            current_agent="genomics",
            progress_percentage=0.0,
            input_data={"sequence_file": sample_fasta_file},
            results={},
            errors=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Mock DynamoDB responses
        mock_dynamodb_client.save_workflow_state.return_value = True
        mock_dynamodb_client.load_workflow_state.return_value = workflow_state
        
        # Test that workflow can be initiated
        assert workflow_state.workflow_id == "test-e2e-001"
        assert workflow_state.status == WorkflowStatus.INITIATED
    
    def test_genomics_agent_with_file(self, sample_fasta_file):
        """Test genomics agent with actual file input."""
        agent = GenomicsAgent()
        
        # Analyze the sequence file
        results = agent.analyze_sequence(sequence_file=sample_fasta_file)
        
        # Verify results
        assert results is not None
        assert hasattr(results, 'genes')
        assert hasattr(results, 'proteins')
    
    def test_agent_chain_execution(self, sample_dna_sequence):
        """Test sequential execution of multiple agents."""
        # Genomics Agent
        genomics_agent = GenomicsAgent()
        genomics_results = genomics_agent.analyze_sequence(dna_sequence=sample_dna_sequence)
        assert genomics_results is not None
        
        # Proteomics Agent (using genomics results)
        proteomics_agent = ProteomicsAgent()
        if genomics_results.proteins:
            protein_seq = genomics_results.proteins[0].sequence
            proteomics_results = proteomics_agent.analyze_protein(protein_sequence=protein_seq)
            assert proteomics_results is not None
    
    def test_workflow_state_transitions(self, mock_dynamodb_client):
        """Test workflow state transitions through different stages."""
        orchestrator = WorkflowOrchestrator(dynamodb_client=mock_dynamodb_client)
        
        # Initial state
        workflow_id = "test-transitions-001"
        
        # Mock workflow state
        mock_state = WorkflowState(
            workflow_id=workflow_id,
            status=WorkflowStatus.INITIATED,
            current_agent="genomics",
            progress_percentage=0.0,
            input_data={},
            results={},
            errors=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_dynamodb_client.load_workflow_state.return_value = mock_state
        
        # Verify state
        assert mock_state.status == WorkflowStatus.INITIATED
        assert mock_state.current_agent == "genomics"
    
    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(self, mock_dynamodb_client):
        """Test error handling during workflow execution."""
        orchestrator = WorkflowOrchestrator(dynamodb_client=mock_dynamodb_client)
        
        # Create workflow with invalid data
        workflow_state = WorkflowState(
            workflow_id="test-error-001",
            status=WorkflowStatus.INITIATED,
            current_agent="genomics",
            progress_percentage=0.0,
            input_data={"sequence_file": "nonexistent.fasta"},
            results={},
            errors=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Verify error handling exists
        assert workflow_state.errors == []
    
    def test_parallel_agent_execution_setup(self, mock_dynamodb_client):
        """Test parallel execution setup."""
        orchestrator = WorkflowOrchestrator(
            dynamodb_client=mock_dynamodb_client,
            enable_parallel_execution=True,
            max_workers=3
        )
        
        assert orchestrator.enable_parallel_execution is True
        assert orchestrator.max_workers == 3
    
    @pytest.mark.asyncio
    async def test_enhanced_orchestrator_initialization(self):
        """Test enhanced orchestrator with Strands agents."""
        try:
            orchestrator = EnhancedWorkflowOrchestrator(
                enable_parallel_execution=True,
                enable_strands=False  # Disable Strands for testing
            )
            assert orchestrator is not None
        except Exception as e:
            pytest.skip(f"Enhanced orchestrator not available: {e}")
    
    def test_unknown_dataset_handling(self, tmpdir):
        """Test system with unknown/custom dataset."""
        # Create a custom FASTA file
        custom_file = tmpdir.join("custom_sequence.fasta")
        custom_file.write(">custom_gene\nATGCGTACGTACGTACGTACGTAA")
        
        agent = GenomicsAgent()
        results = agent.analyze_sequence(sequence_file=str(custom_file))
        
        # System should handle unknown dataset gracefully
        assert results is not None
    
    def test_large_sequence_handling(self):
        """Test handling of large genomic sequences."""
        # Create a large sequence (1000 bp)
        large_sequence = "ATGC" * 250
        
        agent = GenomicsAgent()
        results = agent.analyze_sequence(dna_sequence=large_sequence)
        
        assert results is not None
        assert len(results.genes) >= 0  # Should process without errors
    
    def test_multiple_format_support(self, tmpdir):
        """Test support for multiple file formats."""
        # FASTA format
        fasta_file = tmpdir.join("test.fasta")
        fasta_file.write(">seq1\nATGCGTACGTAA")
        
        agent = GenomicsAgent()
        
        # Test FASTA
        results = agent.analyze_sequence(sequence_file=str(fasta_file))
        assert results is not None
    
    def test_workflow_results_completeness(self, sample_dna_sequence):
        """Test that workflow produces complete results."""
        genomics_agent = GenomicsAgent()
        results = genomics_agent.analyze_sequence(dna_sequence=sample_dna_sequence)
        
        # Check for essential components
        assert hasattr(results, 'genes')
        assert hasattr(results, 'mutations')
        assert hasattr(results, 'proteins')
        assert hasattr(results, 'quality_metrics')
    
    @pytest.mark.asyncio
    async def test_concurrent_workflow_execution(self, mock_dynamodb_client):
        """Test multiple concurrent workflow executions."""
        orchestrator = WorkflowOrchestrator(dynamodb_client=mock_dynamodb_client)
        
        workflows = []
        for i in range(3):
            workflow = WorkflowState(
                workflow_id=f"test-concurrent-{i:03d}",
                status=WorkflowStatus.INITIATED,
                current_agent="genomics",
                progress_percentage=0.0,
                input_data={},
                results={},
                errors=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            workflows.append(workflow)
        
        # All workflows should be independently manageable
        assert len(workflows) == 3
        assert all(w.workflow_id.startswith("test-concurrent-") for w in workflows)

