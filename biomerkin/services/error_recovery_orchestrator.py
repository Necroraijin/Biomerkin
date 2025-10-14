"""
Enhanced orchestrator with comprehensive error handling and recovery capabilities.

This module extends the base orchestrator with advanced error handling, retry logic,
graceful degradation, circuit breakers, and workflow recovery mechanisms.
"""

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..models.base import WorkflowState, WorkflowStatus
from ..models.error_models import (
    EnhancedWorkflowError, ErrorContext, RecoveryStrategy, RecoveryAction,
    ErrorImpact, AgentHealthStatus, WorkflowHealthStatus, ErrorMetrics,
    CircuitBreakerState, BulkheadConfig
)
from ..utils.error_handling import (
    ErrorClassifier, RetryHandler, GracefulDegradationHandler, 
    WorkflowRecoveryHandler, RetryConfig
)
from ..utils.logging_config import get_logger, log_workflow_event, log_agent_activity
from ..utils.config import get_config
from .dynamodb_client import DynamoDBClient
from .orchestrator import WorkflowOrchestrator, AgentExecutionResult


class ErrorRecoveryOrchestrator(WorkflowOrchestrator):
    """
    Enhanced orchestrator with comprehensive error handling and recovery.
    
    Extends the base orchestrator with:
    - Retry logic with exponential backoff
    - Graceful degradation when agents fail
    - Circuit breaker pattern for failing services
    - Bulkhead pattern for resource isolation
    - Workflow recovery and partial result handling
    - Comprehensive error metrics and monitoring
    """
    
    def __init__(self, dynamodb_client: Optional[DynamoDBClient] = None,
                 enable_parallel_execution: bool = True, max_workers: int = 4,
                 enable_circuit_breakers: bool = True, enable_bulkheads: bool = True):
        """
        Initialize the error recovery orchestrator.
        
        Args:
            dynamodb_client: Optional DynamoDB client for state persistence
            enable_parallel_execution: Whether to enable parallel agent execution
            max_workers: Maximum number of worker threads
            enable_circuit_breakers: Whether to enable circuit breaker pattern
            enable_bulkheads: Whether to enable bulkhead pattern
        """
        super().__init__(dynamodb_client, enable_parallel_execution, max_workers)
        
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Error handling components
        self.error_classifier = ErrorClassifier()
        self.retry_handler = RetryHandler()
        self.degradation_handler = GracefulDegradationHandler()
        self.recovery_handler = WorkflowRecoveryHandler()
        
        # Circuit breakers for each agent
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.enable_circuit_breakers = enable_circuit_breakers
        
        # Bulkheads for resource isolation
        self.bulkheads: Dict[str, BulkheadConfig] = {}
        self.enable_bulkheads = enable_bulkheads
        
        # Health monitoring
        self.agent_health: Dict[str, AgentHealthStatus] = {}
        self.workflow_health: Dict[str, WorkflowHealthStatus] = {}
        
        # Error metrics
        self.error_metrics = ErrorMetrics()
        
        # Initialize circuit breakers and bulkheads for each agent
        for agent_name in self.agent_sequence:
            if self.enable_circuit_breakers:
                self.circuit_breakers[agent_name] = CircuitBreakerState(
                    agent_name=agent_name,
                    state='closed',
                    failure_threshold=5,  # Default threshold
                    recovery_timeout=60   # Default timeout in seconds
                )
            
            if self.enable_bulkheads:
                self.bulkheads[agent_name] = BulkheadConfig(
                    agent_name=agent_name,
                    max_concurrent_requests=3,  # Default max concurrent
                    queue_size=10,              # Default queue size
                    timeout_seconds=300         # Default timeout
                )
            
            # Initialize health status
            self.agent_health[agent_name] = AgentHealthStatus(
                agent_name=agent_name,
                status='healthy'
            )
    
    async def execute_agent_with_recovery(self, workflow_id: str, agent_name: str,
                                        agent_instance: Any, input_data: Dict[str, Any],
                                        retry_config: Optional[RetryConfig] = None) -> AgentExecutionResult:
        """
        Execute an agent with comprehensive error handling and recovery.
        
        Args:
            workflow_id: Unique workflow identifier
            agent_name: Name of the agent to execute
            agent_instance: Instance of the agent
            input_data: Input data for the agent
            retry_config: Optional retry configuration
            
        Returns:
            AgentExecutionResult with execution details and recovery information
        """
        start_time = datetime.utcnow()
        execution_start = time.time()
        
        # Check circuit breaker
        if self.enable_circuit_breakers and not self._check_circuit_breaker(agent_name):
            error_msg = f"Circuit breaker open for {agent_name}"
            self.logger.warning(error_msg)
            
            # Apply graceful degradation
            error_info = self.error_classifier.classify_error(
                Exception(error_msg), agent_name, workflow_id
            )
            fallback_results = self.degradation_handler.handle_agent_failure(
                agent_name, error_info
            )
            
            return AgentExecutionResult(
                agent_name=agent_name,
                success=False,
                results=fallback_results,
                error=Exception(error_msg),
                execution_time=0.0,
                start_time=start_time,
                end_time=datetime.utcnow()
            )
        
        # Check bulkhead capacity
        if self.enable_bulkheads and not self._acquire_bulkhead_slot(agent_name):
            error_msg = f"Bulkhead capacity exceeded for {agent_name}"
            self.logger.warning(error_msg)
            
            # Queue the request or apply degradation
            return await self._handle_bulkhead_overflow(
                workflow_id, agent_name, agent_instance, input_data
            )
        
        try:
            # Execute with retry logic
            result = await self._execute_with_retry(
                workflow_id, agent_name, agent_instance, input_data, retry_config
            )
            
            # Record success
            self._record_agent_success(agent_name)
            
            return result
            
        except Exception as e:
            # Record failure
            self._record_agent_failure(agent_name, e)
            
            # Create enhanced error
            error_context = ErrorContext(
                operation=f"execute_{agent_name}",
                input_data=input_data,
                execution_time=time.time() - execution_start,
                retry_count=0
            )
            
            error_info = self.error_classifier.classify_error(e, agent_name, workflow_id)
            enhanced_error = self._create_enhanced_error(error_info, error_context)
            
            # Apply recovery strategy
            recovery_result = await self._apply_recovery_strategy(
                workflow_id, agent_name, enhanced_error, input_data
            )
            
            return recovery_result
            
        finally:
            # Release bulkhead slot
            if self.enable_bulkheads:
                self._release_bulkhead_slot(agent_name)
    
    async def _execute_with_retry(self, workflow_id: str, agent_name: str,
                                agent_instance: Any, input_data: Dict[str, Any],
                                retry_config: Optional[RetryConfig] = None) -> AgentExecutionResult:
        """Execute agent with retry logic."""
        config = retry_config or RetryConfig(
            max_retries=3,    # Default max retries
            base_delay=1.0,   # Default base delay
            max_delay=60.0    # Default max delay
        )
        
        last_exception = None
        
        for attempt in range(config.max_retries + 1):
            try:
                log_agent_activity(
                    self.logger, agent_name, workflow_id,
                    f"Executing attempt {attempt + 1}/{config.max_retries + 1}"
                )
                
                # Execute the agent
                result = await self._execute_agent_async(
                    workflow_id, agent_name, agent_instance, input_data
                )
                
                if result.success:
                    log_agent_activity(
                        self.logger, agent_name, workflow_id,
                        f"Execution successful on attempt {attempt + 1}"
                    )
                    return result
                else:
                    raise result.error or Exception("Agent execution failed")
                    
            except Exception as e:
                last_exception = e
                
                # Classify error
                error_info = self.error_classifier.classify_error(
                    e, agent_name, workflow_id, {'attempt': attempt + 1}
                )
                
                log_agent_activity(
                    self.logger, agent_name, workflow_id,
                    f"Attempt {attempt + 1} failed: {error_info.category.value} - {error_info.message}",
                    {'error_category': error_info.category.value, 'recoverable': error_info.recoverable}
                )
                
                # Check if we should retry
                if not self._should_retry(error_info, attempt, config):
                    break
                
                # Calculate delay and wait
                if attempt < config.max_retries:
                    delay = self.retry_handler._calculate_delay(attempt, config, error_info.category)
                    log_agent_activity(
                        self.logger, agent_name, workflow_id,
                        f"Retrying in {delay:.2f} seconds"
                    )
                    await asyncio.sleep(delay)
        
        # All retries failed
        raise last_exception
    
    async def _apply_recovery_strategy(self, workflow_id: str, agent_name: str,
                                     enhanced_error: EnhancedWorkflowError,
                                     input_data: Dict[str, Any]) -> AgentExecutionResult:
        """Apply recovery strategy for failed agent."""
        
        # Determine recovery strategy
        recovery_strategy = self._determine_recovery_strategy(enhanced_error)
        enhanced_error.recovery_strategy = recovery_strategy
        
        log_workflow_event(
            self.logger, workflow_id, 'recovery',
            f"Applying recovery strategy for {agent_name}: {recovery_strategy.action.value}",
            agent=agent_name, strategy=recovery_strategy.action.value
        )
        
        if recovery_strategy.action == RecoveryAction.FALLBACK:
            # Apply graceful degradation
            fallback_results = self.degradation_handler.handle_agent_failure(
                agent_name, enhanced_error, recovery_strategy.fallback_data
            )
            
            return AgentExecutionResult(
                agent_name=agent_name,
                success=False,
                results=fallback_results,
                error=enhanced_error.exception,
                execution_time=0.0,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow()
            )
        
        elif recovery_strategy.action == RecoveryAction.SKIP:
            # Skip this agent and continue
            log_workflow_event(
                self.logger, workflow_id, 'skip',
                f"Skipping {agent_name}: {recovery_strategy.skip_reason}",
                agent=agent_name
            )
            
            return AgentExecutionResult(
                agent_name=agent_name,
                success=False,
                results={'status': 'skipped', 'reason': recovery_strategy.skip_reason},
                error=enhanced_error.exception,
                execution_time=0.0,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow()
            )
        
        elif recovery_strategy.action == RecoveryAction.ABORT:
            # Abort the workflow
            log_workflow_event(
                self.logger, workflow_id, 'abort',
                f"Aborting workflow due to critical error in {agent_name}",
                agent=agent_name
            )
            raise enhanced_error.exception
        
        else:
            # Default to fallback
            fallback_results = self.degradation_handler.handle_agent_failure(
                agent_name, enhanced_error
            )
            
            return AgentExecutionResult(
                agent_name=agent_name,
                success=False,
                results=fallback_results,
                error=enhanced_error.exception,
                execution_time=0.0,
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow()
            )
    
    def _determine_recovery_strategy(self, enhanced_error: EnhancedWorkflowError) -> RecoveryStrategy:
        """Determine the best recovery strategy for an error."""
        
        # Critical errors should abort
        if enhanced_error.impact == ErrorImpact.CRITICAL:
            return RecoveryStrategy(
                action=RecoveryAction.ABORT,
                description="Critical error requires workflow termination",
                estimated_success_rate=0.0
            )
        
        # Authentication errors should abort (can't recover without intervention)
        if enhanced_error.category == 'authentication_error':
            return RecoveryStrategy(
                action=RecoveryAction.ABORT,
                description="Authentication error requires manual intervention",
                estimated_success_rate=0.0
            )
        
        # Validation errors should skip
        if enhanced_error.category == 'validation_error':
            return RecoveryStrategy(
                action=RecoveryAction.SKIP,
                description="Invalid input data cannot be processed",
                estimated_success_rate=0.0,
                skip_reason="Input validation failed"
            )
        
        # For other errors, use fallback with degraded functionality
        success_rate = 0.8  # Default success rate for fallback
        
        # Adjust success rate based on error category
        if enhanced_error.category in ['network_error', 'timeout_error']:
            success_rate = 0.9
        elif enhanced_error.category == 'api_error':
            success_rate = 0.7
        elif enhanced_error.category == 'processing_error':
            success_rate = 0.6
        
        return RecoveryStrategy(
            action=RecoveryAction.FALLBACK,
            description=f"Apply graceful degradation for {enhanced_error.category}",
            estimated_success_rate=success_rate,
            fallback_data={}
        )
    
    def _create_enhanced_error(self, error_info, error_context: ErrorContext) -> EnhancedWorkflowError:
        """Create an enhanced workflow error with recovery information."""
        
        # Determine error impact
        impact = ErrorImpact.MODERATE
        if error_info.severity.value == 'critical':
            impact = ErrorImpact.CRITICAL
        elif error_info.severity.value == 'high':
            impact = ErrorImpact.SEVERE
        elif error_info.severity.value == 'low':
            impact = ErrorImpact.MINIMAL
        
        enhanced_error = EnhancedWorkflowError(
            error_id=str(uuid.uuid4()),
            agent=error_info.agent,
            error_type=type(error_info.exception).__name__,
            message=error_info.message,
            timestamp=error_info.timestamp,
            recoverable=error_info.recoverable,
            category=error_info.category.value,
            severity=error_info.severity.value,
            impact=impact,
            context=error_context,
            exception=error_info.exception
        )
        
        # Add to metrics
        self.error_metrics.add_error(enhanced_error)
        
        return enhanced_error
    
    def _check_circuit_breaker(self, agent_name: str) -> bool:
        """Check if circuit breaker allows request."""
        if agent_name not in self.circuit_breakers:
            return True
        
        return self.circuit_breakers[agent_name].should_allow_request()
    
    def _acquire_bulkhead_slot(self, agent_name: str) -> bool:
        """Try to acquire a bulkhead slot for agent execution."""
        if agent_name not in self.bulkheads:
            return True
        
        return self.bulkheads[agent_name].acquire_slot()
    
    def _release_bulkhead_slot(self, agent_name: str, was_queued: bool = False) -> None:
        """Release a bulkhead slot after execution."""
        if agent_name in self.bulkheads:
            self.bulkheads[agent_name].release_slot(was_queued)
    
    async def _handle_bulkhead_overflow(self, workflow_id: str, agent_name: str,
                                      agent_instance: Any, input_data: Dict[str, Any]) -> AgentExecutionResult:
        """Handle bulkhead capacity overflow."""
        
        # For now, apply graceful degradation
        # In a more sophisticated implementation, we could queue the request
        error_msg = f"Bulkhead capacity exceeded for {agent_name}"
        error_info = self.error_classifier.classify_error(
            Exception(error_msg), agent_name, workflow_id
        )
        
        fallback_results = self.degradation_handler.handle_agent_failure(
            agent_name, error_info
        )
        
        return AgentExecutionResult(
            agent_name=agent_name,
            success=False,
            results=fallback_results,
            error=Exception(error_msg),
            execution_time=0.0,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow()
        )
    
    def _record_agent_success(self, agent_name: str) -> None:
        """Record successful agent execution."""
        if self.enable_circuit_breakers and agent_name in self.circuit_breakers:
            self.circuit_breakers[agent_name].record_success()
        
        if agent_name in self.agent_health:
            health = self.agent_health[agent_name]
            health.last_success = datetime.utcnow()
            health.consecutive_successes += 1
            health.consecutive_failures = 0
            health.status = 'healthy'
    
    def _record_agent_failure(self, agent_name: str, exception: Exception) -> None:
        """Record failed agent execution."""
        if self.enable_circuit_breakers and agent_name in self.circuit_breakers:
            self.circuit_breakers[agent_name].record_failure()
        
        if agent_name in self.agent_health:
            health = self.agent_health[agent_name]
            health.last_failure = datetime.utcnow()
            health.consecutive_failures += 1
            health.consecutive_successes = 0
            
            # Update status based on failure count
            if health.consecutive_failures >= 3:
                health.status = 'failed'
            elif health.consecutive_failures >= 1:
                health.status = 'degraded'
    
    def _should_retry(self, error_info, attempt: int, config: RetryConfig) -> bool:
        """Determine if we should retry based on error info and attempt count."""
        return self.retry_handler._should_retry(error_info, attempt, config)
    
    def get_workflow_health(self, workflow_id: str) -> WorkflowHealthStatus:
        """Get comprehensive health status for a workflow."""
        if workflow_id not in self.workflow_health:
            # Create initial health status
            agent_statuses = {}
            for agent_name in self.agent_sequence:
                if agent_name in self.agent_health:
                    agent_statuses[agent_name] = self.agent_health[agent_name]
                else:
                    agent_statuses[agent_name] = AgentHealthStatus(
                        agent_name=agent_name, status='healthy'
                    )
            
            self.workflow_health[workflow_id] = WorkflowHealthStatus(
                workflow_id=workflow_id,
                overall_status='healthy',
                agent_statuses=agent_statuses
            )
        
        return self.workflow_health[workflow_id]
    
    def get_error_metrics(self) -> ErrorMetrics:
        """Get comprehensive error metrics."""
        return self.error_metrics
    
    def reset_circuit_breaker(self, agent_name: str) -> bool:
        """Manually reset a circuit breaker."""
        if agent_name in self.circuit_breakers:
            self.circuit_breakers[agent_name].state = 'closed'
            self.circuit_breakers[agent_name].failure_count = 0
            self.circuit_breakers[agent_name].success_count = 0
            self.logger.info(f"Circuit breaker reset for {agent_name}")
            return True
        return False
    
    def get_circuit_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers."""
        status = {}
        for agent_name, breaker in self.circuit_breakers.items():
            status[agent_name] = {
                'state': breaker.state,
                'failure_count': breaker.failure_count,
                'success_count': breaker.success_count,
                'last_failure_time': breaker.last_failure_time.isoformat() if breaker.last_failure_time else None
            }
        return status
    
    def get_bulkhead_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all bulkheads."""
        status = {}
        for agent_name, bulkhead in self.bulkheads.items():
            status[agent_name] = {
                'current_requests': bulkhead.current_requests,
                'queued_requests': bulkhead.queued_requests,
                'max_concurrent': bulkhead.max_concurrent_requests,
                'queue_size': bulkhead.queue_size,
                'utilization': bulkhead.current_requests / bulkhead.max_concurrent_requests
            }
        return status