"""
Dashboard service for the Biomerkin multi-agent system.

This module provides comprehensive dashboard capabilities including CloudWatch dashboard
management, custom dashboard creation, and real-time monitoring visualization.
"""

import logging
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from botocore.exceptions import ClientError

from ..utils.config import get_config
from ..utils.logging_config import get_logger
from .monitoring_service import SystemHealthMetrics, get_monitoring_service
from .alerting_service import get_alerting_service


class DashboardType(Enum):
    """Types of dashboards."""
    SYSTEM_OVERVIEW = "system_overview"
    WORKFLOW_PERFORMANCE = "workflow_performance"
    AGENT_METRICS = "agent_metrics"
    API_MONITORING = "api_monitoring"
    COST_OPTIMIZATION = "cost_optimization"
    ERROR_ANALYSIS = "error_analysis"


class WidgetType(Enum):
    """Types of dashboard widgets."""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    NUMBER = "number"
    LOG_INSIGHTS = "log_insights"
    TABLE = "table"
    GAUGE = "gauge"


@dataclass
class DashboardWidget:
    """Dashboard widget configuration."""
    widget_type: WidgetType
    title: str
    metrics: List[Dict[str, Any]]
    position: Tuple[int, int, int, int]  # x, y, width, height
    properties: Dict[str, Any]
    
    def to_cloudwatch_widget(self, region: str) -> Dict[str, Any]:
        """Convert to CloudWatch widget format."""
        widget_config = {
            "type": self._get_cloudwatch_type(),
            "x": self.position[0],
            "y": self.position[1],
            "width": self.position[2],
            "height": self.position[3],
            "properties": {
                "title": self.title,
                "region": region,
                **self.properties
            }
        }
        
        if self.widget_type != WidgetType.LOG_INSIGHTS:
            widget_config["properties"]["metrics"] = self.metrics
        
        return widget_config
    
    def _get_cloudwatch_type(self) -> str:
        """Get CloudWatch widget type."""
        type_map = {
            WidgetType.LINE_CHART: "metric",
            WidgetType.BAR_CHART: "metric",
            WidgetType.PIE_CHART: "metric",
            WidgetType.NUMBER: "metric",
            WidgetType.LOG_INSIGHTS: "log",
            WidgetType.TABLE: "metric",
            WidgetType.GAUGE: "metric"
        }
        return type_map.get(self.widget_type, "metric")


class DashboardService:
    """
    Comprehensive dashboard service for the Biomerkin system.
    
    Provides CloudWatch dashboard management, custom dashboard creation,
    and real-time monitoring visualization capabilities.
    """
    
    def __init__(self):
        """Initialize dashboard service."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Initialize AWS clients
        self.cloudwatch = None
        
        if self.config.environment == 'production':
            try:
                self.cloudwatch = boto3.client('cloudwatch', region_name=self.config.aws.region)
            except Exception as e:
                self.logger.warning(f"Failed to initialize CloudWatch client: {str(e)}")
        
        # Services
        self.monitoring_service = get_monitoring_service()
        self.alerting_service = get_alerting_service()
        
        # Configuration
        self.namespace = 'Biomerkin/System'
        self.region = self.config.aws.region
        
        # Dashboard configurations
        self.dashboard_configs = self._initialize_dashboard_configs()
    
    def create_system_overview_dashboard(self) -> Dict[str, Any]:
        """
        Create comprehensive system overview dashboard.
        
        Returns:
            Dashboard configuration
        """
        widgets = [
            # System health summary
            DashboardWidget(
                widget_type=WidgetType.NUMBER,
                title="System Health Score",
                metrics=[
                    [self.namespace, "SystemHealthScore"]
                ],
                position=(0, 0, 6, 3),
                properties={
                    "view": "singleValue",
                    "stat": "Average",
                    "period": 300
                }
            ),
            
            # Active workflows
            DashboardWidget(
                widget_type=WidgetType.NUMBER,
                title="Active Workflows",
                metrics=[
                    [self.namespace, "ActiveWorkflows"]
                ],
                position=(6, 0, 6, 3),
                properties={
                    "view": "singleValue",
                    "stat": "Maximum",
                    "period": 300
                }
            ),
            
            # Success rate
            DashboardWidget(
                widget_type=WidgetType.GAUGE,
                title="Workflow Success Rate",
                metrics=[
                    [self.namespace, "WorkflowSuccessRate"]
                ],
                position=(12, 0, 6, 3),
                properties={
                    "view": "gauge",
                    "stat": "Average",
                    "period": 300,
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 100
                        }
                    }
                }
            ),
            
            # Processing time
            DashboardWidget(
                widget_type=WidgetType.NUMBER,
                title="Avg Processing Time (s)",
                metrics=[
                    [self.namespace, "ProcessingTime"]
                ],
                position=(18, 0, 6, 3),
                properties={
                    "view": "singleValue",
                    "stat": "Average",
                    "period": 300
                }
            ),
            
            # Workflow trends
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="Workflow Trends",
                metrics=[
                    [self.namespace, "WorkflowsStarted"],
                    [".", "WorkflowsCompleted"],
                    [".", "WorkflowsFailed"]
                ],
                position=(0, 3, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 300,
                    "stat": "Sum"
                }
            ),
            
            # Agent performance
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="Agent Execution Times",
                metrics=[
                    [self.namespace, "AgentExecutionTime", "AgentName", "genomics"],
                    [".", ".", ".", "proteomics"],
                    [".", ".", ".", "literature"],
                    [".", ".", ".", "drug"],
                    [".", ".", ".", "decision"]
                ],
                position=(12, 3, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 300,
                    "stat": "Average"
                }
            ),
            
            # Resource utilization
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="Resource Utilization",
                metrics=[
                    [self.namespace, "ResourceUtilization", "ResourceType", "memory"],
                    [".", ".", ".", "cpu"],
                    [".", ".", ".", "disk"]
                ],
                position=(0, 9, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 300,
                    "stat": "Average",
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 100
                        }
                    }
                }
            ),
            
            # Cache performance
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="Cache Performance",
                metrics=[
                    [self.namespace, "CacheHitRate"],
                    [".", "CacheRequests"],
                    [".", "CacheSize"]
                ],
                position=(12, 9, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 300,
                    "stat": "Average"
                }
            ),
            
            # Recent errors
            DashboardWidget(
                widget_type=WidgetType.LOG_INSIGHTS,
                title="Recent Errors",
                metrics=[],
                position=(0, 15, 24, 6),
                properties={
                    "query": "SOURCE '/aws/lambda/biomerkin-orchestrator'\n| fields @timestamp, @message, @requestId\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 50",
                    "view": "table"
                }
            )
        ]
        
        return self._create_dashboard_config("BiomerkinSystemOverview", widgets)
    
    def create_workflow_performance_dashboard(self) -> Dict[str, Any]:
        """
        Create workflow performance dashboard.
        
        Returns:
            Dashboard configuration
        """
        widgets = [
            # Workflow throughput
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="Workflow Throughput",
                metrics=[
                    [self.namespace, "WorkflowsStarted"],
                    [".", "WorkflowsCompleted"]
                ],
                position=(0, 0, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 300,
                    "stat": "Sum"
                }
            ),
            
            # Processing time distribution
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="Processing Time Distribution",
                metrics=[
                    [self.namespace, "ProcessingTime"]
                ],
                position=(12, 0, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 300,
                    "stat": "Average"
                }
            ),
            
            # Parallel execution efficiency
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="Parallel Execution Efficiency",
                metrics=[
                    [self.namespace, "ParallelEfficiency"],
                    [".", "TimeSaved"]
                ],
                position=(0, 6, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 300,
                    "stat": "Average"
                }
            ),
            
            # Agent execution breakdown
            DashboardWidget(
                widget_type=WidgetType.BAR_CHART,
                title="Agent Execution Count",
                metrics=[
                    [self.namespace, "AgentExecutions", "AgentName", "genomics"],
                    [".", ".", ".", "proteomics"],
                    [".", ".", ".", "literature"],
                    [".", ".", ".", "drug"],
                    [".", ".", ".", "decision"]
                ],
                position=(12, 6, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": True,
                    "period": 300,
                    "stat": "Sum"
                }
            ),
            
            # Workflow status distribution
            DashboardWidget(
                widget_type=WidgetType.PIE_CHART,
                title="Workflow Status Distribution",
                metrics=[
                    [self.namespace, "WorkflowsCompleted"],
                    [".", "WorkflowsFailed"],
                    [".", "WorkflowsInProgress"]
                ],
                position=(0, 12, 12, 6),
                properties={
                    "view": "pie",
                    "period": 3600,
                    "stat": "Sum"
                }
            ),
            
            # Performance trends
            DashboardWidget(
                widget_type=WidgetType.LOG_INSIGHTS,
                title="Performance Analysis",
                metrics=[],
                position=(12, 12, 12, 6),
                properties={
                    "query": "SOURCE '/aws/lambda/biomerkin-orchestrator'\n| fields @timestamp, @message\n| filter @message like /workflow.*completed/\n| parse @message /processing_time=(?<time>\\d+\\.\\d+)/\n| stats avg(time) as avg_time, max(time) as max_time, min(time) as min_time by bin(5m)",
                    "view": "table"
                }
            )
        ]
        
        return self._create_dashboard_config("BiomerkinWorkflowPerformance", widgets)
    
    def create_api_monitoring_dashboard(self) -> Dict[str, Any]:
        """
        Create API monitoring dashboard.
        
        Returns:
            Dashboard configuration
        """
        widgets = [
            # API call volume
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="API Call Volume",
                metrics=[
                    [self.namespace, "ExternalAPICalls", "APIName", "PubMed"],
                    [".", ".", ".", "PDB"],
                    [".", ".", ".", "DrugBank"],
                    [".", ".", ".", "ClinicalTrials"]
                ],
                position=(0, 0, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 300,
                    "stat": "Sum"
                }
            ),
            
            # API response times
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="API Response Times",
                metrics=[
                    [self.namespace, "APIResponseTime", "APIName", "PubMed"],
                    [".", ".", ".", "PDB"],
                    [".", ".", ".", "DrugBank"],
                    [".", ".", ".", "ClinicalTrials"]
                ],
                position=(12, 0, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 300,
                    "stat": "Average"
                }
            ),
            
            # API error rates
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="API Error Rates",
                metrics=[
                    [self.namespace, "APIErrors", "APIName", "PubMed"],
                    [".", ".", ".", "PDB"],
                    [".", ".", ".", "DrugBank"],
                    [".", ".", ".", "ClinicalTrials"]
                ],
                position=(0, 6, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 300,
                    "stat": "Sum"
                }
            ),
            
            # API success rates
            DashboardWidget(
                widget_type=WidgetType.GAUGE,
                title="API Success Rates",
                metrics=[
                    [self.namespace, "APISuccessRate", "APIName", "PubMed"],
                    [".", ".", ".", "PDB"],
                    [".", ".", ".", "DrugBank"],
                    [".", ".", ".", "ClinicalTrials"]
                ],
                position=(12, 6, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 300,
                    "stat": "Average",
                    "yAxis": {
                        "left": {
                            "min": 0,
                            "max": 100
                        }
                    }
                }
            )
        ]
        
        return self._create_dashboard_config("BiomerkinAPIMonitoring", widgets)
    
    def create_cost_optimization_dashboard(self) -> Dict[str, Any]:
        """
        Create cost optimization dashboard.
        
        Returns:
            Dashboard configuration
        """
        widgets = [
            # Lambda invocations
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="Lambda Invocations",
                metrics=[
                    ["AWS/Lambda", "Invocations", "FunctionName", "biomerkin-orchestrator"],
                    [".", ".", ".", "biomerkin-genomics"],
                    [".", ".", ".", "biomerkin-proteomics"],
                    [".", ".", ".", "biomerkin-literature"],
                    [".", ".", ".", "biomerkin-drug"],
                    [".", ".", ".", "biomerkin-decision"]
                ],
                position=(0, 0, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 300,
                    "stat": "Sum"
                }
            ),
            
            # Lambda duration
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="Lambda Duration",
                metrics=[
                    ["AWS/Lambda", "Duration", "FunctionName", "biomerkin-orchestrator"],
                    [".", ".", ".", "biomerkin-genomics"],
                    [".", ".", ".", "biomerkin-proteomics"],
                    [".", ".", ".", "biomerkin-literature"],
                    [".", ".", ".", "biomerkin-drug"],
                    [".", ".", ".", "biomerkin-decision"]
                ],
                position=(12, 0, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 300,
                    "stat": "Average"
                }
            ),
            
            # DynamoDB consumption
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="DynamoDB Read/Write Units",
                metrics=[
                    ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "biomerkin-workflows"],
                    [".", "ConsumedWriteCapacityUnits", ".", "."],
                    [".", "ConsumedReadCapacityUnits", ".", "biomerkin-analysis-results"],
                    [".", "ConsumedWriteCapacityUnits", ".", "."]
                ],
                position=(0, 6, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 300,
                    "stat": "Sum"
                }
            ),
            
            # S3 storage metrics
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="S3 Storage Usage",
                metrics=[
                    ["AWS/S3", "BucketSizeBytes", "BucketName", "biomerkin-data", "StorageType", "StandardStorage"],
                    [".", ".", ".", "biomerkin-results", ".", "."],
                    [".", "NumberOfObjects", ".", "biomerkin-data", ".", "AllStorageTypes"],
                    [".", ".", ".", "biomerkin-results", ".", "."]
                ],
                position=(12, 6, 12, 6),
                properties={
                    "view": "timeSeries",
                    "stacked": False,
                    "period": 86400,
                    "stat": "Average"
                }
            )
        ]
        
        return self._create_dashboard_config("BiomerkinCostOptimization", widgets)
    
    def deploy_dashboard(self, dashboard_name: str, dashboard_config: Dict[str, Any]) -> bool:
        """
        Deploy dashboard to CloudWatch.
        
        Args:
            dashboard_name: Name of the dashboard
            dashboard_config: Dashboard configuration
            
        Returns:
            True if deployment was successful
        """
        if not self.cloudwatch:
            self.logger.warning("CloudWatch client not available")
            return False
        
        try:
            self.cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_config)
            )
            
            self.logger.info(f"Successfully deployed dashboard: {dashboard_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to deploy dashboard {dashboard_name}: {str(e)}")
            return False
    
    def deploy_all_dashboards(self) -> Dict[str, bool]:
        """
        Deploy all predefined dashboards.
        
        Returns:
            Dictionary of deployment results
        """
        results = {}
        
        # System overview dashboard
        system_overview = self.create_system_overview_dashboard()
        results['system_overview'] = self.deploy_dashboard('BiomerkinSystemOverview', system_overview)
        
        # Workflow performance dashboard
        workflow_performance = self.create_workflow_performance_dashboard()
        results['workflow_performance'] = self.deploy_dashboard('BiomerkinWorkflowPerformance', workflow_performance)
        
        # API monitoring dashboard
        api_monitoring = self.create_api_monitoring_dashboard()
        results['api_monitoring'] = self.deploy_dashboard('BiomerkinAPIMonitoring', api_monitoring)
        
        # Cost optimization dashboard
        cost_optimization = self.create_cost_optimization_dashboard()
        results['cost_optimization'] = self.deploy_dashboard('BiomerkinCostOptimization', cost_optimization)
        
        return results
    
    def get_dashboard_url(self, dashboard_name: str) -> Optional[str]:
        """
        Get CloudWatch dashboard URL.
        
        Args:
            dashboard_name: Name of the dashboard
            
        Returns:
            Dashboard URL if available
        """
        if not self.region:
            return None
        
        return f"https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}#dashboards:name={dashboard_name}"
    
    def _create_dashboard_config(self, dashboard_name: str, widgets: List[DashboardWidget]) -> Dict[str, Any]:
        """
        Create dashboard configuration from widgets.
        
        Args:
            dashboard_name: Name of the dashboard
            widgets: List of dashboard widgets
            
        Returns:
            Dashboard configuration
        """
        return {
            "widgets": [
                widget.to_cloudwatch_widget(self.region)
                for widget in widgets
            ]
        }
    
    def _initialize_dashboard_configs(self) -> Dict[DashboardType, Dict[str, Any]]:
        """Initialize dashboard configurations."""
        return {
            DashboardType.SYSTEM_OVERVIEW: {
                'name': 'BiomerkinSystemOverview',
                'description': 'Comprehensive system overview dashboard'
            },
            DashboardType.WORKFLOW_PERFORMANCE: {
                'name': 'BiomerkinWorkflowPerformance',
                'description': 'Workflow performance and throughput dashboard'
            },
            DashboardType.API_MONITORING: {
                'name': 'BiomerkinAPIMonitoring',
                'description': 'External API monitoring dashboard'
            },
            DashboardType.COST_OPTIMIZATION: {
                'name': 'BiomerkinCostOptimization',
                'description': 'Cost optimization and resource usage dashboard'
            }
        }


# Global dashboard service instance
_dashboard_service: Optional[DashboardService] = None


def get_dashboard_service() -> DashboardService:
    """Get the global dashboard service instance."""
    global _dashboard_service
    if _dashboard_service is None:
        _dashboard_service = DashboardService()
    return _dashboard_service


def clear_dashboard_service():
    """Clear the global dashboard service instance (useful for testing)."""
    global _dashboard_service
    _dashboard_service = None