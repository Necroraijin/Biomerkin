"""
Advanced Monitoring and Observability Framework.
Provides comprehensive monitoring for the multi-agent system.
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

import boto3
from .logging_config import get_logger


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """Metric data structure."""
    name: str
    value: float
    metric_type: MetricType
    tags: Dict[str, str]
    timestamp: datetime


@dataclass
class AgentPerformance:
    """Agent performance metrics."""
    agent_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: float
    last_execution: datetime
    error_rate: float


class MonitoringService:
    """
    Comprehensive monitoring service for the multi-agent system.
    Provides metrics, health checks, and performance monitoring.
    """
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize monitoring service."""
        self.logger = get_logger(__name__)
        self.region = region
        
        # Initialize CloudWatch client
        try:
            self.cloudwatch = boto3.client('cloudwatch', region_name=region)
            self.logger.info("CloudWatch monitoring initialized")
        except Exception as e:
            self.logger.error(f"Error initializing CloudWatch: {e}")
            self.cloudwatch = None
        
        # Initialize metrics storage
        self.metrics = []
        self.agent_performance = {}
        self.health_checks = {}
        
        # Performance tracking
        self.execution_times = {}
        self.error_counts = {}
        self.success_counts = {}
    
    def record_metric(self, name: str, value: float, metric_type: MetricType, 
                     tags: Optional[Dict[str, str]] = None):
        """Record a metric."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {},
            timestamp=datetime.now()
        )
        
        self.metrics.append(metric)
        
        # Send to CloudWatch if available
        if self.cloudwatch:
            self._send_to_cloudwatch(metric)
    
    def record_agent_execution(self, agent_name: str, execution_time: float, 
                              success: bool, error_message: Optional[str] = None):
        """Record agent execution metrics."""
        # Update execution times
        if agent_name not in self.execution_times:
            self.execution_times[agent_name] = []
        self.execution_times[agent_name].append(execution_time)
        
        # Update success/error counts
        if success:
            self.success_counts[agent_name] = self.success_counts.get(agent_name, 0) + 1
        else:
            self.error_counts[agent_name] = self.error_counts.get(agent_name, 0) + 1
        
        # Record metrics
        self.record_metric(
            f"agent.{agent_name}.execution_time",
            execution_time,
            MetricType.TIMER,
            {"agent": agent_name, "success": str(success)}
        )
        
        self.record_metric(
            f"agent.{agent_name}.execution_count",
            1,
            MetricType.COUNTER,
            {"agent": agent_name, "success": str(success)}
        )
        
        if error_message:
            self.record_metric(
                f"agent.{agent_name}.error",
                1,
                MetricType.COUNTER,
                {"agent": agent_name, "error_type": error_message[:50]}
            )
    
    def record_workflow_metrics(self, workflow_id: str, total_time: float, 
                               agents_used: List[str], success: bool):
        """Record workflow-level metrics."""
        self.record_metric(
            "workflow.total_time",
            total_time,
            MetricType.TIMER,
            {"workflow_id": workflow_id, "success": str(success)}
        )
        
        self.record_metric(
            "workflow.agent_count",
            len(agents_used),
            MetricType.GAUGE,
            {"workflow_id": workflow_id}
        )
        
        for agent in agents_used:
            self.record_metric(
                "workflow.agent_used",
                1,
                MetricType.COUNTER,
                {"workflow_id": workflow_id, "agent": agent}
            )
    
    def record_bedrock_usage(self, model_id: str, tokens_used: int, 
                           response_time: float, success: bool):
        """Record Bedrock usage metrics."""
        self.record_metric(
            "bedrock.tokens_used",
            tokens_used,
            MetricType.COUNTER,
            {"model": model_id, "success": str(success)}
        )
        
        self.record_metric(
            "bedrock.response_time",
            response_time,
            MetricType.TIMER,
            {"model": model_id, "success": str(success)}
        )
        
        self.record_metric(
            "bedrock.request_count",
            1,
            MetricType.COUNTER,
            {"model": model_id, "success": str(success)}
        )
    
    def record_api_usage(self, api_name: str, response_time: float, 
                        status_code: int, success: bool):
        """Record external API usage metrics."""
        self.record_metric(
            f"api.{api_name}.response_time",
            response_time,
            MetricType.TIMER,
            {"api": api_name, "status_code": str(status_code)}
        )
        
        self.record_metric(
            f"api.{api_name}.request_count",
            1,
            MetricType.COUNTER,
            {"api": api_name, "success": str(success)}
        )
    
    def get_agent_performance(self, agent_name: str) -> AgentPerformance:
        """Get performance metrics for a specific agent."""
        total_executions = (self.success_counts.get(agent_name, 0) + 
                          self.error_counts.get(agent_name, 0))
        
        successful_executions = self.success_counts.get(agent_name, 0)
        failed_executions = self.error_counts.get(agent_name, 0)
        
        execution_times = self.execution_times.get(agent_name, [])
        average_execution_time = (
            sum(execution_times) / len(execution_times) 
            if execution_times else 0
        )
        
        error_rate = (
            failed_executions / total_executions 
            if total_executions > 0 else 0
        )
        
        return AgentPerformance(
            agent_name=agent_name,
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            average_execution_time=average_execution_time,
            last_execution=datetime.now(),
            error_rate=error_rate
        )
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health metrics."""
        total_agents = len(set(list(self.success_counts.keys()) + 
                             list(self.error_counts.keys())))
        
        total_executions = sum(self.success_counts.values()) + sum(self.error_counts.values())
        total_successes = sum(self.success_counts.values())
        total_errors = sum(self.error_counts.values())
        
        overall_success_rate = (
            total_successes / total_executions 
            if total_executions > 0 else 0
        )
        
        # Calculate average execution time across all agents
        all_execution_times = []
        for times in self.execution_times.values():
            all_execution_times.extend(times)
        
        average_execution_time = (
            sum(all_execution_times) / len(all_execution_times)
            if all_execution_times else 0
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_agents": total_agents,
            "total_executions": total_executions,
            "total_successes": total_successes,
            "total_errors": total_errors,
            "overall_success_rate": overall_success_rate,
            "average_execution_time": average_execution_time,
            "active_agents": list(self.success_counts.keys()),
            "health_status": self._determine_health_status(overall_success_rate, total_errors)
        }
    
    def _determine_health_status(self, success_rate: float, total_errors: int) -> str:
        """Determine overall health status."""
        if success_rate >= 0.95 and total_errors < 10:
            return "healthy"
        elif success_rate >= 0.80 and total_errors < 50:
            return "warning"
        else:
            return "critical"
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        agent_performances = {}
        for agent_name in set(list(self.success_counts.keys()) + 
                            list(self.error_counts.keys())):
            agent_performances[agent_name] = asdict(self.get_agent_performance(agent_name))
        
        return {
            "system_health": self.get_system_health(),
            "agent_performances": agent_performances,
            "recent_metrics": self._get_recent_metrics(),
            "top_errors": self._get_top_errors()
        }
    
    def _get_recent_metrics(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get recent metrics within specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_metrics = [
            asdict(metric) for metric in self.metrics
            if metric.timestamp > cutoff_time
        ]
        
        return recent_metrics[-100:]  # Return last 100 metrics
    
    def _get_top_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top errors by frequency."""
        error_metrics = [
            metric for metric in self.metrics
            if metric.name.endswith('.error')
        ]
        
        error_counts = {}
        for metric in error_metrics:
            error_type = metric.tags.get('error_type', 'unknown')
            error_counts[error_type] = error_counts.get(error_type, 0) + metric.value
        
        # Sort by count and return top errors
        sorted_errors = sorted(
            error_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [
            {"error_type": error_type, "count": count}
            for error_type, count in sorted_errors[:limit]
        ]
    
    def _send_to_cloudwatch(self, metric: Metric):
        """Send metric to CloudWatch."""
        try:
            namespace = "Biomerkin/MultiAgent"
            
            cloudwatch_metric = {
                'MetricName': metric.name,
                'Value': metric.value,
                'Unit': self._get_cloudwatch_unit(metric.metric_type),
                'Timestamp': metric.timestamp,
                'Dimensions': [
                    {'Name': key, 'Value': value}
                    for key, value in metric.tags.items()
                ]
            }
            
            self.cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=[cloudwatch_metric]
            )
            
        except Exception as e:
            self.logger.error(f"Error sending metric to CloudWatch: {e}")
    
    def _get_cloudwatch_unit(self, metric_type: MetricType) -> str:
        """Get CloudWatch unit for metric type."""
        unit_mapping = {
            MetricType.COUNTER: "Count",
            MetricType.GAUGE: "None",
            MetricType.HISTOGRAM: "None",
            MetricType.TIMER: "Seconds"
        }
        return unit_mapping.get(metric_type, "None")
    
    def create_health_check(self, name: str, check_function: callable) -> None:
        """Create a health check."""
        self.health_checks[name] = {
            "function": check_function,
            "last_run": None,
            "last_result": None,
            "status": "unknown"
        }
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        
        for name, health_check in self.health_checks.items():
            try:
                start_time = time.time()
                result = await health_check["function"]()
                execution_time = time.time() - start_time
                
                health_check["last_run"] = datetime.now()
                health_check["last_result"] = result
                health_check["status"] = "healthy" if result.get("healthy", False) else "unhealthy"
                
                results[name] = {
                    "status": health_check["status"],
                    "result": result,
                    "execution_time": execution_time,
                    "last_run": health_check["last_run"].isoformat()
                }
                
            except Exception as e:
                health_check["status"] = "error"
                results[name] = {
                    "status": "error",
                    "error": str(e),
                    "last_run": datetime.now().isoformat()
                }
        
        return results


# Global monitoring service
monitoring_service = MonitoringService()

