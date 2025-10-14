"""
CloudWatch monitoring and cost alerts setup for Biomerkin
"""
import boto3
import json
from typing import Dict, Any, List

class CloudWatchManager:
    def __init__(self, region='us-east-1'):
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        self.logs_client = boto3.client('logs', region_name=region)
        self.sns_client = boto3.client('sns', region_name=region)
        self.budgets_client = boto3.client('budgets', region_name='us-east-1')  # Budgets is only in us-east-1
        self.region = region
    
    def create_log_group(self, log_group_name: str, retention_days: int = 30) -> bool:
        """Create a CloudWatch log group"""
        try:
            self.logs_client.create_log_group(
                logGroupName=log_group_name,
                retentionInDays=retention_days
            )
            print(f"Log group {log_group_name} created")
            return True
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            print(f"Log group {log_group_name} already exists")
            return True
        except Exception as e:
            print(f"Error creating log group {log_group_name}: {e}")
            return False
    
    def create_custom_metric(self, namespace: str, metric_name: str, 
                           dimensions: List[Dict[str, str]], value: float,
                           unit: str = 'Count') -> bool:
        """Create a custom CloudWatch metric"""
        try:
            self.cloudwatch_client.put_metric_data(
                Namespace=namespace,
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Dimensions': dimensions,
                        'Value': value,
                        'Unit': unit
                    }
                ]
            )
            return True
        except Exception as e:
            print(f"Error creating custom metric: {e}")
            return False
    
    def create_alarm(self, alarm_name: str, metric_name: str, namespace: str,
                    statistic: str, period: int, evaluation_periods: int,
                    threshold: float, comparison_operator: str,
                    alarm_actions: List[str] = None,
                    dimensions: List[Dict[str, str]] = None) -> bool:
        """Create a CloudWatch alarm"""
        try:
            alarm_config = {
                'AlarmName': alarm_name,
                'ComparisonOperator': comparison_operator,
                'EvaluationPeriods': evaluation_periods,
                'MetricName': metric_name,
                'Namespace': namespace,
                'Period': period,
                'Statistic': statistic,
                'Threshold': threshold,
                'ActionsEnabled': True,
                'AlarmDescription': f'Alarm for {metric_name} in {namespace}'
            }
            
            if alarm_actions:
                alarm_config['AlarmActions'] = alarm_actions
            
            if dimensions:
                alarm_config['Dimensions'] = dimensions
            
            self.cloudwatch_client.put_metric_alarm(**alarm_config)
            print(f"Alarm {alarm_name} created")
            return True
        except Exception as e:
            print(f"Error creating alarm {alarm_name}: {e}")
            return False
    
    def create_dashboard(self, dashboard_name: str, dashboard_body: Dict[str, Any]) -> bool:
        """Create a CloudWatch dashboard"""
        try:
            self.cloudwatch_client.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_body)
            )
            print(f"Dashboard {dashboard_name} created")
            return True
        except Exception as e:
            print(f"Error creating dashboard: {e}")
            return False
    
    def create_sns_topic(self, topic_name: str) -> str:
        """Create an SNS topic for notifications"""
        try:
            response = self.sns_client.create_topic(Name=topic_name)
            topic_arn = response['TopicArn']
            print(f"SNS topic {topic_name} created: {topic_arn}")
            return topic_arn
        except Exception as e:
            print(f"Error creating SNS topic: {e}")
            return None
    
    def subscribe_to_topic(self, topic_arn: str, protocol: str, endpoint: str) -> bool:
        """Subscribe to an SNS topic"""
        try:
            self.sns_client.subscribe(
                TopicArn=topic_arn,
                Protocol=protocol,
                Endpoint=endpoint
            )
            print(f"Subscribed {endpoint} to topic")
            return True
        except Exception as e:
            print(f"Error subscribing to topic: {e}")
            return False
    
    def create_budget_alert(self, budget_name: str, budget_limit: float, 
                           email_address: str, account_id: str) -> bool:
        """Create a budget alert for cost monitoring"""
        try:
            budget = {
                'BudgetName': budget_name,
                'BudgetLimit': {
                    'Amount': str(budget_limit),
                    'Unit': 'USD'
                },
                'TimeUnit': 'MONTHLY',
                'BudgetType': 'COST',
                'CostFilters': {
                    'Service': ['Amazon Elastic Compute Cloud - Compute',
                               'AWS Lambda', 'Amazon DynamoDB', 'Amazon S3',
                               'Amazon Bedrock', 'Amazon API Gateway']
                }
            }
            
            notifications = [
                {
                    'Notification': {
                        'NotificationType': 'ACTUAL',
                        'ComparisonOperator': 'GREATER_THAN',
                        'Threshold': 80.0,
                        'ThresholdType': 'PERCENTAGE'
                    },
                    'Subscribers': [
                        {
                            'SubscriptionType': 'EMAIL',
                            'Address': email_address
                        }
                    ]
                },
                {
                    'Notification': {
                        'NotificationType': 'FORECASTED',
                        'ComparisonOperator': 'GREATER_THAN',
                        'Threshold': 100.0,
                        'ThresholdType': 'PERCENTAGE'
                    },
                    'Subscribers': [
                        {
                            'SubscriptionType': 'EMAIL',
                            'Address': email_address
                        }
                    ]
                }
            ]
            
            self.budgets_client.create_budget(
                AccountId=account_id,
                Budget=budget,
                NotificationsWithSubscribers=notifications
            )
            print(f"Budget alert {budget_name} created")
            return True
        except Exception as e:
            print(f"Error creating budget alert: {e}")
            return False

def create_biomerkin_dashboard() -> Dict[str, Any]:
    """Create a comprehensive dashboard for Biomerkin monitoring"""
    dashboard_body = {
        "widgets": [
            {
                "type": "metric",
                "x": 0,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Invocations", "FunctionName", "biomerkin-orchestrator"],
                        [".", "Duration", ".", "."],
                        [".", "Errors", ".", "."],
                        [".", "Throttles", ".", "."]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Orchestrator Lambda Metrics",
                    "period": 300
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 0,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/Lambda", "Invocations", "FunctionName", "biomerkin-genomics"],
                        [".", ".", ".", "biomerkin-proteomics"],
                        [".", ".", ".", "biomerkin-literature"],
                        [".", ".", ".", "biomerkin-drug"],
                        [".", ".", ".", "biomerkin-decision"]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Agent Lambda Invocations",
                    "period": 300
                }
            },
            {
                "type": "metric",
                "x": 0,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", "biomerkin-workflows"],
                        [".", "ConsumedWriteCapacityUnits", ".", "."],
                        [".", "UserErrors", ".", "."],
                        [".", "SystemErrors", ".", "."]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "DynamoDB Metrics",
                    "period": 300
                }
            },
            {
                "type": "metric",
                "x": 12,
                "y": 6,
                "width": 12,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["AWS/S3", "BucketSizeBytes", "BucketName", "biomerkin-data", "StorageType", "StandardStorage"],
                        [".", ".", ".", "biomerkin-results", ".", "."],
                        [".", "NumberOfObjects", ".", "biomerkin-data", ".", "AllStorageTypes"],
                        [".", ".", ".", "biomerkin-results", ".", "."]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "S3 Storage Metrics",
                    "period": 86400
                }
            },
            {
                "type": "metric",
                "x": 0,
                "y": 12,
                "width": 24,
                "height": 6,
                "properties": {
                    "metrics": [
                        ["Biomerkin/Workflows", "WorkflowsStarted"],
                        [".", "WorkflowsCompleted"],
                        [".", "WorkflowsFailed"],
                        [".", "AverageProcessingTime"]
                    ],
                    "view": "timeSeries",
                    "stacked": False,
                    "region": "us-east-1",
                    "title": "Custom Workflow Metrics",
                    "period": 300
                }
            },
            {
                "type": "log",
                "x": 0,
                "y": 18,
                "width": 24,
                "height": 6,
                "properties": {
                    "query": "SOURCE '/aws/lambda/biomerkin-orchestrator'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 100",
                    "region": "us-east-1",
                    "title": "Recent Errors",
                    "view": "table"
                }
            }
        ]
    }
    return dashboard_body

def setup_cloudwatch_monitoring(email_address: str, budget_limit: float = 100.0) -> Dict[str, Any]:
    """Set up comprehensive CloudWatch monitoring for Biomerkin"""
    cw_manager = CloudWatchManager()
    results = {}
    
    # Get account ID
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()['Account']
    
    # Create log groups for Lambda functions
    log_groups = [
        '/aws/lambda/biomerkin-orchestrator',
        '/aws/lambda/biomerkin-genomics',
        '/aws/lambda/biomerkin-proteomics',
        '/aws/lambda/biomerkin-literature',
        '/aws/lambda/biomerkin-drug',
        '/aws/lambda/biomerkin-decision',
        '/aws/apigateway/biomerkin-api'
    ]
    
    for log_group in log_groups:
        results[f"log_group_{log_group.split('/')[-1]}"] = cw_manager.create_log_group(log_group)
    
    # Create SNS topic for alerts
    alert_topic_arn = cw_manager.create_sns_topic('biomerkin-alerts')
    if alert_topic_arn and email_address:
        cw_manager.subscribe_to_topic(alert_topic_arn, 'email', email_address)
    
    # Create alarms
    alarms = [
        {
            'name': 'biomerkin-orchestrator-errors',
            'metric': 'Errors',
            'namespace': 'AWS/Lambda',
            'statistic': 'Sum',
            'period': 300,
            'evaluation_periods': 2,
            'threshold': 5.0,
            'comparison': 'GreaterThanThreshold',
            'dimensions': [{'Name': 'FunctionName', 'Value': 'biomerkin-orchestrator'}]
        },
        {
            'name': 'biomerkin-high-duration',
            'metric': 'Duration',
            'namespace': 'AWS/Lambda',
            'statistic': 'Average',
            'period': 300,
            'evaluation_periods': 3,
            'threshold': 30000.0,  # 30 seconds
            'comparison': 'GreaterThanThreshold',
            'dimensions': [{'Name': 'FunctionName', 'Value': 'biomerkin-orchestrator'}]
        },
        {
            'name': 'biomerkin-dynamodb-throttles',
            'metric': 'UserErrors',
            'namespace': 'AWS/DynamoDB',
            'statistic': 'Sum',
            'period': 300,
            'evaluation_periods': 2,
            'threshold': 10.0,
            'comparison': 'GreaterThanThreshold',
            'dimensions': [{'Name': 'TableName', 'Value': 'biomerkin-workflows'}]
        }
    ]
    
    for alarm in alarms:
        success = cw_manager.create_alarm(
            alarm_name=alarm['name'],
            metric_name=alarm['metric'],
            namespace=alarm['namespace'],
            statistic=alarm['statistic'],
            period=alarm['period'],
            evaluation_periods=alarm['evaluation_periods'],
            threshold=alarm['threshold'],
            comparison_operator=alarm['comparison'],
            alarm_actions=[alert_topic_arn] if alert_topic_arn else None,
            dimensions=alarm.get('dimensions')
        )
        results[f"alarm_{alarm['name']}"] = success
    
    # Create dashboard
    dashboard_body = create_biomerkin_dashboard()
    results['dashboard'] = cw_manager.create_dashboard('BiomerkinMonitoring', dashboard_body)
    
    # Create budget alert
    if email_address:
        results['budget_alert'] = cw_manager.create_budget_alert(
            'BiomerkinMonthlyCost', budget_limit, email_address, account_id
        )
    
    return results

def create_custom_metrics_utility():
    """Create utility for sending custom metrics to CloudWatch"""
    metrics_code = '''
"""
Custom metrics utility for Biomerkin system monitoring
"""
import boto3
import time
from datetime import datetime
from typing import Dict, Any, List

class BiomerkinMetrics:
    def __init__(self, region='us-east-1'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.namespace = 'Biomerkin/Workflows'
    
    def record_workflow_started(self, workflow_id: str, user_id: str = None):
        """Record when a workflow is started"""
        dimensions = [{'Name': 'WorkflowId', 'Value': workflow_id}]
        if user_id:
            dimensions.append({'Name': 'UserId', 'Value': user_id})
        
        self._put_metric('WorkflowsStarted', 1, dimensions)
    
    def record_workflow_completed(self, workflow_id: str, processing_time: float,
                                 user_id: str = None):
        """Record when a workflow is completed"""
        dimensions = [{'Name': 'WorkflowId', 'Value': workflow_id}]
        if user_id:
            dimensions.append({'Name': 'UserId', 'Value': user_id})
        
        self._put_metric('WorkflowsCompleted', 1, dimensions)
        self._put_metric('ProcessingTime', processing_time, dimensions, 'Seconds')
    
    def record_workflow_failed(self, workflow_id: str, error_type: str,
                              user_id: str = None):
        """Record when a workflow fails"""
        dimensions = [
            {'Name': 'WorkflowId', 'Value': workflow_id},
            {'Name': 'ErrorType', 'Value': error_type}
        ]
        if user_id:
            dimensions.append({'Name': 'UserId', 'Value': user_id})
        
        self._put_metric('WorkflowsFailed', 1, dimensions)
    
    def record_agent_execution(self, agent_name: str, execution_time: float,
                              success: bool = True):
        """Record agent execution metrics"""
        dimensions = [
            {'Name': 'AgentName', 'Value': agent_name},
            {'Name': 'Status', 'Value': 'Success' if success else 'Failed'}
        ]
        
        self._put_metric('AgentExecutions', 1, dimensions)
        self._put_metric('AgentExecutionTime', execution_time, dimensions, 'Seconds')
    
    def record_api_call(self, api_name: str, response_time: float, 
                       status_code: int):
        """Record external API call metrics"""
        dimensions = [
            {'Name': 'APIName', 'Value': api_name},
            {'Name': 'StatusCode', 'Value': str(status_code)}
        ]
        
        self._put_metric('ExternalAPICalls', 1, dimensions)
        self._put_metric('APIResponseTime', response_time, dimensions, 'Milliseconds')
    
    def record_cost_metric(self, service_name: str, estimated_cost: float):
        """Record estimated cost metrics"""
        dimensions = [{'Name': 'Service', 'Value': service_name}]
        self._put_metric('EstimatedCost', estimated_cost, dimensions, 'None')
    
    def _put_metric(self, metric_name: str, value: float, 
                   dimensions: List[Dict[str, str]], unit: str = 'Count'):
        """Put a metric to CloudWatch"""
        try:
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Dimensions': dimensions,
                        'Value': value,
                        'Unit': unit,
                        'Timestamp': datetime.utcnow()
                    }
                ]
            )
        except Exception as e:
            print(f"Error putting metric {metric_name}: {e}")

# Decorator for automatic metrics collection
def track_execution_time(metrics_client: BiomerkinMetrics, agent_name: str):
    """Decorator to automatically track agent execution time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise e
            finally:
                execution_time = time.time() - start_time
                metrics_client.record_agent_execution(agent_name, execution_time, success)
        return wrapper
    return decorator
'''
    
    with open('biomerkin/utils/metrics.py', 'w') as f:
        f.write(metrics_code)

if __name__ == "__main__":
    # Example usage - replace with actual email
    email = "admin@biomerkin.com"
    budget = 100.0  # $100 monthly budget
    
    results = setup_cloudwatch_monitoring(email, budget)
    create_custom_metrics_utility()
    
    print("CloudWatch setup results:")
    for component, success in results.items():
        status = "✓" if success else "✗"
        print(f"{status} {component}")