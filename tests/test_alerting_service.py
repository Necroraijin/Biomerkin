"""
Tests for the alerting service module.

This module tests the comprehensive alerting capabilities including threshold monitoring,
notification management, and alert escalation.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from biomerkin.services.alerting_service import (
    AlertingService, AlertConfiguration, AlertRule, AlertChannel, AlertSeverity,
    NotificationTemplate, get_alerting_service, clear_alerting_service
)
from biomerkin.services.monitoring_service import Alert, SystemHealthMetrics


class TestAlertingService:
    """Test cases for AlertingService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        clear_alerting_service()
        self.alerting_service = AlertingService()
        
        # Mock AWS clients
        self.alerting_service.sns_client = Mock()
        self.alerting_service.cloudwatch = Mock()
    
    def test_initialization(self):
        """Test alerting service initialization."""
        assert self.alerting_service is not None
        assert len(self.alerting_service.alert_rules) > 0
        assert self.alerting_service.notification_template is not None
        assert len(self.alerting_service.active_alerts) == 0
        assert len(self.alerting_service.alert_history) == 0
        assert len(self.alerting_service.last_alert_times) == 0
    
    def test_configure_sns_topic(self):
        """Test SNS topic configuration."""
        topic_arn = "arn:aws:sns:us-east-1:123456789012:biomerkin-alerts"
        
        self.alerting_service.configure_sns_topic(topic_arn)
        
        assert self.alerting_service.sns_topic_arn == topic_arn
    
    def test_add_webhook_url(self):
        """Test adding webhook URL."""
        webhook_name = "slack"
        webhook_url = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
        
        self.alerting_service.add_webhook_url(webhook_name, webhook_url)
        
        assert webhook_name in self.alerting_service.webhook_urls
        assert self.alerting_service.webhook_urls[webhook_name] == webhook_url
    
    def test_register_custom_handler(self):
        """Test registering custom alert handler."""
        alert_type = "custom_alert"
        handler = Mock()
        
        self.alerting_service.register_custom_handler(alert_type, handler)
        
        assert alert_type in self.alerting_service.custom_handlers
        assert self.alerting_service.custom_handlers[alert_type] == handler
    
    def test_evaluate_alerts_no_triggers(self):
        """Test alert evaluation with no triggers."""
        # Create healthy system metrics
        health_metrics = SystemHealthMetrics(
            timestamp=datetime.utcnow(),
            workflow_success_rate=0.95,  # Above threshold
            average_processing_time=120.0,  # Below threshold
            active_workflows=5,
            failed_workflows_last_hour=1,
            api_response_times={'PubMed': 250.0},
            resource_utilization={'memory': 0.65},  # Below threshold
            error_rates={'genomics_agent': 0.02},
            cache_hit_rate=0.75  # Above threshold
        )
        
        alerts = self.alerting_service.evaluate_alerts(health_metrics)
        
        assert len(alerts) == 0
        assert len(self.alerting_service.active_alerts) == 0
    
    def test_evaluate_alerts_with_triggers(self):
        """Test alert evaluation with triggered alerts."""
        # Create unhealthy system metrics
        health_metrics = SystemHealthMetrics(
            timestamp=datetime.utcnow(),
            workflow_success_rate=0.85,  # Below 90% threshold
            average_processing_time=350.0,  # Above 300s threshold
            active_workflows=5,
            failed_workflows_last_hour=6,  # Above 5 threshold
            api_response_times={'PubMed': 250.0},
            resource_utilization={'memory': 0.85},  # Above 80% threshold
            error_rates={'genomics_agent': 0.02},
            cache_hit_rate=0.25  # Below 30% threshold
        )
        
        alerts = self.alerting_service.evaluate_alerts(health_metrics)
        
        # Should trigger multiple alerts
        assert len(alerts) > 0
        assert len(self.alerting_service.active_alerts) > 0
        
        # Check alert properties
        for alert in alerts:
            assert isinstance(alert, Alert)
            assert alert.alert_id is not None
            assert alert.severity in [AlertSeverity.LOW, AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL]
            assert alert.title is not None
            assert alert.description is not None
            assert alert.current_value is not None
            assert alert.threshold_value is not None
    
    def test_evaluate_alerts_cooldown_period(self):
        """Test alert cooldown period functionality."""
        # Create unhealthy metrics
        health_metrics = SystemHealthMetrics(
            timestamp=datetime.utcnow(),
            workflow_success_rate=0.85,  # Below threshold
            average_processing_time=120.0,
            active_workflows=5,
            failed_workflows_last_hour=1,
            api_response_times={'PubMed': 250.0},
            resource_utilization={'memory': 0.65},
            error_rates={'genomics_agent': 0.02},
            cache_hit_rate=0.75
        )
        
        # First evaluation should trigger alert
        alerts1 = self.alerting_service.evaluate_alerts(health_metrics)
        assert len(alerts1) > 0
        
        # Second evaluation immediately after should not trigger due to cooldown
        alerts2 = self.alerting_service.evaluate_alerts(health_metrics)
        assert len(alerts2) == 0
    
    def test_resolve_alert(self):
        """Test resolving an active alert."""
        # Create and add an alert
        alert = Alert(
            alert_id="test-alert-123",
            severity=AlertSeverity.MEDIUM,
            title="Test Alert",
            description="Test alert description",
            metric_name="test_metric",
            threshold_value=100.0,
            current_value=150.0,
            timestamp=datetime.utcnow()
        )
        
        self.alerting_service.active_alerts[alert.alert_id] = alert
        
        # Resolve the alert
        result = self.alerting_service.resolve_alert(alert.alert_id)
        
        assert result is True
        assert alert.alert_id not in self.alerting_service.active_alerts
        assert len(self.alerting_service.alert_history) == 1
        assert self.alerting_service.alert_history[0].resolved is True
    
    def test_resolve_nonexistent_alert(self):
        """Test resolving a non-existent alert."""
        result = self.alerting_service.resolve_alert("nonexistent-alert")
        
        assert result is False
    
    def test_get_active_alerts(self):
        """Test getting active alerts."""
        # Add some alerts
        alert1 = Alert(
            alert_id="alert-1",
            severity=AlertSeverity.HIGH,
            title="High Alert",
            description="High severity alert",
            metric_name="test_metric",
            threshold_value=100.0,
            current_value=150.0,
            timestamp=datetime.utcnow()
        )
        
        alert2 = Alert(
            alert_id="alert-2",
            severity=AlertSeverity.LOW,
            title="Low Alert",
            description="Low severity alert",
            metric_name="test_metric",
            threshold_value=50.0,
            current_value=25.0,
            timestamp=datetime.utcnow()
        )
        
        self.alerting_service.active_alerts[alert1.alert_id] = alert1
        self.alerting_service.active_alerts[alert2.alert_id] = alert2
        
        # Get all active alerts
        all_alerts = self.alerting_service.get_active_alerts()
        assert len(all_alerts) == 2
        
        # Get alerts filtered by severity
        high_alerts = self.alerting_service.get_active_alerts(AlertSeverity.HIGH)
        assert len(high_alerts) == 1
        assert high_alerts[0].severity == AlertSeverity.HIGH
    
    def test_get_alert_history(self):
        """Test getting alert history."""
        # Add some historical alerts
        old_alert = Alert(
            alert_id="old-alert",
            severity=AlertSeverity.MEDIUM,
            title="Old Alert",
            description="Old alert",
            metric_name="test_metric",
            threshold_value=100.0,
            current_value=150.0,
            timestamp=datetime.utcnow() - timedelta(hours=25),  # Older than 24 hours
            resolved=True
        )
        
        recent_alert = Alert(
            alert_id="recent-alert",
            severity=AlertSeverity.HIGH,
            title="Recent Alert",
            description="Recent alert",
            metric_name="test_metric",
            threshold_value=100.0,
            current_value=150.0,
            timestamp=datetime.utcnow() - timedelta(hours=1),  # Within 24 hours
            resolved=True
        )
        
        self.alerting_service.alert_history.extend([old_alert, recent_alert])
        
        # Get recent history (default 24 hours)
        recent_history = self.alerting_service.get_alert_history()
        assert len(recent_history) == 1
        assert recent_history[0].alert_id == "recent-alert"
        
        # Get longer history
        longer_history = self.alerting_service.get_alert_history(hours=48)
        assert len(longer_history) == 2
    
    def test_create_cloudwatch_alarms(self):
        """Test creating CloudWatch alarms."""
        # Configure SNS topic
        self.alerting_service.configure_sns_topic("arn:aws:sns:us-east-1:123456789012:alerts")
        
        results = self.alerting_service.create_cloudwatch_alarms()
        
        # Should have attempted to create alarms for all rules
        assert len(results) == len(self.alerting_service.alert_rules)
        
        # Check that CloudWatch was called
        assert self.alerting_service.cloudwatch.put_metric_alarm.call_count > 0
    
    def test_create_cloudwatch_alarms_no_sns(self):
        """Test creating CloudWatch alarms without SNS topic."""
        results = self.alerting_service.create_cloudwatch_alarms()
        
        # Should return empty results
        assert len(results) == 0
    
    def test_notification_template_format(self):
        """Test notification template formatting."""
        alert = Alert(
            alert_id="test-alert-123",
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="Test alert description",
            metric_name="test_metric",
            threshold_value=100.0,
            current_value=150.0,
            timestamp=datetime.utcnow()
        )
        
        notification = self.alerting_service.notification_template.format_notification(alert)
        
        assert 'title' in notification
        assert 'message' in notification
        assert 'color' in notification
        assert alert.title in notification['title']
        assert alert.description in notification['message']
        assert alert.alert_id in notification['message']
    
    @patch('requests.post')
    def test_send_webhook_notifications(self, mock_post):
        """Test sending webhook notifications."""
        # Configure webhook
        self.alerting_service.add_webhook_url("test", "https://example.com/webhook")
        
        alert = Alert(
            alert_id="test-alert-123",
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="Test alert description",
            metric_name="test_metric",
            threshold_value=100.0,
            current_value=150.0,
            timestamp=datetime.utcnow()
        )
        
        notification = {'title': 'Test Alert', 'message': 'Test message', 'color': '#ff4444'}
        
        # Mock successful response
        mock_post.return_value.raise_for_status.return_value = None
        
        self.alerting_service._send_webhook_notifications(alert, notification)
        
        # Check that webhook was called
        mock_post.assert_called_once()
        
        # Check payload
        call_args = mock_post.call_args
        assert 'json' in call_args.kwargs
        payload = call_args.kwargs['json']
        assert 'alert' in payload
        assert 'notification' in payload
    
    def test_send_sns_notification(self):
        """Test sending SNS notification."""
        # Configure SNS topic
        self.alerting_service.configure_sns_topic("arn:aws:sns:us-east-1:123456789012:alerts")
        
        alert = Alert(
            alert_id="test-alert-123",
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="Test alert description",
            metric_name="test_metric",
            threshold_value=100.0,
            current_value=150.0,
            timestamp=datetime.utcnow()
        )
        
        notification = {'title': 'Test Alert', 'message': 'Test message', 'color': '#ff4444'}
        
        self.alerting_service._send_sns_notification(alert, notification)
        
        # Check that SNS was called
        self.alerting_service.sns_client.publish.assert_called_once()
        
        # Check call arguments
        call_args = self.alerting_service.sns_client.publish.call_args
        assert call_args.kwargs['TopicArn'] == self.alerting_service.sns_topic_arn
        assert call_args.kwargs['Subject'] == notification['title']
        assert call_args.kwargs['MessageStructure'] == 'json'
    
    def test_send_log_notification(self):
        """Test sending log notification."""
        alert = Alert(
            alert_id="test-alert-123",
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            description="Test alert description",
            metric_name="test_metric",
            threshold_value=100.0,
            current_value=150.0,
            timestamp=datetime.utcnow()
        )
        
        notification = {'title': 'Test Alert', 'message': 'Test message', 'color': '#ff4444'}
        
        with patch.object(self.alerting_service.logger, 'log') as mock_log:
            self.alerting_service._send_log_notification(alert, notification)
            
            # Check that log was called with appropriate level
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            # High severity should use ERROR level
            assert call_args[0][0] == 40  # logging.ERROR
    
    def test_alert_configuration_to_dict(self):
        """Test AlertConfiguration to_dict conversion."""
        config = AlertConfiguration(
            rule_name="Test Rule",
            metric_name="test_metric",
            threshold=100.0,
            comparison_operator=">",
            evaluation_period=300,
            severity=AlertSeverity.HIGH,
            channels=[AlertChannel.EMAIL, AlertChannel.SNS],
            enabled=True,
            cooldown_period=600
        )
        
        config_dict = config.to_dict()
        
        assert config_dict['rule_name'] == "Test Rule"
        assert config_dict['metric_name'] == "test_metric"
        assert config_dict['threshold'] == 100.0
        assert config_dict['comparison_operator'] == ">"
        assert config_dict['evaluation_period'] == 300
        assert config_dict['severity'] == "high"
        assert config_dict['channels'] == ["email", "sns"]
        assert config_dict['enabled'] is True
        assert config_dict['cooldown_period'] == 600
    
    def test_default_alert_rules(self):
        """Test default alert rules initialization."""
        rules = self.alerting_service.alert_rules
        
        # Check that all expected rules are present
        expected_rules = [
            AlertRule.HIGH_ERROR_RATE.value,
            AlertRule.SLOW_PROCESSING.value,
            AlertRule.LOW_CACHE_HIT_RATE.value,
            AlertRule.HIGH_MEMORY_USAGE.value,
            AlertRule.API_FAILURES.value,
            AlertRule.WORKFLOW_FAILURES.value
        ]
        
        for rule in expected_rules:
            assert rule in rules
            assert isinstance(rules[rule], AlertConfiguration)
            assert rules[rule].enabled is True
    
    def test_evaluate_threshold_operators(self):
        """Test threshold evaluation with different operators."""
        # Test greater than
        assert self.alerting_service._evaluate_threshold(150.0, 100.0, '>') is True
        assert self.alerting_service._evaluate_threshold(50.0, 100.0, '>') is False
        
        # Test greater than or equal
        assert self.alerting_service._evaluate_threshold(100.0, 100.0, '>=') is True
        assert self.alerting_service._evaluate_threshold(150.0, 100.0, '>=') is True
        assert self.alerting_service._evaluate_threshold(50.0, 100.0, '>=') is False
        
        # Test less than
        assert self.alerting_service._evaluate_threshold(50.0, 100.0, '<') is True
        assert self.alerting_service._evaluate_threshold(150.0, 100.0, '<') is False
        
        # Test less than or equal
        assert self.alerting_service._evaluate_threshold(100.0, 100.0, '<=') is True
        assert self.alerting_service._evaluate_threshold(50.0, 100.0, '<=') is True
        assert self.alerting_service._evaluate_threshold(150.0, 100.0, '<=') is False
        
        # Test equal
        assert self.alerting_service._evaluate_threshold(100.0, 100.0, '==') is True
        assert self.alerting_service._evaluate_threshold(150.0, 100.0, '==') is False
        
        # Test invalid operator
        assert self.alerting_service._evaluate_threshold(150.0, 100.0, 'invalid') is False
    
    def test_global_alerting_service(self):
        """Test global alerting service instance."""
        service1 = get_alerting_service()
        service2 = get_alerting_service()
        
        # Should return the same instance
        assert service1 is service2
        
        # Clear and get new instance
        clear_alerting_service()
        service3 = get_alerting_service()
        
        # Should be a different instance
        assert service1 is not service3


if __name__ == '__main__':
    pytest.main([__file__])