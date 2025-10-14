"""
Tests for the dashboard service module.

This module tests the comprehensive dashboard capabilities including CloudWatch dashboard
management, custom dashboard creation, and real-time monitoring visualization.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from biomerkin.services.dashboard_service import (
    DashboardService, DashboardWidget, DashboardType, WidgetType,
    get_dashboard_service, clear_dashboard_service
)


class TestDashboardService:
    """Test cases for DashboardService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        clear_dashboard_service()
        self.dashboard_service = DashboardService()
        
        # Mock AWS clients
        self.dashboard_service.cloudwatch = Mock()
        
        # Mock services
        self.dashboard_service.monitoring_service = Mock()
        self.dashboard_service.alerting_service = Mock()
    
    def test_initialization(self):
        """Test dashboard service initialization."""
        assert self.dashboard_service is not None
        assert self.dashboard_service.namespace == 'Biomerkin/System'
        assert len(self.dashboard_service.dashboard_configs) > 0
    
    def test_dashboard_widget_creation(self):
        """Test dashboard widget creation."""
        widget = DashboardWidget(
            widget_type=WidgetType.LINE_CHART,
            title="Test Widget",
            metrics=[["Biomerkin/System", "WorkflowsStarted"]],
            position=(0, 0, 12, 6),
            properties={
                "view": "timeSeries",
                "period": 300
            }
        )
        
        assert widget.widget_type == WidgetType.LINE_CHART
        assert widget.title == "Test Widget"
        assert len(widget.metrics) == 1
        assert widget.position == (0, 0, 12, 6)
        assert widget.properties["view"] == "timeSeries"
    
    def test_dashboard_widget_to_cloudwatch(self):
        """Test converting dashboard widget to CloudWatch format."""
        widget = DashboardWidget(
            widget_type=WidgetType.LINE_CHART,
            title="Test Widget",
            metrics=[["Biomerkin/System", "WorkflowsStarted"]],
            position=(0, 0, 12, 6),
            properties={
                "view": "timeSeries",
                "period": 300
            }
        )
        
        cloudwatch_widget = widget.to_cloudwatch_widget("us-east-1")
        
        assert cloudwatch_widget["type"] == "metric"
        assert cloudwatch_widget["x"] == 0
        assert cloudwatch_widget["y"] == 0
        assert cloudwatch_widget["width"] == 12
        assert cloudwatch_widget["height"] == 6
        assert cloudwatch_widget["properties"]["title"] == "Test Widget"
        assert cloudwatch_widget["properties"]["region"] == "us-east-1"
        assert cloudwatch_widget["properties"]["metrics"] == [["Biomerkin/System", "WorkflowsStarted"]]
    
    def test_dashboard_widget_log_insights(self):
        """Test log insights widget conversion."""
        widget = DashboardWidget(
            widget_type=WidgetType.LOG_INSIGHTS,
            title="Error Logs",
            metrics=[],
            position=(0, 0, 24, 6),
            properties={
                "query": "SOURCE '/aws/lambda/biomerkin-orchestrator' | fields @timestamp, @message | filter @message like /ERROR/",
                "view": "table"
            }
        )
        
        cloudwatch_widget = widget.to_cloudwatch_widget("us-east-1")
        
        assert cloudwatch_widget["type"] == "log"
        assert "metrics" not in cloudwatch_widget["properties"]
        assert "query" in cloudwatch_widget["properties"]
    
    def test_create_system_overview_dashboard(self):
        """Test creating system overview dashboard."""
        dashboard_config = self.dashboard_service.create_system_overview_dashboard()
        
        assert "widgets" in dashboard_config
        widgets = dashboard_config["widgets"]
        assert len(widgets) > 0
        
        # Check for expected widget types
        widget_titles = [widget["properties"]["title"] for widget in widgets]
        expected_titles = [
            "System Health Score",
            "Active Workflows",
            "Workflow Success Rate",
            "Avg Processing Time (s)",
            "Workflow Trends",
            "Agent Execution Times",
            "Resource Utilization",
            "Cache Performance",
            "Recent Errors"
        ]
        
        for title in expected_titles:
            assert title in widget_titles
    
    def test_create_workflow_performance_dashboard(self):
        """Test creating workflow performance dashboard."""
        dashboard_config = self.dashboard_service.create_workflow_performance_dashboard()
        
        assert "widgets" in dashboard_config
        widgets = dashboard_config["widgets"]
        assert len(widgets) > 0
        
        # Check for expected widget types
        widget_titles = [widget["properties"]["title"] for widget in widgets]
        expected_titles = [
            "Workflow Throughput",
            "Processing Time Distribution",
            "Parallel Execution Efficiency",
            "Agent Execution Count",
            "Workflow Status Distribution",
            "Performance Analysis"
        ]
        
        for title in expected_titles:
            assert title in widget_titles
    
    def test_create_api_monitoring_dashboard(self):
        """Test creating API monitoring dashboard."""
        dashboard_config = self.dashboard_service.create_api_monitoring_dashboard()
        
        assert "widgets" in dashboard_config
        widgets = dashboard_config["widgets"]
        assert len(widgets) > 0
        
        # Check for expected widget types
        widget_titles = [widget["properties"]["title"] for widget in widgets]
        expected_titles = [
            "API Call Volume",
            "API Response Times",
            "API Error Rates",
            "API Success Rates"
        ]
        
        for title in expected_titles:
            assert title in widget_titles
        
        # Check that all expected APIs are included
        for widget in widgets:
            if "metrics" in widget["properties"]:
                metrics = widget["properties"]["metrics"]
                api_names = []
                for metric in metrics:
                    if len(metric) >= 4 and metric[2] == "APIName":
                        api_names.append(metric[3])
                
                if api_names:  # If this widget has API metrics
                    expected_apis = ["PubMed", "PDB", "DrugBank", "ClinicalTrials"]
                    for api in expected_apis:
                        assert api in api_names
    
    def test_create_cost_optimization_dashboard(self):
        """Test creating cost optimization dashboard."""
        dashboard_config = self.dashboard_service.create_cost_optimization_dashboard()
        
        assert "widgets" in dashboard_config
        widgets = dashboard_config["widgets"]
        assert len(widgets) > 0
        
        # Check for expected widget types
        widget_titles = [widget["properties"]["title"] for widget in widgets]
        expected_titles = [
            "Lambda Invocations",
            "Lambda Duration",
            "DynamoDB Read/Write Units",
            "S3 Storage Usage"
        ]
        
        for title in expected_titles:
            assert title in widget_titles
    
    def test_deploy_dashboard_success(self):
        """Test successful dashboard deployment."""
        dashboard_config = {"widgets": []}
        dashboard_name = "TestDashboard"
        
        result = self.dashboard_service.deploy_dashboard(dashboard_name, dashboard_config)
        
        assert result is True
        self.dashboard_service.cloudwatch.put_dashboard.assert_called_once_with(
            DashboardName=dashboard_name,
            DashboardBody=json.dumps(dashboard_config)
        )
    
    def test_deploy_dashboard_failure(self):
        """Test dashboard deployment failure."""
        dashboard_config = {"widgets": []}
        dashboard_name = "TestDashboard"
        
        # Mock CloudWatch to raise exception
        self.dashboard_service.cloudwatch.put_dashboard.side_effect = Exception("CloudWatch error")
        
        result = self.dashboard_service.deploy_dashboard(dashboard_name, dashboard_config)
        
        assert result is False
    
    def test_deploy_dashboard_no_cloudwatch(self):
        """Test dashboard deployment without CloudWatch client."""
        self.dashboard_service.cloudwatch = None
        
        dashboard_config = {"widgets": []}
        dashboard_name = "TestDashboard"
        
        result = self.dashboard_service.deploy_dashboard(dashboard_name, dashboard_config)
        
        assert result is False
    
    def test_deploy_all_dashboards(self):
        """Test deploying all predefined dashboards."""
        results = self.dashboard_service.deploy_all_dashboards()
        
        assert isinstance(results, dict)
        assert len(results) == 4  # Number of predefined dashboards
        
        expected_dashboards = [
            'system_overview',
            'workflow_performance',
            'api_monitoring',
            'cost_optimization'
        ]
        
        for dashboard in expected_dashboards:
            assert dashboard in results
            assert isinstance(results[dashboard], bool)
        
        # Check that CloudWatch was called for each dashboard
        assert self.dashboard_service.cloudwatch.put_dashboard.call_count == 4
    
    def test_get_dashboard_url(self):
        """Test getting dashboard URL."""
        dashboard_name = "TestDashboard"
        
        url = self.dashboard_service.get_dashboard_url(dashboard_name)
        
        assert url is not None
        assert dashboard_name in url
        assert "console.aws.amazon.com" in url
        assert "cloudwatch" in url
        assert self.dashboard_service.region in url
    
    def test_get_dashboard_url_no_region(self):
        """Test getting dashboard URL without region."""
        self.dashboard_service.region = None
        dashboard_name = "TestDashboard"
        
        url = self.dashboard_service.get_dashboard_url(dashboard_name)
        
        assert url is None
    
    def test_widget_type_mapping(self):
        """Test widget type to CloudWatch type mapping."""
        widget_types = [
            (WidgetType.LINE_CHART, "metric"),
            (WidgetType.BAR_CHART, "metric"),
            (WidgetType.PIE_CHART, "metric"),
            (WidgetType.NUMBER, "metric"),
            (WidgetType.LOG_INSIGHTS, "log"),
            (WidgetType.TABLE, "metric"),
            (WidgetType.GAUGE, "metric")
        ]
        
        for widget_type, expected_cw_type in widget_types:
            widget = DashboardWidget(
                widget_type=widget_type,
                title="Test",
                metrics=[],
                position=(0, 0, 12, 6),
                properties={}
            )
            
            assert widget._get_cloudwatch_type() == expected_cw_type
    
    def test_dashboard_config_initialization(self):
        """Test dashboard configuration initialization."""
        configs = self.dashboard_service.dashboard_configs
        
        expected_types = [
            DashboardType.SYSTEM_OVERVIEW,
            DashboardType.WORKFLOW_PERFORMANCE,
            DashboardType.API_MONITORING,
            DashboardType.COST_OPTIMIZATION
        ]
        
        for dashboard_type in expected_types:
            assert dashboard_type in configs
            assert 'name' in configs[dashboard_type]
            assert 'description' in configs[dashboard_type]
    
    def test_create_dashboard_config(self):
        """Test creating dashboard configuration from widgets."""
        widgets = [
            DashboardWidget(
                widget_type=WidgetType.LINE_CHART,
                title="Test Widget 1",
                metrics=[["Biomerkin/System", "WorkflowsStarted"]],
                position=(0, 0, 12, 6),
                properties={"view": "timeSeries"}
            ),
            DashboardWidget(
                widget_type=WidgetType.NUMBER,
                title="Test Widget 2",
                metrics=[["Biomerkin/System", "ActiveWorkflows"]],
                position=(12, 0, 12, 6),
                properties={"view": "singleValue"}
            )
        ]
        
        dashboard_config = self.dashboard_service._create_dashboard_config("TestDashboard", widgets)
        
        assert "widgets" in dashboard_config
        assert len(dashboard_config["widgets"]) == 2
        
        # Check widget properties
        for i, widget_config in enumerate(dashboard_config["widgets"]):
            assert widget_config["properties"]["title"] == f"Test Widget {i + 1}"
            assert widget_config["properties"]["region"] == self.dashboard_service.region
    
    def test_complex_widget_properties(self):
        """Test widget with complex properties."""
        widget = DashboardWidget(
            widget_type=WidgetType.LINE_CHART,
            title="Complex Widget",
            metrics=[
                ["Biomerkin/System", "WorkflowsStarted"],
                [".", "WorkflowsCompleted"],
                [".", "WorkflowsFailed"]
            ],
            position=(0, 0, 12, 6),
            properties={
                "view": "timeSeries",
                "stacked": False,
                "period": 300,
                "stat": "Sum",
                "yAxis": {
                    "left": {
                        "min": 0,
                        "max": 100
                    }
                }
            }
        )
        
        cloudwatch_widget = widget.to_cloudwatch_widget("us-east-1")
        
        assert cloudwatch_widget["properties"]["view"] == "timeSeries"
        assert cloudwatch_widget["properties"]["stacked"] is False
        assert cloudwatch_widget["properties"]["period"] == 300
        assert cloudwatch_widget["properties"]["stat"] == "Sum"
        assert "yAxis" in cloudwatch_widget["properties"]
        assert cloudwatch_widget["properties"]["yAxis"]["left"]["min"] == 0
        assert cloudwatch_widget["properties"]["yAxis"]["left"]["max"] == 100
    
    def test_global_dashboard_service(self):
        """Test global dashboard service instance."""
        service1 = get_dashboard_service()
        service2 = get_dashboard_service()
        
        # Should return the same instance
        assert service1 is service2
        
        # Clear and get new instance
        clear_dashboard_service()
        service3 = get_dashboard_service()
        
        # Should be a different instance
        assert service1 is not service3
    
    @patch('boto3.client')
    def test_aws_client_initialization_failure(self, mock_boto_client):
        """Test handling of AWS client initialization failure."""
        mock_boto_client.side_effect = Exception("AWS credentials not found")
        
        # Should not raise exception, but log warning
        service = DashboardService()
        
        assert service.cloudwatch is None
    
    def test_dashboard_widget_positions(self):
        """Test that dashboard widgets have non-overlapping positions."""
        dashboard_config = self.dashboard_service.create_system_overview_dashboard()
        widgets = dashboard_config["widgets"]
        
        positions = []
        for widget in widgets:
            x, y, width, height = widget["x"], widget["y"], widget["width"], widget["height"]
            positions.append((x, y, width, height))
        
        # Check that no two widgets have the exact same position
        unique_positions = set(positions)
        assert len(unique_positions) == len(positions)
        
        # Check that all positions are valid (non-negative)
        for x, y, width, height in positions:
            assert x >= 0
            assert y >= 0
            assert width > 0
            assert height > 0


if __name__ == '__main__':
    pytest.main([__file__])