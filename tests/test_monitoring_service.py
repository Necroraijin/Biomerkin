"""
Tests for the monitoring service module.

This module tests the comprehensive monitoring capabilities including CloudWatch integration,
custom metrics collection, performance tracking, and system health monitoring.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from biomerkin.services.monitoring_service import (
    MonitoringService, SystemHealthMetrics, PerformanceMetrics,
    MetricType, get_monitoring_service, clear_monitoring_service
)
from biomerkin.models.base import WorkflowState, WorkflowStatus


class TestMonitoringService:
    """Test cases for MonitoringService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        clear_monitoring_service()
        self.monitoring_service = MonitoringService()
        
        # Mock AWS clients
        self.monitoring_service.cloudwatch = Mock()
        self.monitoring_service.logs_client = Mock()
        self.monitoring_service.sns_client = Mock()
    
    def test_initialization(self):
        """Test monitoring service initialization."""
        assert self.monitoring_service is not None
        assert self.monitoring_service.namespace == 'Biomerkin/System'
        assert self.monitoring_service.buffer_size == 100
        assert len(self.monitoring_service.metrics_buffer) == 0
        assert len(self.monitoring_service.performance_data) == 0
        assert len(self.monitoring_service.active_alerts) == 0
    
    def test_record_workflow_started(self):
        """Test recording workflow started event."""
        workflow_id = "test-workflow-123"
        user_id = "test-user"
        
        self.monitoring_service.record_workflow_started(workflow_id, user_id)
        
        # Check that metric was buffered
        assert len(self.monitoring_service.metrics_buffer) == 1
        
        metric = self.monitoring_service.metrics_buffer[0]
        assert metric['MetricName'] == 'WorkflowsStarted'
        assert metric['Value'] == 1
        assert metric['Unit'] == 'Count'
        
        # Check dimensions
        dimensions = metric['Dimensions']
        assert len(dimensions) == 2
        assert {'Name': 'WorkflowId', 'Value': workflow_id} in dimensions
        assert {'Name': 'UserId', 'Value': user_id} in dimensions
    
    def test_record_workflow_completed(self):
        """Test recording workflow completed event."""
        workflow_id = "test-workflow-123"
        processing_time = 120.5
        user_id = "test-user"
        
        self.monitoring_service.record_workflow_completed(workflow_id, processing_time, user_id)
        
        # Check that two metrics were buffered (completed count and processing time)
        assert len(self.monitoring_service.metrics_buffer) == 2
        
        # Check completed metric
        completed_metric = next(m for m in self.monitoring_service.metrics_buffer if m['MetricName'] == 'WorkflowsCompleted')
        assert completed_metric['Value'] == 1
        assert completed_metric['Unit'] == 'Count'
        
        # Check processing time metric
        time_metric = next(m for m in self.monitoring_service.metrics_buffer if m['MetricName'] == 'ProcessingTime')
        assert time_metric['Value'] == processing_time
        assert time_metric['Unit'] == 'Seconds'
    
    def test_record_workflow_failed(self):
        """Test recording workflow failed event."""
        workflow_id = "test-workflow-123"
        error_type = "ValidationError"
        error_message = "Invalid DNA sequence format"
        user_id = "test-user"
        
        self.monitoring_service.record_workflow_failed(workflow_id, error_type, error_message, user_id)
        
        # Check that metric was buffered
        assert len(self.monitoring_service.metrics_buffer) == 1
        
        metric = self.monitoring_service.metrics_buffer[0]
        assert metric['MetricName'] == 'WorkflowsFailed'
        assert metric['Value'] == 1
        assert metric['Unit'] == 'Count'
        
        # Check dimensions include error type
        dimensions = metric['Dimensions']
        assert {'Name': 'ErrorType', 'Value': error_type} in dimensions
    
    def test_record_agent_execution(self):
        """Test recording agent execution metrics."""
        workflow_id = "test-workflow-123"
        agent_name = "genomics"
        execution_time = 45.2
        memory_usage = 256.0
        
        self.monitoring_service.record_agent_execution(
            workflow_id, agent_name, execution_time, True, memory_usage
        )
        
        # Check that three metrics were buffered
        assert len(self.monitoring_service.metrics_buffer) == 3
        
        # Check execution count metric
        execution_metric = next(m for m in self.monitoring_service.metrics_buffer if m['MetricName'] == 'AgentExecutions')
        assert execution_metric['Value'] == 1
        
        # Check execution time metric
        time_metric = next(m for m in self.monitoring_service.metrics_buffer if m['MetricName'] == 'AgentExecutionTime')
        assert time_metric['Value'] == execution_time
        assert time_metric['Unit'] == 'Seconds'
        
        # Check memory usage metric
        memory_metric = next(m for m in self.monitoring_service.metrics_buffer if m['MetricName'] == 'AgentMemoryUsage')
        assert memory_metric['Value'] == memory_usage
        assert memory_metric['Unit'] == 'Megabytes'
    
    def test_record_api_call(self):
        """Test recording API call metrics."""
        api_name = "PubMed"
        response_time = 250.0
        status_code = 200
        workflow_id = "test-workflow-123"
        
        self.monitoring_service.record_api_call(api_name, response_time, status_code, workflow_id)
        
        # Check that two metrics were buffered (call count and response time)
        assert len(self.monitoring_service.metrics_buffer) == 2
        
        # Check API call metric
        call_metric = next(m for m in self.monitoring_service.metrics_buffer if m['MetricName'] == 'ExternalAPICalls')
        assert call_metric['Value'] == 1
        
        # Check response time metric
        time_metric = next(m for m in self.monitoring_service.metrics_buffer if m['MetricName'] == 'APIResponseTime')
        assert time_metric['Value'] == response_time
        assert time_metric['Unit'] == 'Milliseconds'
    
    def test_record_api_call_error(self):
        """Test recording API call with error status."""
        api_name = "PubMed"
        response_time = 5000.0
        status_code = 500
        
        self.monitoring_service.record_api_call(api_name, response_time, status_code)
        
        # Check that three metrics were buffered (call count, response time, and error)
        assert len(self.monitoring_service.metrics_buffer) == 3
        
        # Check error metric was recorded
        error_metric = next(m for m in self.monitoring_service.metrics_buffer if m['MetricName'] == 'APIErrors')
        assert error_metric['Value'] == 1
    
    def test_record_cache_metrics(self):
        """Test recording cache performance metrics."""
        hit_rate = 0.75
        total_requests = 1000
        cache_size_mb = 128.5
        
        self.monitoring_service.record_cache_metrics(hit_rate, total_requests, cache_size_mb)
        
        # Check that three metrics were buffered
        assert len(self.monitoring_service.metrics_buffer) == 3
        
        # Check hit rate metric (converted to percentage)
        hit_rate_metric = next(m for m in self.monitoring_service.metrics_buffer if m['MetricName'] == 'CacheHitRate')
        assert hit_rate_metric['Value'] == 75.0
        assert hit_rate_metric['Unit'] == 'Percent'
        
        # Check requests metric
        requests_metric = next(m for m in self.monitoring_service.metrics_buffer if m['MetricName'] == 'CacheRequests')
        assert requests_metric['Value'] == total_requests
        
        # Check size metric
        size_metric = next(m for m in self.monitoring_service.metrics_buffer if m['MetricName'] == 'CacheSize')
        assert size_metric['Value'] == cache_size_mb
        assert size_metric['Unit'] == 'Megabytes'
    
    def test_record_resource_utilization(self):
        """Test recording resource utilization metrics."""
        resource_type = "memory"
        utilization = 0.65
        
        self.monitoring_service.record_resource_utilization(resource_type, utilization)
        
        # Check that metric was buffered
        assert len(self.monitoring_service.metrics_buffer) == 1
        
        metric = self.monitoring_service.metrics_buffer[0]
        assert metric['MetricName'] == 'ResourceUtilization'
        assert metric['Value'] == 65.0  # Converted to percentage
        assert metric['Unit'] == 'Percent'
        
        # Check dimensions
        dimensions = metric['Dimensions']
        assert {'Name': 'ResourceType', 'Value': resource_type} in dimensions
    
    def test_get_system_health(self):
        """Test getting system health metrics."""
        health_metrics = self.monitoring_service.get_system_health()
        
        assert isinstance(health_metrics, SystemHealthMetrics)
        assert isinstance(health_metrics.timestamp, datetime)
        assert isinstance(health_metrics.workflow_success_rate, float)
        assert isinstance(health_metrics.average_processing_time, float)
        assert isinstance(health_metrics.active_workflows, int)
        assert isinstance(health_metrics.failed_workflows_last_hour, int)
        assert isinstance(health_metrics.api_response_times, dict)
        assert isinstance(health_metrics.resource_utilization, dict)
        assert isinstance(health_metrics.error_rates, dict)
        assert isinstance(health_metrics.cache_hit_rate, float)
    
    def test_check_alerts(self):
        """Test alert checking functionality."""
        # Mock system health to trigger alerts
        with patch.object(self.monitoring_service, 'get_system_health') as mock_health:
            mock_health.return_value = SystemHealthMetrics(
                timestamp=datetime.utcnow(),
                workflow_success_rate=0.85,  # Below 90% threshold
                average_processing_time=350.0,  # Above 300s threshold
                active_workflows=5,
                failed_workflows_last_hour=2,
                api_response_times={'PubMed': 250.0},
                resource_utilization={'memory': 0.85},  # Above 80% threshold
                error_rates={'genomics_agent': 0.02},
                cache_hit_rate=0.25  # Below 30% threshold
            )
            
            alerts = self.monitoring_service.check_alerts()
            
            # Should trigger multiple alerts
            assert len(alerts) > 0
            
            # Check that alerts were added to active alerts
            assert len(self.monitoring_service.active_alerts) > 0
    
    def test_flush_metrics(self):
        """Test flushing metrics to CloudWatch."""
        # Add some metrics to buffer
        self.monitoring_service.record_workflow_started("test-workflow")
        self.monitoring_service.record_workflow_completed("test-workflow", 120.0)
        
        initial_buffer_size = len(self.monitoring_service.metrics_buffer)
        assert initial_buffer_size > 0
        
        # Flush metrics
        self.monitoring_service.flush_metrics()
        
        # Check that CloudWatch was called
        self.monitoring_service.cloudwatch.put_metric_data.assert_called_once()
        
        # Check that buffer was cleared
        assert len(self.monitoring_service.metrics_buffer) == 0
    
    def test_flush_metrics_large_batch(self):
        """Test flushing large batch of metrics."""
        # Add more than 20 metrics (CloudWatch batch limit)
        for i in range(25):
            self.monitoring_service.record_workflow_started(f"test-workflow-{i}")
        
        # Flush metrics
        self.monitoring_service.flush_metrics()
        
        # Check that CloudWatch was called multiple times for batching
        assert self.monitoring_service.cloudwatch.put_metric_data.call_count >= 2
        
        # Check that buffer was cleared
        assert len(self.monitoring_service.metrics_buffer) == 0
    
    def test_auto_flush_on_buffer_full(self):
        """Test automatic flushing when buffer is full."""
        # Set small buffer size for testing
        self.monitoring_service.buffer_size = 5
        
        # Add metrics to fill buffer
        for i in range(6):  # One more than buffer size
            self.monitoring_service.record_workflow_started(f"test-workflow-{i}")
        
        # Should have automatically flushed
        self.monitoring_service.cloudwatch.put_metric_data.assert_called()
    
    def test_auto_flush_on_time_interval(self):
        """Test automatic flushing based on time interval."""
        # Set short flush interval for testing
        self.monitoring_service.flush_interval = 1
        
        # Add a metric
        self.monitoring_service.record_workflow_started("test-workflow")
        
        # Wait for flush interval
        time.sleep(1.1)
        
        # Add another metric to trigger time-based flush
        self.monitoring_service.record_workflow_started("test-workflow-2")
        
        # Should have flushed due to time interval
        self.monitoring_service.cloudwatch.put_metric_data.assert_called()
    
    def test_global_monitoring_service(self):
        """Test global monitoring service instance."""
        service1 = get_monitoring_service()
        service2 = get_monitoring_service()
        
        # Should return the same instance
        assert service1 is service2
        
        # Clear and get new instance
        clear_monitoring_service()
        service3 = get_monitoring_service()
        
        # Should be a different instance
        assert service1 is not service3
    
    def test_system_health_metrics_to_dict(self):
        """Test SystemHealthMetrics to_dict conversion."""
        timestamp = datetime.utcnow()
        metrics = SystemHealthMetrics(
            timestamp=timestamp,
            workflow_success_rate=0.95,
            average_processing_time=120.0,
            active_workflows=5,
            failed_workflows_last_hour=1,
            api_response_times={'PubMed': 250.0},
            resource_utilization={'memory': 0.65},
            error_rates={'genomics_agent': 0.02},
            cache_hit_rate=0.75
        )
        
        metrics_dict = metrics.to_dict()
        
        assert metrics_dict['timestamp'] == timestamp.isoformat()
        assert metrics_dict['workflow_success_rate'] == 0.95
        assert metrics_dict['average_processing_time'] == 120.0
        assert metrics_dict['active_workflows'] == 5
        assert metrics_dict['failed_workflows_last_hour'] == 1
        assert metrics_dict['api_response_times'] == {'PubMed': 250.0}
        assert metrics_dict['resource_utilization'] == {'memory': 0.65}
        assert metrics_dict['error_rates'] == {'genomics_agent': 0.02}
        assert metrics_dict['cache_hit_rate'] == 0.75
    
    def test_performance_metrics_to_dict(self):
        """Test PerformanceMetrics to_dict conversion."""
        metrics = PerformanceMetrics(
            workflow_id="test-workflow-123",
            agent_metrics={
                'genomics': {'execution_time': 45.2, 'memory_usage': 256.0},
                'proteomics': {'execution_time': 32.1, 'memory_usage': 128.0}
            },
            total_execution_time=120.5,
            parallel_efficiency=0.75,
            resource_usage={'memory': 0.65, 'cpu': 0.45},
            api_call_metrics={
                'PubMed': {'calls': 5, 'avg_response_time': 250.0},
                'PDB': {'calls': 3, 'avg_response_time': 180.0}
            },
            error_count=2
        )
        
        metrics_dict = metrics.to_dict()
        
        assert metrics_dict['workflow_id'] == "test-workflow-123"
        assert metrics_dict['total_execution_time'] == 120.5
        assert metrics_dict['parallel_efficiency'] == 0.75
        assert metrics_dict['error_count'] == 2
        assert 'agent_metrics' in metrics_dict
        assert 'resource_usage' in metrics_dict
        assert 'api_call_metrics' in metrics_dict
    
    @patch('boto3.client')
    def test_aws_client_initialization_failure(self, mock_boto_client):
        """Test handling of AWS client initialization failure."""
        mock_boto_client.side_effect = Exception("AWS credentials not found")
        
        # Should not raise exception, but log warning
        service = MonitoringService()
        
        assert service.cloudwatch is None
        assert service.logs_client is None
        assert service.sns_client is None
    
    def test_flush_metrics_cloudwatch_error(self):
        """Test handling of CloudWatch errors during flush."""
        # Add metrics to buffer
        self.monitoring_service.record_workflow_started("test-workflow")
        
        # Mock CloudWatch to raise exception
        self.monitoring_service.cloudwatch.put_metric_data.side_effect = Exception("CloudWatch error")
        
        # Should not raise exception
        self.monitoring_service.flush_metrics()
        
        # Buffer should not be cleared on error
        assert len(self.monitoring_service.metrics_buffer) > 0


if __name__ == '__main__':
    pytest.main([__file__])