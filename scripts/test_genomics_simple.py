#!/usr/bin/env python3
"""
Simple test for GenomicsAgent Bedrock Agent implementation.
"""

import json
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_genomics_action_structure():
    """Test the structure of the genomics action file."""
    logger.info("Testing GenomicsAgent Bedrock Action structure...")
    
    try:
        # Check if the file exists and can be read
        action_file = 'lambda_functions/bedrock_genomics_action.py'
        
        if not os.path.exists(action_file):
            logger.error(f"Action file not found: {action_file}")
            return False
        
        # Read the file and check basic structure
        with open(action_file, 'r') as f:
            content = f.read()
        
        # Check for required functions
        required_functions = [
            'def handler(',
            'def analyze_sequence_action(',
            'def interpret_variant_action(',
            'def identify_genes_action(',
            'def detect_mutations_action('
        ]
        
        missing_functions = []
        for func in required_functions:
            if func not in content:
                missing_functions.append(func)
        
        if missing_functions:
            logger.error(f"Missing required functions: {missing_functions}")
            return False
        
        # Check for autonomous reasoning functions
        autonomous_functions = [
            '_perform_autonomous_reasoning',
            '_make_autonomous_clinical_decisions',
            '_generate_llm_powered_insights'
        ]
        
        found_autonomous = []
        for func in autonomous_functions:
            if func in content:
                found_autonomous.append(func)
        
        logger.info(f"Found {len(found_autonomous)} autonomous reasoning functions")
        
        # Check file size (should be substantial for enhanced capabilities)
        file_size = len(content)
        logger.info(f"Action file size: {file_size} characters")
        
        if file_size < 10000:
            logger.warning("Action file seems small - may be missing enhanced capabilities")
        
        logger.info("✓ GenomicsAgent Bedrock Action structure test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ Structure test FAILED: {str(e)}")
        return False


def test_genomics_config_structure():
    """Test the structure of the genomics config file."""
    logger.info("Testing GenomicsAgent Bedrock Config structure...")
    
    try:
        config_file = 'lambda_functions/bedrock_genomics_agent_config.py'
        
        if not os.path.exists(config_file):
            logger.error(f"Config file not found: {config_file}")
            return False
        
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Check for required classes and functions
        required_elements = [
            'class GenomicsBedrockAgentConfig',
            'def get_agent_instruction',
            'def get_genomics_api_schema',
            'def create_agent_with_action_group'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            logger.error(f"Missing required elements: {missing_elements}")
            return False
        
        logger.info("✓ GenomicsAgent Bedrock Config structure test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ Config structure test FAILED: {str(e)}")
        return False


def test_deployment_script():
    """Test the deployment script structure."""
    logger.info("Testing deployment script structure...")
    
    try:
        deploy_file = 'scripts/deploy_genomics_bedrock_agent_enhanced.py'
        
        if not os.path.exists(deploy_file):
            logger.error(f"Deployment script not found: {deploy_file}")
            return False
        
        with open(deploy_file, 'r') as f:
            content = f.read()
        
        # Check for required deployment functions
        required_functions = [
            'class EnhancedGenomicsAgentDeployer',
            'def deploy_enhanced_genomics_agent',
            'def _create_enhanced_bedrock_agent'
        ]
        
        missing_functions = []
        for func in required_functions:
            if func not in content:
                missing_functions.append(func)
        
        if missing_functions:
            logger.error(f"Missing deployment functions: {missing_functions}")
            return False
        
        logger.info("✓ Deployment script structure test PASSED")
        return True
        
    except Exception as e:
        logger.error(f"✗ Deployment script test FAILED: {str(e)}")
        return False


def main():
    """Main test function."""
    logger.info("GenomicsAgent Bedrock Agent Implementation Test")
    logger.info("=" * 60)
    
    tests = [
        test_genomics_action_structure,
        test_genomics_config_structure,
        test_deployment_script
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Tests: {total}")
    logger.info(f"Passed: {passed}")
    logger.info(f"Failed: {total - passed}")
    logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        logger.info("\n🎉 All structure tests passed!")
        logger.info("GenomicsAgent Bedrock Agent implementation is ready!")
        return True
    else:
        logger.error(f"\n❌ {total - passed} tests failed. Please review the implementation.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)