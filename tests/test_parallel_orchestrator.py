"""
Tests for parallel execution functionality in WorkflowOrchestrator.
"""

import asyncio
import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from biomerkin.services.orchestrator import (
    WorkflowOrchestrator, 
    AgentExecutionResult, 
    ParallelExecutionMetrics
)
from biomerkin.models.base import WorkflowState, WorkflowStatus, GenomicLocation, MutationType


class TestParallelOrchestrator:
    """Test cases for parallel execution in WorkflowOrchestrator."""
    
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
    
    @pytest.fixture
    def sample_genomics_results(self):
        """Sample genomics results for testing."""
        genes = [
            Gene(
                id="GENE001",
                name="BRCA1",
                location=None,
                function="DNA repair",
                confidence_score=0.95,
                synonyms=["BRCA1"]
            ),
            Gene(
                id="GENE002", 
                name="TP53",
                location=None,
                function="Tumor suppressor",
                confidence_score=0.90,
                synonyms=["TP53"]
            )
        ]
        
        mutations = [
            Mutation(
                position=100,
                reference_base="A",
                alternate_base="T",
                mutation_type="SNP",
                clinical_significance="Pathogenic",
                gene_id="GENE001"
            )
        ]
        
        protein_sequences = [
            ProteinSequence(
                sequence="MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG",
                gene_id="GENE001",
                length=65,
                molecular_weight=7500.0
            )
        ]
        
        return GenomicsResults(
            genes=genes,
            mutations=mutations,
            protein_sequences=protein_sequences,
            quality_metrics=None
        )
    
    @pytest.fixture
    def sample_proteomics_results(self):
        """Sample proteomics results for testing."""
        annotations = [
            FunctionAnnotation(
                description="DNA binding protein",
                confidence_score=0.85,
                source="UniProt"
            )
        ]
        
        return ProteomicsResults(
            structure_data=None,
            functional_annotations=annotations,
            domains=[],
            interactions=[]
        )
    
    @pytest.fixture
    def mock_literature_agent(self):
        """Mock literature agent."""
        agent = Mock()
        agent.analyze_literature.return_value = LiteratureResults(
            articles=[],
            summary=LiteratureSummary(
                search_terms=["BRCA1", "TP53"],
                total_articles_found=10,
                articles_analyzed=10,
                key_findings=["BRCA1 is involved in DNA repair"],
                relevant_studies=[],
                research_gaps=[],
                confidence_level=0.8,
                analysis_timestamp=datetime.now().isoformat()
            ),
            search_metadata={}
        )
        return agent
    
    @pytest.fixture
    def mock_drug_agent(self):
        """Mock drug agent."""
        agent = Mock()
        agent.find_drug_candidates.return_value = DrugResults(
            target_genes=["BRCA1", "TP53"],
            drug_candidates=[
                DrugCandidate(
                    drug_id="DRUG001",
                    name="Olaparib",
                    drug_type="small_molecule",
                    mechanism_of_action="PARP inhibitor",
                    target_proteins=["BRCA1"],
                    trial_phase="approved",
                    effectiveness_score=0.85,
                    side_effects=[],
                    indication="Breast cancer",
                    manufacturer="AstraZeneca"
                )
            ],
            clinical_trials=[],
            interaction_analysis=None,
            analysis_timestamp=datetime.now().isoformat()
        )
        return agent
    
    def test_parallel_execution_enabled(self, orchestrator):
        """Test that parallel execution is enabled by default."""
        assert orchestrator.enable_parallel_execution is True
        assert orchestrator.max_workers == 2
        assert orchestrator.executor is not None
    
    def test_parallel_execution_disabled(self, mock_dynamodb_client):
        """Test orchestrator with parallel execution disabled."""
        orchestrator = WorkflowOrchestrator(
            dynamodb_client=mock_dynamodb_client,
            enable_parallel_execution=False
        )
        assert orchestrator.enable_parallel_execution is False
    
    @pytest.mark.asyncio
    async def test_execute_agent_async_success(self, orchestrator, mock_literature_agent, sample_genomics_results):
        """Test successful async agent execution."""
        workflow_id = "test-workflow-001"
        
        with patch.object(orchestrator, 'update_agent_progress'):
            result = await orchestrator._execute_agent_async(
                workflow_id=workflow_id,
                agent_name='literature',
                agent_instance=mock_literature_agent,
                input_data={
                    'genomics_results': sample_genomics_results,
                    'proteomics_results': None
                }
            )
        
        assert isinstance(result, AgentExecutionResult)
        assert result.agent_name == 'literature'
        assert result.success is True
        assert result.error is None
        assert result.results is not None
        assert result.execution_time > 0
        assert 'literature_results' in result.results
    
    @pytest.mark.asyncio
    async def test_execute_agent_async_failure(self, orchestrator, mock_literature_agent):
        """Test async agent execution with failure."""
        workflow_id = "test-workflow-002"
        
        # Make the agent raise an exception
        mock_literature_agent.analyze_literature.side_effect = Exception("Test error")
        
        with patch.object(orchestrator, 'update_agent_progress'):
            result = await orchestrator._execute_agent_async(
                workflow_id=workflow_id,
                agent_name='literature',
                agent_instance=mock_literature_agent,
                input_data={'genomics_results': None}
            )
        
        assert isinstance(result, AgentExecutionResult)
        assert result.agent_name == 'literature'
        assert result.success is False
        assert result.error is not None
        assert result.results is None
        assert "Test error" in str(result.error)
    
    @pytest.mark.asyncio
    async def test_execute_agents_parallel_success(self, orchestrator, mock_literature_agent, 
                                                 mock_drug_agent, sample_genomics_results, 
                                                 sample_proteomics_results):
        """Test successful parallel execution of multiple agents."""
        workflow_id = "test-workflow-003"
        
        agent_configs = [
            {
                'agent_name': 'literature',
                'agent_instance': mock_literature_agent,
                'input_data': {
                    'genomics_results': sample_genomics_results,
                    'proteomics_results': sample_proteomics_results
                }
            },
            {
                'agent_name': 'drug',
                'agent_instance': mock_drug_agent,
                'input_data': {
                    'target_data': {
                        'genes': ['BRCA1', 'TP53'],
                        'proteins': ['DNA binding protein'],
                        'pathways': [],
                        'conditions': ['Pathogenic']
                    }
                }
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
    
    @pytest.mark.asyncio
    async def test_execute_agents_parallel_with_failure(self, orchestrator, mock_literature_agent, 
                                                      mock_drug_agent, sample_genomics_results):
        """Test parallel execution with one agent failing."""
        workflow_id = "test-workflow-004"
        
        # Make literature agent fail
        mock_literature_agent.analyze_literature.side_effect = Exception("Literature agent failed")
        
        agent_configs = [
            {
                'agent_name': 'literature',
                'agent_instance': mock_literature_agent,
                'input_data': {'genomics_results': sample_genomics_results}
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
        
        # Check that one agent failed and one succeeded
        literature_result = next(r for r in metrics.execution_results if r.agent_name == 'literature')
        drug_result = next(r for r in metrics.execution_results if r.agent_name == 'drug')
        
        assert literature_result.success is False
        assert literature_result.error is not None
        assert drug_result.success is True
        assert drug_result.error is None
    
    def test_execute_literature_and_drug_parallel(self, orchestrator, mock_literature_agent, 
                                                mock_drug_agent, sample_genomics_results, 
                                                sample_proteomics_results):
        """Test parallel execution of literature and drug agents."""
        workflow_id = "test-workflow-005"
        
        with patch.object(orchestrator, 'update_agent_progress'):
            literature_results, drug_results, metrics = orchestrator.execute_literature_and_drug_parallel(
                workflow_id=workflow_id,
                genomics_results=sample_genomics_results,
                proteomics_results=sample_proteomics_results,
                literature_agent=mock_literature_agent,
                drug_agent=mock_drug_agent
            )
        
        assert literature_results is not None
        assert drug_results is not None
        assert isinstance(metrics, ParallelExecutionMetrics)
        assert len(metrics.execution_results) == 2
        assert 'literature' in metrics.agents_executed
        assert 'drug' in metrics.agents_executed
    
    def test_execute_literature_and_drug_sequential_fallback(self, mock_dynamodb_client, 
                                                           mock_literature_agent, mock_drug_agent, 
                                                           sample_genomics_results, sample_proteomics_results):
        """Test sequential execution when parallel is disabled."""
        orchestrator = WorkflowOrchestrator(
            dynamodb_client=mock_dynamodb_client,
            enable_parallel_execution=False
        )
        workflow_id = "test-workflow-006"
        
        literature_results, drug_results, metrics = orchestrator.execute_literature_and_drug_parallel(
            workflow_id=workflow_id,
            genomics_results=sample_genomics_results,
            proteomics_results=sample_proteomics_results,
            literature_agent=mock_literature_agent,
            drug_agent=mock_drug_agent
        )
        
        assert literature_results is not None
        assert drug_results is not None
        assert isinstance(metrics, ParallelExecutionMetrics)
        assert metrics.time_saved == 0.0  # No time saved in sequential execution
        assert metrics.parallel_efficiency == 0.0
    
    def test_prepare_drug_target_data(self, orchestrator, sample_genomics_results, sample_proteomics_results):
        """Test preparation of target data for drug agent."""
        target_data = orchestrator._prepare_drug_target_data(
            sample_genomics_results, 
            sample_proteomics_results
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
        workflow_id = "test-workflow-007"
        
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
    
    def test_parallel_groups_configuration(self, orchestrator):
        """Test that parallel groups are properly configured."""
        assert 'literature_drug' in orchestrator.parallel_groups
        assert orchestrator.parallel_groups['literature_drug'] == ['literature', 'drug']
    
    @pytest.mark.asyncio
    async def test_concurrent_api_calls_simulation(self, orchestrator, mock_literature_agent, mock_drug_agent):
        """Test that agents can handle concurrent API calls."""
        workflow_id = "test-workflow-008"
        
        # Simulate slow API calls
        def slow_literature_analysis(*args, **kwargs):
            time.sleep(0.1)  # Simulate API delay
            return LiteratureResults(articles=[], summary=LiteratureSummary(
                search_terms=[], total_articles_found=0, articles_analyzed=0,
                key_findings=[], relevant_studies=[], research_gaps=[],
                confidence_level=0.0, analysis_timestamp=datetime.now().isoformat()
            ), search_metadata={})
        
        def slow_drug_analysis(*args, **kwargs):
            time.sleep(0.1)  # Simulate API delay
            return DrugResults(target_genes=[], drug_candidates=[], clinical_trials=[],
                             interaction_analysis=None, analysis_timestamp=datetime.now().isoformat())
        
        mock_literature_agent.analyze_literature.side_effect = slow_literature_analysis
        mock_drug_agent.find_drug_candidates.side_effect = slow_drug_analysis
        
        agent_configs = [
            {
                'agent_name': 'literature',
                'agent_instance': mock_literature_agent,
                'input_data': {'genomics_results': None}
            },
            {
                'agent_name': 'drug',
                'agent_instance': mock_drug_agent,
                'input_data': {'target_data': {'genes': []}}
            }
        ]
        
        start_time = time.time()
        
        with patch.object(orchestrator, 'update_agent_progress'):
            metrics = await orchestrator.execute_agents_parallel(workflow_id, agent_configs)
        
        total_time = time.time() - start_time
        
        # Parallel execution should be faster than sequential
        assert total_time < 0.2  # Should be less than sum of individual delays
        assert metrics.time_saved > 0
        assert metrics.parallel_efficiency > 0
    
    def test_error_handling_in_parallel_execution(self, orchestrator, mock_literature_agent, mock_drug_agent):
        """Test error handling and recovery in parallel execution."""
        workflow_id = "test-workflow-009"
        
        # Make one agent fail
        mock_literature_agent.analyze_literature.side_effect = Exception("Network timeout")
        
        literature_results, drug_results, metrics = orchestrator.execute_literature_and_drug_parallel(
            workflow_id=workflow_id,
            genomics_results=Mock(),
            proteomics_results=Mock(),
            literature_agent=mock_literature_agent,
            drug_agent=mock_drug_agent
        )
        
        # Drug agent should still succeed
        assert drug_results is not None
        
        # Literature agent should fail gracefully
        assert literature_results is None
        
        # Metrics should reflect the mixed results
        assert len(metrics.execution_results) == 2
        literature_result = next(r for r in metrics.execution_results if r.agent_name == 'literature')
        drug_result = next(r for r in metrics.execution_results if r.agent_name == 'drug')
        
        assert literature_result.success is False
        assert drug_result.success is True


class TestPerformanceMonitoring:
    """Test cases for performance monitoring and metrics."""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for performance testing."""
        return WorkflowOrchestrator(enable_parallel_execution=True, max_workers=4)
    
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
    
    def test_timing_accuracy(self, orchestrator):
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
    pytest.main([__file__])