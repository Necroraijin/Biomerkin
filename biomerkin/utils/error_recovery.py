"""
Advanced Error Recovery and Resilience Framework.
Provides intelligent error handling and recovery mechanisms.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

from .logging_config import get_logger


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Recovery strategies."""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    ESCALATE = "escalate"
    CIRCUIT_BREAK = "circuit_break"


@dataclass
class ErrorContext:
    """Context information for error handling."""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    component: str
    timestamp: datetime
    retry_count: int = 0
    max_retries: int = 3
    context_data: Dict[str, Any] = None


@dataclass
class RecoveryAction:
    """Recovery action to take."""
    strategy: RecoveryStrategy
    action: Callable
    delay: float = 0
    max_attempts: int = 1
    success_criteria: Optional[Callable] = None


class ErrorRecoveryManager:
    """
    Advanced error recovery and resilience manager.
    Provides intelligent error handling and recovery mechanisms.
    """
    
    def __init__(self):
        """Initialize error recovery manager."""
        self.logger = get_logger(__name__)
        self.circuit_breakers = {}
        self.error_history = []
        self.recovery_strategies = self._initialize_recovery_strategies()
    
    def _initialize_recovery_strategies(self) -> Dict[str, List[RecoveryAction]]:
        """Initialize recovery strategies for different error types."""
        return {
            "network_error": [
                RecoveryAction(
                    strategy=RecoveryStrategy.RETRY,
                    action=self._retry_with_backoff,
                    delay=1.0,
                    max_attempts=3
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.FALLBACK,
                    action=self._use_cached_data,
                    max_attempts=1
                )
            ],
            "api_rate_limit": [
                RecoveryAction(
                    strategy=RecoveryStrategy.RETRY,
                    action=self._retry_with_exponential_backoff,
                    delay=5.0,
                    max_attempts=5
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.CIRCUIT_BREAK,
                    action=self._open_circuit_breaker,
                    max_attempts=1
                )
            ],
            "bedrock_error": [
                RecoveryAction(
                    strategy=RecoveryStrategy.RETRY,
                    action=self._retry_bedrock_request,
                    delay=2.0,
                    max_attempts=3
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.FALLBACK,
                    action=self._use_simplified_analysis,
                    max_attempts=1
                )
            ],
            "data_validation_error": [
                RecoveryAction(
                    strategy=RecoveryStrategy.FALLBACK,
                    action=self._sanitize_input_data,
                    max_attempts=1
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.ESCALATE,
                    action=self._log_validation_error,
                    max_attempts=1
                )
            ],
            "timeout_error": [
                RecoveryAction(
                    strategy=RecoveryStrategy.RETRY,
                    action=self._retry_with_timeout_increase,
                    delay=1.0,
                    max_attempts=2
                ),
                RecoveryAction(
                    strategy=RecoveryStrategy.SKIP,
                    action=self._skip_timeout_operation,
                    max_attempts=1
                )
            ]
        }
    
    async def handle_error(self, error_context: ErrorContext, 
                          operation: Callable, *args, **kwargs) -> Any:
        """
        Handle error with appropriate recovery strategy.
        
        Args:
            error_context: Context of the error
            operation: Operation to retry
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation or recovery action
        """
        self.logger.error(f"Handling error: {error_context.error_type} - {error_context.error_message}")
        
        # Record error in history
        self.error_history.append(error_context)
        
        # Get recovery strategies for this error type
        strategies = self.recovery_strategies.get(error_context.error_type, [])
        
        if not strategies:
            self.logger.warning(f"No recovery strategies for error type: {error_context.error_type}")
            return await self._default_error_handling(error_context, operation, *args, **kwargs)
        
        # Try each recovery strategy
        for strategy in strategies:
            try:
                result = await self._execute_recovery_strategy(
                    strategy, error_context, operation, *args, **kwargs
                )
                
                if result is not None:
                    self.logger.info(f"Recovery successful using strategy: {strategy.strategy.value}")
                    return result
                    
            except Exception as e:
                self.logger.warning(f"Recovery strategy {strategy.strategy.value} failed: {e}")
                continue
        
        # If all strategies failed, escalate
        return await self._escalate_error(error_context)
    
    async def _execute_recovery_strategy(self, strategy: RecoveryAction, 
                                       error_context: ErrorContext,
                                       operation: Callable, *args, **kwargs) -> Any:
        """Execute a specific recovery strategy."""
        if strategy.delay > 0:
            await asyncio.sleep(strategy.delay)
        
        for attempt in range(strategy.max_attempts):
            try:
                result = await strategy.action(error_context, operation, *args, **kwargs)
                
                # Check success criteria if provided
                if strategy.success_criteria and not strategy.success_criteria(result):
                    continue
                
                return result
                
            except Exception as e:
                self.logger.warning(f"Recovery attempt {attempt + 1} failed: {e}")
                if attempt < strategy.max_attempts - 1:
                    await asyncio.sleep(strategy.delay * (2 ** attempt))  # Exponential backoff
        
        return None
    
    async def _retry_with_backoff(self, error_context: ErrorContext, 
                                operation: Callable, *args, **kwargs) -> Any:
        """Retry operation with exponential backoff."""
        if error_context.retry_count >= error_context.max_retries:
            raise Exception("Max retries exceeded")
        
        error_context.retry_count += 1
        delay = 2 ** error_context.retry_count
        await asyncio.sleep(delay)
        
        return await operation(*args, **kwargs)
    
    async def _retry_with_exponential_backoff(self, error_context: ErrorContext,
                                            operation: Callable, *args, **kwargs) -> Any:
        """Retry with exponential backoff for rate limiting."""
        if error_context.retry_count >= 5:  # Max 5 retries for rate limits
            raise Exception("Max retries for rate limit exceeded")
        
        error_context.retry_count += 1
        delay = min(60, 5 * (2 ** error_context.retry_count))  # Cap at 60 seconds
        await asyncio.sleep(delay)
        
        return await operation(*args, **kwargs)
    
    async def _retry_bedrock_request(self, error_context: ErrorContext,
                                   operation: Callable, *args, **kwargs) -> Any:
        """Retry Bedrock request with specific handling."""
        if error_context.retry_count >= 3:
            raise Exception("Max Bedrock retries exceeded")
        
        error_context.retry_count += 1
        
        # Add jitter to avoid thundering herd
        jitter = time.time() % 1
        await asyncio.sleep(2 + jitter)
        
        return await operation(*args, **kwargs)
    
    async def _use_cached_data(self, error_context: ErrorContext,
                             operation: Callable, *args, **kwargs) -> Any:
        """Use cached data as fallback."""
        # This would integrate with your cache system
        self.logger.info("Using cached data as fallback")
        
        # Return cached result if available
        cache_key = self._generate_cache_key(operation, *args, **kwargs)
        cached_result = await self._get_cached_result(cache_key)
        
        if cached_result:
            return cached_result
        
        raise Exception("No cached data available")
    
    async def _use_simplified_analysis(self, error_context: ErrorContext,
                                     operation: Callable, *args, **kwargs) -> Any:
        """Use simplified analysis as fallback."""
        self.logger.info("Using simplified analysis as fallback")
        
        # Implement simplified version of the operation
        # This would be specific to each agent
        return {"fallback_result": True, "message": "Simplified analysis used"}
    
    async def _sanitize_input_data(self, error_context: ErrorContext,
                                 operation: Callable, *args, **kwargs) -> Any:
        """Sanitize input data and retry."""
        self.logger.info("Sanitizing input data")
        
        # Sanitize the input data
        sanitized_args = self._sanitize_args(*args)
        sanitized_kwargs = self._sanitize_kwargs(**kwargs)
        
        return await operation(*sanitized_args, **sanitized_kwargs)
    
    async def _retry_with_timeout_increase(self, error_context: ErrorContext,
                                         operation: Callable, *args, **kwargs) -> Any:
        """Retry with increased timeout."""
        if error_context.retry_count >= 2:
            raise Exception("Max timeout retries exceeded")
        
        error_context.retry_count += 1
        
        # Increase timeout for the operation
        timeout = 30 * (2 ** error_context.retry_count)  # 30s, 60s, 120s
        
        return await asyncio.wait_for(operation(*args, **kwargs), timeout=timeout)
    
    async def _skip_timeout_operation(self, error_context: ErrorContext,
                                    operation: Callable, *args, **kwargs) -> Any:
        """Skip the operation that's timing out."""
        self.logger.warning("Skipping operation due to timeout")
        return {"skipped": True, "reason": "timeout"}
    
    async def _open_circuit_breaker(self, error_context: ErrorContext,
                                  operation: Callable, *args, **kwargs) -> Any:
        """Open circuit breaker for failing service."""
        component = error_context.component
        self.circuit_breakers[component] = {
            "open": True,
            "opened_at": datetime.now(),
            "failure_count": 0
        }
        
        self.logger.warning(f"Circuit breaker opened for {component}")
        raise Exception(f"Circuit breaker open for {component}")
    
    async def _default_error_handling(self, error_context: ErrorContext,
                                    operation: Callable, *args, **kwargs) -> Any:
        """Default error handling when no specific strategy exists."""
        self.logger.error(f"No recovery strategy for {error_context.error_type}")
        return {"error": error_context.error_message, "recovered": False}
    
    async def _escalate_error(self, error_context: ErrorContext) -> Any:
        """Escalate error when all recovery strategies fail."""
        self.logger.critical(f"Escalating error: {error_context.error_type}")
        
        # Log critical error
        # Send alert to monitoring system
        # Return error response
        
        return {
            "error": "Critical error - all recovery strategies failed",
            "error_type": error_context.error_type,
            "escalated": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_cache_key(self, operation: Callable, *args, **kwargs) -> str:
        """Generate cache key for operation."""
        import hashlib
        
        key_data = {
            "operation": operation.__name__,
            "args": str(args),
            "kwargs": str(sorted(kwargs.items()))
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result (placeholder implementation)."""
        # This would integrate with your actual cache system
        return None
    
    def _sanitize_args(self, *args) -> tuple:
        """Sanitize function arguments."""
        sanitized = []
        for arg in args:
            if isinstance(arg, str):
                # Remove potentially problematic characters
                sanitized.append(arg.strip()[:1000])  # Limit length
            else:
                sanitized.append(arg)
        return tuple(sanitized)
    
    def _sanitize_kwargs(self, **kwargs) -> dict:
        """Sanitize function keyword arguments."""
        sanitized = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                sanitized[key] = value.strip()[:1000]  # Limit length
            else:
                sanitized[key] = value
        return sanitized
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and health metrics."""
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        
        recent_errors = [
            error for error in self.error_history 
            if error.timestamp > last_hour
        ]
        
        error_counts = {}
        for error in recent_errors:
            error_type = error.error_type
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors": len(recent_errors),
            "error_types": error_counts,
            "circuit_breakers": len(self.circuit_breakers),
            "timestamp": now.isoformat()
        }


# Global error recovery manager
error_recovery_manager = ErrorRecoveryManager()

