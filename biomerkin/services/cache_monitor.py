"""
Cache monitoring and metrics collection for the Biomerkin system.

This module provides comprehensive monitoring capabilities for the cache layer,
including performance metrics, health checks, and alerting.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import boto3
from botocore.exceptions import ClientError

from .cache_manager import get_cache_manager, CacheType, CacheMetrics
from ..utils.config import get_config


@dataclass
class CacheHealthStatus:
    """Cache health status information."""
    is_healthy: bool
    backend_available: bool
    hit_rate: float
    total_entries: int
    total_size_mb: float
    last_check: datetime
    issues: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'is_healthy': self.is_healthy,
            'backend_available': self.backend_available,
            'hit_rate': self.hit_rate,
            'total_entries': self.total_entries,
            'total_size_mb': self.total_size_mb,
            'last_check': self.last_check.isoformat(),
            'issues': self.issues
        }


@dataclass
class CachePerformanceReport:
    """Detailed cache performance report."""
    period_start: datetime
    period_end: datetime
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_rate: float
    miss_rate: float
    average_response_time_ms: float
    entries_by_type: Dict[str, int]
    size_by_type: Dict[str, int]
    top_accessed_keys: List[Dict[str, Any]]
    evictions: int
    errors: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'total_requests': self.total_requests,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': self.hit_rate,
            'miss_rate': self.miss_rate,
            'average_response_time_ms': self.average_response_time_ms,
            'entries_by_type': self.entries_by_type,
            'size_by_type': self.size_by_type,
            'top_accessed_keys': self.top_accessed_keys,
            'evictions': self.evictions,
            'errors': self.errors
        }


class CacheMonitor:
    """
    Comprehensive cache monitoring and metrics collection.
    
    Provides health checks, performance monitoring, and alerting
    capabilities for the cache layer.
    """
    
    def __init__(self):
        """Initialize cache monitor."""
        self.logger = logging.getLogger(__name__)
        self.config = get_config()
        self.cache_manager = get_cache_manager()
        
        # Initialize CloudWatch client if in AWS environment
        self.cloudwatch = None
        if self.config.environment == 'production':
            try:
                self.cloudwatch = boto3.client('cloudwatch', region_name=self.config.aws.region)
            except Exception as e:
                self.logger.warning(f"Failed to initialize CloudWatch client: {str(e)}")
        
        # Performance tracking
        self.request_times: List[float] = []
        self.error_count = 0
        self.last_health_check: Optional[datetime] = None
        self.health_check_interval = timedelta(minutes=5)
    
    def health_check(self) -> CacheHealthStatus:
        """
        Perform comprehensive cache health check.
        
        Returns:
            CacheHealthStatus with current health information
        """
        issues = []
        backend_available = True
        
        try:
            # Test backend connectivity
            test_key = "health_check_test"
            test_value = {"timestamp": datetime.utcnow().isoformat()}
            
            # Try to store and retrieve a test value
            success = self.cache_manager.put(test_key, test_value, CacheType.API_RESPONSE, ttl_seconds=60)
            if not success:
                backend_available = False
                issues.append("Failed to store test value in cache backend")
            else:
                retrieved = self.cache_manager.get(test_key, CacheType.API_RESPONSE)
                if retrieved != test_value:
                    backend_available = False
                    issues.append("Failed to retrieve test value from cache backend")
                else:
                    # Clean up test value
                    self.cache_manager.delete(test_key, CacheType.API_RESPONSE)
        
        except Exception as e:
            backend_available = False
            issues.append(f"Cache backend error: {str(e)}")
        
        # Get current metrics
        metrics = self.cache_manager.get_metrics()
        
        # Check hit rate
        if metrics.hit_rate < 0.3:  # Less than 30% hit rate
            issues.append(f"Low cache hit rate: {metrics.hit_rate:.2%}")
        
        # Check for high error rate
        if self.error_count > 10:  # More than 10 errors since last check
            issues.append(f"High error count: {self.error_count}")
        
        # Determine overall health
        is_healthy = backend_available and len(issues) == 0
        
        health_status = CacheHealthStatus(
            is_healthy=is_healthy,
            backend_available=backend_available,
            hit_rate=metrics.hit_rate,
            total_entries=metrics.entries_count,
            total_size_mb=metrics.total_size_bytes / (1024 * 1024),
            last_check=datetime.utcnow(),
            issues=issues
        )
        
        self.last_health_check = datetime.utcnow()
        
        # Send metrics to CloudWatch if available
        if self.cloudwatch:
            self._send_health_metrics_to_cloudwatch(health_status)
        
        # Reset error count after health check
        self.error_count = 0
        
        return health_status
    
    def get_performance_report(self, hours: int = 24) -> CachePerformanceReport:
        """
        Generate detailed performance report.
        
        Args:
            hours: Number of hours to include in the report
            
        Returns:
            CachePerformanceReport with performance data
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        metrics = self.cache_manager.get_metrics()
        
        # Calculate average response time
        avg_response_time = 0.0
        if self.request_times:
            avg_response_time = sum(self.request_times) / len(self.request_times)
        
        # Get entries by type (simplified - in production you'd query the backend)
        entries_by_type = {}
        size_by_type = {}
        
        for cache_type in CacheType:
            try:
                keys = self.cache_manager.backend.list_keys(cache_type)
                entries_by_type[cache_type.value] = len(keys)
                
                # Estimate size (simplified calculation)
                total_size = 0
                for key in keys[:10]:  # Sample first 10 entries
                    entry = self.cache_manager.backend.get(key)
                    if entry:
                        total_size += entry.size_bytes
                
                # Extrapolate total size
                if len(keys) > 0:
                    avg_size = total_size / min(len(keys), 10)
                    size_by_type[cache_type.value] = int(avg_size * len(keys))
                else:
                    size_by_type[cache_type.value] = 0
                    
            except Exception as e:
                self.logger.warning(f"Error getting stats for cache type {cache_type}: {str(e)}")
                entries_by_type[cache_type.value] = 0
                size_by_type[cache_type.value] = 0
        
        # Top accessed keys (simplified - would need access tracking in production)
        top_accessed_keys = []
        
        report = CachePerformanceReport(
            period_start=start_time,
            period_end=end_time,
            total_requests=metrics.total_requests,
            cache_hits=metrics.cache_hits,
            cache_misses=metrics.cache_misses,
            hit_rate=metrics.hit_rate,
            miss_rate=metrics.miss_rate,
            average_response_time_ms=avg_response_time * 1000,
            entries_by_type=entries_by_type,
            size_by_type=size_by_type,
            top_accessed_keys=top_accessed_keys,
            evictions=metrics.evictions_count,
            errors=self.error_count
        )
        
        return report
    
    def record_request_time(self, duration_seconds: float):
        """Record a cache request duration."""
        self.request_times.append(duration_seconds)
        
        # Keep only recent request times (last 1000)
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
    
    def record_error(self):
        """Record a cache error."""
        self.error_count += 1
    
    def should_perform_health_check(self) -> bool:
        """Check if it's time for a health check."""
        if self.last_health_check is None:
            return True
        
        return datetime.utcnow() - self.last_health_check > self.health_check_interval
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get current cache statistics."""
        metrics = self.cache_manager.get_metrics()
        
        stats = {
            'metrics': metrics.to_dict(),
            'backend_type': type(self.cache_manager.backend).__name__,
            'request_times_count': len(self.request_times),
            'error_count': self.error_count,
            'last_health_check': self.last_health_check.isoformat() if self.last_health_check else None
        }
        
        return stats
    
    def clear_performance_data(self):
        """Clear accumulated performance data."""
        self.request_times.clear()
        self.error_count = 0
        self.cache_manager.reset_metrics()
    
    def _send_health_metrics_to_cloudwatch(self, health_status: CacheHealthStatus):
        """Send health metrics to CloudWatch."""
        if not self.cloudwatch:
            return
        
        try:
            namespace = 'Biomerkin/Cache'
            timestamp = datetime.utcnow()
            
            metrics_data = [
                {
                    'MetricName': 'HealthStatus',
                    'Value': 1.0 if health_status.is_healthy else 0.0,
                    'Unit': 'None',
                    'Timestamp': timestamp
                },
                {
                    'MetricName': 'BackendAvailable',
                    'Value': 1.0 if health_status.backend_available else 0.0,
                    'Unit': 'None',
                    'Timestamp': timestamp
                },
                {
                    'MetricName': 'HitRate',
                    'Value': health_status.hit_rate,
                    'Unit': 'Percent',
                    'Timestamp': timestamp
                },
                {
                    'MetricName': 'TotalEntries',
                    'Value': health_status.total_entries,
                    'Unit': 'Count',
                    'Timestamp': timestamp
                },
                {
                    'MetricName': 'TotalSizeMB',
                    'Value': health_status.total_size_mb,
                    'Unit': 'None',
                    'Timestamp': timestamp
                }
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=metrics_data
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to send metrics to CloudWatch: {str(e)}")
    
    def send_performance_metrics_to_cloudwatch(self, report: CachePerformanceReport):
        """Send performance metrics to CloudWatch."""
        if not self.cloudwatch:
            return
        
        try:
            namespace = 'Biomerkin/Cache'
            timestamp = datetime.utcnow()
            
            metrics_data = [
                {
                    'MetricName': 'TotalRequests',
                    'Value': report.total_requests,
                    'Unit': 'Count',
                    'Timestamp': timestamp
                },
                {
                    'MetricName': 'CacheHits',
                    'Value': report.cache_hits,
                    'Unit': 'Count',
                    'Timestamp': timestamp
                },
                {
                    'MetricName': 'CacheMisses',
                    'Value': report.cache_misses,
                    'Unit': 'Count',
                    'Timestamp': timestamp
                },
                {
                    'MetricName': 'AverageResponseTime',
                    'Value': report.average_response_time_ms,
                    'Unit': 'Milliseconds',
                    'Timestamp': timestamp
                },
                {
                    'MetricName': 'Evictions',
                    'Value': report.evictions,
                    'Unit': 'Count',
                    'Timestamp': timestamp
                },
                {
                    'MetricName': 'Errors',
                    'Value': report.errors,
                    'Unit': 'Count',
                    'Timestamp': timestamp
                }
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=metrics_data
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to send performance metrics to CloudWatch: {str(e)}")


# Global cache monitor instance
_cache_monitor: Optional[CacheMonitor] = None


def get_cache_monitor() -> CacheMonitor:
    """Get the global cache monitor instance."""
    global _cache_monitor
    if _cache_monitor is None:
        _cache_monitor = CacheMonitor()
    return _cache_monitor


def clear_cache_monitor():
    """Clear the global cache monitor instance (useful for testing)."""
    global _cache_monitor
    _cache_monitor = None