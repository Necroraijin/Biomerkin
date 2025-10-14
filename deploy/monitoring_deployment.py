"""
Monitoring infrastructure deployment script for Biomerkin.

This script deploys comprehensive monitoring, alerting, and dashboard infrastructure
including CloudWatch dashboards, alarms, SNS topics, and custom metrics.
"""

import boto3
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from biomerkin.services.monitoring_service import get_monitoring_service
from biomerkin.services.alerting_service import get_alerting_service
from biomerkin.services.dashboard_service import get_dashboard_service
from biomerkin.utils.monitoring_integration import get_monitoring_integration, MonitoringConfiguration


class MonitoringDeployment:
    """
    Comprehensive monitoring infrastructure deployment.
    
    Deploys CloudWatch dashboards, alarms, SNS topics, and configures
    monitoring services for the Biomerkin system.
    """
    
    def __init__(self, region: str = 'us-east-1', email_address: Optional[str] = None):
        """
        Initialize monitoring deployment.
        
        Args:
            region: AWS region for deployment
            email_address: Email address for alert notifications
        """
        self.region = region
        self.email_address = email_address
        self.deployment_results = {}
        
        # Initialize AWS clients
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        self.logs = boto3.client('logs', region_name=region)
        
        # Get account ID
        sts = boto3.client('sts')
        self.account_id = sts.get_caller_identity()['Account']
        
        # Initialize services
        self.monitoring_service = get_monitoring_service()
        self.alerting_service = get_alerting_service()
        self.dashboard_service = get_dashboard_service()
        
        print(f"Initializing monitoring deployment for account {self.account_id} in region {region}")
    
    def deploy_complete_monitoring_infrastructure(self) -> Dict[str, Any]:
        """
        Deploy complete monitoring infrastructure.
        
        Returns:
            Dictionary with deployment results
        """
        print("\n" + "="*60)
        print("BIOMERKIN MONITORING INFRASTRUCTURE DEPLOYMENT")
        print("="*60)
        
        # Step 1: Create SNS topics and subscriptions
        print("\n1. Creating SNS topics and subscriptions...")
        sns_results = self._create_sns_infrastructure()
        self.deployment_results['sns'] = sns_results
        
        # Step 2: Create log groups
        print("\n2. Creating CloudWatch log groups...")
        log_results = self._create_log_groups()
        self.deployment_results['logs'] = log_results
        
        # Step 3: Deploy dashboards
        print("\n3. Deploying CloudWatch dashboards...")
        dashboard_results = self.dashboard_service.deploy_all_dashboards()
        self.deployment_results['dashboards'] = dashboard_results
        
        # Step 4: Create CloudWatch alarms
        print("\n4. Creating CloudWatch alarms...")
        if sns_results.get('alert_topic_arn'):
            self.alerting_service.configure_sns_topic(sns_results['alert_topic_arn'])
            alarm_results = self.alerting_service.create_cloudwatch_alarms()
            self.deployment_results['alarms'] = alarm_results
        else:
            print("⚠️  Skipping alarms - SNS topic not available")
            self.deployment_results['alarms'] = {}
        
        # Step 5: Create custom metrics
        print("\n5. Creating custom metrics...")
        metrics_results = self._create_custom_metrics()
        self.deployment_results['custom_metrics'] = metrics_results
        
        # Step 6: Configure monitoring integration
        print("\n6. Configuring monitoring integration...")
        integration_results = self._configure_monitoring_integration()
        self.deployment_results['integration'] = integration_results
        
        # Step 7: Validate deployment
        print("\n7. Validating deployment...")
        validation_results = self._validate_deployment()
        self.deployment_results['validation'] = validation_results
        
        return self.deployment_results
    
    def _create_sns_infrastructure(self) -> Dict[str, Any]:
        """Create SNS topics and subscriptions."""
        results = {}
        
        try:
            # Create alert topic
            alert_topic_response = self.sns.create_topic(Name='biomerkin-alerts')
            alert_topic_arn = alert_topic_response['TopicArn']
            results['alert_topic_arn'] = alert_topic_arn
            print(f"✓ Created SNS topic: {alert_topic_arn}")
            
            # Subscribe email if provided
            if self.email_address:
                self.sns.subscribe(
                    TopicArn=alert_topic_arn,
                    Protocol='email',
                    Endpoint=self.email_address
                )
                results['email_subscription'] = True
                print(f"✓ Subscribed email {self.email_address} to alerts")
            else:
                results['email_subscription'] = False
                print("⚠️  No email address provided for alert subscriptions")
            
            # Create topic policy for CloudWatch alarms
            topic_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "cloudwatch.amazonaws.com"
                        },
                        "Action": "SNS:Publish",
                        "Resource": alert_topic_arn,
                        "Condition": {
                            "StringEquals": {
                                "aws:SourceAccount": self.account_id
                            }
                        }
                    }
                ]
            }
            
            self.sns.set_topic_attributes(
                TopicArn=alert_topic_arn,
                AttributeName='Policy',
                AttributeValue=json.dumps(topic_policy)
            )
            results['topic_policy'] = True
            print("✓ Set SNS topic policy for CloudWatch")
            
        except Exception as e:
            print(f"✗ Error creating SNS infrastructure: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def _create_log_groups(self) -> Dict[str, bool]:
        """Create CloudWatch log groups."""
        results = {}
        
        log_groups = [
            '/aws/lambda/biomerkin-orchestrator',
            '/aws/lambda/biomerkin-genomics',
            '/aws/lambda/biomerkin-proteomics',
            '/aws/lambda/biomerkin-literature',
            '/aws/lambda/biomerkin-drug',
            '/aws/lambda/biomerkin-decision',
            '/aws/apigateway/biomerkin-api',
            '/biomerkin/monitoring',
            '/biomerkin/alerts',
            '/biomerkin/performance'
        ]
        
        for log_group in log_groups:
            try:
                self.logs.create_log_group(
                    logGroupName=log_group,
                    retentionInDays=30
                )
                results[log_group] = True
                print(f"✓ Created log group: {log_group}")
                
            except self.logs.exceptions.ResourceAlreadyExistsException:
                results[log_group] = True
                print(f"✓ Log group already exists: {log_group}")
                
            except Exception as e:
                results[log_group] = False
                print(f"✗ Error creating log group {log_group}: {str(e)}")
        
        return results
    
    def _create_custom_metrics(self) -> Dict[str, bool]:
        """Create custom CloudWatch metrics."""
        results = {}
        
        try:
            # Create sample metrics to establish the namespace
            sample_metrics = [
                {
                    'MetricName': 'SystemHealthScore',
                    'Value': 100.0,
                    'Unit': 'Percent',
                    'Dimensions': [{'Name': 'Environment', 'Value': 'production'}]
                },
                {
                    'MetricName': 'WorkflowsStarted',
                    'Value': 0.0,
                    'Unit': 'Count',
                    'Dimensions': [{'Name': 'Environment', 'Value': 'production'}]
                },
                {
                    'MetricName': 'WorkflowsCompleted',
                    'Value': 0.0,
                    'Unit': 'Count',
                    'Dimensions': [{'Name': 'Environment', 'Value': 'production'}]
                },
                {
                    'MetricName': 'WorkflowsFailed',
                    'Value': 0.0,
                    'Unit': 'Count',
                    'Dimensions': [{'Name': 'Environment', 'Value': 'production'}]
                }
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace='Biomerkin/System',
                MetricData=sample_metrics
            )
            
            results['custom_metrics'] = True
            print("✓ Created custom metrics namespace")
            
        except Exception as e:
            results['custom_metrics'] = False
            print(f"✗ Error creating custom metrics: {str(e)}")
        
        return results
    
    def _configure_monitoring_integration(self) -> Dict[str, bool]:
        """Configure monitoring integration."""
        results = {}
        
        try:
            # Configure monitoring integration
            config = MonitoringConfiguration(
                health_check_interval=300,  # 5 minutes
                alert_check_interval=60,    # 1 minute
                metrics_flush_interval=60,  # 1 minute
                enable_auto_recovery=True,
                enable_predictive_alerts=True
            )
            
            monitoring_integration = get_monitoring_integration(config)
            
            # Deploy monitoring infrastructure
            deployment_results = monitoring_integration.deploy_monitoring_infrastructure()
            results.update(deployment_results)
            
            print("✓ Configured monitoring integration")
            
        except Exception as e:
            results['integration_error'] = str(e)
            print(f"✗ Error configuring monitoring integration: {str(e)}")
        
        return results
    
    def _validate_deployment(self) -> Dict[str, bool]:
        """Validate monitoring deployment."""
        results = {}
        
        # Validate SNS topics
        try:
            if 'alert_topic_arn' in self.deployment_results.get('sns', {}):
                topic_arn = self.deployment_results['sns']['alert_topic_arn']
                self.sns.get_topic_attributes(TopicArn=topic_arn)
                results['sns_topic'] = True
            else:
                results['sns_topic'] = False
        except Exception:
            results['sns_topic'] = False
        
        # Validate dashboards
        dashboard_names = [
            'BiomerkinSystemOverview',
            'BiomerkinWorkflowPerformance',
            'BiomerkinAPIMonitoring',
            'BiomerkinCostOptimization'
        ]
        
        for dashboard_name in dashboard_names:
            try:
                self.cloudwatch.get_dashboard(DashboardName=dashboard_name)
                results[f'dashboard_{dashboard_name}'] = True
            except Exception:
                results[f'dashboard_{dashboard_name}'] = False
        
        # Validate log groups
        log_groups = [
            '/aws/lambda/biomerkin-orchestrator',
            '/biomerkin/monitoring'
        ]
        
        for log_group in log_groups:
            try:
                self.logs.describe_log_groups(logGroupNamePrefix=log_group)
                results[f'log_group_{log_group.replace("/", "_")}'] = True
            except Exception:
                results[f'log_group_{log_group.replace("/", "_")}'] = False
        
        return results
    
    def generate_deployment_report(self) -> str:
        """Generate deployment report."""
        report = []
        report.append("BIOMERKIN MONITORING DEPLOYMENT REPORT")
        report.append("=" * 50)
        report.append(f"Deployment Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        report.append(f"AWS Region: {self.region}")
        report.append(f"Account ID: {self.account_id}")
        report.append("")
        
        # SNS Infrastructure
        if 'sns' in self.deployment_results:
            report.append("SNS INFRASTRUCTURE:")
            sns_results = self.deployment_results['sns']
            if 'alert_topic_arn' in sns_results:
                report.append(f"  ✓ Alert Topic: {sns_results['alert_topic_arn']}")
            if sns_results.get('email_subscription'):
                report.append(f"  ✓ Email Subscription: {self.email_address}")
            report.append("")
        
        # Dashboards
        if 'dashboards' in self.deployment_results:
            report.append("CLOUDWATCH DASHBOARDS:")
            for dashboard, success in self.deployment_results['dashboards'].items():
                status = "✓" if success else "✗"
                report.append(f"  {status} {dashboard}")
            report.append("")
        
        # Alarms
        if 'alarms' in self.deployment_results:
            report.append("CLOUDWATCH ALARMS:")
            for alarm, success in self.deployment_results['alarms'].items():
                status = "✓" if success else "✗"
                report.append(f"  {status} {alarm}")
            report.append("")
        
        # Log Groups
        if 'logs' in self.deployment_results:
            report.append("LOG GROUPS:")
            for log_group, success in self.deployment_results['logs'].items():
                status = "✓" if success else "✗"
                report.append(f"  {status} {log_group}")
            report.append("")
        
        # Validation Results
        if 'validation' in self.deployment_results:
            report.append("DEPLOYMENT VALIDATION:")
            validation_results = self.deployment_results['validation']
            passed = sum(1 for v in validation_results.values() if v)
            total = len(validation_results)
            report.append(f"  Validation Score: {passed}/{total}")
            
            for component, success in validation_results.items():
                status = "✓" if success else "✗"
                report.append(f"  {status} {component}")
            report.append("")
        
        # Dashboard URLs
        report.append("DASHBOARD URLS:")
        dashboard_names = [
            'BiomerkinSystemOverview',
            'BiomerkinWorkflowPerformance',
            'BiomerkinAPIMonitoring',
            'BiomerkinCostOptimization'
        ]
        
        for dashboard_name in dashboard_names:
            url = self.dashboard_service.get_dashboard_url(dashboard_name)
            if url:
                report.append(f"  • {dashboard_name}: {url}")
        report.append("")
        
        # Next Steps
        report.append("NEXT STEPS:")
        report.append("  1. Confirm email subscription for alert notifications")
        report.append("  2. Review dashboard configurations and customize as needed")
        report.append("  3. Test alert thresholds with sample data")
        report.append("  4. Configure additional webhook integrations if needed")
        report.append("  5. Set up monitoring integration in your application")
        report.append("")
        
        # Monitoring Integration Code
        report.append("INTEGRATION CODE EXAMPLE:")
        report.append("```python")
        report.append("from biomerkin.utils.monitoring_integration import get_monitoring_integration")
        report.append("")
        report.append("# Initialize monitoring")
        report.append("monitoring = get_monitoring_integration()")
        report.append("monitoring.start_monitoring()")
        report.append("")
        report.append("# Record workflow events")
        report.append("monitoring.monitoring_service.record_workflow_started('workflow-123')")
        report.append("monitoring.monitoring_service.record_workflow_completed('workflow-123', 120.5)")
        report.append("```")
        report.append("")
        
        return "\n".join(report)
    
    def save_deployment_config(self, filename: str = 'monitoring_deployment_config.json') -> None:
        """Save deployment configuration."""
        config = {
            'deployment_timestamp': datetime.utcnow().isoformat(),
            'region': self.region,
            'account_id': self.account_id,
            'email_address': self.email_address,
            'deployment_results': self.deployment_results
        }
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        print(f"Deployment configuration saved to {filename}")
    
    def cleanup_deployment(self) -> Dict[str, bool]:
        """Clean up monitoring deployment (for testing/development)."""
        results = {}
        
        print("Cleaning up monitoring deployment...")
        
        # Delete dashboards
        dashboard_names = [
            'BiomerkinSystemOverview',
            'BiomerkinWorkflowPerformance',
            'BiomerkinAPIMonitoring',
            'BiomerkinCostOptimization'
        ]
        
        for dashboard_name in dashboard_names:
            try:
                self.cloudwatch.delete_dashboards(DashboardNames=[dashboard_name])
                results[f'delete_dashboard_{dashboard_name}'] = True
                print(f"✓ Deleted dashboard: {dashboard_name}")
            except Exception as e:
                results[f'delete_dashboard_{dashboard_name}'] = False
                print(f"✗ Error deleting dashboard {dashboard_name}: {str(e)}")
        
        # Delete SNS topic
        if 'sns' in self.deployment_results and 'alert_topic_arn' in self.deployment_results['sns']:
            try:
                topic_arn = self.deployment_results['sns']['alert_topic_arn']
                self.sns.delete_topic(TopicArn=topic_arn)
                results['delete_sns_topic'] = True
                print(f"✓ Deleted SNS topic: {topic_arn}")
            except Exception as e:
                results['delete_sns_topic'] = False
                print(f"✗ Error deleting SNS topic: {str(e)}")
        
        return results


def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy Biomerkin monitoring infrastructure')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--email', help='Email address for alert notifications')
    parser.add_argument('--cleanup', action='store_true', help='Clean up existing deployment')
    
    args = parser.parse_args()
    
    deployment = MonitoringDeployment(
        region=args.region,
        email_address=args.email
    )
    
    if args.cleanup:
        print("Cleaning up monitoring deployment...")
        cleanup_results = deployment.cleanup_deployment()
        print(f"\nCleanup results: {cleanup_results}")
        return
    
    # Deploy monitoring infrastructure
    results = deployment.deploy_complete_monitoring_infrastructure()
    
    # Generate and display report
    report = deployment.generate_deployment_report()
    print("\n" + report)
    
    # Save configuration
    deployment.save_deployment_config()
    
    # Check deployment success
    if 'validation' in results:
        validation_results = results['validation']
        failed_components = [k for k, v in validation_results.items() if not v]
        
        if failed_components:
            print(f"\n⚠️  Warning: {len(failed_components)} components failed validation:")
            for component in failed_components:
                print(f"   - {component}")
            return 1
        else:
            print("\n🎉 Monitoring deployment completed successfully! All components validated.")
            return 0
    else:
        print("\n❌ Monitoring deployment failed - validation not performed")
        return 1


if __name__ == "__main__":
    exit(main())