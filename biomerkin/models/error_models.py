"""
Enhanced error models for comprehensive error handling and recovery.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .base import WorkflowError


class RecoveryAction(Enum):
    """Types of recovery actions that can be taken."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ABORT = "abort"
    CONTINUE_PARTIAL = "continue_partial"


class ErrorImpact(Enum):
    """Impact level of errors on workflow execution."""
    MINIMAL = "minimal"  # Can continue with full functionality
    MODERATE = "moderate"  # Can continue with reduced functionality
    SEVERE = "severe"  # Can continue with significant limitations
    CRITICAL = "critical"  # Cannot continue


@dataclass
class ErrorContext:
    """Additional context information for errors."""
    operation: str
    input_data: Optional[Dict[str, Any]] = None
    api_endpoint: Optional[str] = None
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    execution_time: Optional[float] = None
    memory_usage: Optional[float] = None
    retry_count: int = 0
    previous_errors: List[str] = field(default_factory=list)


@dataclass
class RecoveryStrategy:
    """Strategy for recovering from an error."""
    action: RecoveryAction
    description: str
    estimated_success_rate: float
    fallback_data: Optional[Dict[str, Any]] = None
    retry_config: Optional[Dict[str, Any]] = None
    skip_reason: Optional[str] = None
    continue_conditions: Optional[List[str]] = None


@dataclass
class EnhancedWorkflowError:
    """Enhanced workflow error with additional recovery information."""
    error_id: str
    agent: str
    error_type: str
    message: str
    timestamp: datetime
    recoverable: bool
    category: str
    severity: str
    impact: ErrorImpact
    context: ErrorContext
    exception: Exception
    recovery_strategy: Optional[RecoveryStrategy] = None
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None
    resolution_method: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = {
            'error_id': self.error_id,
            'agent': self.agent,
            'error_type': self.error_type,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'recoverable': self.recoverable,
            'category': self.category,
            'severity': self.severity,
            'impact': self.impact.value,
            'context': {
                'operation': self.context.operation,
                'input_data': self.context.input_data,
                'api_endpoint': self.context.api_endpoint,
                'response_code': self.context.response_code,
                'response_body': self.context.response_body,
                'execution_time': self.context.execution_time,
                'memory_usage': self.context.memory_usage,
                'retry_count': self.context.retry_count,
                'previous_errors': self.context.previous_errors
            },
            'resolved': self.resolved,
            'resolution_timestamp': self.resolution_timestamp.isoformat() if self.resolution_timestamp else None,
            'resolution_method': self.resolution_method
        }
        
        if self.recovery_strategy:
            data['recovery_strategy'] = {
                'action': self.recovery_strategy.action.value,
                'description': self.recovery_strategy.description,
                'estimated_success_rate': self.recovery_strategy.estimated_success_rate,
                'fallback_data': self.recovery_strategy.fallback_data,
                'retry_config': self.recovery_strategy.retry_config,
                'skip_reason': self.recovery_strategy.skip_reason,
                'continue_conditions': self.recovery_strategy.continue_conditions
            }
        
        return data


@dataclass
class AgentHealthStatus:
    """Health status of an individual agent."""
    agent_name: str
    status: str  # healthy, degraded, failed, recovering
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    error_rate: float = 0.0
    average_response_time: float = 0.0
    current_errors: List[EnhancedWorkflowError] = field(default_factory=list)
    recovery_attempts: int = 0
    
    def is_healthy(self) -> bool:
        """Check if agent is in healthy state."""
        return self.status == 'healthy' and self.consecutive_failures == 0
    
    def is_degraded(self) -> bool:
        """Check if agent is in degraded state."""
        return self.status == 'degraded' or (self.error_rate > 0.1 and self.consecutive_failures < 3)
    
    def is_failed(self) -> bool:
        """Check if agent has failed."""
        return self.status == 'failed' or self.consecutive_failures >= 3


@dataclass
class WorkflowHealthStatus:
    """Overall health status of a workflow."""
    workflow_id: str
    overall_status: str  # healthy, degraded, failed, recovering
    agent_statuses: Dict[str, AgentHealthStatus]
    total_errors: int = 0
    resolved_errors: int = 0
    active_errors: int = 0
    recovery_in_progress: bool = False
    degraded_functionality: List[str] = field(default_factory=list)
    estimated_completion_probability: float = 1.0
    
    def get_failed_agents(self) -> List[str]:
        """Get list of failed agents."""
        return [name for name, status in self.agent_statuses.items() if status.is_failed()]
    
    def get_degraded_agents(self) -> List[str]:
        """Get list of degraded agents."""
        return [name for name, status in self.agent_statuses.items() if status.is_degraded()]
    
    def can_continue(self) -> bool:
        """Check if workflow can continue execution."""
        failed_agents = self.get_failed_agents()
        
        # Critical agents that must be functional
        critical_agents = ['genomics']
        
        for agent in critical_agents:
            if agent in failed_agents:
                return False
        
        return True


@dataclass
class ErrorMetrics:
    """Metrics for error tracking and analysis."""
    total_errors: int = 0
    errors_by_category: Dict[str, int] = field(default_factory=dict)
    errors_by_agent: Dict[str, int] = field(default_factory=dict)
    errors_by_severity: Dict[str, int] = field(default_factory=dict)
    recovery_success_rate: float = 0.0
    average_recovery_time: float = 0.0
    most_common_errors: List[str] = field(default_factory=list)
    error_trends: Dict[str, List[int]] = field(default_factory=dict)
    
    def add_error(self, error: EnhancedWorkflowError) -> None:
        """Add an error to the metrics."""
        self.total_errors += 1
        
        # Update category counts
        if error.category not in self.errors_by_category:
            self.errors_by_category[error.category] = 0
        self.errors_by_category[error.category] += 1
        
        # Update agent counts
        if error.agent not in self.errors_by_agent:
            self.errors_by_agent[error.agent] = 0
        self.errors_by_agent[error.agent] += 1
        
        # Update severity counts
        if error.severity not in self.errors_by_severity:
            self.errors_by_severity[error.severity] = 0
        self.errors_by_severity[error.severity] += 1
    
    def calculate_recovery_rate(self, resolved_errors: int) -> None:
        """Calculate recovery success rate."""
        if self.total_errors > 0:
            self.recovery_success_rate = resolved_errors / self.total_errors
        else:
            self.recovery_success_rate = 1.0


@dataclass
class CircuitBreakerState:
    """State for circuit breaker pattern implementation."""
    agent_name: str
    state: str  # closed, open, half_open
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[datetime] = None
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    success_threshold: int = 3  # for half-open to closed transition
    
    def should_allow_request(self) -> bool:
        """Check if request should be allowed based on circuit breaker state."""
        if self.state == 'closed':
            return True
        elif self.state == 'open':
            # Check if recovery timeout has passed
            if self.last_failure_time and \
               (datetime.utcnow() - self.last_failure_time).seconds >= self.recovery_timeout:
                self.state = 'half_open'
                self.success_count = 0
                return True
            return False
        elif self.state == 'half_open':
            return True
        
        return False
    
    def record_success(self) -> None:
        """Record a successful operation."""
        if self.state == 'half_open':
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = 'closed'
                self.failure_count = 0
        elif self.state == 'closed':
            self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record a failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.state == 'closed' and self.failure_count >= self.failure_threshold:
            self.state = 'open'
        elif self.state == 'half_open':
            self.state = 'open'
            self.success_count = 0


@dataclass
class BulkheadConfig:
    """Configuration for bulkhead pattern implementation."""
    agent_name: str
    max_concurrent_requests: int = 10
    queue_size: int = 100
    timeout_seconds: int = 30
    current_requests: int = 0
    queued_requests: int = 0
    
    def can_accept_request(self) -> bool:
        """Check if bulkhead can accept new request."""
        return (self.current_requests < self.max_concurrent_requests or 
                self.queued_requests < self.queue_size)
    
    def acquire_slot(self) -> bool:
        """Try to acquire a slot for request execution."""
        if self.current_requests < self.max_concurrent_requests:
            self.current_requests += 1
            return True
        elif self.queued_requests < self.queue_size:
            self.queued_requests += 1
            return True
        return False
    
    def release_slot(self, was_queued: bool = False) -> None:
        """Release a slot after request completion."""
        if was_queued:
            self.queued_requests = max(0, self.queued_requests - 1)
        else:
            self.current_requests = max(0, self.current_requests - 1)