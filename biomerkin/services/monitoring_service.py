"""
Comprehensive monitoring and logging service for the Biomerkin multi-agent system.

This module provides centralized monitoring capabilities including CloudWatch integration,
custom metrics collection, performance tracking, and alerting for system health monitoring.
"""

import logging
import time
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from botocore.exceptions import ClientError

from ..utils.config import get_config
from ..utils.logging_config import get_logger, log_workflow_event, log_agent_activity
from ..models.base import WorkflowState, WorkflowStatus


class MetricType(Enum):
    """Types of metrics that can be recorded."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SystemHealthMetrics:
    """System health metrics snapshot."""
    timestamp: datetime
    workflow_success_rate: float
    average_processing_time: float
    active_workflows: int
    failed_workflows_last_hour: int
    api_response_times: Dict[str, float]
    resource_utilization: Dict[str, float]
    error_rates: Dict[str, float]
    cache_hit_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'workflow_success_rate': self.workflow_success_rate,
            'average_processing_time': self.average_processing_time,
            'active_workflows': self.active_workflows,
            'failed_workflows_last_hour': self.failed_workflows_last_hour,
            'api_response_times': self.api_response_times,
            'resource_utilization': self.resource_utilization,
            'error_rates': self.error_rates,
            'cache_hit_rate': self.cache_hit_rate
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for workflow execution."""
    workflow_id: str
    agent_metrics: Dict[str, Dict[str, float]]
    total_execution_time: float
    parallel_efficiency: float
    resource_usage: Dict[str, float]
    api_call_metrics: Dict[str, Dict[str, Any]]
    error_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'workflow_id': self.workflow_id,
            'agent_metrics': self.agent_metrics,
            'total_execution_time': self.total_execution_time,
            'parallel_efficiency': self.parallel_efficiency,
            'resource_usage': self.resource_usage,
            'api_call_metrics': self.api_call_metrics,
            'error_count': self.error_count
        }


@dataclass
class Alert:
    """System alert information."""
    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    metric_name: str
    threshold_value: float
    current_value: float
    timestamp: datetime
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'alert_id': self.alert_id,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'metric_name': self.metric_name,
            'threshold_value': self.threshold_value,
            'current_value': self.current_value,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved
        }


class MonitoringService:
    """
    Comprehensive monitoring service for the Biomerkin system.
    
    Provides CloudWatch integration, custom metrics collection, performance tracking,
    alerting, and dashboard management for system health monitoring.
    """
    
    def __init__(self):
        """Initialize monitoring service."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Initialize AWS clients
        self.cloudwatch = None
        self.logs_client = None
        self.sns_client = None
        
        if self.config.environment == 'production':
            try:
                self.cloudwatch = boto3.client('cloudwatch', region_name=self.config.aws.region)
                self.logs_client = boto3.client('logs', region_name=self.config.aws.region)
                self.sns_client = boto3.client('sns', region_name=self.config.aws.region)
            except Exception as e:
                self.logger.warning(f"Failed to initialize AWS clients: {str(e)}")
        
        # Metrics storage
        self.metrics_buffer: List[Dict[str, Any]] = []
        self.performance_data: Dict[str, PerformanceMetrics] = {}
        self.active_alerts: Dict[str, Alert] = {}
        
        # Configuration
        self.namespace = 'Biomerkin/System'
        self.buffer_size = 100
        self.flush_interval = 60  # seconds
        self.last_flush = time.time()
        
        # Alert thresholds
        self.alert_thresholds = {
            'workflow_failure_rate': 0.1,  # 10%
            'average_processing_time': 300,  # 5 minutes
            'api_error_rate': 0.05,  # 5%
            'memory_utilization': 0.8,  # 80%
            'cache_hit_rate': 0.3  # 30% minimum
        }
    
    def record_workflow_started(self, workflow_id: str, user_id: Optional[str] = None) -> None:
        """
        Record when a workflow is started.
        
        Args:
            workflow_id: Unique workflow identifier
            user_id: Optional user identifier
        """
        dimensions = [{'Name': 'WorkflowId', 'Value': workflow_id}]
        if user_id:
            dimensions.append({'Name': 'UserId', 'Value': user_id})
        
        self._record_metric('WorkflowsStarted', 1, dimensions)
        
        log_workflow_event(
            self.logger,
            workflow_id,
            'start',
            'Workflow started',
            user_id=user_id
        )
    
    def record_workflow_completed(self, workflow_id: str, processing_time: float,
                                 user_id: Optional[str] = None) -> None:
        """
        Record when a workflow is completed successfully.
        
        Args:
            workflow_id: Unique workflow identifier
            processing_time: Total processing time in seconds
            user_id: Optional user identifier
        """
        dimensions = [{'Name': 'WorkflowId', 'Value': workflow_id}]
        if user_id:
            dimensions.append({'Name': 'UserId', 'Value': user_id})
        
        self._record_metric('WorkflowsCompleted', 1, dimensions)
        self._record_metric('ProcessingTime', processing_time, dimensions, 'Seconds')
        
        log_workflow_event(
            self.logger,
            workflow_id,
            'complete',
            f'Workflow completed in {processing_time:.2f}s',
            user_id=user_id,
            processing_time=processing_time
        )
    
    def record_workflow_failed(self, workflow_id: str, error_type: str,
                              error_message: str, user_id: Optional[str] = None) -> None:
        """
        Record when a workflow fails.
        
        Args:
            workflow_id: Unique workflow identifier
            error_type: Type of error that occurred
            error_message: Error message
            user_id: Optional user identifier
        """
        dimensions = [
            {'Name': 'WorkflowId', 'Value': workflow_id},
            {'Name': 'ErrorType', 'Value': error_type}
        ]
        if user_id:
            dimensions.append({'Name': 'UserId', 'Value': user_id})
        
        self._record_metric('WorkflowsFailed', 1, dimensions)
        
        log_workflow_event(
            self.logger,
            workflow_id,
            'failed',
            f'Workflow failed: {error_message}',
            user_id=user_id,
            error_type=error_type,
            error_message=error_message
        )
    
    def record_agent_execution(self, workflow_id: str, agent_name: str,
                              execution_time: float, success: bool = True,
                              memory_usage: Optional[float] = None) -> None:
        """
        Record agent execution metrics.
        
        Args:
            workflow_id: Unique workflow identifier
            agent_name: Name of the agent
            execution_time: Execution time in seconds
            success: Whether execution was successful
            memory_usage: Optional memory usage in MB
        """
        dimensions = [
            {'Name': 'AgentName', 'Value': agent_name},
            {'Name': 'Status', 'Value': 'Success' if success else 'Failed'}
        ]
        
        self._record_metric('AgentExecutions', 1, dimensions)
        self._record_metric('AgentExecutionTime', execution_time, dimensions, 'Seconds')
        
        if memory_usage:
            self._record_metric('AgentMemoryUsage', memory_usage, dimensions, 'Megabytes')
        
        log_agent_activity(
            self.logger,
            agent_name,
            workflow_id,
            f'Agent execution {"succeeded" if success else "failed"} in {execution_time:.2f}s',
            {
                'execution_time': execution_time,
                'success': success,
                'memory_usage': memory_usage
            }
        )
    
    def record_api_call(self, api_name: str, response_time: float,
                       status_code: int, workflow_id: Optional[str] = None) -> None:
        """
        Record external API call metrics.
        
        Args:
            api_name: Name of the API
            response_time: Response time in milliseconds
            status_code: HTTP status code
            workflow_id: Optional workflow identifier
        """
        dimensions = [
            {'Name': 'APIName', 'Value': api_name},
            {'Name': 'StatusCode', 'Value': str(status_code)}
        ]
        
        if workflow_id:
            dimensions.append({'Name': 'WorkflowId', 'Value': workflow_id})
        
        self._record_metric('ExternalAPICalls', 1, dimensions)
        self._record_metric('APIResponseTime', response_time, dimensions, 'Milliseconds')
        
        # Record error if status code indicates failure
        if status_code >= 400:
            self._record_metric('APIErrors', 1, dimensions)
    
    def record_cache_metrics(self, hit_rate: float, total_requests: int,
                           cache_size_mb: float) -> None:
        """
        Record cache performance metrics.
        
        Args:
            hit_rate: Cache hit rate (0.0 to 1.0)
            total_requests: Total number of cache requests
            cache_size_mb: Current cache size in MB
        """
        dimensions = [{'Name': 'CacheType', 'Value': 'System'}]
        
        self._record_metric('CacheHitRate', hit_rate * 100, dimensions, 'Percent')
        self._record_metric('CacheRequests', total_requests, dimensions)
        self._record_metric('CacheSize', cache_size_mb, dimensions, 'Megabytes')
    
    def record_resource_utilization(self, resource_type: str, utilization: float) -> None:
        """
        Record resource utilization metrics.
        
        Args:
            resource_type: Type of resource (memory, cpu, disk, etc.)
            utilization: Utilization percentage (0.0 to 1.0)
        """
        dimensions = [{'Name': 'ResourceType', 'Value': resource_type}]
        
        self._record_metric('ResourceUtilization', utilization * 100, dimensions, 'Percent')
    
    def get_system_health(self) -> SystemHealthMetrics:
        """
        Get current system health metrics.
        
        Returns:
            SystemHealthMetrics with current system status
        """
        try:
            # Calculate workflow success rate (last 24 hours)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=24)
            
            workflow_success_rate = self._calculate_workflow_success_rate(start_time, end_time)
            average_processing_time = self._calculate_average_processing_time(start_time, end_time)
            active_workflows = self._count_active_workflows()
            failed_workflows_last_hour = self._count_failed_workflows(
                end_time - timedelta(hours=1), end_time
            )
            
            # Get API response times
            api_response_times = self._get_api_response_times(start_time, end_time)
            
            # Get resource utilization
            resource_utilization = self._get_resource_utilization()
            
            # Get error rates
            error_rates = self._get_error_rates(start_time, end_time)
            
            # Get cache hit rate
            cache_hit_rate = self._get_cache_hit_rate(start_time, end_time)
            
            return SystemHealthMetrics(
                timestamp=datetime.utcnow(),
                workflow_success_rate=workflow_success_rate,
                average_processing_time=average_processing_time,
                active_workflows=active_workflows,
                failed_workflows_last_hour=failed_workflows_last_hour,
                api_response_times=api_response_times,
                resource_utilization=resource_utilization,
                error_rates=error_rates,
                cache_hit_rate=cache_hit_rate
            )
            
        except Exception as e:
            self.logger.error(f"Error getting system health metrics: {str(e)}")
            # Return default metrics on error
            return SystemHealthMetrics(
                timestamp=datetime.utcnow(),
                workflow_success_rate=0.0,
                average_processing_time=0.0,
                active_workflows=0,
                failed_workflows_last_hour=0,
                api_response_times={},
                resource_utilization={},
                error_rates={},
                cache_hit_rate=0.0
            )
    
    def check_alerts(self) -> List[Alert]:
        """
        Check for system alerts based on current metrics.
        
        Returns:
            List of active alerts
        """
        alerts = []
        health_metrics = self.get_system_health()
        
        # Check workflow failure rate
        if health_metrics.workflow_success_rate < (1 - self.alert_thresholds['workflow_failure_rate']):
            alert = Alert(
                alert_id=f"workflow_failure_rate_{int(time.time())}",
                severity=AlertSeverity.HIGH,
                title="High Workflow Failure Rate",
                description=f"Workflow success rate is {health_metrics.workflow_success_rate:.2%}, below threshold",
                metric_name="workflow_success_rate",
                threshold_value=1 - self.alert_thresholds['workflow_failure_rate'],
                current_value=health_metrics.workflow_success_rate,
                timestamp=datetime.utcnow()
            )
            alerts.append(alert)
            self.active_alerts[alert.alert_id] = alert
        
        # Check average processing time
        if health_metrics.average_processing_time > self.alert_thresholds['average_processing_time']:
            alert = Alert(
                alert_id=f"processing_time_{int(time.time())}",
                severity=AlertSeverity.MEDIUM,
                title="High Processing Time",
                description=f"Average processing time is {health_metrics.average_processing_time:.2f}s",
                metric_name="average_processing_time",
                threshold_value=self.alert_thresholds['average_processing_time'],
                current_value=health_metrics.average_processing_time,
                timestamp=datetime.utcnow()
            )
            alerts.append(alert)
            self.active_alerts[alert.alert_id] = alert
        
        # Check cache hit rate
        if health_metrics.cache_hit_rate < self.alert_thresholds['cache_hit_rate']:
            alert = Alert(
                alert_id=f"cache_hit_rate_{int(time.time())}",
                severity=AlertSeverity.LOW,
                title="Low Cache Hit Rate",
                description=f"Cache hit rate is {health_metrics.cache_hit_rate:.2%}",
                metric_name="cache_hit_rate",
                threshold_value=self.alert_thresholds['cache_hit_rate'],
                current_value=health_metrics.cache_hit_rate,
                timestamp=datetime.utcnow()
            )
            alerts.append(alert)
            self.active_alerts[alert.alert_id] = alert
        
        return alerts
    
    def send_alert_notification(self, alert: Alert, topic_arn: Optional[str] = None) -> bool:
        """
        Send alert notification via SNS.
        
        Args:
            alert: Alert to send
            topic_arn: Optional SNS topic ARN
            
        Returns:
            True if notification sent successfully
        """
        if not self.sns_client or not topic_arn:
            self.logger.warning("SNS client or topic ARN not available for alert notification")
            return False
        
        try:
            message = {
                'alert_id': alert.alert_id,
                'severity': alert.severity.value,
                'title': alert.title,
                'description': alert.description,
                'timestamp': alert.timestamp.isoformat(),
                'metric_name': alert.metric_name,
                'threshold_value': alert.threshold_value,
                'current_value': alert.current_value
            }
            
            self.sns_client.publish(
                TopicArn=topic_arn,
                Subject=f"Biomerkin Alert: {alert.title}",
                Message=json.dumps(message, indent=2)
            )
            
            self.logger.info(f"Alert notification sent: {alert.alert_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send alert notification: {str(e)}")
            return False
    
    def create_dashboard_config(self) -> Dict[str, Any]:
        """
        Create CloudWatch dashboard configuration.
        
        Returns:
            Dashboard configuration dictionary
        """
        dashboard_config = {
            "widgets": [
                # Workflow metrics
                {
                    "type": "metric",
                    "x": 0,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "WorkflowsStarted"],
                            [".", "WorkflowsCompleted"],
                            [".", "WorkflowsFailed"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.config.aws.region,
                        "title": "Workflow Metrics",
                        "period": 300
                    }
                },
                # Agent execution metrics
                {
                    "type": "metric",
                    "x": 12,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "AgentExecutions", "AgentName", "genomics"],
                            [".", ".", ".", "proteomics"],
                            [".", ".", ".", "literature"],
                            [".", ".", ".", "drug"],
                            [".", ".", ".", "decision"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.config.aws.region,
                        "title": "Agent Executions",
                        "period": 300
                    }
                },
                # Processing time metrics
                {
                    "type": "metric",
                    "x": 0,
                    "y": 6,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "ProcessingTime"],
                            [".", "AgentExecutionTime", "AgentName", "genomics"],
                            [".", ".", ".", "proteomics"],
                            [".", ".", ".", "literature"],
                            [".", ".", ".", "drug"],
                            [".", ".", ".", "decision"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.config.aws.region,
                        "title": "Processing Times",
                        "period": 300,
                        "stat": "Average"
                    }
                },
                # API call metrics
                {
                    "type": "metric",
                    "x": 12,
                    "y": 6,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "ExternalAPICalls", "APIName", "PubMed"],
                            [".", ".", ".", "PDB"],
                            [".", ".", ".", "DrugBank"],
                            [".", ".", ".", "ClinicalTrials"],
                            [".", "APIErrors", ".", "PubMed"],
                            [".", ".", ".", "PDB"],
                            [".", ".", ".", "DrugBank"],
                            [".", ".", ".", "ClinicalTrials"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.config.aws.region,
                        "title": "External API Calls",
                        "period": 300
                    }
                },
                # Cache metrics
                {
                    "type": "metric",
                    "x": 0,
                    "y": 12,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "CacheHitRate"],
                            [".", "CacheRequests"],
                            [".", "CacheSize"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.config.aws.region,
                        "title": "Cache Performance",
                        "period": 300
                    }
                },
                # Resource utilization
                {
                    "type": "metric",
                    "x": 12,
                    "y": 12,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            [self.namespace, "ResourceUtilization", "ResourceType", "memory"],
                            [".", ".", ".", "cpu"],
                            [".", ".", ".", "disk"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.config.aws.region,
                        "title": "Resource Utilization",
                        "period": 300
                    }
                },
                # Error log insights
                {
                    "type": "log",
                    "x": 0,
                    "y": 18,
                    "width": 24,
                    "height": 6,
                    "properties": {
                        "query": f"SOURCE '/aws/lambda/biomerkin-orchestrator'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 50",
                        "region": self.config.aws.region,
                        "title": "Recent Errors",
                        "view": "table"
                    }
                }
            ]
        }
        
        return dashboard_config
    
    def flush_metrics(self) -> None:
        """Flush buffered metrics to CloudWatch."""
        if not self.cloudwatch or not self.metrics_buffer:
            return
        
        try:
            # Send metrics in batches of 20 (CloudWatch limit)
            batch_size = 20
            for i in range(0, len(self.metrics_buffer), batch_size):
                batch = self.metrics_buffer[i:i + batch_size]
                
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=batch
                )
            
            self.logger.debug(f"Flushed {len(self.metrics_buffer)} metrics to CloudWatch")
            self.metrics_buffer.clear()
            self.last_flush = time.time()
            
        except Exception as e:
            self.logger.error(f"Failed to flush metrics to CloudWatch: {str(e)}")
    
    def _record_metric(self, metric_name: str, value: float,
                      dimensions: List[Dict[str, str]], unit: str = 'Count') -> None:
        """
        Record a metric to the buffer.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            dimensions: Metric dimensions
            unit: Metric unit
        """
        metric_data = {
            'MetricName': metric_name,
            'Dimensions': dimensions,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }
        
        self.metrics_buffer.append(metric_data)
        
        # Flush if buffer is full or enough time has passed
        if (len(self.metrics_buffer) >= self.buffer_size or 
            time.time() - self.last_flush > self.flush_interval):
            self.flush_metrics()
    
    def _calculate_workflow_success_rate(self, start_time: datetime, end_time: datetime) -> float:
        """Calculate workflow success rate for the given time period."""
        # This would query CloudWatch metrics in a real implementation
        # For now, return a placeholder value
        return 0.95  # 95% success rate
    
    def _calculate_average_processing_time(self, start_time: datetime, end_time: datetime) -> float:
        """Calculate average processing time for the given time period."""
        # This would query CloudWatch metrics in a real implementation
        # For now, return a placeholder value
        return 120.0  # 2 minutes average
    
    def _count_active_workflows(self) -> int:
        """Count currently active workflows."""
        # This would query the workflow state from DynamoDB
        # For now, return a placeholder value
        return 5
    
    def _count_failed_workflows(self, start_time: datetime, end_time: datetime) -> int:
        """Count failed workflows in the given time period."""
        # This would query CloudWatch metrics or DynamoDB
        # For now, return a placeholder value
        return 2
    
    def _get_api_response_times(self, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Get API response times for the given time period."""
        # This would query CloudWatch metrics in a real implementation
        return {
            'PubMed': 250.0,
            'PDB': 180.0,
            'DrugBank': 320.0,
            'ClinicalTrials': 400.0
        }
    
    def _get_resource_utilization(self) -> Dict[str, float]:
        """Get current resource utilization."""
        # This would query system metrics in a real implementation
        return {
            'memory': 0.65,
            'cpu': 0.45,
            'disk': 0.30
        }
    
    def _get_error_rates(self, start_time: datetime, end_time: datetime) -> Dict[str, float]:
        """Get error rates for different components."""
        # This would query CloudWatch metrics in a real implementation
        return {
            'genomics_agent': 0.02,
            'proteomics_agent': 0.01,
            'literature_agent': 0.03,
            'drug_agent': 0.02,
            'decision_agent': 0.01
        }
    
    def _get_cache_hit_rate(self, start_time: datetime, end_time: datetime) -> float:
        """Get cache hit rate for the given time period."""
        # This would query cache metrics in a real implementation
        return 0.75  # 75% hit rate


# Global monitoring service instance
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get the global monitoring service instance."""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service


def clear_monitoring_service():
    """Clear the global monitoring service instance (useful for testing)."""
    global _monitoring_service
    _monitoring_service = None