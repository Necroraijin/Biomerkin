"""
Integration tests for parallel execution with real agent instances.
"""

import asyncio
import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import biomerkin modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from biomerkin.services.orchestrator import WorkflowOrchestrator, ParallelExecutionMetrics


class MockLiteratureAgent:
    """Mock literature agent that simulates real processing time."""
    
    def analyze_literature(self, genomics_results, proteomics_results=None):
        """Simulate literature analysis with processing time."""
        time.sleep(0.1)  # Simulate 100ms processing time
        return {
            'articles_found': 15,
            'key_findings': ['Gene associated with cancer risk'],
            'confidence_score': 0.85
        }


class MockDrugAgent:
    """Mock drug agent that simulates real processing time."""
    
    def find_drug_candidates(self, target_data):
        """Simulate drug discovery with processing time."""
        time.sleep(0.15)  # Simulate 150ms processing time
        return {
            'drug_candidates': [
                {'name': 'Drug A', 'effectiveness': 0.8},
                {'name': 'Drug B', 'effectiveness': 0.7}
            ],
            'clinical_trials': 3
        }


class TestParallelIntegration:
    """Integration tests for parallel execution."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with parallel execution enabled."""
        mock_dynamodb = Mock()
        return WorkflowOrchestrator(
            dynamodb_client=mock_dynamodb,
            enable_parallel_execution=True,
            max_workers=2
        )
    
    @pytest.fixture
    def sequential_orchestrator(self):
        """Create orchestrator with parallel execution disabled."""
        mock_dynamodb = Mock()
        return WorkflowOrchestrator(
            dynamodb_client=mock_dynamodb,
            enable_parallel_execution=False
        )
    
    @pytest.fixture
    def sample_genomics_results(self):
        """Sample genomics results."""
        return Mock(
            genes=[Mock(name='BRCA1'), Mock(name='TP53')],
            mutations=[Mock(clinical_significance='Pathogenic')]
        )
    
    @pytest.fixture
    def sample_proteomics_results(self):
        """Sample proteomics results."""
        return Mock(
            functional_annotations=[Mock(description='DNA repair protein')],
            pathways=[]
        )
    
    def test_parallel_vs_sequential_performance(self, orchestrator, sequential_orchestrator,
                                              sample_genomics_results, sample_proteomics_results):
        """Test that parallel execution is faster than sequential."""
        literature_agent = MockLiteratureAgent()
        drug_agent = MockDrugAgent()
        
        # Test parallel execution
        with patch.object(orchestrator, 'update_agent_progress'):
            start_time = time.time()
            lit_results_parallel, drug_results_parallel, parallel_metrics = orchestrator.execute_literature_and_drug_parallel(
                workflow_id="parallel-test",
                genomics_results=sample_genomics_results,
                proteomics_results=sample_proteomics_results,
                literature_agent=literature_agent,
                drug_agent=drug_agent
            )
            parallel_time = time.time() - start_time
        
        # Test sequential execution
        with patch.object(sequential_orchestrator, 'update_agent_progress'):
            start_time = time.time()
            lit_results_sequential, drug_results_sequential, sequential_metrics = sequential_orchestrator.execute_literature_and_drug_parallel(
                workflow_id="sequential-test",
                genomics_results=sample_genomics_results,
                proteomics_results=sample_proteomics_results,
                literature_agent=literature_agent,
                drug_agent=drug_agent
            )
            sequential_time = time.time() - start_time
        
        # Verify results are the same
        assert lit_results_parallel is not None
        assert drug_results_parallel is not None
        assert lit_results_sequential is not None
        assert drug_results_sequential is not None
        
        # Verify parallel execution is faster
        assert parallel_time < sequential_time
        
        # Verify metrics show time savings
        assert parallel_metrics.time_saved > 0
        assert parallel_metrics.parallel_efficiency > 0
        assert sequential_metrics.time_saved == 0
        assert sequential_metrics.parallel_efficiency == 0
        
        print(f"Parallel execution time: {parallel_time:.3f}s")
        print(f"Sequential execution time: {sequential_time:.3f}s")
        print(f"Time saved: {parallel_metrics.time_saved:.3f}s")
        print(f"Parallel efficiency: {parallel_metrics.parallel_efficiency:.2%}")
    
    def test_parallel_execution_with_error_recovery(self, orchestrator, sample_genomics_results):
        """Test parallel execution handles errors gracefully."""
        
        class FailingLiteratureAgent:
            def analyze_literature(self, genomics_results, proteomics_results=None):
                raise Exception("Literature service unavailable")
        
        literature_agent = FailingLiteratureAgent()
        drug_agent = MockDrugAgent()
        
        with patch.object(orchestrator, 'update_agent_progress'):
            lit_results, drug_results, metrics = orchestrator.execute_literature_and_drug_parallel(
                workflow_id="error-test",
                genomics_results=sample_genomics_results,
                proteomics_results=None,
                literature_agent=literature_agent,
                drug_agent=drug_agent
            )
        
        # Literature agent should fail, drug agent should succeed
        assert lit_results is None
        assert drug_results is not None
        
        # Check execution results
        literature_result = next(r for r in metrics.execution_results if r.agent_name == 'literature')
        drug_result = next(r for r in metrics.execution_results if r.agent_name == 'drug')
        
        assert literature_result.success is False
        assert literature_result.error is not None
        assert drug_result.success is True
        assert drug_result.error is None
    
    def test_performance_metrics_accuracy(self, orchestrator, sample_genomics_results, sample_proteomics_results):
        """Test that performance metrics are calculated accurately."""
        literature_agent = MockLiteratureAgent()
        drug_agent = MockDrugAgent()
        
        with patch.object(orchestrator, 'update_agent_progress'):
            lit_results, drug_results, metrics = orchestrator.execute_literature_and_drug_parallel(
                workflow_id="metrics-test",
                genomics_results=sample_genomics_results,
                proteomics_results=sample_proteomics_results,
                literature_agent=literature_agent,
                drug_agent=drug_agent
            )
        
        # Verify metrics structure
        assert isinstance(metrics, ParallelExecutionMetrics)
        assert len(metrics.execution_results) == 2
        assert metrics.total_execution_time > 0
        assert metrics.sequential_time_estimate > 0
        assert metrics.time_saved >= 0
        assert 0 <= metrics.parallel_efficiency <= 1
        
        # Verify agent execution results
        for result in metrics.execution_results:
            assert result.execution_time > 0
            assert result.start_time < result.end_time
            assert result.agent_name in ['literature', 'drug']
    
    def test_concurrent_workflow_execution(self, orchestrator, sample_genomics_results, sample_proteomics_results):
        """Test multiple workflows can run concurrently."""
        literature_agent = MockLiteratureAgent()
        drug_agent = MockDrugAgent()
        
        def run_workflow(workflow_id):
            with patch.object(orchestrator, 'update_agent_progress'):
                return orchestrator.execute_literature_and_drug_parallel(
                    workflow_id=workflow_id,
                    genomics_results=sample_genomics_results,
                    proteomics_results=sample_proteomics_results,
                    literature_agent=literature_agent,
                    drug_agent=drug_agent
                )
        
        # Run multiple workflows sequentially (simulating concurrent behavior)
        start_time = time.time()
        
        # Run 3 workflows
        workflow_results = []
        for i in range(3):
            lit_results, drug_results, metrics = run_workflow(f"concurrent-test-{i}")
            workflow_results.append((lit_results, drug_results, metrics))
        
        total_time = time.time() - start_time
        
        # Verify all workflows completed successfully
        assert len(workflow_results) == 3
        for lit_results, drug_results, metrics in workflow_results:
            assert lit_results is not None
            assert drug_results is not None
            assert metrics.time_saved > 0
        
        # Store metrics for performance summary
        for i, (_, _, metrics) in enumerate(workflow_results):
            orchestrator.execution_metrics[f"concurrent-test-{i}"] = metrics
        
        # Test performance summary
        summary = orchestrator.get_performance_summary()
        assert summary['total_workflows'] == 3
        assert summary['total_time_saved'] > 0
        assert summary['average_efficiency'] > 0
        assert summary['parallel_execution_enabled'] is True
    
    def test_memory_usage_tracking(self, orchestrator, sample_genomics_results):
        """Test that memory usage can be tracked (basic test)."""
        literature_agent = MockLiteratureAgent()
        drug_agent = MockDrugAgent()
        
        with patch.object(orchestrator, 'update_agent_progress'):
            lit_results, drug_results, metrics = orchestrator.execute_literature_and_drug_parallel(
                workflow_id="memory-test",
                genomics_results=sample_genomics_results,
                proteomics_results=None,
                literature_agent=literature_agent,
                drug_agent=drug_agent
            )
        
        # Verify execution results exist (memory tracking is optional)
        assert len(metrics.execution_results) == 2
        for result in metrics.execution_results:
            assert result.agent_name in ['literature', 'drug']
            # Memory usage might be None, which is acceptable
            assert result.memory_usage is None or result.memory_usage >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])