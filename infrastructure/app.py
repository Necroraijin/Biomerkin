#!/usr/bin/env python3
"""
AWS CDK App for Biomerkin Multi-Agent System
Infrastructure as Code for complete deployment automation
"""

import aws_cdk as cdk
from constructs import Construct

from stacks.biomerkin_stack import BiomerkinStack
from stacks.pipeline_stack import PipelineStack


class BiomerkinApp(cdk.App):
    """Main CDK Application for Biomerkin deployment"""
    
    def __init__(self):
        super().__init__()
        
        # Environment configuration
        env_dev = cdk.Environment(
            account=self.node.try_get_context("dev_account"),
            region=self.node.try_get_context("dev_region") or "us-east-1"
        )
        
        env_staging = cdk.Environment(
            account=self.node.try_get_context("staging_account"),
            region=self.node.try_get_context("staging_region") or "us-east-1"
        )
        
        env_prod = cdk.Environment(
            account=self.node.try_get_context("prod_account"),
            region=self.node.try_get_context("prod_region") or "us-east-1"
        )
        
        # Development environment
        dev_stack = BiomerkinStack(
            self, "BiomerkinDev",
            env=env_dev,
            environment_name="dev",
            enable_monitoring=False,
            enable_backup=False
        )
        
        # Staging environment
        staging_stack = BiomerkinStack(
            self, "BiomerkinStaging",
            env=env_staging,
            environment_name="staging",
            enable_monitoring=True,
            enable_backup=True
        )
        
        # Production environment
        prod_stack = BiomerkinStack(
            self, "BiomerkinProd",
            env=env_prod,
            environment_name="prod",
            enable_monitoring=True,
            enable_backup=True,
            enable_multi_az=True
        )
        
        # CI/CD Pipeline
        pipeline_stack = PipelineStack(
            self, "BiomerkinPipeline",
            dev_stack=dev_stack,
            staging_stack=staging_stack,
            prod_stack=prod_stack,
            env=env_dev
        )


if __name__ == "__main__":
    app = BiomerkinApp()
    app.synth()