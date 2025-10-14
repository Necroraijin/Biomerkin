"""
AWS Cost Optimization Service for Biomerkin.
Provides real-time cost tracking, optimization recommendations, and budget monitoring.
"""

import json
import boto3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from ..utils.logging_config import get_logger
from ..utils.config import get_config


@dataclass
class CostMetric:
    """Cost metric data structure."""
    service: str
    cost: float
    currency: str
    period: str
    timestamp: datetime
    region: str
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None


@dataclass
class OptimizationRecommendation:
    """Cost optimization recommendation."""
    service: str
    recommendation_type: str
    description: str
    potential_savings: float
    currency: str
    confidence: float
    implementation_effort: str  # low, medium, high
    priority: str  # low, medium, high, critical


@dataclass
class BudgetAlert:
    """Budget alert data structure."""
    budget_name: str
    threshold: float
    current_spend: float
    alert_type: str  # forecasted, actual
    severity: str  # low, medium, high, critical
    timestamp: datetime


class CostOptimizationService:
    """
    Service for AWS cost tracking and optimization.
    Provides real-time cost monitoring and optimization recommendations.
    """
    
    def __init__(self, region: str = "us-east-1"):
        """Initialize cost optimization service."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.region = region
        
        # Initialize AWS clients
        try:
            self.ce_client = boto3.client('ce', region_name=region)  # Cost Explorer
            self.budgets_client = boto3.client('budgets', region_name=region)
            self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
            self.logger.info("Cost optimization service initialized")
        except Exception as e:
            self.logger.error(f"Error initializing cost optimization service: {e}")
            self.ce_client = None
            self.budgets_client = None
            self.cloudwatch_client = None
    
    def get_current_costs(self, days: int = 7) -> List[CostMetric]:
        """
        Get current costs for the last N days.
        
        Args:
            days: Number of days to retrieve costs for
            
        Returns:
            List of cost metrics
        """
        if not self.ce_client:
            return []
        
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                Granularity='DAILY',
                Metrics=['BlendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'REGION'}
                ]
            )
            
            cost_metrics = []
            for result in response.get('ResultsByTime', []):
                for group in result.get('Groups', []):
                    service = group['Keys'][0]
                    region = group['Keys'][1]
                    cost = float(group['Metrics']['BlendedCost']['Amount'])
                    
                    if cost > 0:  # Only include services with costs
                        cost_metrics.append(CostMetric(
                            service=service,
                            cost=cost,
                            currency='USD',
                            period=result['TimePeriod']['Start'],
                            timestamp=datetime.now(),
                            region=region
                        ))
            
            self.logger.info(f"Retrieved {len(cost_metrics)} cost metrics")
            return cost_metrics
            
        except Exception as e:
            self.logger.error(f"Error retrieving current costs: {e}")
            return []
    
    def get_biomerkin_costs(self, days: int = 7) -> Dict[str, Any]:
        """
        Get Biomerkin-specific costs.
        
        Args:
            days: Number of days to retrieve costs for
            
        Returns:
            Biomerkin cost breakdown
        """
        cost_metrics = self.get_current_costs(days)
        
        # Filter for Biomerkin-related services
        biomerkin_services = [
            'Amazon Lambda',
            'Amazon DynamoDB',
            'Amazon S3',
            'Amazon API Gateway',
            'Amazon Bedrock',
            'Amazon CloudWatch',
            'Amazon SNS',
            'Amazon SQS'
        ]
        
        biomerkin_costs = {}
        total_cost = 0.0
        
        for metric in cost_metrics:
            if metric.service in biomerkin_services:
                if metric.service not in biomerkin_costs:
                    biomerkin_costs[metric.service] = 0.0
                biomerkin_costs[metric.service] += metric.cost
                total_cost += metric.cost
        
        return {
            'total_cost': total_cost,
            'currency': 'USD',
            'period_days': days,
            'service_breakdown': biomerkin_costs,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_cost_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """
        Get cost optimization recommendations.
        
        Returns:
            List of optimization recommendations
        """
        recommendations = []
        
        # Lambda optimization recommendations
        recommendations.append(OptimizationRecommendation(
            service='Amazon Lambda',
            recommendation_type='memory_optimization',
            description='Optimize Lambda memory allocation based on actual usage patterns',
            potential_savings=15.0,
            currency='USD',
            confidence=0.85,
            implementation_effort='low',
            priority='medium'
        ))
        
        recommendations.append(OptimizationRecommendation(
            service='Amazon Lambda',
            recommendation_type='reserved_capacity',
            description='Use provisioned concurrency for predictable workloads',
            potential_savings=25.0,
            currency='USD',
            confidence=0.75,
            implementation_effort='medium',
            priority='high'
        ))
        
        # DynamoDB optimization recommendations
        recommendations.append(OptimizationRecommendation(
            service='Amazon DynamoDB',
            recommendation_type='billing_mode',
            description='Switch to on-demand billing for variable workloads',
            potential_savings=30.0,
            currency='USD',
            confidence=0.90,
            implementation_effort='low',
            priority='high'
        ))
        
        # S3 optimization recommendations
        recommendations.append(OptimizationRecommendation(
            service='Amazon S3',
            recommendation_type='lifecycle_policies',
            description='Implement lifecycle policies for data archival',
            potential_savings=40.0,
            currency='USD',
            confidence=0.95,
            implementation_effort='low',
            priority='high'
        ))
        
        # Bedrock optimization recommendations
        recommendations.append(OptimizationRecommendation(
            service='Amazon Bedrock',
            recommendation_type='model_selection',
            description='Use smaller models for simple tasks to reduce costs',
            potential_savings=20.0,
            currency='USD',
            confidence=0.80,
            implementation_effort='medium',
            priority='medium'
        ))
        
        # CloudWatch optimization recommendations
        recommendations.append(OptimizationRecommendation(
            service='Amazon CloudWatch',
            recommendation_type='log_retention',
            description='Reduce log retention periods for non-critical logs',
            potential_savings=10.0,
            currency='USD',
            confidence=0.85,
            implementation_effort='low',
            priority='low'
        ))
        
        self.logger.info(f"Generated {len(recommendations)} optimization recommendations")
        return recommendations
    
    def get_cost_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get cost trends over time.
        
        Args:
            days: Number of days to analyze trends for
            
        Returns:
            Cost trend analysis
        """
        cost_metrics = self.get_current_costs(days)
        
        # Group by date and calculate daily totals
        daily_costs = {}
        for metric in cost_metrics:
            date = metric.period
            if date not in daily_costs:
                daily_costs[date] = 0.0
            daily_costs[date] += metric.cost
        
        # Calculate trends
        dates = sorted(daily_costs.keys())
        costs = [daily_costs[date] for date in dates]
        
        if len(costs) < 2:
            return {'trend': 'insufficient_data', 'change_percent': 0.0}
        
        # Calculate percentage change
        first_cost = costs[0]
        last_cost = costs[-1]
        change_percent = ((last_cost - first_cost) / first_cost) * 100 if first_cost > 0 else 0
        
        # Determine trend
        if change_percent > 10:
            trend = 'increasing'
        elif change_percent < -10:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change_percent': change_percent,
            'daily_costs': daily_costs,
            'average_daily_cost': sum(costs) / len(costs),
            'total_period_cost': sum(costs),
            'period_days': days
        }
    
    def create_budget_alerts(self, budget_name: str, threshold_percent: float = 80.0) -> List[BudgetAlert]:
        """
        Create budget alerts for monitoring.
        
        Args:
            budget_name: Name of the budget
            threshold_percent: Alert threshold percentage
            
        Returns:
            List of budget alerts
        """
        alerts = []
        
        try:
            # Get current spend
            current_costs = self.get_biomerkin_costs(30)  # Last 30 days
            current_spend = current_costs['total_cost']
            
            # Calculate monthly projection
            daily_average = current_spend / 30
            monthly_projection = daily_average * 30
            
            # Create alerts based on thresholds
            thresholds = [50, 75, 90, 100]
            severities = ['low', 'medium', 'high', 'critical']
            
            for threshold, severity in zip(thresholds, severities):
                if monthly_projection >= (threshold / 100) * 1000:  # Assuming $1000 monthly budget
                    alerts.append(BudgetAlert(
                        budget_name=budget_name,
                        threshold=threshold,
                        current_spend=current_spend,
                        alert_type='forecasted',
                        severity=severity,
                        timestamp=datetime.now()
                    ))
            
            self.logger.info(f"Created {len(alerts)} budget alerts")
            return alerts
            
        except Exception as e:
            self.logger.error(f"Error creating budget alerts: {e}")
            return []
    
    def get_cost_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive cost dashboard data.
        
        Returns:
            Complete cost dashboard data
        """
        try:
            # Get current costs
            current_costs = self.get_biomerkin_costs(7)
            
            # Get optimization recommendations
            recommendations = self.get_cost_optimization_recommendations()
            
            # Get cost trends
            trends = self.get_cost_trends(30)
            
            # Get budget alerts
            budget_alerts = self.create_budget_alerts('Biomerkin Monthly Budget')
            
            # Calculate potential savings
            total_potential_savings = sum(rec.potential_savings for rec in recommendations)
            
            # Calculate optimization score
            optimization_score = min(100, max(0, 100 - (total_potential_savings / 10)))
            
            dashboard_data = {
                'current_costs': current_costs,
                'optimization_recommendations': [
                    {
                        'service': rec.service,
                        'type': rec.recommendation_type,
                        'description': rec.description,
                        'potential_savings': rec.potential_savings,
                        'currency': rec.currency,
                        'confidence': rec.confidence,
                        'effort': rec.implementation_effort,
                        'priority': rec.priority
                    }
                    for rec in recommendations
                ],
                'cost_trends': trends,
                'budget_alerts': [
                    {
                        'budget_name': alert.budget_name,
                        'threshold': alert.threshold,
                        'current_spend': alert.current_spend,
                        'alert_type': alert.alert_type,
                        'severity': alert.severity,
                        'timestamp': alert.timestamp.isoformat()
                    }
                    for alert in budget_alerts
                ],
                'summary': {
                    'total_current_cost': current_costs['total_cost'],
                    'total_potential_savings': total_potential_savings,
                    'optimization_score': optimization_score,
                    'recommendations_count': len(recommendations),
                    'alerts_count': len(budget_alerts),
                    'last_updated': datetime.now().isoformat()
                }
            }
            
            self.logger.info("Generated comprehensive cost dashboard data")
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error generating cost dashboard data: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def publish_cost_metrics(self, metrics: List[CostMetric]):
        """
        Publish cost metrics to CloudWatch.
        
        Args:
            metrics: List of cost metrics to publish
        """
        if not self.cloudwatch_client:
            return
        
        try:
            for metric in metrics:
                self.cloudwatch_client.put_metric_data(
                    Namespace='Biomerkin/Cost',
                    MetricData=[
                        {
                            'MetricName': 'ServiceCost',
                            'Dimensions': [
                                {'Name': 'Service', 'Value': metric.service},
                                {'Name': 'Region', 'Value': metric.region}
                            ],
                            'Value': metric.cost,
                            'Unit': 'None',
                            'Timestamp': metric.timestamp
                        }
                    ]
                )
            
            self.logger.info(f"Published {len(metrics)} cost metrics to CloudWatch")
            
        except Exception as e:
            self.logger.error(f"Error publishing cost metrics: {e}")


# Global cost optimization service instance
cost_optimization_service = None

def get_cost_optimization_service() -> CostOptimizationService:
    """Get global cost optimization service instance."""
    global cost_optimization_service
    if cost_optimization_service is None:
        cost_optimization_service = CostOptimizationService()
    return cost_optimization_service

