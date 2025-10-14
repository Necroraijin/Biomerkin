"""
Base agent class with comprehensive error handling capabilities.

This module provides a base class for all agents with built-in error handling,
retry logic, circuit breakers, and graceful degradation support.
"""

import asyncio
import functools
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..models.error_models import ErrorContext, EnhancedWorkflowError
from ..utils.error_handling import (
    ErrorClassifier, RetryHandler, GracefulDegradationHandler,
    RetryConfig, with_retry, handle_api_errors
)
from ..utils.logging_config import get_logger, log_agent_activity
from ..utils.config import get_config


class BaseAgent(ABC):
    """
    Base class for all bioinformatics agents with error handling capabilities.
    
    Provides:
    - Standardized error handling and logging
    - Retry logic with exponential backoff
    - Circuit breaker pattern support
    - Request session management with connection pooling
    - Graceful degradation capabilities
    - Performance monitoring
    """
    
    def __init__(self, agent_name: str):
        """
        Initialize the base agent.
        
        Args:
            agent_name: Name of the agent for logging and error tracking
        """
        self.agent_name = agent_name
        self.logger = get_logger(f"{__name__}.{agent_name}")
        self.config = get_config()
        
        # Error handling components
        self.error_classifier = ErrorClassifier()
        self.retry_handler = RetryHandler()
        self.degradation_handler = GracefulDegradationHandler()
        
        # Performance tracking
        self.execution_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'last_execution_time': None
        }
        
        # Initialize HTTP session with retry strategy
        self.session = self._create_http_session()
        
        # Default retry configuration
        self.default_retry_config = RetryConfig(
            max_retries=self.config.api.max_retries,
            base_delay=self.config.api.retry_delay,
            max_delay=60.0
        )
    
    def _create_http_session(self) -> requests.Session:
        """Create HTTP session with retry strategy and connection pooling."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.api.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'User-Agent': f'Biomerkin-{self.agent_name}/1.0',
            'Accept': 'application/json',
            'Connection': 'keep-alive'
        })
        
        # Set timeout
        session.timeout = self.config.api.request_timeout
        
        return session
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any], workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the agent's main functionality.
        
        Args:
            input_data: Input data for the agent
            workflow_id: Optional workflow identifier for tracking
            
        Returns:
            Dictionary containing the agent's results
        """
        pass
    
    def execute_with_error_handling(self, input_data: Dict[str, Any], 
                                   workflow_id: Optional[str] = None,
                                   retry_config: Optional[RetryConfig] = None) -> Dict[str, Any]:
        """
        Execute the agent with comprehensive error handling.
        
        Args:
            input_data: Input data for the agent
            workflow_id: Optional workflow identifier for tracking
            retry_config: Optional retry configuration
            
        Returns:
            Dictionary containing the agent's results or fallback data
        """
        start_time = time.time()
        config = retry_config or self.default_retry_config
        
        try:
            log_agent_activity(
                self.logger, self.agent_name, workflow_id or 'unknown',
                "Starting agent execution"
            )
            
            # Execute with retry logic
            result = self._execute_with_retry(input_data, workflow_id, config)
            
            # Update metrics
            execution_time = time.time() - start_time
            self._update_success_metrics(execution_time)
            
            log_agent_activity(
                self.logger, self.agent_name, workflow_id or 'unknown',
                f"Agent execution completed successfully in {execution_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            # Update metrics
            execution_time = time.time() - start_time
            self._update_failure_metrics(execution_time)
            
            # Classify error
            error_info = self.error_classifier.classify_error(
                e, self.agent_name, workflow_id
            )
            
            log_agent_activity(
                self.logger, self.agent_name, workflow_id or 'unknown',
                f"Agent execution failed after {execution_time:.2f}s: {error_info.category.value}",
                {'error_message': str(e), 'error_category': error_info.category.value}
            )
            
            # Apply graceful degradation
            return self.degradation_handler.handle_agent_failure(
                self.agent_name, error_info
            )
    
    def _execute_with_retry(self, input_data: Dict[str, Any], 
                           workflow_id: Optional[str], 
                           config: RetryConfig) -> Dict[str, Any]:
        """Execute the agent with retry logic."""
        last_exception = None
        
        for attempt in range(config.max_retries + 1):
            try:
                self.logger.debug(f"Executing {self.agent_name}, attempt {attempt + 1}")
                
                # Validate input data
                self._validate_input_data(input_data)
                
                # Execute the agent
                result = self.execute(input_data, workflow_id)
                
                # Validate output data
                self._validate_output_data(result)
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Classify error
                error_info = self.error_classifier.classify_error(
                    e, self.agent_name, workflow_id, {'attempt': attempt + 1}
                )
                
                self.logger.warning(f"Attempt {attempt + 1} failed for {self.agent_name}: "
                                  f"{error_info.category.value} - {error_info.message}")
                
                # Check if we should retry
                if not self.retry_handler._should_retry(error_info, attempt, config):
                    self.logger.error(f"Max retries exceeded or non-recoverable error for {self.agent_name}")
                    break
                
                # Calculate delay and wait
                if attempt < config.max_retries:
                    delay = self.retry_handler._calculate_delay(attempt, config, error_info.category)
                    self.logger.info(f"Retrying {self.agent_name} in {delay:.2f} seconds...")
                    time.sleep(delay)
        
        # All retries failed
        raise last_exception
    
    def _validate_input_data(self, input_data: Dict[str, Any]) -> None:
        """
        Validate input data before processing.
        
        Args:
            input_data: Input data to validate
            
        Raises:
            ValueError: If input data is invalid
        """
        if not isinstance(input_data, dict):
            raise ValueError("Input data must be a dictionary")
        
        # Subclasses can override this method for specific validation
    
    def _validate_output_data(self, output_data: Dict[str, Any]) -> None:
        """
        Validate output data after processing.
        
        Args:
            output_data: Output data to validate
            
        Raises:
            ValueError: If output data is invalid
        """
        if not isinstance(output_data, dict):
            raise ValueError("Output data must be a dictionary")
        
        # Subclasses can override this method for specific validation
    
    def _update_success_metrics(self, execution_time: float) -> None:
        """Update metrics for successful execution."""
        self.execution_metrics['total_requests'] += 1
        self.execution_metrics['successful_requests'] += 1
        self.execution_metrics['last_execution_time'] = execution_time
        
        # Update average response time
        total_successful = self.execution_metrics['successful_requests']
        current_avg = self.execution_metrics['average_response_time']
        self.execution_metrics['average_response_time'] = (
            (current_avg * (total_successful - 1) + execution_time) / total_successful
        )
    
    def _update_failure_metrics(self, execution_time: float) -> None:
        """Update metrics for failed execution."""
        self.execution_metrics['total_requests'] += 1
        self.execution_metrics['failed_requests'] += 1
        self.execution_metrics['last_execution_time'] = execution_time
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the agent."""
        total_requests = self.execution_metrics['total_requests']
        success_rate = 0.0
        
        if total_requests > 0:
            success_rate = self.execution_metrics['successful_requests'] / total_requests
        
        return {
            'agent_name': self.agent_name,
            'total_requests': total_requests,
            'successful_requests': self.execution_metrics['successful_requests'],
            'failed_requests': self.execution_metrics['failed_requests'],
            'success_rate': success_rate,
            'average_response_time': self.execution_metrics['average_response_time'],
            'last_execution_time': self.execution_metrics['last_execution_time']
        }
    
    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.execution_metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'last_execution_time': None
        }
    
    def make_api_request(self, method: str, url: str, 
                        headers: Optional[Dict[str, str]] = None,
                        params: Optional[Dict[str, Any]] = None,
                        data: Optional[Dict[str, Any]] = None,
                        json_data: Optional[Dict[str, Any]] = None,
                        timeout: Optional[int] = None) -> requests.Response:
        """
        Make an API request with error handling and retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Optional headers
            params: Optional query parameters
            data: Optional form data
            json_data: Optional JSON data
            timeout: Optional timeout override
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails after retries
        """
        request_headers = headers or {}
        request_timeout = timeout or self.config.api.request_timeout
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=request_headers,
                params=params,
                data=data,
                json=json_data,
                timeout=request_timeout
            )
            
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            self.logger.error(f"API request failed for {self.agent_name}: {str(e)}")
            raise
    
    def close(self) -> None:
        """Clean up resources."""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class APIAgent(BaseAgent):
    """
    Base class for agents that interact with external APIs.
    
    Provides additional functionality for API-based agents:
    - Rate limiting
    - API key management
    - Response caching
    - API-specific error handling
    """
    
    def __init__(self, agent_name: str, api_key: Optional[str] = None,
                 rate_limit: Optional[float] = None):
        """
        Initialize the API agent.
        
        Args:
            agent_name: Name of the agent
            api_key: Optional API key for authentication
            rate_limit: Optional rate limit (requests per second)
        """
        super().__init__(agent_name)
        
        self.api_key = api_key
        self.rate_limit = rate_limit or 10.0  # Default 10 requests per second
        self.last_request_time = 0.0
        
        # Add API key to session headers if provided
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}'
            })
    
    def _rate_limit_wait(self) -> None:
        """Implement rate limiting."""
        if self.rate_limit <= 0:
            return
        
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def make_api_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Make API request with rate limiting."""
        self._rate_limit_wait()
        return super().make_api_request(method, url, **kwargs)


# Decorator for adding error handling to agent methods
def agent_error_handler(fallback_result: Optional[Dict[str, Any]] = None):
    """
    Decorator for adding error handling to agent methods.
    
    Args:
        fallback_result: Optional fallback result to return on error
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error in {func.__name__}: {str(e)}")
                
                if fallback_result is not None:
                    return fallback_result
                
                # Re-raise if no fallback provided
                raise
        
        return wrapper
    
    return decorator