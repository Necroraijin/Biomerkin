"""
Tests for data models and serialization.
"""

import pytest
from datetime import datetime
from biomerkin.models import (
    Gene, Mutation, GenomicsResults, WorkflowState, WorkflowStatus,
    MutationType, GenomicLocation, QualityMetrics
)
from biomerkin.utils import SerializationUtils


def test_gene_model():
    """Test Gene model creation and serialization."""
    location = GenomicLocation(
        chromosome="chr1",
        start_position=1000,
        end_position=2000,
        strand="+"
    )
    
    gene = Gene(
        id="GENE001",
        name="Test Gene",
        location=location,
        function="Test function",
        confidence_score=0.95
    )
    
    # Test serialization
    gene_dict = gene.to_dict()
    assert gene_dict['id'] == "GENE001"
    assert gene_dict['name'] == "Test Gene"
    assert gene_dict['confidence_score'] == 0.95
    
    # Test deserialization
    gene_restored = Gene.from_dict(gene_dict)
    assert gene_restored.id == gene.id
    assert gene_restored.name == gene.name
    assert gene_restored.location.chromosome == "chr1"


def test_mutation_model():
    """Test Mutation model creation and serialization."""
    mutation = Mutation(
        position=1500,
        reference_base="A",
        alternate_base="T",
        mutation_type=MutationType.SNP,
        clinical_significance="Pathogenic"
    )
    
    # Test serialization
    mutation_dict = mutation.to_dict()
    assert mutation_dict['position'] == 1500
    assert mutation_dict['mutation_type'] == "single_nucleotide_polymorphism"
    
    # Test deserialization
    mutation_restored = Mutation.from_dict(mutation_dict)
    assert mutation_restored.position == mutation.position
    assert mutation_restored.mutation_type == MutationType.SNP


def test_workflow_state_model():
    """Test WorkflowState model creation and serialization."""
    now = datetime.now()
    
    workflow_state = WorkflowState(
        workflow_id="test-workflow-001",
        status=WorkflowStatus.GENOMICS_PROCESSING,
        current_agent="GenomicsAgent",
        progress_percentage=25.0,
        results={},
        errors=[],
        created_at=now,
        updated_at=now
    )
    
    # Test serialization
    state_dict = workflow_state.to_dict()
    assert state_dict['workflow_id'] == "test-workflow-001"
    assert state_dict['status'] == "genomics_processing"
    assert state_dict['progress_percentage'] == 25.0
    
    # Test deserialization
    state_restored = WorkflowState.from_dict(state_dict)
    assert state_restored.workflow_id == workflow_state.workflow_id
    assert state_restored.status == WorkflowStatus.GENOMICS_PROCESSING


def test_genomics_results_model():
    """Test GenomicsResults model with complex nested data."""
    location = GenomicLocation(
        chromosome="chr1",
        start_position=1000,
        end_position=2000
    )
    
    gene = Gene(
        id="GENE001",
        name="Test Gene",
        location=location,
        function="Test function",
        confidence_score=0.95
    )
    
    mutation = Mutation(
        position=1500,
        reference_base="A",
        alternate_base="T",
        mutation_type=MutationType.SNP,
        clinical_significance="Pathogenic"
    )
    
    quality_metrics = QualityMetrics(
        coverage_depth=50.0,
        quality_score=0.98,
        confidence_level=0.95
    )
    
    results = GenomicsResults(
        genes=[gene],
        mutations=[mutation],
        protein_sequences=[],
        quality_metrics=quality_metrics
    )
    
    # Test serialization
    results_dict = results.to_dict()
    assert len(results_dict['genes']) == 1
    assert len(results_dict['mutations']) == 1
    assert results_dict['quality_metrics']['coverage_depth'] == 50.0
    
    # Test deserialization
    results_restored = GenomicsResults.from_dict(results_dict)
    assert len(results_restored.genes) == 1
    assert results_restored.genes[0].id == "GENE001"
    assert len(results_restored.mutations) == 1
    assert results_restored.mutations[0].position == 1500


def test_serialization_utils():
    """Test SerializationUtils functionality."""
    location = GenomicLocation(
        chromosome="chr1",
        start_position=1000,
        end_position=2000
    )
    
    gene = Gene(
        id="GENE001",
        name="Test Gene",
        location=location,
        function="Test function",
        confidence_score=0.95
    )
    
    # Test JSON serialization
    json_str = SerializationUtils.to_json(gene)
    assert "GENE001" in json_str
    assert "Test Gene" in json_str
    
    # Test JSON deserialization
    gene_restored = SerializationUtils.from_json(json_str, Gene)
    assert gene_restored.id == gene.id
    assert gene_restored.name == gene.name


if __name__ == "__main__":
    pytest.main([__file__])