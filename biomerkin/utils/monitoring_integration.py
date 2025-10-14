"""
Monitoring integration utilities for the Biomerkin multi-agent system.

This module provides integration utilities that tie together monitoring, alerting,
and dashboard services for comprehensive system observability.
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from ..services.monitoring_service import get_monitoring_service, SystemHealthMetrics
from ..services.alerting_service import get_alerting_service, Alert
from ..services.dashboard_service import get_dashboard_service
from ..utils.config import get_config
from ..utils.logging_config import get_logger


@dataclass
class MonitoringConfiguration:
    """Configuration for monitoring integration."""
    health_check_interval: int = 300  # 5 minutes
    alert_check_interval: int = 60   # 1 minute
    metrics_flush_interval: int = 60  # 1 minute
    dashboard_update_interval: int = 3600  # 1 hour
    enable_auto_recovery: bool = True
    enable_predictive_alerts: bool = True
    max_concurrent_checks: int = 5


class MonitoringIntegration:
    """
    Comprehensive monitoring integration service.
    
    Coordinates monitoring, alerting, and dashboard services to provide
    unified system observability and automated health management.
    """
    
    def __init__(self, config: Optional[MonitoringConfiguration] = None):
        """
        Initialize monitoring integration.
        
        Args:
            config: Optional monitoring configuration
        """
        self.logger = get_logger(__name__)
        self.config = config or MonitoringConfiguration()
        self.app_config = get_config()
        
        # Initialize services
        self.monitoring_service = get_monitoring_service()
        self.alerting_service = get_alerting_service()
        self.dashboard_service = get_dashboard_service()
        
        # State management
        self.is_running = False
        self.last_health_check = None
        self.last_alert_check = None
        self.last_metrics_flush = None
        self.last_dashboard_update = None
        
        # Performance tracking
        self.health_history: List[SystemHealthMetrics] = []
        self.alert_history: List[Alert] = []
        
        # Thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_checks)
        
        # Custom handlers
        self.health_change_handlers: List[Callable[[SystemHealthMetrics], None]] = []
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self.recovery_handlers: List[Callable[[str, Dict[str, Any]], None]] = []
    
    def start_monitoring(self) -> None:
        """Start the integrated monitoring system."""
        if self.is_running:
            self.logger.warning("Monitoring integration is already running")
            return
        
        self.is_running = True
        self.logger.info("Starting monitoring integration")
        
        # Initialize monitoring components
        self._initialize_monitoring_components()
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
    
    def stop_monitoring(self) -> None:
        """Stop the integrated monitoring system."""
        if not self.is_running:
            return
        
        self.is_running = False
        self.logger.info("Stopping monitoring integration")
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True)
    
    def register_health_change_handler(self, handler: Callable[[SystemHealthMetrics], None]) -> None:
        """
        Register a handler for health metric changes.
        
        Args:
            handler: Function to call when health metrics change
        """
        self.health_change_handlers.append(handler)
        self.logger.info("Registered health change handler")
    
    def register_alert_handler(self, handler: Callable[[Alert], None]) -> None:
        """
        Register a handler for new alerts.
        
        Args:
            handler: Function to call when new alerts are triggered
        """
        self.alert_handlers.append(handler)
        self.logger.info("Registered alert handler")
    
    def register_recovery_handler(self, handler: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        Register a handler for auto-recovery actions.
        
        Args:
            handler: Function to call when recovery actions are taken
        """
        self.recovery_handlers.append(handler)
        self.logger.info("Registered recovery handler")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            Dictionary with system status information
        """
        current_health = self.monitoring_service.get_system_health()
        active_alerts = self.alerting_service.get_active_alerts()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'monitoring_active': self.is_running,
            'health_metrics': current_health.to_dict(),
            'active_alerts': [alert.to_dict() for alert in active_alerts],
            'alert_count_by_severity': self._count_alerts_by_severity(active_alerts),
            'system_health_score': self._calculate_health_score(current_health),
            'last_checks': {
                'health_check': self.last_health_check.isoformat() if self.last_health_check else None,
                'alert_check': self.last_alert_check.isoformat() if self.last_alert_check else None,
                'metrics_flush': self.last_metrics_flush.isoformat() if self.last_metrics_flush else None,
                'dashboard_update': self.last_dashboard_update.isoformat() if self.last_dashboard_update else None
            },
            'performance_trends': self._get_performance_trends()
        }
    
    def trigger_health_check(self) -> SystemHealthMetrics:
        """
        Manually trigger a health check.
        
        Returns:
            Current system health metrics
        """
        self.logger.info("Manual health check triggered")
        return self._perform_health_check()
    
    def trigger_alert_check(self) -> List[Alert]:
        """
        Manually trigger an alert check.
        
        Returns:
            List of triggered alerts
        """
        self.logger.info("Manual alert check triggered")
        return self._perform_alert_check()
    
    def deploy_monitoring_infrastructure(self) -> Dict[str, bool]:
        """
        Deploy complete monitoring infrastructure.
        
        Returns:
            Dictionary of deployment results
        """
        self.logger.info("Deploying monitoring infrastructure")
        
        results = {}
        
        # Deploy dashboards
        dashboard_results = self.dashboard_service.deploy_all_dashboards()
        results.update({f"dashboard_{k}": v for k, v in dashboard_results.items()})
        
        # Create CloudWatch alarms
        alarm_results = self.alerting_service.create_cloudwatch_alarms()
        results.update({f"alarm_{k}": v for k, v in alarm_results.items()})
        
        # Configure SNS topic if available
        if hasattr(self.app_config, 'aws') and hasattr(self.app_config.aws, 'sns_topic_arn'):
            self.alerting_service.configure_sns_topic(self.app_config.aws.sns_topic_arn)
            results['sns_configuration'] = True
        else:
            results['sns_configuration'] = False
        
        self.logger.info(f"Monitoring infrastructure deployment completed: {results}")
        return results
    
    def generate_health_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        Generate comprehensive health report.
        
        Args:
            hours: Number of hours to include in the report
            
        Returns:
            Health report dictionary
        """
        current_health = self.monitoring_service.get_system_health()
        alert_history = self.alerting_service.get_alert_history(hours)
        
        # Calculate trends
        health_trend = self._calculate_health_trend(hours)
        alert_trend = self._calculate_alert_trend(hours)
        
        return {
            'report_timestamp': datetime.utcnow().isoformat(),
            'report_period_hours': hours,
            'current_health': current_health.to_dict(),
            'health_score': self._calculate_health_score(current_health),
            'health_trend': health_trend,
            'alert_summary': {
                'total_alerts': len(alert_history),
                'alerts_by_severity': self._count_alerts_by_severity(alert_history),
                'alert_trend': alert_trend,
                'most_common_alerts': self._get_most_common_alerts(alert_history)
            },
            'performance_summary': {
                'avg_workflow_success_rate': current_health.workflow_success_rate,
                'avg_processing_time': current_health.average_processing_time,
                'cache_performance': current_health.cache_hit_rate,
                'resource_utilization': current_health.resource_utilization
            },
            'recommendations': self._generate_recommendations(current_health, alert_history)
        }
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        self.logger.info("Starting monitoring loop")
        
        while self.is_running:
            try:
                current_time = datetime.utcnow()
                
                # Schedule concurrent checks
                tasks = []
                
                # Health check
                if self._should_perform_health_check(current_time):
                    tasks.append(self._async_health_check())
                
                # Alert check
                if self._should_perform_alert_check(current_time):
                    tasks.append(self._async_alert_check())
                
                # Metrics flush
                if self._should_flush_metrics(current_time):
                    tasks.append(self._async_metrics_flush())
                
                # Dashboard update
                if self._should_update_dashboards(current_time):
                    tasks.append(self._async_dashboard_update())
                
                # Execute tasks concurrently
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
                # Sleep until next check
                await asyncio.sleep(min(
                    self.config.health_check_interval,
                    self.config.alert_check_interval,
                    self.config.metrics_flush_interval
                ) / 10)  # Check 10 times per interval
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
    
    def _initialize_monitoring_components(self) -> None:
        """Initialize monitoring components."""
        try:
            # Configure alerting service
            if hasattr(self.app_config, 'aws') and hasattr(self.app_config.aws, 'sns_topic_arn'):
                self.alerting_service.configure_sns_topic(self.app_config.aws.sns_topic_arn)
            
            # Add webhook URLs if configured
            if hasattr(self.app_config, 'webhooks'):
                for name, url in self.app_config.webhooks.items():
                    self.alerting_service.add_webhook_url(name, url)
            
            self.logger.info("Monitoring components initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize monitoring components: {str(e)}")
    
    def _perform_health_check(self) -> SystemHealthMetrics:
        """Perform system health check."""
        try:
            health_metrics = self.monitoring_service.get_system_health()
            
            # Store in history
            self.health_history.append(health_metrics)
            
            # Keep only recent history (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self.health_history = [
                h for h in self.health_history 
                if h.timestamp >= cutoff_time
            ]
            
            # Notify handlers
            for handler in self.health_change_handlers:
                try:
                    handler(health_metrics)
                except Exception as e:
                    self.logger.error(f"Error in health change handler: {str(e)}")
            
            self.last_health_check = datetime.utcnow()
            return health_metrics
            
        except Exception as e:
            self.logger.error(f"Error performing health check: {str(e)}")
            raise
    
    def _perform_alert_check(self) -> List[Alert]:
        """Perform alert check."""
        try:
            # Get current health metrics
            health_metrics = self.monitoring_service.get_system_health()
            
            # Evaluate alerts
            triggered_alerts = self.alerting_service.evaluate_alerts(health_metrics)
            
            # Store in history
            self.alert_history.extend(triggered_alerts)
            
            # Notify handlers
            for alert in triggered_alerts:
                for handler in self.alert_handlers:
                    try:
                        handler(alert)
                    except Exception as e:
                        self.logger.error(f"Error in alert handler: {str(e)}")
                
                # Attempt auto-recovery if enabled
                if self.config.enable_auto_recovery:
                    self._attempt_auto_recovery(alert)
            
            self.last_alert_check = datetime.utcnow()
            return triggered_alerts
            
        except Exception as e:
            self.logger.error(f"Error performing alert check: {str(e)}")
            return []
    
    def _attempt_auto_recovery(self, alert: Alert) -> None:
        """Attempt automatic recovery for an alert."""
        try:
            recovery_actions = self._get_recovery_actions(alert)
            
            for action_name, action_params in recovery_actions.items():
                self.logger.info(f"Attempting auto-recovery action: {action_name}")
                
                # Notify recovery handlers
                for handler in self.recovery_handlers:
                    try:
                        handler(action_name, action_params)
                    except Exception as e:
                        self.logger.error(f"Error in recovery handler: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Error in auto-recovery for alert {alert.alert_id}: {str(e)}")
    
    def _get_recovery_actions(self, alert: Alert) -> Dict[str, Dict[str, Any]]:
        """Get recovery actions for an alert."""
        recovery_actions = {}
        
        if alert.metric_name == 'cache_hit_rate':
            recovery_actions['clear_cache'] = {'cache_type': 'all'}
        elif alert.metric_name == 'memory_utilization':
            recovery_actions['garbage_collect'] = {}
        elif alert.metric_name == 'workflow_success_rate':
            recovery_actions['restart_failed_workflows'] = {'max_retries': 3}
        
        return recovery_actions
    
    async def _async_health_check(self) -> None:
        """Asynchronous health check."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self._perform_health_check)
    
    async def _async_alert_check(self) -> None:
        """Asynchronous alert check."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self._perform_alert_check)
    
    async def _async_metrics_flush(self) -> None:
        """Asynchronous metrics flush."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self.monitoring_service.flush_metrics)
        self.last_metrics_flush = datetime.utcnow()
    
    async def _async_dashboard_update(self) -> None:
        """Asynchronous dashboard update."""
        # Dashboard updates are typically handled by CloudWatch automatically
        # This could be used for custom dashboard updates if needed
        self.last_dashboard_update = datetime.utcnow()
    
    def _should_perform_health_check(self, current_time: datetime) -> bool:
        """Check if health check should be performed."""
        if self.last_health_check is None:
            return True
        
        time_since_last = current_time - self.last_health_check
        return time_since_last.total_seconds() >= self.config.health_check_interval
    
    def _should_perform_alert_check(self, current_time: datetime) -> bool:
        """Check if alert check should be performed."""
        if self.last_alert_check is None:
            return True
        
        time_since_last = current_time - self.last_alert_check
        return time_since_last.total_seconds() >= self.config.alert_check_interval
    
    def _should_flush_metrics(self, current_time: datetime) -> bool:
        """Check if metrics should be flushed."""
        if self.last_metrics_flush is None:
            return True
        
        time_since_last = current_time - self.last_metrics_flush
        return time_since_last.total_seconds() >= self.config.metrics_flush_interval
    
    def _should_update_dashboards(self, current_time: datetime) -> bool:
        """Check if dashboards should be updated."""
        if self.last_dashboard_update is None:
            return True
        
        time_since_last = current_time - self.last_dashboard_update
        return time_since_last.total_seconds() >= self.config.dashboard_update_interval
    
    def _calculate_health_score(self, health_metrics: SystemHealthMetrics) -> float:
        """Calculate overall health score (0-100)."""
        # Weighted health score calculation
        weights = {
            'workflow_success_rate': 0.3,
            'cache_hit_rate': 0.2,
            'resource_utilization': 0.2,
            'api_performance': 0.2,
            'error_rate': 0.1
        }
        
        # Normalize metrics to 0-1 scale
        success_rate_score = health_metrics.workflow_success_rate
        cache_score = health_metrics.cache_hit_rate
        
        # Resource utilization (lower is better, so invert)
        avg_resource_util = sum(health_metrics.resource_utilization.values()) / len(health_metrics.resource_utilization) if health_metrics.resource_utilization else 0
        resource_score = max(0, 1 - avg_resource_util)
        
        # API performance (based on response times)
        avg_api_time = sum(health_metrics.api_response_times.values()) / len(health_metrics.api_response_times) if health_metrics.api_response_times else 0
        api_score = max(0, 1 - (avg_api_time / 1000))  # Normalize to 1 second
        
        # Error rate (lower is better, so invert)
        avg_error_rate = sum(health_metrics.error_rates.values()) / len(health_metrics.error_rates) if health_metrics.error_rates else 0
        error_score = max(0, 1 - avg_error_rate)
        
        # Calculate weighted score
        total_score = (
            success_rate_score * weights['workflow_success_rate'] +
            cache_score * weights['cache_hit_rate'] +
            resource_score * weights['resource_utilization'] +
            api_score * weights['api_performance'] +
            error_score * weights['error_rate']
        )
        
        return round(total_score * 100, 2)
    
    def _count_alerts_by_severity(self, alerts: List[Alert]) -> Dict[str, int]:
        """Count alerts by severity."""
        counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        for alert in alerts:
            counts[alert.severity.value] += 1
        
        return counts
    
    def _get_performance_trends(self) -> Dict[str, str]:
        """Get performance trends."""
        if len(self.health_history) < 2:
            return {'trend': 'insufficient_data'}
        
        # Compare recent vs older metrics
        recent = self.health_history[-1]
        older = self.health_history[0]
        
        trends = {}
        
        # Workflow success rate trend
        if recent.workflow_success_rate > older.workflow_success_rate:
            trends['workflow_success_rate'] = 'improving'
        elif recent.workflow_success_rate < older.workflow_success_rate:
            trends['workflow_success_rate'] = 'declining'
        else:
            trends['workflow_success_rate'] = 'stable'
        
        # Processing time trend
        if recent.average_processing_time < older.average_processing_time:
            trends['processing_time'] = 'improving'
        elif recent.average_processing_time > older.average_processing_time:
            trends['processing_time'] = 'declining'
        else:
            trends['processing_time'] = 'stable'
        
        return trends
    
    def _calculate_health_trend(self, hours: int) -> str:
        """Calculate health trend over time."""
        if len(self.health_history) < 2:
            return 'insufficient_data'
        
        # Simple trend calculation based on health scores
        recent_scores = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        for health in self.health_history:
            if health.timestamp >= cutoff_time:
                score = self._calculate_health_score(health)
                recent_scores.append(score)
        
        if len(recent_scores) < 2:
            return 'insufficient_data'
        
        # Calculate trend
        first_half = recent_scores[:len(recent_scores)//2]
        second_half = recent_scores[len(recent_scores)//2:]
        
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        
        if avg_second > avg_first + 5:
            return 'improving'
        elif avg_second < avg_first - 5:
            return 'declining'
        else:
            return 'stable'
    
    def _calculate_alert_trend(self, hours: int) -> str:
        """Calculate alert trend over time."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_alerts = [a for a in self.alert_history if a.timestamp >= cutoff_time]
        
        if len(recent_alerts) == 0:
            return 'no_alerts'
        
        # Simple trend based on alert frequency
        mid_point = cutoff_time + timedelta(hours=hours/2)
        first_half = [a for a in recent_alerts if a.timestamp < mid_point]
        second_half = [a for a in recent_alerts if a.timestamp >= mid_point]
        
        if len(second_half) > len(first_half):
            return 'increasing'
        elif len(second_half) < len(first_half):
            return 'decreasing'
        else:
            return 'stable'
    
    def _get_most_common_alerts(self, alerts: List[Alert]) -> List[Dict[str, Any]]:
        """Get most common alert types."""
        alert_counts = {}
        
        for alert in alerts:
            key = alert.metric_name
            if key not in alert_counts:
                alert_counts[key] = {'count': 0, 'severity': alert.severity.value}
            alert_counts[key]['count'] += 1
        
        # Sort by count
        sorted_alerts = sorted(alert_counts.items(), key=lambda x: x[1]['count'], reverse=True)
        
        return [
            {'metric_name': metric, 'count': data['count'], 'severity': data['severity']}
            for metric, data in sorted_alerts[:5]  # Top 5
        ]
    
    def _generate_recommendations(self, health_metrics: SystemHealthMetrics, 
                                alert_history: List[Alert]) -> List[str]:
        """Generate system recommendations."""
        recommendations = []
        
        # Workflow success rate recommendations
        if health_metrics.workflow_success_rate < 0.9:
            recommendations.append("Consider investigating workflow failures and implementing retry mechanisms")
        
        # Cache performance recommendations
        if health_metrics.cache_hit_rate < 0.5:
            recommendations.append("Cache hit rate is low - consider optimizing cache strategies or increasing cache size")
        
        # Resource utilization recommendations
        avg_memory = health_metrics.resource_utilization.get('memory', 0)
        if avg_memory > 0.8:
            recommendations.append("Memory utilization is high - consider scaling resources or optimizing memory usage")
        
        # API performance recommendations
        slow_apis = [api for api, time in health_metrics.api_response_times.items() if time > 1000]
        if slow_apis:
            recommendations.append(f"Slow API responses detected for: {', '.join(slow_apis)} - consider implementing caching or retry logic")
        
        # Alert frequency recommendations
        if len(alert_history) > 10:
            recommendations.append("High alert frequency detected - consider adjusting alert thresholds or addressing underlying issues")
        
        return recommendations


# Global monitoring integration instance
_monitoring_integration: Optional[MonitoringIntegration] = None


def get_monitoring_integration(config: Optional[MonitoringConfiguration] = None) -> MonitoringIntegration:
    """Get the global monitoring integration instance."""
    global _monitoring_integration
    if _monitoring_integration is None:
        _monitoring_integration = MonitoringIntegration(config)
    return _monitoring_integration


def clear_monitoring_integration():
    """Clear the global monitoring integration instance (useful for testing)."""
    global _monitoring_integration
    if _monitoring_integration and _monitoring_integration.is_running:
        _monitoring_integration.stop_monitoring()
    _monitoring_integration = None