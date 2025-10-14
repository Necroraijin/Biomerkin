"""
Comprehensive error handling and recovery utilities for the Biomerkin multi-agent system.

This module provides retry logic with exponential backoff, graceful degradation,
error categorization, and workflow recovery mechanisms.
"""

import asyncio
import functools
import logging
import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union, Tuple
from concurrent.futures import TimeoutError

import requests
from botocore.exceptions import ClientError, BotoCoreError
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError

from .logging_config import get_logger


class ErrorCategory(Enum):
    """Categories of errors for appropriate handling strategies."""
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    AUTHENTICATION_ERROR = "authentication_error"
    VALIDATION_ERROR = "validation_error"
    PROCESSING_ERROR = "processing_error"
    SYSTEM_ERROR = "system_error"
    TIMEOUT_ERROR = "timeout_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Severity levels for error handling."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorInfo:
    """Information about an error occurrence."""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    exception: Exception
    timestamp: datetime
    agent: str
    workflow_id: Optional[str] = None
    retry_count: int = 0
    recoverable: bool = True
    context: Optional[Dict[str, Any]] = None


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    backoff_factor: float = 1.0


class ErrorClassifier:
    """Classifies errors into categories and determines handling strategies."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Define error mappings
        self.error_mappings = {
            # Network errors
            ConnectionError: (ErrorCategory.NETWORK_ERROR, ErrorSeverity.MEDIUM),
            Timeout: (ErrorCategory.TIMEOUT_ERROR, ErrorSeverity.MEDIUM),
            TimeoutError: (ErrorCategory.TIMEOUT_ERROR, ErrorSeverity.MEDIUM),
            
            # HTTP errors
            HTTPError: (ErrorCategory.API_ERROR, ErrorSeverity.MEDIUM),
            
            # AWS errors
            ClientError: (ErrorCategory.API_ERROR, ErrorSeverity.MEDIUM),
            BotoCoreError: (ErrorCategory.SYSTEM_ERROR, ErrorSeverity.HIGH),
            
            # Request errors
            RequestException: (ErrorCategory.NETWORK_ERROR, ErrorSeverity.MEDIUM),
            
            # Python built-in errors
            ValueError: (ErrorCategory.VALIDATION_ERROR, ErrorSeverity.LOW),
            TypeError: (ErrorCategory.VALIDATION_ERROR, ErrorSeverity.LOW),
            KeyError: (ErrorCategory.VALIDATION_ERROR, ErrorSeverity.LOW),
            FileNotFoundError: (ErrorCategory.RESOURCE_ERROR, ErrorSeverity.MEDIUM),
            PermissionError: (ErrorCategory.SYSTEM_ERROR, ErrorSeverity.HIGH),
            MemoryError: (ErrorCategory.SYSTEM_ERROR, ErrorSeverity.CRITICAL),
        }
    
    def classify_error(self, exception: Exception, agent: str, 
                      workflow_id: Optional[str] = None, 
                      context: Optional[Dict[str, Any]] = None) -> ErrorInfo:
        """
        Classify an error and return error information.
        
        Args:
            exception: The exception to classify
            agent: Name of the agent where error occurred
            workflow_id: Optional workflow identifier
            context: Optional additional context
            
        Returns:
            ErrorInfo with classification details
        """
        # Get base classification
        category, severity = self._get_base_classification(exception)
        
        # Refine classification based on specific error details
        category, severity = self._refine_classification(exception, category, severity)
        
        # Determine if error is recoverable
        recoverable = self._is_recoverable(exception, category, severity)
        
        error_info = ErrorInfo(
            category=category,
            severity=severity,
            message=str(exception),
            exception=exception,
            timestamp=datetime.utcnow(),
            agent=agent,
            workflow_id=workflow_id,
            recoverable=recoverable,
            context=context or {}
        )
        
        self.logger.debug(f"Classified error: {category.value}, severity: {severity.value}, "
                         f"recoverable: {recoverable}, agent: {agent}")
        
        return error_info
    
    def _get_base_classification(self, exception: Exception) -> Tuple[ErrorCategory, ErrorSeverity]:
        """Get base classification for an exception type."""
        exception_type = type(exception)
        
        # Check direct mapping
        if exception_type in self.error_mappings:
            return self.error_mappings[exception_type]
        
        # Check inheritance hierarchy
        for error_type, (category, severity) in self.error_mappings.items():
            if isinstance(exception, error_type):
                return category, severity
        
        # Default classification
        return ErrorCategory.UNKNOWN_ERROR, ErrorSeverity.MEDIUM
    
    def _refine_classification(self, exception: Exception, 
                             category: ErrorCategory, 
                             severity: ErrorSeverity) -> Tuple[ErrorCategory, ErrorSeverity]:
        """Refine classification based on specific error details."""
        
        # Handle HTTP errors specifically
        if isinstance(exception, HTTPError):
            if hasattr(exception, 'response') and exception.response is not None:
                status_code = exception.response.status_code
                
                if status_code == 401:
                    return ErrorCategory.AUTHENTICATION_ERROR, ErrorSeverity.HIGH
                elif status_code == 403:
                    return ErrorCategory.AUTHENTICATION_ERROR, ErrorSeverity.HIGH
                elif status_code == 429:
                    return ErrorCategory.RATE_LIMIT_ERROR, ErrorSeverity.MEDIUM
                elif 500 <= status_code < 600:
                    return ErrorCategory.API_ERROR, ErrorSeverity.HIGH
        
        # Handle AWS ClientError specifically
        if isinstance(exception, ClientError):
            error_code = exception.response.get('Error', {}).get('Code', '')
            
            if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                return ErrorCategory.AUTHENTICATION_ERROR, ErrorSeverity.HIGH
            elif error_code in ['Throttling', 'ThrottlingException']:
                return ErrorCategory.RATE_LIMIT_ERROR, ErrorSeverity.MEDIUM
            elif error_code in ['ResourceNotFound', 'NoSuchBucket']:
                return ErrorCategory.RESOURCE_ERROR, ErrorSeverity.MEDIUM
        
        # Handle timeout errors
        if 'timeout' in str(exception).lower():
            return ErrorCategory.TIMEOUT_ERROR, ErrorSeverity.MEDIUM
        
        # Handle rate limiting
        if 'rate limit' in str(exception).lower() or 'too many requests' in str(exception).lower():
            return ErrorCategory.RATE_LIMIT_ERROR, ErrorSeverity.MEDIUM
        
        return category, severity
    
    def _is_recoverable(self, exception: Exception, 
                       category: ErrorCategory, 
                       severity: ErrorSeverity) -> bool:
        """Determine if an error is recoverable."""
        
        # Critical errors are generally not recoverable
        if severity == ErrorSeverity.CRITICAL:
            return False
        
        # Authentication errors are not recoverable without intervention
        if category == ErrorCategory.AUTHENTICATION_ERROR:
            return False
        
        # Validation errors are generally not recoverable
        if category == ErrorCategory.VALIDATION_ERROR:
            return False
        
        # Network, API, rate limit, and timeout errors are usually recoverable
        recoverable_categories = {
            ErrorCategory.NETWORK_ERROR,
            ErrorCategory.API_ERROR,
            ErrorCategory.RATE_LIMIT_ERROR,
            ErrorCategory.TIMEOUT_ERROR,
            ErrorCategory.PROCESSING_ERROR
        }
        
        return category in recoverable_categories


class RetryHandler:
    """Handles retry logic with exponential backoff."""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
        self.logger = get_logger(__name__)
    
    def retry_with_backoff(self, 
                          func: Callable,
                          error_classifier: ErrorClassifier,
                          agent_name: str,
                          workflow_id: Optional[str] = None,
                          retry_config: Optional[RetryConfig] = None) -> Callable:
        """
        Decorator for retry logic with exponential backoff.
        
        Args:
            func: Function to retry
            error_classifier: Error classifier instance
            agent_name: Name of the agent
            workflow_id: Optional workflow identifier
            retry_config: Optional retry configuration
            
        Returns:
            Decorated function with retry logic
        """
        config = retry_config or self.config
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Classify the error
                    error_info = error_classifier.classify_error(
                        e, agent_name, workflow_id, {'attempt': attempt + 1}
                    )
                    error_info.retry_count = attempt
                    
                    # Log the error
                    self.logger.warning(f"Attempt {attempt + 1} failed for {agent_name}: "
                                      f"{error_info.category.value} - {error_info.message}")
                    
                    # Check if we should retry
                    if not self._should_retry(error_info, attempt, config):
                        self.logger.error(f"Max retries exceeded or non-recoverable error for {agent_name}")
                        raise e
                    
                    # Calculate delay and wait
                    if attempt < config.max_retries:
                        delay = self._calculate_delay(attempt, config, error_info.category)
                        self.logger.info(f"Retrying {agent_name} in {delay:.2f} seconds...")
                        time.sleep(delay)
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    
    async def async_retry_with_backoff(self,
                                     func: Callable,
                                     error_classifier: ErrorClassifier,
                                     agent_name: str,
                                     workflow_id: Optional[str] = None,
                                     retry_config: Optional[RetryConfig] = None) -> Callable:
        """
        Async version of retry decorator.
        
        Args:
            func: Async function to retry
            error_classifier: Error classifier instance
            agent_name: Name of the agent
            workflow_id: Optional workflow identifier
            retry_config: Optional retry configuration
            
        Returns:
            Decorated async function with retry logic
        """
        config = retry_config or self.config
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Classify the error
                    error_info = error_classifier.classify_error(
                        e, agent_name, workflow_id, {'attempt': attempt + 1}
                    )
                    error_info.retry_count = attempt
                    
                    # Log the error
                    self.logger.warning(f"Async attempt {attempt + 1} failed for {agent_name}: "
                                      f"{error_info.category.value} - {error_info.message}")
                    
                    # Check if we should retry
                    if not self._should_retry(error_info, attempt, config):
                        self.logger.error(f"Max retries exceeded or non-recoverable error for {agent_name}")
                        raise e
                    
                    # Calculate delay and wait
                    if attempt < config.max_retries:
                        delay = self._calculate_delay(attempt, config, error_info.category)
                        self.logger.info(f"Retrying {agent_name} in {delay:.2f} seconds...")
                        await asyncio.sleep(delay)
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    
    def _should_retry(self, error_info: ErrorInfo, attempt: int, config: RetryConfig) -> bool:
        """Determine if we should retry based on error info and attempt count."""
        
        # Don't retry if we've exceeded max attempts
        if attempt >= config.max_retries:
            return False
        
        # Don't retry non-recoverable errors
        if not error_info.recoverable:
            return False
        
        # Don't retry authentication errors
        if error_info.category == ErrorCategory.AUTHENTICATION_ERROR:
            return False
        
        # Don't retry validation errors
        if error_info.category == ErrorCategory.VALIDATION_ERROR:
            return False
        
        return True
    
    def _calculate_delay(self, attempt: int, config: RetryConfig, 
                        error_category: ErrorCategory) -> float:
        """Calculate delay for exponential backoff."""
        
        # Base delay calculation
        delay = config.base_delay * (config.exponential_base ** attempt) * config.backoff_factor
        
        # Apply category-specific adjustments
        if error_category == ErrorCategory.RATE_LIMIT_ERROR:
            # Longer delays for rate limiting
            delay *= 2.0
        elif error_category == ErrorCategory.NETWORK_ERROR:
            # Shorter delays for network errors
            delay *= 0.5
        
        # Apply maximum delay limit
        delay = min(delay, config.max_delay)
        
        # Add jitter if enabled
        if config.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(delay, 0.1)  # Minimum 0.1 second delay


class GracefulDegradationHandler:
    """Handles graceful degradation when agents fail or APIs are unavailable."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.fallback_strategies = {
            'genomics': self._genomics_fallback,
            'proteomics': self._proteomics_fallback,
            'literature': self._literature_fallback,
            'drug': self._drug_fallback,
            'decision': self._decision_fallback
        }
    
    def handle_agent_failure(self, agent_name: str, error_info: ErrorInfo, 
                           partial_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle agent failure with graceful degradation.
        
        Args:
            agent_name: Name of the failed agent
            error_info: Information about the error
            partial_results: Any partial results that were obtained
            
        Returns:
            Fallback results or empty results with error information
        """
        self.logger.warning(f"Applying graceful degradation for {agent_name} due to {error_info.category.value}")
        
        # Try agent-specific fallback strategy
        if agent_name in self.fallback_strategies:
            try:
                fallback_results = self.fallback_strategies[agent_name](error_info, partial_results)
                self.logger.info(f"Applied fallback strategy for {agent_name}")
                return fallback_results
            except Exception as e:
                self.logger.error(f"Fallback strategy failed for {agent_name}: {str(e)}")
        
        # Return minimal results with error information
        return {
            'status': 'failed',
            'error': {
                'category': error_info.category.value,
                'severity': error_info.severity.value,
                'message': error_info.message,
                'timestamp': error_info.timestamp.isoformat()
            },
            'partial_results': partial_results or {},
            'fallback_applied': True
        }
    
    def _genomics_fallback(self, error_info: ErrorInfo, 
                          partial_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback strategy for genomics agent."""
        return {
            'status': 'degraded',
            'genes': partial_results.get('genes', []) if partial_results else [],
            'mutations': partial_results.get('mutations', []) if partial_results else [],
            'protein_sequences': partial_results.get('protein_sequences', []) if partial_results else [],
            'quality_metrics': {
                'coverage_depth': 0.0,
                'quality_score': 0.0,
                'confidence_level': 0.0,
                'error_rate': 1.0
            },
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'fallback_reason': f"Genomics analysis failed: {error_info.message}",
            'fallback_applied': True
        }
    
    def _proteomics_fallback(self, error_info: ErrorInfo, 
                           partial_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback strategy for proteomics agent."""
        return {
            'status': 'degraded',
            'structure_data': None,
            'functional_annotations': partial_results.get('functional_annotations', []) if partial_results else [],
            'domains': [],
            'interactions': [],
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'fallback_reason': f"Proteomics analysis failed: {error_info.message}",
            'fallback_applied': True
        }
    
    def _literature_fallback(self, error_info: ErrorInfo, 
                           partial_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback strategy for literature agent."""
        return {
            'status': 'degraded',
            'key_findings': ["Literature search unavailable due to API issues"],
            'relevant_studies': [],
            'research_gaps': ["Unable to identify research gaps due to search failure"],
            'confidence_level': 0.0,
            'search_terms': partial_results.get('search_terms', []) if partial_results else [],
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'fallback_reason': f"Literature search failed: {error_info.message}",
            'fallback_applied': True
        }
    
    def _drug_fallback(self, error_info: ErrorInfo, 
                      partial_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback strategy for drug agent."""
        return {
            'status': 'degraded',
            'drug_candidates': partial_results.get('drug_candidates', []) if partial_results else [],
            'clinical_trials': [],
            'interaction_analysis': None,
            'target_genes': partial_results.get('target_genes', []) if partial_results else [],
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'fallback_reason': f"Drug discovery failed: {error_info.message}",
            'fallback_applied': True
        }
    
    def _decision_fallback(self, error_info: ErrorInfo, 
                         partial_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback strategy for decision agent."""
        return {
            'status': 'degraded',
            'report': {
                'summary': "Analysis completed with limited data due to system issues.",
                'genetic_findings': partial_results.get('genetic_findings', 'Not available') if partial_results else 'Not available',
                'protein_analysis': partial_results.get('protein_analysis', 'Not available') if partial_results else 'Not available',
                'literature_insights': 'Literature search unavailable',
                'drug_recommendations': [],
                'treatment_options': [],
                'limitations': [f"Report generation limited due to: {error_info.message}"]
            },
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'fallback_reason': f"Report generation failed: {error_info.message}",
            'fallback_applied': True
        }


class WorkflowRecoveryHandler:
    """Handles workflow recovery and partial result handling."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def recover_workflow(self, workflow_id: str, failed_agents: List[str], 
                        available_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recover a workflow by continuing with available data.
        
        Args:
            workflow_id: Workflow identifier
            failed_agents: List of agents that failed
            available_results: Results from successful agents
            
        Returns:
            Recovery strategy and updated results
        """
        self.logger.info(f"Attempting workflow recovery for {workflow_id}. "
                        f"Failed agents: {failed_agents}")
        
        recovery_strategy = self._determine_recovery_strategy(failed_agents, available_results)
        
        if recovery_strategy['can_continue']:
            self.logger.info(f"Workflow {workflow_id} can continue with degraded functionality")
            return {
                'status': 'recovered',
                'strategy': recovery_strategy,
                'results': available_results,
                'limitations': recovery_strategy['limitations']
            }
        else:
            self.logger.warning(f"Workflow {workflow_id} cannot be recovered")
            return {
                'status': 'failed',
                'strategy': recovery_strategy,
                'results': available_results,
                'reason': recovery_strategy['failure_reason']
            }
    
    def _determine_recovery_strategy(self, failed_agents: List[str], 
                                   available_results: Dict[str, Any]) -> Dict[str, Any]:
        """Determine the best recovery strategy based on failed agents."""
        
        # Define agent dependencies
        dependencies = {
            'proteomics': ['genomics'],
            'literature': ['genomics', 'proteomics'],
            'drug': ['genomics', 'proteomics'],
            'decision': ['genomics', 'proteomics', 'literature', 'drug']
        }
        
        # Check if critical dependencies are available
        can_continue = True
        limitations = []
        failure_reason = None
        
        # If genomics failed, most other agents can't function properly
        if 'genomics' in failed_agents:
            if 'proteomics' not in failed_agents and 'proteomics' in available_results:
                # Can continue with protein-only analysis
                limitations.append("Genomic analysis unavailable - protein-focused analysis only")
            else:
                can_continue = False
                failure_reason = "Critical genomics analysis failed and no protein data available"
        
        # Check literature and drug agents
        if 'literature' in failed_agents:
            limitations.append("Literature insights unavailable")
        
        if 'drug' in failed_agents:
            limitations.append("Drug recommendations unavailable")
        
        # Decision agent can usually continue with partial data
        if 'decision' in failed_agents:
            limitations.append("Automated report generation unavailable")
        
        return {
            'can_continue': can_continue,
            'limitations': limitations,
            'failure_reason': failure_reason,
            'available_agents': [agent for agent in ['genomics', 'proteomics', 'literature', 'drug', 'decision'] 
                               if agent not in failed_agents],
            'recovery_mode': 'partial' if limitations else 'full'
        }


# Convenience functions for common error handling patterns

def with_retry(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator for adding retry logic to functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff
    """
    def decorator(func):
        error_classifier = ErrorClassifier()
        retry_handler = RetryHandler(RetryConfig(max_retries=max_retries, base_delay=base_delay))
        
        return retry_handler.retry_with_backoff(
            func, error_classifier, func.__name__
        )
    
    return decorator


def handle_api_errors(agent_name: str):
    """
    Decorator for handling API errors with appropriate classification.
    
    Args:
        agent_name: Name of the agent for error context
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_classifier = ErrorClassifier()
            degradation_handler = GracefulDegradationHandler()
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_info = error_classifier.classify_error(e, agent_name)
                
                if error_info.severity == ErrorSeverity.CRITICAL:
                    raise e
                
                # Apply graceful degradation for recoverable errors
                return degradation_handler.handle_agent_failure(agent_name, error_info)
        
        return wrapper
    
    return decorator