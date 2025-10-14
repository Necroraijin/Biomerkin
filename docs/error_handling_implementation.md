# Error Handling and Recovery Implementation

## Overview

This document describes the comprehensive error handling and recovery system implemented for the Biomerkin multi-agent system. The implementation addresses all requirements from task 12, providing robust error handling, retry logic, graceful degradation, and workflow recovery mechanisms.

## Components Implemented

### 1. Error Classification System (`biomerkin/utils/error_handling.py`)

**ErrorClassifier**: Automatically categorizes errors into appropriate types for handling:

- **Network Errors**: Connection failures, timeouts
- **API Errors**: HTTP errors, service unavailable
- **Rate Limit Errors**: API rate limiting (429 errors)
- **Authentication Errors**: 401/403 errors, access denied
- **Validation Errors**: Invalid input data
- **Processing Errors**: Internal processing failures
- **System Errors**: Memory, permission, resource errors
- **Unknown Errors**: Fallback category

**Error Severity Levels**:
- **Low**: Validation errors, minor issues
- **Medium**: Network errors, API failures
- **High**: Authentication errors, system issues
- **Critical**: Memory errors, critical system failures

### 2. Retry Logic with Exponential Backoff

**RetryHandler**: Implements sophisticated retry mechanisms:

- **Exponential Backoff**: Delays increase exponentially between retries
- **Jitter**: Random variation to prevent thundering herd
- **Category-Specific Delays**: Different strategies for different error types
- **Max Retry Limits**: Configurable maximum retry attempts
- **Non-Recoverable Detection**: Skips retries for authentication/validation errors

**Features**:
- Async and sync retry support
- Configurable base delay, max delay, and exponential base
- Smart retry decisions based on error classification
- Performance monitoring and timing metrics

### 3. Graceful Degradation System

**GracefulDegradationHandler**: Provides fallback strategies when agents fail:

**Agent-Specific Fallbacks**:
- **GenomicsAgent**: Returns empty results with error indicators
- **ProteomicsAgent**: Provides basic structure data placeholders
- **LiteratureAgent**: Returns "unavailable" messages with search terms
- **DrugAgent**: Returns partial drug candidates if available
- **DecisionAgent**: Generates limited reports with available data

**Fallback Features**:
- Preserves partial results when possible
- Clear error messaging and limitations
- Maintains workflow continuity
- Structured fallback data format

### 4. Enhanced Agent Base Classes

**BaseAgent** (`biomerkin/agents/base_agent.py`):
- Built-in error handling and retry logic
- Performance metrics tracking
- Input/output validation
- HTTP session management with connection pooling
- Graceful resource cleanup

**APIAgent** (extends BaseAgent):
- Rate limiting for external APIs
- API key management
- Request timeout handling
- Connection pooling optimization

### 5. Circuit Breaker Pattern

**CircuitBreakerState**: Prevents cascading failures:

**States**:
- **Closed**: Normal operation, requests allowed
- **Open**: Failures exceeded threshold, requests blocked
- **Half-Open**: Testing recovery, limited requests allowed

**Features**:
- Configurable failure thresholds
- Automatic recovery timeout
- Success threshold for closing circuit
- Per-agent circuit breaker isolation

### 6. Bulkhead Pattern

**BulkheadConfig**: Resource isolation and capacity management:

- **Concurrent Request Limits**: Prevents resource exhaustion
- **Request Queuing**: Handles overflow with queuing
- **Timeout Management**: Prevents hanging requests
- **Utilization Monitoring**: Tracks resource usage

### 7. Enhanced Error Models

**EnhancedWorkflowError**: Comprehensive error information:
- Unique error IDs for tracking
- Error categorization and severity
- Recovery strategy information
- Resolution tracking
- Contextual information (operation, timing, etc.)

**Error Metrics**: System-wide error tracking:
- Error counts by category and agent
- Recovery success rates
- Performance impact analysis
- Trend analysis capabilities

### 8. Error Recovery Orchestrator

**ErrorRecoveryOrchestrator**: Enhanced orchestrator with error handling:

**Features**:
- Circuit breaker integration
- Bulkhead pattern implementation
- Agent health monitoring
- Workflow recovery strategies
- Comprehensive error metrics
- Recovery strategy selection

**Recovery Strategies**:
- **Fallback**: Apply graceful degradation
- **Skip**: Skip failed agent and continue
- **Retry**: Attempt operation again
- **Abort**: Terminate workflow for critical errors

### 9. Workflow Recovery System

**WorkflowRecoveryHandler**: Determines workflow continuation strategies:

**Recovery Logic**:
- Analyzes failed agents and dependencies
- Determines if workflow can continue
- Identifies required vs. optional agents
- Provides degraded functionality options

**Continuation Strategies**:
- **Full Recovery**: All agents functional
- **Partial Recovery**: Some agents failed but workflow continues
- **Failed Recovery**: Critical agents failed, workflow cannot continue

### 10. Health Monitoring

**Agent Health Tracking**:
- Success/failure rates
- Consecutive failure counts
- Response time monitoring
- Health status classification (healthy, degraded, failed)

**Workflow Health Assessment**:
- Overall workflow status
- Individual agent health
- Degraded functionality tracking
- Completion probability estimation

## Testing Implementation

### Unit Tests (`tests/test_error_handling.py`)
- Error classification tests
- Retry logic verification
- Graceful degradation testing
- Circuit breaker behavior
- Bulkhead pattern testing
- Agent error handling

### Integration Tests (`tests/test_error_recovery_integration.py`)
- End-to-end error recovery scenarios
- Multi-agent failure handling
- Workflow continuation testing
- Performance under load
- Recovery strategy validation

### Simple Tests (`tests/test_error_handling_simple.py`)
- Basic error handling functionality
- Agent retry success scenarios
- Metrics tracking verification
- HTTP error classification
- Non-recoverable error handling

## Configuration

The error handling system is configurable through the existing configuration system:

```python
# Retry configuration
RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True
)

# Circuit breaker configuration
CircuitBreakerState(
    failure_threshold=5,
    recovery_timeout=60,
    success_threshold=3
)

# Bulkhead configuration
BulkheadConfig(
    max_concurrent_requests=3,
    queue_size=10,
    timeout_seconds=300
)
```

## Usage Examples

### Basic Agent Error Handling
```python
from biomerkin.agents.base_agent import BaseAgent, agent_error_handler

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__("my_agent")
    
    @agent_error_handler()
    def execute(self, input_data, workflow_id=None):
        # Agent implementation with automatic error handling
        return {"result": "success"}

# Usage
agent = MyAgent()
result = agent.execute_with_error_handling({"data": "test"})
```

### Retry Decorator
```python
from biomerkin.utils.error_handling import with_retry

@with_retry(max_retries=3, base_delay=1.0)
def api_call():
    # Function with automatic retry logic
    return make_external_api_call()
```

### Error Recovery Orchestrator
```python
from biomerkin.services.error_recovery_orchestrator import ErrorRecoveryOrchestrator

orchestrator = ErrorRecoveryOrchestrator(
    enable_circuit_breakers=True,
    enable_bulkheads=True
)

# Execute agent with comprehensive error handling
result = await orchestrator.execute_agent_with_recovery(
    workflow_id="test",
    agent_name="genomics",
    agent_instance=genomics_agent,
    input_data={"sequence": "ATCG..."}
)
```

## Benefits

1. **Resilience**: System continues operating despite individual component failures
2. **Observability**: Comprehensive error tracking and metrics
3. **Performance**: Intelligent retry strategies prevent resource waste
4. **Maintainability**: Centralized error handling logic
5. **User Experience**: Graceful degradation provides partial results
6. **Scalability**: Circuit breakers and bulkheads prevent cascading failures

## Requirements Compliance

✅ **Retry logic with exponential backoff for external API calls**
- Implemented in RetryHandler with configurable parameters
- Category-specific delay adjustments
- Jitter to prevent thundering herd

✅ **Graceful degradation when agents fail or APIs are unavailable**
- Agent-specific fallback strategies
- Partial result preservation
- Clear error messaging and limitations

✅ **Error categorization and appropriate response strategies**
- Comprehensive error classification system
- Severity-based handling strategies
- Recovery action selection

✅ **Workflow recovery and partial result handling**
- WorkflowRecoveryHandler for continuation strategies
- Dependency analysis for recovery decisions
- Partial result aggregation and reporting

✅ **Tests for various error scenarios and recovery mechanisms**
- Unit tests for all error handling components
- Integration tests for end-to-end scenarios
- Simple tests for basic functionality verification

The implementation provides a robust, production-ready error handling system that ensures the Biomerkin multi-agent system can handle failures gracefully while maintaining service availability and data integrity.