"""
Simple tests for error handling functionality without complex dependencies.
"""

import pytest
import time
from unittest.mock import Mock
from requests.exceptions import ConnectionError, Timeout, HTTPError

from biomerkin.utils.error_handling import (
    ErrorClassifier, RetryHandler, GracefulDegradationHandler,
    ErrorCategory, ErrorSeverity, RetryConfig
)
from biomerkin.agents.base_agent import BaseAgent


class SimpleTestAgent(BaseAgent):
    """Simple test agent for testing error handling."""
    
    def __init__(self, should_fail=False, failure_count=0):
        super().__init__("test_agent")
        self.should_fail = should_fail
        self.failure_count = failure_count
        self.call_count = 0
    
    def execute(self, input_data, workflow_id=None):
        self.call_count += 1
        
        if self.should_fail and self.call_count <= self.failure_count:
            if self.call_count <= 2:
                raise ConnectionError("Network error")
            else:
                raise ValueError("Invalid input data")
        
        return {"result": "success", "call_count": self.call_count}


class TestSimpleErrorHandling:
    """Test basic error handling functionality."""
    
    def test_error_classification(self):
        """Test basic error classification."""
        classifier = ErrorClassifier()
        
        # Test network error
        error = ConnectionError("Connection failed")
        error_info = classifier.classify_error(error, "test_agent")
        
        assert error_info.category == ErrorCategory.NETWORK_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.recoverable is True
        
        # Test validation error
        error = ValueError("Invalid input")
        error_info = classifier.classify_error(error, "test_agent")
        
        assert error_info.category == ErrorCategory.VALIDATION_ERROR
        assert error_info.severity == ErrorSeverity.LOW
        assert error_info.recoverable is False
    
    def test_retry_logic(self):
        """Test retry logic with exponential backoff."""
        retry_handler = RetryHandler()
        classifier = ErrorClassifier()
        
        call_count = 0
        
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"
        
        # Apply retry decorator
        retried_function = retry_handler.retry_with_backoff(
            failing_function, classifier, "test_agent"
        )
        
        result = retried_function()
        assert result == "success"
        assert call_count == 3
    
    def test_graceful_degradation(self):
        """Test graceful degradation."""
        degradation_handler = GracefulDegradationHandler()
        classifier = ErrorClassifier()
        
        error = ConnectionError("API unavailable")
        error_info = classifier.classify_error(error, "genomics")
        
        result = degradation_handler.handle_agent_failure(
            "genomics", error_info, {"genes": ["BRCA1"]}
        )
        
        assert result["status"] == "degraded"
        assert result["genes"] == ["BRCA1"]
        assert result["fallback_applied"] is True
    
    def test_base_agent_error_handling(self):
        """Test base agent error handling."""
        # Test successful execution
        agent = SimpleTestAgent()
        result = agent.execute_with_error_handling({"test": "data"})
        
        assert result["result"] == "success"
        assert result["call_count"] == 1
        
        # Test failed execution with fallback
        failing_agent = SimpleTestAgent(should_fail=True, failure_count=10)
        result = failing_agent.execute_with_error_handling({"test": "data"})
        
        # Should return fallback result
        assert result["status"] == "failed"
        assert result["fallback_applied"] is True
    
    def test_agent_retry_success(self):
        """Test agent retry success."""
        # Agent fails twice, then succeeds
        agent = SimpleTestAgent(should_fail=True, failure_count=2)
        
        result = agent.execute_with_error_handling({"test": "data"})
        
        # Should succeed after retries
        assert result["result"] == "success"
        assert result["call_count"] == 3  # Failed twice, succeeded on third
    
    def test_agent_metrics(self):
        """Test agent performance metrics."""
        agent = SimpleTestAgent()
        
        # Execute successful request
        agent.execute_with_error_handling({"test": "data"})
        
        # Execute failed request
        failing_agent = SimpleTestAgent(should_fail=True, failure_count=10)
        failing_agent.execute_with_error_handling({"test": "data"})
        
        # Check successful agent metrics
        metrics = agent.get_metrics()
        assert metrics["total_requests"] == 1
        assert metrics["successful_requests"] == 1
        assert metrics["failed_requests"] == 0
        assert metrics["success_rate"] == 1.0
        
        # Check failing agent metrics
        failing_metrics = failing_agent.get_metrics()
        assert failing_metrics["total_requests"] == 1
        assert failing_metrics["successful_requests"] == 0
        assert failing_metrics["failed_requests"] == 1
        assert failing_metrics["success_rate"] == 0.0
    
    def test_delay_calculation(self):
        """Test exponential backoff delay calculation."""
        retry_handler = RetryHandler()
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, max_delay=10.0, jitter=False)
        
        delay_0 = retry_handler._calculate_delay(0, config, ErrorCategory.NETWORK_ERROR)
        delay_1 = retry_handler._calculate_delay(1, config, ErrorCategory.NETWORK_ERROR)
        delay_2 = retry_handler._calculate_delay(2, config, ErrorCategory.NETWORK_ERROR)
        
        # Should increase exponentially (with network error adjustment)
        assert delay_0 == 0.5  # base_delay * 0.5 for network errors
        assert delay_1 == 1.0  # base_delay * exponential_base^1 * 0.5
        assert delay_2 == 2.0  # base_delay * exponential_base^2 * 0.5
    
    def test_http_error_classification(self):
        """Test HTTP error classification."""
        classifier = ErrorClassifier()
        
        # Test 401 error
        response = Mock()
        response.status_code = 401
        error = HTTPError("Unauthorized", response=response)
        
        error_info = classifier.classify_error(error, "test_agent")
        assert error_info.category == ErrorCategory.AUTHENTICATION_ERROR
        assert error_info.severity == ErrorSeverity.HIGH
        assert error_info.recoverable is False
        
        # Test 429 error
        response = Mock()
        response.status_code = 429
        error = HTTPError("Too Many Requests", response=response)
        
        error_info = classifier.classify_error(error, "test_agent")
        assert error_info.category == ErrorCategory.RATE_LIMIT_ERROR
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert error_info.recoverable is True
    
    def test_non_recoverable_error_handling(self):
        """Test that non-recoverable errors are not retried."""
        retry_handler = RetryHandler()
        classifier = ErrorClassifier()
        
        call_count = 0
        
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input")  # Non-recoverable
        
        retried_function = retry_handler.retry_with_backoff(
            failing_function, classifier, "test_agent"
        )
        
        with pytest.raises(ValueError):
            retried_function()
        
        assert call_count == 1  # Should not retry


if __name__ == "__main__":
    pytest.main([__file__, "-v"])