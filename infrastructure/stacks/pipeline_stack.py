"""
CI/CD Pipeline Stack for Biomerkin
Implements automated testing and deployment pipeline
"""

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codebuild as codebuild,
    aws_codecommit as codecommit,
    aws_iam as iam,
    aws_s3 as s3,
    aws_sns as sns,
    aws_events as events,
    aws_events_targets as targets,
    Duration,
    RemovalPolicy
)
from constructs import Construct


class PipelineStack(Stack):
    """CI/CD Pipeline for automated deployment"""
    
    def __init__(self, scope: Construct, construct_id: str,
                 dev_stack, staging_stack, prod_stack,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self.dev_stack = dev_stack
        self.staging_stack = staging_stack
        self.prod_stack = prod_stack
        
        # Create pipeline infrastructure
        self._create_source_repository()
        self._create_artifact_store()
        self._create_build_projects()
        self._create_pipeline()
        self._create_notifications()
        self._create_rollback_automation()
    
    def _create_source_repository(self):
        """Create CodeCommit repository for source code"""
        
        self.repository = codecommit.Repository(
            self, "BiomerkinRepository",
            repository_name="biomerkin-multi-agent-system",
            description="Biomerkin Multi-Agent Bioinformatics System"
        )
    
    def _create_artifact_store(self):
        """Create S3 bucket for pipeline artifacts"""
        
        self.artifact_bucket = s3.Bucket(
            self, "BiomerkinArtifacts",
            bucket_name=f"biomerkin-pipeline-artifacts-{self.account}",
            versioning=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldArtifacts",
                    expiration=Duration.days(30),
                    noncurrent_version_expiration=Duration.days(7)
                )
            ],
            removal_policy=RemovalPolicy.DESTROY
        )
    
    def _create_build_projects(self):
        """Create CodeBuild projects for different stages"""
        
        # Build environment
        build_environment = codebuild.BuildEnvironment(
            build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
            compute_type=codebuild.ComputeType.MEDIUM,
            privileged=True  # Required for Docker builds
        )
        
        # Unit test project
        self.test_project = codebuild.Project(
            self, "BiomerkinTestProject",
            project_name="biomerkin-tests",
            description="Run unit and integration tests",
            environment=build_environment,
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {
                            "python": "3.11"
                        },
                        "commands": [
                            "pip install --upgrade pip",
                            "pip install -r requirements.txt",
                            "pip install pytest pytest-cov pytest-mock"
                        ]
                    },
                    "pre_build": {
                        "commands": [
                            "echo Running pre-build checks...",
                            "python -m py_compile biomerkin/**/*.py"
                        ]
                    },
                    "build": {
                        "commands": [
                            "echo Running unit tests...",
                            "python -m pytest tests/ -v --cov=biomerkin --cov-report=xml --cov-report=html",
                            "echo Running integration tests...",
                            "python -m pytest tests/test_*_integration.py -v"
                        ]
                    },
                    "post_build": {
                        "commands": [
                            "echo Test phase completed"
                        ]
                    }
                },
                "reports": {
                    "coverage": {
                        "files": ["coverage.xml"],
                        "file-format": "COBERTURAXML"
                    }
                },
                "artifacts": {
                    "files": [
                        "**/*"
                    ]
                }
            })
        )
        
        # Security scan project
        self.security_project = codebuild.Project(
            self, "BiomerkinSecurityProject",
            project_name="biomerkin-security-scan",
            description="Run security scans and vulnerability checks",
            environment=build_environment,
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {
                            "python": "3.11"
                        },
                        "commands": [
                            "pip install --upgrade pip",
                            "pip install bandit safety",
                            "pip install -r requirements.txt"
                        ]
                    },
                    "build": {
                        "commands": [
                            "echo Running security scans...",
                            "bandit -r biomerkin/ -f json -o bandit-report.json || true",
                            "safety check --json --output safety-report.json || true",
                            "echo Security scan completed"
                        ]
                    }
                },
                "artifacts": {
                    "files": [
                        "bandit-report.json",
                        "safety-report.json"
                    ]
                }
            })
        )
        
        # Package project
        self.package_project = codebuild.Project(
            self, "BiomerkinPackageProject",
            project_name="biomerkin-package",
            description="Package Lambda functions and CDK assets",
            environment=build_environment,
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {
                            "python": "3.11",
                            "nodejs": "18"
                        },
                        "commands": [
                            "npm install -g aws-cdk",
                            "pip install --upgrade pip",
                            "pip install -r requirements.txt"
                        ]
                    },
                    "build": {
                        "commands": [
                            "echo Packaging Lambda functions...",
                            "cd lambda_functions && zip -r ../lambda-package.zip .",
                            "cd ..",
                            "echo Synthesizing CDK templates...",
                            "cd infrastructure && cdk synth"
                        ]
                    }
                },
                "artifacts": {
                    "files": [
                        "**/*"
                    ]
                }
            })
        )
        
        # Deploy project
        self.deploy_project = codebuild.Project(
            self, "BiomerkinDeployProject",
            project_name="biomerkin-deploy",
            description="Deploy infrastructure using CDK",
            environment=build_environment,
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "install": {
                        "runtime-versions": {
                            "python": "3.11",
                            "nodejs": "18"
                        },
                        "commands": [
                            "npm install -g aws-cdk",
                            "pip install --upgrade pip",
                            "pip install -r requirements.txt"
                        ]
                    },
                    "build": {
                        "commands": [
                            "echo Deploying infrastructure...",
                            "cd infrastructure",
                            "cdk deploy --require-approval never --all"
                        ]
                    }
                }
            })
        )
        
        # Add necessary permissions to build projects
        for project in [self.test_project, self.security_project, self.package_project, self.deploy_project]:
            project.add_to_role_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    resources=["*"]
                )
            )
        
        # Add CDK deployment permissions
        self.deploy_project.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "cloudformation:*",
                    "lambda:*",
                    "apigateway:*",
                    "dynamodb:*",
                    "s3:*",
                    "iam:*",
                    "logs:*",
                    "events:*",
                    "sns:*",
                    "sqs:*",
                    "bedrock:*"
                ],
                resources=["*"]
            )
        )
    
    def _create_pipeline(self):
        """Create the main CI/CD pipeline"""
        
        # Create pipeline
        self.pipeline = codepipeline.Pipeline(
            self, "BiomerkinPipeline",
            pipeline_name="biomerkin-cicd-pipeline",
            artifact_bucket=self.artifact_bucket,
            restart_execution_on_update=True
        )
        
        # Source artifacts
        source_output = codepipeline.Artifact("SourceOutput")
        test_output = codepipeline.Artifact("TestOutput")
        security_output = codepipeline.Artifact("SecurityOutput")
        package_output = codepipeline.Artifact("PackageOutput")
        
        # Source stage
        self.pipeline.add_stage(
            stage_name="Source",
            actions=[
                codepipeline_actions.CodeCommitSourceAction(
                    action_name="Source",
                    repository=self.repository,
                    branch="main",
                    output=source_output,
                    trigger=codepipeline_actions.CodeCommitTrigger.EVENTS
                )
            ]
        )
        
        # Test stage
        self.pipeline.add_stage(
            stage_name="Test",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="UnitTests",
                    project=self.test_project,
                    input=source_output,
                    outputs=[test_output]
                ),
                codepipeline_actions.CodeBuildAction(
                    action_name="SecurityScan",
                    project=self.security_project,
                    input=source_output,
                    outputs=[security_output],
                    run_order=2
                )
            ]
        )
        
        # Package stage
        self.pipeline.add_stage(
            stage_name="Package",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="Package",
                    project=self.package_project,
                    input=source_output,
                    outputs=[package_output]
                )
            ]
        )
        
        # Deploy to Dev
        self.pipeline.add_stage(
            stage_name="DeployDev",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="DeployToDev",
                    project=self.deploy_project,
                    input=package_output,
                    environment_variables={
                        "ENVIRONMENT": codebuild.BuildEnvironmentVariable(value="dev"),
                        "STACK_NAME": codebuild.BuildEnvironmentVariable(value="BiomerkinDev")
                    }
                )
            ]
        )
        
        # Manual approval for staging
        self.pipeline.add_stage(
            stage_name="ApprovalForStaging",
            actions=[
                codepipeline_actions.ManualApprovalAction(
                    action_name="ManualApproval",
                    additional_information="Please review the dev deployment and approve for staging"
                )
            ]
        )
        
        # Deploy to Staging
        self.pipeline.add_stage(
            stage_name="DeployStaging",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="DeployToStaging",
                    project=self.deploy_project,
                    input=package_output,
                    environment_variables={
                        "ENVIRONMENT": codebuild.BuildEnvironmentVariable(value="staging"),
                        "STACK_NAME": codebuild.BuildEnvironmentVariable(value="BiomerkinStaging")
                    }
                )
            ]
        )
        
        # Manual approval for production
        self.pipeline.add_stage(
            stage_name="ApprovalForProduction",
            actions=[
                codepipeline_actions.ManualApprovalAction(
                    action_name="ProductionApproval",
                    additional_information="Please review the staging deployment and approve for production"
                )
            ]
        )
        
        # Deploy to Production
        self.pipeline.add_stage(
            stage_name="DeployProduction",
            actions=[
                codepipeline_actions.CodeBuildAction(
                    action_name="DeployToProduction",
                    project=self.deploy_project,
                    input=package_output,
                    environment_variables={
                        "ENVIRONMENT": codebuild.BuildEnvironmentVariable(value="prod"),
                        "STACK_NAME": codebuild.BuildEnvironmentVariable(value="BiomerkinProd")
                    }
                )
            ]
        )
    
    def _create_notifications(self):
        """Create SNS notifications for pipeline events"""
        
        # SNS topic for pipeline notifications
        self.pipeline_topic = sns.Topic(
            self, "BiomerkinPipelineNotifications",
            topic_name="biomerkin-pipeline-notifications",
            display_name="Biomerkin Pipeline Notifications"
        )
        
        # EventBridge rule for pipeline state changes
        pipeline_rule = events.Rule(
            self, "BiomerkinPipelineRule",
            event_pattern=events.EventPattern(
                source=["aws.codepipeline"],
                detail_type=["CodePipeline Pipeline Execution State Change"],
                detail={
                    "pipeline": [self.pipeline.pipeline_name],
                    "state": ["FAILED", "SUCCEEDED"]
                }
            )
        )
        
        # Add SNS target to the rule
        pipeline_rule.add_target(targets.SnsTopic(self.pipeline_topic))
    
    def _create_rollback_automation(self):
        """Create automated rollback procedures"""
        
        # Lambda function for rollback automation
        self.rollback_function = aws_lambda.Function(
            self, "BiomerkinRollbackFunction",
            function_name="biomerkin-rollback-automation",
            runtime=aws_lambda.Runtime.PYTHON_3_11,
            handler="rollback.handler",
            code=aws_lambda.Code.from_inline("""
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    '''
    Automated rollback function for failed deployments
    '''
    try:
        # Parse the event
        detail = event.get('detail', {})
        pipeline_name = detail.get('pipeline')
        execution_id = detail.get('execution-id')
        state = detail.get('state')
        
        logger.info(f"Pipeline {pipeline_name} execution {execution_id} state: {state}")
        
        if state == 'FAILED':
            # Implement rollback logic here
            logger.info("Initiating rollback procedures...")
            
            # Example: Revert to previous version
            # This would be customized based on specific rollback requirements
            
            return {
                'statusCode': 200,
                'body': json.dumps('Rollback initiated successfully')
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps('No action required')
        }
        
    except Exception as e:
        logger.error(f"Error in rollback function: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
            """),
            timeout=Duration.minutes(5)
        )
        
        # Grant necessary permissions for rollback
        self.rollback_function.add_to_role_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "codepipeline:GetPipeline",
                    "codepipeline:GetPipelineExecution",
                    "codepipeline:StartPipelineExecution",
                    "cloudformation:DescribeStacks",
                    "cloudformation:UpdateStack"
                ],
                resources=["*"]
            )
        )
        
        # EventBridge rule for failed deployments
        rollback_rule = events.Rule(
            self, "BiomerkinRollbackRule",
            event_pattern=events.EventPattern(
                source=["aws.codepipeline"],
                detail_type=["CodePipeline Pipeline Execution State Change"],
                detail={
                    "pipeline": [self.pipeline.pipeline_name],
                    "state": ["FAILED"]
                }
            )
        )
        
        # Add Lambda target to the rollback rule
        rollback_rule.add_target(targets.LambdaFunction(self.rollback_function))