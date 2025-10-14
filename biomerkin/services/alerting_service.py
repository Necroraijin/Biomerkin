"""
Alerting service for the Biomerkin multi-agent system.

This module provides comprehensive alerting capabilities including threshold monitoring,
notification management, and alert escalation for system health and performance issues.
"""

import logging
import json
import time
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from botocore.exceptions import ClientError

from ..utils.config import get_config
from ..utils.logging_config import get_logger
from .monitoring_service import Alert, AlertSeverity, SystemHealthMetrics


class AlertChannel(Enum):
    """Alert notification channels."""
    EMAIL = "email"
    SNS = "sns"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"


class AlertRule(Enum):
    """Predefined alert rules."""
    HIGH_ERROR_RATE = "high_error_rate"
    SLOW_PROCESSING = "slow_processing"
    LOW_CACHE_HIT_RATE = "low_cache_hit_rate"
    HIGH_MEMORY_USAGE = "high_memory_usage"
    API_FAILURES = "api_failures"
    WORKFLOW_FAILURES = "workflow_failures"
    SYSTEM_OVERLOAD = "system_overload"


@dataclass
class AlertConfiguration:
    """Configuration for an alert rule."""
    rule_name: str
    metric_name: str
    threshold: float
    comparison_operator: str  # >, <, >=, <=, ==
    evaluation_period: int  # seconds
    severity: AlertSeverity
    channels: List[AlertChannel]
    enabled: bool = True
    cooldown_period: int = 300  # 5 minutes default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'rule_name': self.rule_name,
            'metric_name': self.metric_name,
            'threshold': self.threshold,
            'comparison_operator': self.comparison_operator,
            'evaluation_period': self.evaluation_period,
            'severity': self.severity.value,
            'channels': [channel.value for channel in self.channels],
            'enabled': self.enabled,
            'cooldown_period': self.cooldown_period
        }


@dataclass
class NotificationTemplate:
    """Template for alert notifications."""
    title_template: str
    message_template: str
    severity_colors: Dict[str, str]
    
    def format_notification(self, alert: Alert, additional_context: Dict[str, Any] = None) -> Dict[str, str]:
        """Format notification using the template."""
        context = {
            'alert_id': alert.alert_id,
            'severity': alert.severity.value,
            'title': alert.title,
            'description': alert.description,
            'metric_name': alert.metric_name,
            'threshold_value': alert.threshold_value,
            'current_value': alert.current_value,
            'timestamp': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
            **(additional_context or {})
        }
        
        formatted_title = self.title_template.format(**context)
        formatted_message = self.message_template.format(**context)
        
        return {
            'title': formatted_title,
            'message': formatted_message,
            'color': self.severity_colors.get(alert.severity.value, '#808080')
        }


class AlertingService:
    """
    Comprehensive alerting service for the Biomerkin system.
    
    Provides threshold monitoring, notification management, alert escalation,
    and integration with various notification channels.
    """
    
    def __init__(self):
        """Initialize alerting service."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        # Initialize AWS clients
        self.sns_client = None
        self.cloudwatch = None
        
        if self.config.environment == 'production':
            try:
                self.sns_client = boto3.client('sns', region_name=self.config.aws.region)
                self.cloudwatch = boto3.client('cloudwatch', region_name=self.config.aws.region)
            except Exception as e:
                self.logger.warning(f"Failed to initialize AWS clients: {str(e)}")
        
        # Alert state management
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_alert_times: Dict[str, datetime] = {}
        
        # Configuration
        self.alert_rules = self._initialize_default_alert_rules()
        self.notification_template = self._create_notification_template()
        self.sns_topic_arn = None
        
        # Webhook configurations
        self.webhook_urls: Dict[str, str] = {}
        
        # Custom alert handlers
        self.custom_handlers: Dict[str, Callable[[Alert], None]] = {}
    
    def configure_sns_topic(self, topic_arn: str) -> None:
        """
        Configure SNS topic for notifications.
        
        Args:
            topic_arn: ARN of the SNS topic
        """
        self.sns_topic_arn = topic_arn
        self.logger.info(f"Configured SNS topic: {topic_arn}")
    
    def add_webhook_url(self, name: str, url: str) -> None:
        """
        Add webhook URL for notifications.
        
        Args:
            name: Name identifier for the webhook
            url: Webhook URL
        """
        self.webhook_urls[name] = url
        self.logger.info(f"Added webhook: {name}")
    
    def register_custom_handler(self, alert_type: str, handler: Callable[[Alert], None]) -> None:
        """
        Register custom alert handler.
        
        Args:
            alert_type: Type of alert to handle
            handler: Handler function
        """
        self.custom_handlers[alert_type] = handler
        self.logger.info(f"Registered custom handler for: {alert_type}")
    
    def evaluate_alerts(self, health_metrics: SystemHealthMetrics) -> List[Alert]:
        """
        Evaluate alert rules against current metrics.
        
        Args:
            health_metrics: Current system health metrics
            
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        current_time = datetime.utcnow()
        
        for rule_name, rule_config in self.alert_rules.items():
            if not rule_config.enabled:
                continue
            
            # Check cooldown period
            if rule_name in self.last_alert_times:
                time_since_last = current_time - self.last_alert_times[rule_name]
                if time_since_last.total_seconds() < rule_config.cooldown_period:
                    continue
            
            # Get metric value
            metric_value = self._get_metric_value(health_metrics, rule_config.metric_name)
            if metric_value is None:
                continue
            
            # Evaluate threshold
            if self._evaluate_threshold(metric_value, rule_config.threshold, rule_config.comparison_operator):
                alert = Alert(
                    alert_id=f"{rule_name}_{int(time.time())}",
                    severity=rule_config.severity,
                    title=self._generate_alert_title(rule_name, rule_config),
                    description=self._generate_alert_description(rule_name, rule_config, metric_value),
                    metric_name=rule_config.metric_name,
                    threshold_value=rule_config.threshold,
                    current_value=metric_value,
                    timestamp=current_time
                )
                
                triggered_alerts.append(alert)
                self.active_alerts[alert.alert_id] = alert
                self.last_alert_times[rule_name] = current_time
                
                # Send notifications
                self._send_alert_notifications(alert, rule_config.channels)
        
        return triggered_alerts
    
    def resolve_alert(self, alert_id: str) -> bool:
        """
        Resolve an active alert.
        
        Args:
            alert_id: ID of the alert to resolve
            
        Returns:
            True if alert was resolved successfully
        """
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            
            # Move to history
            self.alert_history.append(alert)
            del self.active_alerts[alert_id]
            
            self.logger.info(f"Resolved alert: {alert_id}")
            return True
        
        return False
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """
        Get list of active alerts.
        
        Args:
            severity: Optional severity filter
            
        Returns:
            List of active alerts
        """
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """
        Get alert history for the specified time period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of historical alerts
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            alert for alert in self.alert_history
            if alert.timestamp >= cutoff_time
        ]
    
    def create_cloudwatch_alarms(self) -> Dict[str, bool]:
        """
        Create CloudWatch alarms based on alert rules.
        
        Returns:
            Dictionary of alarm creation results
        """
        if not self.cloudwatch or not self.sns_topic_arn:
            self.logger.warning("CloudWatch client or SNS topic not configured")
            return {}
        
        results = {}
        
        for rule_name, rule_config in self.alert_rules.items():
            try:
                alarm_name = f"Biomerkin-{rule_name}"
                
                # Map comparison operators
                comparison_operator_map = {
                    '>': 'GreaterThanThreshold',
                    '>=': 'GreaterThanOrEqualToThreshold',
                    '<': 'LessThanThreshold',
                    '<=': 'LessThanOrEqualToThreshold'
                }
                
                comparison_operator = comparison_operator_map.get(
                    rule_config.comparison_operator,
                    'GreaterThanThreshold'
                )
                
                self.cloudwatch.put_metric_alarm(
                    AlarmName=alarm_name,
                    ComparisonOperator=comparison_operator,
                    EvaluationPeriods=1,
                    MetricName=rule_config.metric_name,
                    Namespace='Biomerkin/System',
                    Period=rule_config.evaluation_period,
                    Statistic='Average',
                    Threshold=rule_config.threshold,
                    ActionsEnabled=True,
                    AlarmActions=[self.sns_topic_arn],
                    AlarmDescription=f'Alert for {rule_config.metric_name}',
                    Unit='Count'
                )
                
                results[rule_name] = True
                self.logger.info(f"Created CloudWatch alarm: {alarm_name}")
                
            except Exception as e:
                results[rule_name] = False
                self.logger.error(f"Failed to create alarm for {rule_name}: {str(e)}")
        
        return results
    
    def _initialize_default_alert_rules(self) -> Dict[str, AlertConfiguration]:
        """Initialize default alert rules."""
        return {
            AlertRule.HIGH_ERROR_RATE.value: AlertConfiguration(
                rule_name="High Error Rate",
                metric_name="workflow_success_rate",
                threshold=0.9,
                comparison_operator="<",
                evaluation_period=300,
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.EMAIL, AlertChannel.SNS]
            ),
            AlertRule.SLOW_PROCESSING.value: AlertConfiguration(
                rule_name="Slow Processing",
                metric_name="average_processing_time",
                threshold=300.0,
                comparison_operator=">",
                evaluation_period=600,
                severity=AlertSeverity.MEDIUM,
                channels=[AlertChannel.EMAIL, AlertChannel.SNS]
            ),
            AlertRule.LOW_CACHE_HIT_RATE.value: AlertConfiguration(
                rule_name="Low Cache Hit Rate",
                metric_name="cache_hit_rate",
                threshold=0.3,
                comparison_operator="<",
                evaluation_period=900,
                severity=AlertSeverity.LOW,
                channels=[AlertChannel.LOG]
            ),
            AlertRule.HIGH_MEMORY_USAGE.value: AlertConfiguration(
                rule_name="High Memory Usage",
                metric_name="memory_utilization",
                threshold=0.8,
                comparison_operator=">",
                evaluation_period=300,
                severity=AlertSeverity.MEDIUM,
                channels=[AlertChannel.EMAIL, AlertChannel.SNS]
            ),
            AlertRule.API_FAILURES.value: AlertConfiguration(
                rule_name="API Failures",
                metric_name="api_error_rate",
                threshold=0.1,
                comparison_operator=">",
                evaluation_period=300,
                severity=AlertSeverity.HIGH,
                channels=[AlertChannel.EMAIL, AlertChannel.SNS]
            ),
            AlertRule.WORKFLOW_FAILURES.value: AlertConfiguration(
                rule_name="Workflow Failures",
                metric_name="failed_workflows_last_hour",
                threshold=5.0,
                comparison_operator=">",
                evaluation_period=300,
                severity=AlertSeverity.CRITICAL,
                channels=[AlertChannel.EMAIL, AlertChannel.SNS, AlertChannel.WEBHOOK]
            )
        }
    
    def _create_notification_template(self) -> NotificationTemplate:
        """Create notification template."""
        return NotificationTemplate(
            title_template="🚨 Biomerkin Alert: {title}",
            message_template="""
**Alert Details:**
- **Severity:** {severity}
- **Metric:** {metric_name}
- **Current Value:** {current_value}
- **Threshold:** {threshold_value}
- **Time:** {timestamp}

**Description:** {description}

**Alert ID:** {alert_id}
            """.strip(),
            severity_colors={
                'low': '#36a64f',
                'medium': '#ff9500',
                'high': '#ff4444',
                'critical': '#cc0000'
            }
        )
    
    def _get_metric_value(self, health_metrics: SystemHealthMetrics, metric_name: str) -> Optional[float]:
        """Get metric value from health metrics."""
        metric_map = {
            'workflow_success_rate': health_metrics.workflow_success_rate,
            'average_processing_time': health_metrics.average_processing_time,
            'active_workflows': float(health_metrics.active_workflows),
            'failed_workflows_last_hour': float(health_metrics.failed_workflows_last_hour),
            'cache_hit_rate': health_metrics.cache_hit_rate,
            'memory_utilization': health_metrics.resource_utilization.get('memory', 0.0),
            'cpu_utilization': health_metrics.resource_utilization.get('cpu', 0.0),
            'api_error_rate': sum(health_metrics.error_rates.values()) / len(health_metrics.error_rates) if health_metrics.error_rates else 0.0
        }
        
        return metric_map.get(metric_name)
    
    def _evaluate_threshold(self, value: float, threshold: float, operator: str) -> bool:
        """Evaluate threshold condition."""
        if operator == '>':
            return value > threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '<':
            return value < threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '==':
            return value == threshold
        else:
            return False
    
    def _generate_alert_title(self, rule_name: str, rule_config: AlertConfiguration) -> str:
        """Generate alert title."""
        return f"{rule_config.rule_name} Detected"
    
    def _generate_alert_description(self, rule_name: str, rule_config: AlertConfiguration, current_value: float) -> str:
        """Generate alert description."""
        return f"{rule_config.metric_name} is {current_value}, which {rule_config.comparison_operator} {rule_config.threshold}"
    
    def _send_alert_notifications(self, alert: Alert, channels: List[AlertChannel]) -> None:
        """Send alert notifications to specified channels."""
        notification = self.notification_template.format_notification(alert)
        
        for channel in channels:
            try:
                if channel == AlertChannel.EMAIL and self.sns_topic_arn:
                    self._send_email_notification(alert, notification)
                elif channel == AlertChannel.SNS and self.sns_topic_arn:
                    self._send_sns_notification(alert, notification)
                elif channel == AlertChannel.WEBHOOK:
                    self._send_webhook_notifications(alert, notification)
                elif channel == AlertChannel.LOG:
                    self._send_log_notification(alert, notification)
                
            except Exception as e:
                self.logger.error(f"Failed to send notification via {channel.value}: {str(e)}")
    
    def _send_email_notification(self, alert: Alert, notification: Dict[str, str]) -> None:
        """Send email notification via SNS."""
        if not self.sns_client or not self.sns_topic_arn:
            return
        
        self.sns_client.publish(
            TopicArn=self.sns_topic_arn,
            Subject=notification['title'],
            Message=notification['message']
        )
    
    def _send_sns_notification(self, alert: Alert, notification: Dict[str, str]) -> None:
        """Send SNS notification."""
        if not self.sns_client or not self.sns_topic_arn:
            return
        
        message = {
            'default': notification['message'],
            'email': notification['message'],
            'sms': f"{notification['title']}: {alert.description}"
        }
        
        self.sns_client.publish(
            TopicArn=self.sns_topic_arn,
            Subject=notification['title'],
            Message=json.dumps(message),
            MessageStructure='json'
        )
    
    def _send_webhook_notifications(self, alert: Alert, notification: Dict[str, str]) -> None:
        """Send webhook notifications."""
        import requests
        
        payload = {
            'alert': alert.to_dict(),
            'notification': notification
        }
        
        for name, url in self.webhook_urls.items():
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=10,
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()
                
            except Exception as e:
                self.logger.error(f"Failed to send webhook notification to {name}: {str(e)}")
    
    def _send_log_notification(self, alert: Alert, notification: Dict[str, str]) -> None:
        """Send log notification."""
        log_level = {
            AlertSeverity.LOW: logging.INFO,
            AlertSeverity.MEDIUM: logging.WARNING,
            AlertSeverity.HIGH: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }.get(alert.severity, logging.INFO)
        
        self.logger.log(log_level, f"ALERT: {notification['title']} - {alert.description}")


# Global alerting service instance
_alerting_service: Optional[AlertingService] = None


def get_alerting_service() -> AlertingService:
    """Get the global alerting service instance."""
    global _alerting_service
    if _alerting_service is None:
        _alerting_service = AlertingService()
    return _alerting_service


def clear_alerting_service():
    """Clear the global alerting service instance (useful for testing)."""
    global _alerting_service
    _alerting_service = None