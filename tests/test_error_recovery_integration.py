"""
Integration tests for error handling and recovery mechanisms.

Tests end-to-end error handling scenarios including:
- Agent failures with recovery
- Workflow continuation with partial results
- Circuit breaker behavior under load
- Graceful degradation in real scenarios
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from biomerkin.services.error_recovery_orchestrator import ErrorRecoveryOrchestrator
from biomerkin.agents.base_agent import BaseAgent, APIAgent
from biomerkin.models.base import WorkflowState, WorkflowStatus
from biomerkin.models.error_models import ErrorImpact, RecoveryAction
from biomerkin.utils.error_handling import RetryConfig


class MockGenomicsAgent(BaseAgent):
    """Mock genomics agent for testing."""
    
    def __init__(self, should_fail=False, failure_count=0):
        super().__init__("genomics")
        self.should_fail = should_fail
        self.failure_count = failure_count
        self.call_count = 0
    
    def execute(self, input_data, workflow_id=None):
        self.call_count += 1
        
        if self.should_fail and self.call_count <= self.failure_count:
            if self.call_count <= 2:
                raise ConnectionError("Network error")
            else:
                raise ValueError("Invalid sequence data")
        
        return {
            "genes": ["BRCA1", "TP53"],
            "mutations": [{"position": 100, "type": "SNP"}],
            "protein_sequences": ["MKTVRQERLK..."],
            "quality_metrics": {
                "coverage_depth": 95.5,
                "quality_score": 0.98,
                "confidence_level": 0.95
            }
        }


class MockLiteratureAgent(APIAgent):
    """Mock literature agent for testing."""
    
    def __init__(self, should_fail=False, api_unavailable=False):
        super().__init__("literature", rate_limit=10)
        self.should_fail = should_fail
        self.api_unavailable = api_unavailable
        self.call_count = 0
    
    def execute(self, input_data, workflow_id=None):
        self.call_count += 1
        
        if self.should_fail:
            if self.api_unavailable:
                raise ConnectionError("PubMed API unavailable")
            else:
                from requests.exceptions import HTTPError
                response = Mock()
                response.status_code = 429
                raise HTTPError("Rate limit exceeded", response=response)
        
        return {
            "key_findings": [
                "BRCA1 mutations associated with breast cancer risk",
                "TP53 is a tumor suppressor gene"
            ],
            "relevant_studies": [
                {"pmid": "12345", "title": "BRCA1 study", "relevance": 0.9}
            ],
            "confidence_level": 0.85
        }


class MockDrugAgent(APIAgent):
    """Mock drug agent for testing."""
    
    def __init__(self, should_fail=False, partial_failure=False):
        super().__init__("drug", rate_limit=5)
        self.should_fail = should_fail
        self.partial_failure = partial_failure
        self.call_count = 0
    
    def execute(self, input_data, workflow_id=None):
        self.call_count += 1
        
        if self.should_fail:
            raise TimeoutError("DrugBank API timeout")
        
        if self.partial_failure and self.call_count == 1:
            # Return partial results on first call
            return {
                "drug_candidates": [{"name": "Tamoxifen", "confidence": 0.7}],
                "clinical_trials": [],  # Empty due to API failure
                "partial_results": True
            }
        
        return {
            "drug_candidates": [
                {"name": "Tamoxifen", "confidence": 0.9},
                {"name": "Herceptin", "confidence": 0.8}
            ],
            "clinical_trials": [
                {"nct_id": "NCT12345", "phase": "Phase III", "status": "Active"}
            ]
        }


class TestErrorRecoveryIntegration:
    """Integration tests for error recovery scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = ErrorRecoveryOrchestrator(
            dynamodb_client=Mock(),
            enable_parallel_execution=False,  # Simplify for testing
            enable_circuit_breakers=True,
            enable_bulkheads=True
        )
    
    @pytest.mark.asyncio
    async def test_agent_retry_success(self):
        """Test successful agent execution after retries."""
        # Agent fails twice, then succeeds
        agent = MockGenomicsAgent(should_fail=True, failure_count=2)
        
        result = await self.orchestrator.execute_agent_with_recovery(
            workflow_id="test_workflow",
            agent_name="genomics",
            agent_instance=agent,
            input_data={"sequence": "ATCG..."},
            retry_config=RetryConfig(max_retries=3, base_delay=0.1)
        )
        
        assert result.success is True
        assert "genes" in result.results
        assert agent.call_count == 3  # Failed twice, succeeded on third
    
    @pytest.mark.asyncio
    async def test_agent_failure_with_fallback(self):
        """Test agent failure with graceful degradation."""
        # Agent always fails
        agent = MockGenomicsAgent(should_fail=True, failure_count=10)
        
        result = await self.orchestrator.execute_agent_with_recovery(
            workflow_id="test_workflow",
            agent_name="genomics",
            agent_instance=agent,
            input_data={"sequence": "ATCG..."},
            retry_config=RetryConfig(max_retries=2, base_delay=0.1)
        )
        
        assert result.success is False
        assert result.results["status"] == "degraded"
        assert result.results["fallback_applied"] is True
        assert "fallback_reason" in result.results
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_protection(self):
        """Test circuit breaker protection under repeated failures."""
        agent = MockGenomicsAgent(should_fail=True, failure_count=10)
        
        # Execute multiple times to trigger circuit breaker
        results = []
        for i in range(6):  # More than failure threshold
            result = await self.orchestrator.execute_agent_with_recovery(
                workflow_id=f"test_workflow_{i}",
                agent_name="genomics",
                agent_instance=agent,
                input_data={"sequence": "ATCG..."},
                retry_config=RetryConfig(max_retries=1, base_delay=0.1)
            )
            results.append(result)
        
        # First few should fail with retries, later ones should be blocked by circuit breaker
        assert all(not r.success for r in results)
        
        # Check circuit breaker state
        breaker = self.orchestrator.circuit_breakers["genomics"]
        assert breaker.state == "open"
        
        # Later executions should be faster (no retries due to circuit breaker)
        assert "Circuit breaker open" in str(results[-1].error)
    
    @pytest.mark.asyncio
    async def test_bulkhead_isolation(self):
        """Test bulkhead pattern for resource isolation."""
        # Configure small bulkhead for testing
        self.orchestrator.bulkheads["genomics"].max_concurrent_requests = 2
        self.orchestrator.bulkheads["genomics"].queue_size = 1
        
        agent = MockGenomicsAgent()
        
        # Start multiple concurrent executions
        tasks = []
        for i in range(5):  # More than bulkhead capacity
            task = asyncio.create_task(
                self.orchestrator.execute_agent_with_recovery(
                    workflow_id=f"test_workflow_{i}",
                    agent_name="genomics",
                    agent_instance=agent,
                    input_data={"sequence": "ATCG..."}
                )
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Some should succeed, some should be rejected due to bulkhead
        successful_results = [r for r in results if not isinstance(r, Exception) and r.success]
        failed_results = [r for r in results if not isinstance(r, Exception) and not r.success]
        
        assert len(successful_results) > 0
        assert len(failed_results) > 0
        
        # Check that some failures are due to bulkhead overflow
        bulkhead_failures = [r for r in failed_results 
                           if "Bulkhead capacity exceeded" in str(r.error)]
        assert len(bulkhead_failures) > 0
    
    @pytest.mark.asyncio
    async def test_workflow_recovery_with_partial_failures(self):
        """Test workflow recovery when some agents fail."""
        # Create agents with different failure patterns
        genomics_agent = MockGenomicsAgent()  # Succeeds
        literature_agent = MockLiteratureAgent(should_fail=True, api_unavailable=True)  # Fails
        drug_agent = MockDrugAgent(partial_failure=True)  # Partial success
        
        # Execute agents sequentially
        genomics_result = await self.orchestrator.execute_agent_with_recovery(
            "test_workflow", "genomics", genomics_agent, {"sequence": "ATCG..."}
        )
        
        literature_result = await self.orchestrator.execute_agent_with_recovery(
            "test_workflow", "literature", literature_agent, 
            {"genomics_results": genomics_result.results}
        )
        
        drug_result = await self.orchestrator.execute_agent_with_recovery(
            "test_workflow", "drug", drug_agent,
            {"target_data": {"genes": ["BRCA1"]}}
        )
        
        # Check results
        assert genomics_result.success is True
        assert literature_result.success is False  # Failed with fallback
        assert drug_result.success is True  # Partial success
        
        # Test workflow recovery
        failed_agents = ["literature"]
        available_results = {
            "genomics": genomics_result.results,
            "drug": drug_result.results
        }
        
        recovery = self.orchestrator.recovery_handler.recover_workflow(
            "test_workflow", failed_agents, available_results
        )
        
        assert recovery["status"] == "recovered"
        assert recovery["strategy"]["can_continue"] is True
        assert "Literature insights unavailable" in recovery["limitations"]
    
    @pytest.mark.asyncio
    async def test_error_metrics_collection(self):
        """Test error metrics collection during failures."""
        # Execute agents with various failure patterns
        agents_and_configs = [
            (MockGenomicsAgent(should_fail=True, failure_count=1), "genomics"),
            (MockLiteratureAgent(should_fail=True, api_unavailable=True), "literature"),
            (MockDrugAgent(should_fail=True), "drug")
        ]
        
        for agent, agent_name in agents_and_configs:
            await self.orchestrator.execute_agent_with_recovery(
                "test_workflow", agent_name, agent, {"test": "data"},
                retry_config=RetryConfig(max_retries=1, base_delay=0.1)
            )
        
        # Check error metrics
        metrics = self.orchestrator.get_error_metrics()
        assert metrics.total_errors > 0
        assert len(metrics.errors_by_agent) > 0
        assert len(metrics.errors_by_category) > 0
        
        # Should have different error categories
        assert "network_error" in metrics.errors_by_category
        assert "timeout_error" in metrics.errors_by_category
    
    @pytest.mark.asyncio
    async def test_agent_health_monitoring(self):
        """Test agent health status monitoring."""
        # Execute successful agent
        successful_agent = MockGenomicsAgent()
        await self.orchestrator.execute_agent_with_recovery(
            "test_workflow", "genomics", successful_agent, {"sequence": "ATCG..."}
        )
        
        # Execute failing agent
        failing_agent = MockLiteratureAgent(should_fail=True)
        await self.orchestrator.execute_agent_with_recovery(
            "test_workflow", "literature", failing_agent, {"test": "data"}
        )
        
        # Check health statuses
        genomics_health = self.orchestrator.agent_health["genomics"]
        literature_health = self.orchestrator.agent_health["literature"]
        
        assert genomics_health.is_healthy()
        assert genomics_health.consecutive_successes == 1
        assert genomics_health.consecutive_failures == 0
        
        assert not literature_health.is_healthy()
        assert literature_health.consecutive_failures > 0
        assert literature_health.status in ["degraded", "failed"]
    
    @pytest.mark.asyncio
    async def test_workflow_health_assessment(self):
        """Test overall workflow health assessment."""
        workflow_id = "test_workflow"
        
        # Simulate mixed agent results
        self.orchestrator._record_agent_success("genomics")
        self.orchestrator._record_agent_failure("literature", Exception("API error"))
        self.orchestrator._record_agent_success("drug")
        
        # Get workflow health
        health_status = self.orchestrator.get_workflow_health(workflow_id)
        
        assert health_status.workflow_id == workflow_id
        assert len(health_status.agent_statuses) == len(self.orchestrator.agent_sequence)
        
        # Check individual agent statuses
        assert health_status.agent_statuses["genomics"].is_healthy()
        assert health_status.agent_statuses["literature"].is_degraded()
        assert health_status.agent_statuses["drug"].is_healthy()
        
        # Should be able to continue despite literature failure
        assert health_status.can_continue()
    
    @pytest.mark.asyncio
    async def test_recovery_strategy_selection(self):
        """Test recovery strategy selection based on error types."""
        # Test different error types and their recovery strategies
        test_cases = [
            (ConnectionError("Network error"), RecoveryAction.FALLBACK),
            (ValueError("Invalid input"), RecoveryAction.SKIP),
            (PermissionError("Access denied"), RecoveryAction.ABORT),
            (TimeoutError("Request timeout"), RecoveryAction.FALLBACK)
        ]
        
        for error, expected_action in test_cases:
            error_info = self.orchestrator.error_classifier.classify_error(
                error, "test_agent", "test_workflow"
            )
            
            from biomerkin.models.error_models import ErrorContext
            error_context = ErrorContext(operation="test_operation")
            enhanced_error = self.orchestrator._create_enhanced_error(error_info, error_context)
            
            recovery_strategy = self.orchestrator._determine_recovery_strategy(enhanced_error)
            assert recovery_strategy.action == expected_action
    
    def test_circuit_breaker_status_reporting(self):
        """Test circuit breaker status reporting."""
        # Trigger some failures
        self.orchestrator._record_agent_failure("genomics", Exception("Test error"))
        self.orchestrator._record_agent_failure("genomics", Exception("Test error"))
        
        status = self.orchestrator.get_circuit_breaker_status()
        
        assert "genomics" in status
        assert status["genomics"]["failure_count"] == 2
        assert status["genomics"]["state"] == "closed"  # Not yet open
        
        # Trigger more failures to open circuit
        for _ in range(5):
            self.orchestrator._record_agent_failure("genomics", Exception("Test error"))
        
        status = self.orchestrator.get_circuit_breaker_status()
        assert status["genomics"]["state"] == "open"
    
    def test_bulkhead_status_reporting(self):
        """Test bulkhead status reporting."""
        # Simulate some load
        bulkhead = self.orchestrator.bulkheads["genomics"]
        bulkhead.acquire_slot()
        bulkhead.acquire_slot()
        
        status = self.orchestrator.get_bulkhead_status()
        
        assert "genomics" in status
        assert status["genomics"]["current_requests"] == 2
        assert status["genomics"]["utilization"] > 0
        assert status["genomics"]["max_concurrent"] > 0
    
    @pytest.mark.asyncio
    async def test_end_to_end_error_recovery(self):
        """Test complete end-to-end error recovery scenario."""
        # Create a complex scenario with multiple failure types
        agents = {
            "genomics": MockGenomicsAgent(should_fail=True, failure_count=1),  # Recoverable
            "literature": MockLiteratureAgent(should_fail=True, api_unavailable=True),  # Non-recoverable
            "drug": MockDrugAgent(partial_failure=True)  # Partial success
        }
        
        workflow_id = "complex_test_workflow"
        results = {}
        
        # Execute each agent
        for agent_name, agent in agents.items():
            input_data = {"test": "data"}
            if agent_name == "literature" and "genomics" in results:
                input_data["genomics_results"] = results["genomics"]
            
            result = await self.orchestrator.execute_agent_with_recovery(
                workflow_id, agent_name, agent, input_data,
                retry_config=RetryConfig(max_retries=2, base_delay=0.1)
            )
            
            results[agent_name] = result
        
        # Analyze results
        assert results["genomics"].success is True  # Should succeed after retry
        assert results["literature"].success is False  # Should fail with fallback
        assert results["drug"].success is True  # Should succeed with partial data
        
        # Check that fallback was applied for literature
        assert results["literature"].results["status"] == "degraded"
        assert results["literature"].results["fallback_applied"] is True
        
        # Check workflow health
        health_status = self.orchestrator.get_workflow_health(workflow_id)
        assert health_status.can_continue()  # Should be able to continue
        
        # Check error metrics
        metrics = self.orchestrator.get_error_metrics()
        assert metrics.total_errors > 0
        assert "genomics" in metrics.errors_by_agent  # From initial failure
        assert "literature" in metrics.errors_by_agent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])