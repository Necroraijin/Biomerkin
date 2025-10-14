"""
Main Biomerkin Stack - Infrastructure as Code
Deploys all AWS resources for the multi-agent bioinformatics system
"""

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_iam as iam,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
    aws_sns as sns,
    aws_sqs as sqs,
    Duration,
    RemovalPolicy
)
from constructs import Construct
import json


class BiomerkinStack(Stack):
    """Main stack for Biomerkin multi-agent system"""
    
    def __init__(self, scope: Construct, construct_id: str, 
                 environment_name: str,
                 enable_monitoring: bool = True,
                 enable_backup: bool = True,
                 enable_multi_az: bool = False,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.environment_name = environment_name
        self.enable_monitoring = enable_monitoring
        self.enable_backup = enable_backup
        self.enable_multi_az = enable_multi_az
        
        # Create core infrastructure
        self._create_storage()
        self._create_iam_roles()
        self._create_lambda_functions()
        self._create_api_gateway()
        self._create_monitoring()
        self._create_notifications()
        
        # Add tags to all resources
        cdk.Tags.of(self).add("Environment", environment_name)
        cdk.Tags.of(self).add("Project", "Biomerkin")
        cdk.Tags.of(self).add("ManagedBy", "CDK")
    
    def _create_storage(self):
        """Create S3 buckets and DynamoDB tables"""
        
        # S3 bucket for sequence files and results
        self.sequence_bucket = s3.Bucket(
            self, f"BiomerkinSequences{self.environment_name.title()}",
            bucket_name=f"biomerkin-sequences-{self.environment_name}-{self.account}",
            versioning=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN if self.environment_name == "prod" else RemovalPolicy.DESTROY
        )
        
        # S3 bucket for reports and outputs
        self.reports_bucket = s3.Bucket(
            self, f"BiomerkinReports{self.environment_name.title()}",
            bucket_name=f"biomerkin-reports-{self.environment_name}-{self.account}",
            versioning=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN if self.environment_name == "prod" else RemovalPolicy.DESTROY
        )
        
        # DynamoDB table for workflow state
        self.workflow_table = dynamodb.Table(
            self, f"BiomerkinWorkflows{self.environment_name.title()}",
            table_name=f"biomerkin-workflows-{self.environment_name}",
            partition_key=dynamodb.Attribute(
                name="workflow_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery=self.enable_backup,
            removal_policy=RemovalPolicy.RETAIN if self.environment_name == "prod" else RemovalPolicy.DESTROY
        )
        
        # DynamoDB table for caching
        self.cache_table = dynamodb.Table(
            self, f"BiomerkinCache{self.environment_name.title()}",
            table_name=f"biomerkin-cache-{self.environment_name}",
            partition_key=dynamodb.Attribute(
                name="cache_key",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.DESTROY
        )
    
    def _create_iam_roles(self):
        """Create IAM roles for Lambda functions"""
        
        # Base execution role for all Lambda functions
        self.lambda_execution_role = iam.Role(
            self, f"BiomerkinLambdaRole{self.environment_name.title()}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )
        
        # Add permissions for S3 access
        self.lambda_execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:ListBucket"
                ],
                resources=[
                    self.sequence_bucket.bucket_arn,
                    f"{self.sequence_bucket.bucket_arn}/*",
                    self.reports_bucket.bucket_arn,
                    f"{self.reports_bucket.bucket_arn}/*"
                ]
            )
        )
        
        # Add permissions for DynamoDB access
        self.lambda_execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                resources=[
                    self.workflow_table.table_arn,
                    self.cache_table.table_arn
                ]
            )
        )
        
        # Add permissions for Bedrock access
        self.lambda_execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                resources=["*"]
            )
        )
    
    def _create_lambda_functions(self):
        """Create Lambda functions for each agent"""
        
        # Common Lambda configuration
        lambda_config = {
            "runtime": _lambda.Runtime.PYTHON_3_11,
            "timeout": Duration.minutes(15),
            "memory_size": 1024,
            "role": self.lambda_execution_role,
            "environment": {
                "ENVIRONMENT": self.environment_name,
                "WORKFLOW_TABLE": self.workflow_table.table_name,
                "CACHE_TABLE": self.cache_table.table_name,
                "SEQUENCE_BUCKET": self.sequence_bucket.bucket_name,
                "REPORTS_BUCKET": self.reports_bucket.bucket_name
            }
        }
        
        # Orchestrator Lambda
        self.orchestrator_function = _lambda.Function(
            self, f"BiomerkinOrchestrator{self.environment_name.title()}",
            function_name=f"biomerkin-orchestrator-{self.environment_name}",
            code=_lambda.Code.from_asset("../lambda_functions"),
            handler="orchestrator.handler",
            **lambda_config
        )
        
        # GenomicsAgent Lambda
        self.genomics_function = _lambda.Function(
            self, f"BiomerkinGenomics{self.environment_name.title()}",
            function_name=f"biomerkin-genomics-{self.environment_name}",
            code=_lambda.Code.from_asset("../lambda_functions"),
            handler="genomics_agent.handler",
            memory_size=2048,  # Higher memory for sequence processing
            **{k: v for k, v in lambda_config.items() if k != "memory_size"}
        )
        
        # ProteomicsAgent Lambda
        self.proteomics_function = _lambda.Function(
            self, f"BiomerkinProteomics{self.environment_name.title()}",
            function_name=f"biomerkin-proteomics-{self.environment_name}",
            code=_lambda.Code.from_asset("../lambda_functions"),
            handler="proteomics_agent.handler",
            **lambda_config
        )
        
        # LiteratureAgent Lambda
        self.literature_function = _lambda.Function(
            self, f"BiomerkinLiterature{self.environment_name.title()}",
            function_name=f"biomerkin-literature-{self.environment_name}",
            code=_lambda.Code.from_asset("../lambda_functions"),
            handler="literature_agent.handler",
            **lambda_config
        )
        
        # DrugAgent Lambda
        self.drug_function = _lambda.Function(
            self, f"BiomerkinDrug{self.environment_name.title()}",
            function_name=f"biomerkin-drug-{self.environment_name}",
            code=_lambda.Code.from_asset("../lambda_functions"),
            handler="drug_agent.handler",
            **lambda_config
        )
        
        # DecisionAgent Lambda
        self.decision_function = _lambda.Function(
            self, f"BiomerkinDecision{self.environment_name.title()}",
            function_name=f"biomerkin-decision-{self.environment_name}",
            code=_lambda.Code.from_asset("../lambda_functions"),
            handler="decision_agent.handler",
            **lambda_config
        )
        
        # Grant invoke permissions between functions
        self.genomics_function.grant_invoke(self.orchestrator_function)
        self.proteomics_function.grant_invoke(self.orchestrator_function)
        self.literature_function.grant_invoke(self.orchestrator_function)
        self.drug_function.grant_invoke(self.orchestrator_function)
        self.decision_function.grant_invoke(self.orchestrator_function)
    
    def _create_api_gateway(self):
        """Create API Gateway for REST endpoints"""
        
        # Create API Gateway
        self.api = apigateway.RestApi(
            self, f"BiomerkinApi{self.environment_name.title()}",
            rest_api_name=f"biomerkin-api-{self.environment_name}",
            description=f"Biomerkin Multi-Agent System API - {self.environment_name}",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"]
            )
        )
        
        # Create API resources and methods
        workflows = self.api.root.add_resource("workflows")
        
        # POST /workflows - Start new analysis
        workflows.add_method(
            "POST",
            apigateway.LambdaIntegration(self.orchestrator_function),
            authorization_type=apigateway.AuthorizationType.IAM
        )
        
        # GET /workflows/{id} - Get workflow status
        workflow_id = workflows.add_resource("{id}")
        workflow_id.add_method(
            "GET",
            apigateway.LambdaIntegration(self.orchestrator_function),
            authorization_type=apigateway.AuthorizationType.IAM
        )
        
        # GET /workflows/{id}/results - Get workflow results
        results = workflow_id.add_resource("results")
        results.add_method(
            "GET",
            apigateway.LambdaIntegration(self.orchestrator_function),
            authorization_type=apigateway.AuthorizationType.IAM
        )
    
    def _create_monitoring(self):
        """Create CloudWatch monitoring and alarms"""
        
        if not self.enable_monitoring:
            return
        
        # Create CloudWatch dashboard
        self.dashboard = cloudwatch.Dashboard(
            self, f"BiomerkinDashboard{self.environment_name.title()}",
            dashboard_name=f"Biomerkin-{self.environment_name}"
        )
        
        # Lambda function metrics
        functions = [
            ("Orchestrator", self.orchestrator_function),
            ("Genomics", self.genomics_function),
            ("Proteomics", self.proteomics_function),
            ("Literature", self.literature_function),
            ("Drug", self.drug_function),
            ("Decision", self.decision_function)
        ]
        
        for name, function in functions:
            # Error rate alarm
            error_alarm = cloudwatch.Alarm(
                self, f"{name}ErrorAlarm{self.environment_name.title()}",
                alarm_name=f"Biomerkin-{name}-Errors-{self.environment_name}",
                metric=function.metric_errors(),
                threshold=5,
                evaluation_periods=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
            )
            
            # Duration alarm
            duration_alarm = cloudwatch.Alarm(
                self, f"{name}DurationAlarm{self.environment_name.title()}",
                alarm_name=f"Biomerkin-{name}-Duration-{self.environment_name}",
                metric=function.metric_duration(),
                threshold=600000,  # 10 minutes in milliseconds
                evaluation_periods=2,
                comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
            )
        
        # API Gateway metrics
        api_error_alarm = cloudwatch.Alarm(
            self, f"ApiErrorAlarm{self.environment_name.title()}",
            alarm_name=f"Biomerkin-API-Errors-{self.environment_name}",
            metric=self.api.metric_client_error(),
            threshold=10,
            evaluation_periods=2,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD
        )
    
    def _create_notifications(self):
        """Create SNS topics and SQS queues for notifications"""
        
        # SNS topic for alerts
        self.alert_topic = sns.Topic(
            self, f"BiomerkinAlerts{self.environment_name.title()}",
            topic_name=f"biomerkin-alerts-{self.environment_name}",
            display_name=f"Biomerkin Alerts - {self.environment_name}"
        )
        
        # SQS queue for workflow events
        self.workflow_queue = sqs.Queue(
            self, f"BiomerkinWorkflowQueue{self.environment_name.title()}",
            queue_name=f"biomerkin-workflow-{self.environment_name}",
            visibility_timeout=Duration.minutes(15),
            retention_period=Duration.days(14)
        )
        
        # Dead letter queue
        self.dlq = sqs.Queue(
            self, f"BiomerkinDLQ{self.environment_name.title()}",
            queue_name=f"biomerkin-dlq-{self.environment_name}",
            retention_period=Duration.days(14)
        )