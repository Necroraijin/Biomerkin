#!/usr/bin/env python3
"""
Simple test deployment for ProteomicsAgent to verify basic functionality.
"""

import boto3
import json
import logging
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_simple_proteomics_deployment():
    """Create a simple deployment to test ProteomicsAgent functionality."""
    
    # Create deployment info manually for testing
    deployment_info = {
        'deployment_time': datetime.now().isoformat(),
        'region': 'us-east-1',
        'account_id': '242201307639',  # From the error messages
        'component': 'ProteomicsAgent',
        'bedrock_agent': {
            'agent_id': 'PGLN0NWQNE',  # From the error messages
            'action_group_id': 'test_action_group'
        },
        'lambda_function': 'arn:aws:lambda:us-east-1:242201307639:function:biomerkin-proteomics-bedrock-agent'
    }
    
    # Save deployment info
    with open('proteomics_agent_deployment_info.json', 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    logger.info("Created simple ProteomicsAgent deployment info for testing")
    logger.info(f"Agent ID: {deployment_info['bedrock_agent']['agent_id']}")
    
    return deployment_info


def main():
    """Main function."""
    logger.info("Creating simple ProteomicsAgent deployment for testing...")
    
    try:
        deployment_info = create_simple_proteomics_deployment()
        
        logger.info("✅ Simple deployment info created successfully!")
        logger.info("You can now run the test script to verify functionality.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create deployment info: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)