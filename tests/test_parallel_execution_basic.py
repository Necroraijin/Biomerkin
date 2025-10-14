"""
Basic tests for parallel execution functionality in WorkflowOrchestrator.
"""

import asyncio
import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch
from typing import Dict, Any
import sys
import os

# Add the parent directory to the path so we can import biomerkin modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from biomerkin.services.orchestrator import (
    WorkflowOrchestrator, 
    AgentExecutionResult, 
    ParallelExecutionMetrics
)


class TestBasicParallelExecution:
    """Basic test cases for parallel execution functionality."""
    
    @pytest.fixture
    def mock_dynamodb_client(self):
        """Mock DynamoDB client."""
        return Mock()
    
    @pytest.fixture
    def orchestrator(self, mock_dynamodb_client):
        """Create orchestrator instance with mocked dependencies."""
        return WorkflowOrchestrator(
            dynamodb_client=mock_dynamodb_client,
            enable_parallel_execution=True,
            max_workers=2
        )
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test that orchestrator initializes correctly with parallel execution."""
        assert orchestrator.enable_parallel_execution is True
        assert orchestrator.max_workers == 2
        assert orchestrator.executor is not None
        assert 'literature_drug' in orchestrator.parallel_groups
        assert orchestrator.parallel_groups['literature_drug'] == ['literature', 'drug']
    
    def test_orchestrator_parallel_disabled(self, mock_dynamodb_client):
        """Test orchestrator with parallel execution disabled."""
        orchestrator = WorkflowOrchestrator(
            dynamodb_client=mock_dynamodb_client,
            enable_parallel_execution=False
        )
        assert orchestrator.enable_parallel_execution is False
    
    def test_agent_execution_result_creation(self):
        """Test creation of AgentExecutionResult objects."""
        start_time = datetime.now()
        end_time = datetime.now()
        
        result = AgentExecutionResult(
            agent_name='test_agent',
            success=True,
            results={'data': 'test'},
            error=None,
            execution_time=1.5,
            start_time=start_time,
            end_time=end_time,
            memory_usage=100.0
        )
        
        assert result.agent_name == 'test_agent'
        assert result.success is True
        assert result.results == {'data': 'test'}
        assert result.error is None
        assert result.execution_time == 1.5
        assert result.memory_usage == 100.0
    
    def test_parallel_execution_metrics_creation(self):
        """Test creation of ParallelExecutionMetrics objects."""
        execution_results = [
            AgentExecutionResult(
                agent_name='agent1',
                success=True,
                results={},
                error=None,
                execution_time=2.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            )
        ]
        
        metrics = ParallelExecutionMetrics(
            total_execution_time=2.0,
            sequential_time_estimate=4.0,
            time_saved=2.0,
            parallel_efficiency=0.5,
            agents_executed=['agent1'],
            execution_results=execution_results
        )
        
        assert metrics.total_execution_time == 2.0
        assert metrics.sequential_time_estimate == 4.0
        assert metrics.time_saved == 2.0
        assert metrics.parallel_efficiency == 0.5
        assert metrics.agents_executed == ['agent1']
        assert len(metrics.execution_results) == 1
    
    def test_calculate_parallel_metrics(self, orchestrator):
        """Test calculation of parallel execution metrics."""
        execution_results = [
            AgentExecutionResult(
                agent_name='literature',
                success=True,
                results={'data': 'test'},
                error=None,
                execution_time=2.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            ),
            AgentExecutionResult(
                agent_name='drug',
                success=True,
                results={'data': 'test'},
                error=None,
                execution_time=3.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            )
        ]
        
        total_execution_time = 3.5  # Parallel execution took 3.5s instead of 5s
        
        metrics = orchestrator._calculate_parallel_metrics(execution_results, total_execution_time)
        
        assert isinstance(metrics, ParallelExecutionMetrics)
        assert metrics.total_execution_time == 3.5
        assert metrics.sequential_time_estimate == 5.0
        assert metrics.time_saved == 1.5
        assert metrics.parallel_efficiency == 0.3  # 1.5/5.0
        assert len(metrics.agents_executed) == 2
        assert 'literature' in metrics.agents_executed
        assert 'drug' in metrics.agents_executed
    
    def test_get_execution_metrics(self, orchestrator):
        """Test retrieval of execution metrics."""
        workflow_id = "test-workflow-001"
        
        # Initially no metrics
        assert orchestrator.get_execution_metrics(workflow_id) is None
        
        # Add some metrics
        metrics = ParallelExecutionMetrics(
            total_execution_time=2.0,
            sequential_time_estimate=4.0,
            time_saved=2.0,
            parallel_efficiency=0.5,
            agents_executed=['literature', 'drug'],
            execution_results=[]
        )
        orchestrator.execution_metrics[workflow_id] = metrics
        
        retrieved_metrics = orchestrator.get_execution_metrics(workflow_id)
        assert retrieved_metrics is not None
        assert retrieved_metrics.time_saved == 2.0
        assert retrieved_metrics.parallel_efficiency == 0.5
    
    def test_get_performance_summary_empty(self, orchestrator):
        """Test performance summary with no metrics."""
        summary = orchestrator.get_performance_summary()
        
        assert summary['total_workflows'] == 0
        assert summary['average_time_saved'] == 0.0
        assert summary['average_efficiency'] == 0.0
        assert summary['total_time_saved'] == 0.0
        assert summary['parallel_execution_enabled'] is True
    
    def test_get_performance_summary_with_data(self, orchestrator):
        """Test performance summary with metrics data."""
        # Add some test metrics
        orchestrator.execution_metrics['workflow1'] = ParallelExecutionMetrics(
            total_execution_time=2.0,
            sequential_time_estimate=4.0,
            time_saved=2.0,
            parallel_efficiency=0.5,
            agents_executed=['literature', 'drug'],
            execution_results=[]
        )
        
        orchestrator.execution_metrics['workflow2'] = ParallelExecutionMetrics(
            total_execution_time=3.0,
            sequential_time_estimate=5.0,
            time_saved=2.0,
            parallel_efficiency=0.4,
            agents_executed=['literature', 'drug'],
            execution_results=[]
        )
        
        summary = orchestrator.get_performance_summary()
        
        assert summary['total_workflows'] == 2
        assert summary['average_time_saved'] == 2.0
        assert summary['average_efficiency'] == 0.45  # (0.5 + 0.4) / 2
        assert summary['total_time_saved'] == 4.0
        assert summary['parallel_execution_enabled'] is True
    
    @pytest.mark.asyncio
    async def test_execute_agent_async_basic(self, orchestrator):
        """Test basic async agent execution."""
        workflow_id = "test-workflow-002"
        
        # Mock agent that returns simple results
        mock_agent = Mock()
        mock_agent.analyze_literature = Mock(return_value={'result': 'success'})
        
        with patch.object(orchestrator, 'update_agent_progress'):
            result = await orchestrator._execute_agent_async(
                workflow_id=workflow_id,
                agent_name='literature',
                agent_instance=mock_agent,
                input_data={'genomics_results': None, 'proteomics_results': None}
            )
        
        assert isinstance(result, AgentExecutionResult)
        assert result.agent_name == 'literature'
        assert result.success is True
        assert result.error is None
        assert result.results is not None
        assert result.execution_time > 0
        assert 'literature_results' in result.results
    
    @pytest.mark.asyncio
    async def test_execute_agent_async_with_error(self, orchestrator):
        """Test async agent execution with error handling."""
        workflow_id = "test-workflow-003"
        
        # Mock agent that raises an exception
        mock_agent = Mock()
        mock_agent.analyze_literature.side_effect = Exception("Test error")
        
        with patch.object(orchestrator, 'update_agent_progress'):
            result = await orchestrator._execute_agent_async(
                workflow_id=workflow_id,
                agent_name='literature',
                agent_instance=mock_agent,
                input_data={'genomics_results': None}
            )
        
        assert isinstance(result, AgentExecutionResult)
        assert result.agent_name == 'literature'
        assert result.success is False
        assert result.error is not None
        assert result.results is None
        assert "Test error" in str(result.error)
    
    @pytest.mark.asyncio
    async def test_execute_agents_parallel_basic(self, orchestrator):
        """Test basic parallel execution of multiple agents."""
        workflow_id = "test-workflow-004"
        
        # Mock agents with some delay to simulate real execution
        def mock_literature_analysis(*args, **kwargs):
            time.sleep(0.01)  # 10ms delay
            return {'result': 'literature_success'}
        
        def mock_drug_analysis(*args, **kwargs):
            time.sleep(0.01)  # 10ms delay
            return {'result': 'drug_success'}
        
        mock_literature_agent = Mock()
        mock_literature_agent.analyze_literature = Mock(side_effect=mock_literature_analysis)
        
        mock_drug_agent = Mock()
        mock_drug_agent.find_drug_candidates = Mock(side_effect=mock_drug_analysis)
        
        agent_configs = [
            {
                'agent_name': 'literature',
                'agent_instance': mock_literature_agent,
                'input_data': {'genomics_results': None, 'proteomics_results': None}
            },
            {
                'agent_name': 'drug',
                'agent_instance': mock_drug_agent,
                'input_data': {'target_data': {'genes': ['BRCA1']}}
            }
        ]
        
        with patch.object(orchestrator, 'update_agent_progress'):
            metrics = await orchestrator.execute_agents_parallel(workflow_id, agent_configs)
        
        assert isinstance(metrics, ParallelExecutionMetrics)
        assert len(metrics.execution_results) == 2
        assert metrics.total_execution_time > 0
        assert metrics.sequential_time_estimate > 0
        assert 'literature' in metrics.agents_executed
        assert 'drug' in metrics.agents_executed
        
        # Check that both agents succeeded
        for result in metrics.execution_results:
            assert result.success is True
            assert result.error is None
    
    def test_prepare_drug_target_data_basic(self, orchestrator):
        """Test preparation of target data for drug agent."""
        # Mock genomics results
        genomics_results = Mock()
        gene1 = Mock()
        gene1.name = 'BRCA1'
        gene2 = Mock()
        gene2.name = 'TP53'
        genomics_results.genes = [gene1, gene2]
        mutation1 = Mock()
        mutation1.clinical_significance = 'Pathogenic'
        genomics_results.mutations = [mutation1]
        
        # Mock proteomics results
        proteomics_results = Mock()
        annotation1 = Mock()
        annotation1.description = 'DNA binding protein'
        proteomics_results.functional_annotations = [annotation1]
        # Mock pathways as an empty list to avoid iteration issues
        proteomics_results.pathways = []
        
        target_data = orchestrator._prepare_drug_target_data(
            genomics_results, 
            proteomics_results
        )
        
        assert isinstance(target_data, dict)
        assert 'genes' in target_data
        assert 'proteins' in target_data
        assert 'pathways' in target_data
        assert 'conditions' in target_data
        
        assert 'BRCA1' in target_data['genes']
        assert 'TP53' in target_data['genes']
        assert 'DNA binding protein' in target_data['proteins']
        assert 'Pathogenic' in target_data['conditions']
    
    def test_timing_accuracy(self):
        """Test that timing measurements are accurate."""
        def mock_agent_function():
            time.sleep(0.05)  # 50ms delay
            return {'result': 'success'}
        
        start_time = time.time()
        result = mock_agent_function()
        execution_time = time.time() - start_time
        
        # Timing should be approximately 50ms (with some tolerance)
        assert 0.04 < execution_time < 0.1
        assert result == {'result': 'success'}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])