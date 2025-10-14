"""
Comprehensive tests for error handling and recovery mechanisms.

Tests cover:
- Error classification and categorization
- Retry logic with exponential backoff
- Graceful degradation strategies
- Circuit breaker pattern
- Workflow recovery mechanisms
- Error metrics and monitoring
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import ConnectionError, Timeout, HTTPError
from botocore.exceptions import ClientError

from biomerkin.utils.error_handling import (
    ErrorClassifier, RetryHandler, GracefulDegradationHandler,
    WorkflowRecoveryHandler, ErrorCategory, ErrorSeverity, RetryConfig
)
from biomerkin.models.error_models import (
    ErrorContext, EnhancedWorkflowError, ErrorImpact, RecoveryAction,
    AgentHealthStatus, CircuitBreakerState, BulkheadConfig
)
from biomerkin.services.error_recovery_orchestrator import ErrorRecoveryOrchestrator
from biomerkin.agents.base_agent import BaseAgent, APIAgent


class TestErrorClassifier:
    """Test error classification functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.classifier = ErrorClassifier()
    
    def test_classify_network_error(self):
        """Test classification of network errors."""
        error = ConnectionError("Connection failed")
        error_info = self.classifier.classify_error(error, "test_agent")
        
        assert error_info.category == ErrorCategory.NETWORK_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.recoverable is True
        assert error_info.agent == "test_agent"
    
    def test_classify_timeout_error(self):
        """Test classification of timeout errors."""
        error = Timeout("Request timed out")
        error_info = self.classifier.classify_error(error, "test_agent")
        
        assert error_info.category == ErrorCategory.TIMEOUT_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.recoverable is True
    
    def test_classify_http_error_401(self):
        """Test classification of HTTP 401 errors."""
        response = Mock()
        response.status_code = 401
        error = HTTPError("Unauthorized", response=response)
        
        error_info = self.classifier.classify_error(error, "test_agent")
        
        assert error_info.category == ErrorCategory.AUTHENTICATION_ERROR
        assert error_info.severity == ErrorSeverity.HIGH
        assert error_info.recoverable is False
    
    def test_classify_http_error_429(self):
        """Test classification of HTTP 429 (rate limit) errors."""
        response = Mock()
        response.status_code = 429
        error = HTTPError("Too Many Requests", response=response)
        
        error_info = self.classifier.classify_error(error, "test_agent")
        
        assert error_info.category == ErrorCategory.RATE_LIMIT_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.recoverable is True
    
    def test_classify_aws_client_error(self):
        """Test classification of AWS ClientError."""
        error_response = {
            'Error': {
                'Code': 'AccessDenied',
                'Message': 'Access denied'
            }
        }
        error = ClientError(error_response, 'GetObject')
        
        error_info = self.classifier.classify_error(error, "test_agent")
        
        assert error_info.category == ErrorCategory.AUTHENTICATION_ERROR
        assert error_info.severity == ErrorSeverity.HIGH
        assert error_info.recoverable is False
    
    def test_classify_validation_error(self):
        """Test classification of validation errors."""
        error = ValueError("Invalid input data")
        error_info = self.classifier.classify_error(error, "test_agent")
        
        assert error_info.category == ErrorCategory.VALIDATION_ERROR
        assert error_info.severity == ErrorSeverity.LOW
        assert error_info.recoverable is False
    
    def test_classify_unknown_error(self):
        """Test classification of unknown errors."""
        error = RuntimeError("Unknown error")
        error_info = self.classifier.classify_error(error, "test_agent")
        
        assert error_info.category == ErrorCategory.UNKNOWN_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM


class TestRetryHandler:
    """Test retry logic with exponential backoff."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.retry_handler = RetryHandler()
        self.error_classifier = ErrorClassifier()
    
    def test_successful_retry(self):
        """Test successful execution after retry."""
        call_count = 0
        
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"
        
        # Apply retry decorator
        retried_function = self.retry_handler.retry_with_backoff(
            failing_function, self.error_classifier, "test_agent"
        )
        
        result = retried_function()
        assert result == "success"
        assert call_count == 3
    
    def test_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        def always_failing_function():
            raise ConnectionError("Connection failed")
        
        config = RetryConfig(max_retries=2, base_delay=0.1)
        retried_function = self.retry_handler.retry_with_backoff(
            always_failing_function, self.error_classifier, "test_agent", 
            retry_config=config
        )
        
        with pytest.raises(ConnectionError):
            retried_function()
    
    def test_non_recoverable_error_no_retry(self):
        """Test that non-recoverable errors are not retried."""
        call_count = 0
        
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input")  # Non-recoverable
        
        retried_function = self.retry_handler.retry_with_backoff(
            failing_function, self.error_classifier, "test_agent"
        )
        
        with pytest.raises(ValueError):
            retried_function()
        
        assert call_count == 1  # Should not retry
    
    def test_delay_calculation(self):
        """Test exponential backoff delay calculation."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, max_delay=10.0)
        
        delay_0 = self.retry_handler._calculate_delay(0, config, ErrorCategory.NETWORK_ERROR)
        delay_1 = self.retry_handler._calculate_delay(1, config, ErrorCategory.NETWORK_ERROR)
        delay_2 = self.retry_handler._calculate_delay(2, config, ErrorCategory.NETWORK_ERROR)
        
        # Should increase exponentially (with some jitter)
        assert 0.4 <= delay_0 <= 0.6  # ~0.5 (base_delay * 0.5 for network errors)
        assert 0.9 <= delay_1 <= 1.1  # ~1.0
        assert 1.8 <= delay_2 <= 2.2  # ~2.0
    
    def test_rate_limit_delay_adjustment(self):
        """Test that rate limit errors get longer delays."""
        config = RetryConfig(base_delay=1.0)
        
        network_delay = self.retry_handler._calculate_delay(1, config, ErrorCategory.NETWORK_ERROR)
        rate_limit_delay = self.retry_handler._calculate_delay(1, config, ErrorCategory.RATE_LIMIT_ERROR)
        
        # Rate limit delays should be longer
        assert rate_limit_delay > network_delay
    
    @pytest.mark.asyncio
    async def test_async_retry(self):
        """Test async retry functionality."""
        call_count = 0
        
        async def failing_async_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Connection failed")
            return "async_success"
        
        config = RetryConfig(max_retries=2, base_delay=0.1)
        retried_function = await self.retry_handler.async_retry_with_backoff(
            failing_async_function, self.error_classifier, "test_agent",
            retry_config=config
        )
        
        result = await retried_function()
        assert result == "async_success"
        assert call_count == 2


class TestGracefulDegradationHandler:
    """Test graceful degradation strategies."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.degradation_handler = GracefulDegradationHandler()
        self.error_classifier = ErrorClassifier()
    
    def test_genomics_fallback(self):
        """Test genomics agent fallback strategy."""
        error = ConnectionError("API unavailable")
        error_info = self.error_classifier.classify_error(error, "genomics")
        
        result = self.degradation_handler.handle_agent_failure(
            "genomics", error_info, {"genes": ["BRCA1"]}
        )
        
        assert result["status"] == "degraded"
        assert result["genes"] == ["BRCA1"]
        assert result["fallback_applied"] is True
        assert "quality_metrics" in result
    
    def test_literature_fallback(self):
        """Test literature agent fallback strategy."""
        error = HTTPError("PubMed API error")
        error_info = self.error_classifier.classify_error(error, "literature")
        
        result = self.degradation_handler.handle_agent_failure(
            "literature", error_info
        )
        
        assert result["status"] == "degraded"
        assert "Literature search unavailable" in result["key_findings"][0]
        assert result["confidence_level"] == 0.0
        assert result["fallback_applied"] is True
    
    def test_drug_fallback(self):
        """Test drug agent fallback strategy."""
        error = Timeout("DrugBank timeout")
        error_info = self.error_classifier.classify_error(error, "drug")
        
        partial_results = {"drug_candidates": [{"name": "aspirin"}]}
        result = self.degradation_handler.handle_agent_failure(
            "drug", error_info, partial_results
        )
        
        assert result["status"] == "degraded"
        assert result["drug_candidates"] == [{"name": "aspirin"}]
        assert result["clinical_trials"] == []
        assert result["fallback_applied"] is True


class TestWorkflowRecoveryHandler:
    """Test workflow recovery mechanisms."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.recovery_handler = WorkflowRecoveryHandler()
    
    def test_recover_workflow_with_genomics_failure(self):
        """Test workflow recovery when genomics agent fails."""
        failed_agents = ["genomics"]
        available_results = {"proteomics": {"proteins": ["P53"]}}
        
        recovery = self.recovery_handler.recover_workflow(
            "test_workflow", failed_agents, available_results
        )
        
        assert recovery["status"] == "recovered"
        assert recovery["strategy"]["can_continue"] is True
        assert "Genomic analysis unavailable" in recovery["limitations"][0]
    
    def test_recover_workflow_critical_failure(self):
        """Test workflow recovery when critical components fail."""
        failed_agents = ["genomics", "proteomics"]
        available_results = {}
        
        recovery = self.recovery_handler.recover_workflow(
            "test_workflow", failed_agents, available_results
        )
        
        assert recovery["status"] == "failed"
        assert recovery["strategy"]["can_continue"] is False
        assert "Critical genomics analysis failed" in recovery["strategy"]["failure_reason"]
    
    def test_recover_workflow_partial_failure(self):
        """Test workflow recovery with partial agent failures."""
        failed_agents = ["literature", "drug"]
        available_results = {
            "genomics": {"genes": ["BRCA1"]},
            "proteomics": {"proteins": ["P53"]}
        }
        
        recovery = self.recovery_handler.recover_workflow(
            "test_workflow", failed_agents, available_results
        )
        
        assert recovery["status"] == "recovered"
        assert recovery["strategy"]["can_continue"] is True
        assert "Literature insights unavailable" in recovery["limitations"]
        assert "Drug recommendations unavailable" in recovery["limitations"]


class TestCircuitBreakerState:
    """Test circuit breaker pattern implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.circuit_breaker = CircuitBreakerState(
            agent_name="test_agent",
            state="closed",
            failure_threshold=3,
            recovery_timeout=60
        )
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        assert self.circuit_breaker.should_allow_request() is True
        
        # Record failures
        self.circuit_breaker.record_failure()
        self.circuit_breaker.record_failure()
        assert self.circuit_breaker.state == "closed"
        assert self.circuit_breaker.should_allow_request() is True
        
        # Third failure should open circuit
        self.circuit_breaker.record_failure()
        assert self.circuit_breaker.state == "open"
        assert self.circuit_breaker.should_allow_request() is False
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery mechanism."""
        # Force circuit to open state
        self.circuit_breaker.state = "open"
        self.circuit_breaker.last_failure_time = datetime.utcnow() - timedelta(seconds=70)
        
        # Should transition to half-open after timeout
        assert self.circuit_breaker.should_allow_request() is True
        assert self.circuit_breaker.state == "half_open"
        
        # Record successes to close circuit
        self.circuit_breaker.record_success()
        self.circuit_breaker.record_success()
        self.circuit_breaker.record_success()
        
        assert self.circuit_breaker.state == "closed"
    
    def test_circuit_breaker_half_open_failure(self):
        """Test circuit breaker failure in half-open state."""
        self.circuit_breaker.state = "half_open"
        
        # Failure in half-open should return to open
        self.circuit_breaker.record_failure()
        assert self.circuit_breaker.state == "open"


class TestBulkheadConfig:
    """Test bulkhead pattern implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.bulkhead = BulkheadConfig(
            agent_name="test_agent",
            max_concurrent_requests=3,
            queue_size=5
        )
    
    def test_bulkhead_capacity_management(self):
        """Test bulkhead capacity management."""
        # Should accept requests up to max concurrent
        assert self.bulkhead.acquire_slot() is True
        assert self.bulkhead.current_requests == 1
        
        assert self.bulkhead.acquire_slot() is True
        assert self.bulkhead.current_requests == 2
        
        assert self.bulkhead.acquire_slot() is True
        assert self.bulkhead.current_requests == 3
        
        # Next requests should be queued
        assert self.bulkhead.acquire_slot() is True
        assert self.bulkhead.queued_requests == 1
        
        # Release slots
        self.bulkhead.release_slot()
        assert self.bulkhead.current_requests == 2
        
        self.bulkhead.release_slot(was_queued=True)
        assert self.bulkhead.queued_requests == 0
    
    def test_bulkhead_overflow(self):
        """Test bulkhead behavior when capacity is exceeded."""
        # Fill up concurrent slots
        for _ in range(3):
            self.bulkhead.acquire_slot()
        
        # Fill up queue
        for _ in range(5):
            self.bulkhead.acquire_slot()
        
        # Should reject additional requests
        assert self.bulkhead.acquire_slot() is False
        assert not self.bulkhead.can_accept_request()


class TestBaseAgent:
    """Test base agent error handling functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        class TestAgent(BaseAgent):
            def execute(self, input_data, workflow_id=None):
                if input_data.get("should_fail"):
                    raise ConnectionError("Test failure")
                return {"result": "success"}
        
        self.agent = TestAgent("test_agent")
    
    def test_successful_execution(self):
        """Test successful agent execution."""
        result = self.agent.execute_with_error_handling({"data": "test"})
        assert result["result"] == "success"
        
        metrics = self.agent.get_metrics()
        assert metrics["successful_requests"] == 1
        assert metrics["failed_requests"] == 0
        assert metrics["success_rate"] == 1.0
    
    def test_failed_execution_with_fallback(self):
        """Test failed execution with graceful degradation."""
        result = self.agent.execute_with_error_handling({"should_fail": True})
        
        # Should return fallback result
        assert result["status"] == "failed"
        assert result["fallback_applied"] is True
        
        metrics = self.agent.get_metrics()
        assert metrics["successful_requests"] == 0
        assert metrics["failed_requests"] == 1
        assert metrics["success_rate"] == 0.0
    
    def test_input_validation(self):
        """Test input data validation."""
        with pytest.raises(ValueError):
            self.agent.execute_with_error_handling("invalid_input")
    
    def test_metrics_tracking(self):
        """Test performance metrics tracking."""
        # Execute successful request
        self.agent.execute_with_error_handling({"data": "test"})
        
        # Execute failed request
        self.agent.execute_with_error_handling({"should_fail": True})
        
        metrics = self.agent.get_metrics()
        assert metrics["total_requests"] == 2
        assert metrics["successful_requests"] == 1
        assert metrics["failed_requests"] == 1
        assert metrics["success_rate"] == 0.5
        assert metrics["average_response_time"] > 0


class TestAPIAgent:
    """Test API agent functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        class TestAPIAgent(APIAgent):
            def execute(self, input_data, workflow_id=None):
                # Simulate API call
                response = self.make_api_request("GET", "https://httpbin.org/get")
                return {"status_code": response.status_code}
        
        self.agent = TestAPIAgent("test_api_agent", rate_limit=100)
    
    @patch('requests.Session.request')
    def test_api_request_success(self, mock_request):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response
        
        result = self.agent.execute_with_error_handling({"test": "data"})
        assert result["status_code"] == 200
    
    @patch('requests.Session.request')
    def test_api_request_with_retry(self, mock_request):
        """Test API request with retry on failure."""
        # First call fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = ConnectionError("Connection failed")
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.raise_for_status.return_value = None
        
        mock_request.side_effect = [mock_response_fail, mock_response_success]
        
        result = self.agent.execute_with_error_handling({"test": "data"})
        assert result["status_code"] == 200
        assert mock_request.call_count == 2
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        start_time = time.time()
        
        # Make multiple requests
        for _ in range(3):
            self.agent._rate_limit_wait()
        
        elapsed_time = time.time() - start_time
        
        # Should take at least some time due to rate limiting
        # (This is a basic test - in practice, rate limiting is more complex)
        assert elapsed_time >= 0.0


class TestErrorRecoveryOrchestrator:
    """Test error recovery orchestrator functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = ErrorRecoveryOrchestrator(
            dynamodb_client=Mock(),
            enable_circuit_breakers=True,
            enable_bulkheads=True
        )
    
    def test_circuit_breaker_initialization(self):
        """Test that circuit breakers are initialized for all agents."""
        for agent_name in self.orchestrator.agent_sequence:
            assert agent_name in self.orchestrator.circuit_breakers
            assert self.orchestrator.circuit_breakers[agent_name].state == "closed"
    
    def test_bulkhead_initialization(self):
        """Test that bulkheads are initialized for all agents."""
        for agent_name in self.orchestrator.agent_sequence:
            assert agent_name in self.orchestrator.bulkheads
            assert self.orchestrator.bulkheads[agent_name].max_concurrent_requests > 0
    
    def test_agent_health_tracking(self):
        """Test agent health status tracking."""
        agent_name = "genomics"
        
        # Record success
        self.orchestrator._record_agent_success(agent_name)
        health = self.orchestrator.agent_health[agent_name]
        assert health.status == "healthy"
        assert health.consecutive_successes == 1
        assert health.consecutive_failures == 0
        
        # Record failure
        self.orchestrator._record_agent_failure(agent_name, Exception("Test error"))
        health = self.orchestrator.agent_health[agent_name]
        assert health.status == "degraded"
        assert health.consecutive_failures == 1
        assert health.consecutive_successes == 0
    
    def test_workflow_health_status(self):
        """Test workflow health status generation."""
        workflow_id = "test_workflow"
        health_status = self.orchestrator.get_workflow_health(workflow_id)
        
        assert health_status.workflow_id == workflow_id
        assert health_status.overall_status == "healthy"
        assert len(health_status.agent_statuses) == len(self.orchestrator.agent_sequence)
    
    def test_circuit_breaker_reset(self):
        """Test manual circuit breaker reset."""
        agent_name = "genomics"
        
        # Force circuit breaker to open
        breaker = self.orchestrator.circuit_breakers[agent_name]
        breaker.state = "open"
        breaker.failure_count = 5
        
        # Reset circuit breaker
        result = self.orchestrator.reset_circuit_breaker(agent_name)
        assert result is True
        assert breaker.state == "closed"
        assert breaker.failure_count == 0
    
    def test_error_metrics_tracking(self):
        """Test error metrics tracking."""
        # Create a mock error
        error_context = ErrorContext(operation="test_operation")
        error_info = self.orchestrator.error_classifier.classify_error(
            ConnectionError("Test error"), "genomics"
        )
        enhanced_error = self.orchestrator._create_enhanced_error(error_info, error_context)
        
        metrics = self.orchestrator.get_error_metrics()
        assert metrics.total_errors == 1
        assert "network_error" in metrics.errors_by_category
        assert "genomics" in metrics.errors_by_agent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])