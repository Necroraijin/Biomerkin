#!/usr/bin/env python3
"""
Test script for Autonomous Bedrock Agents integration.
This script demonstrates the autonomous AI agent capabilities for the AWS hackathon.
"""

import json
import boto3
import logging
from typing import Dict, Any
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from biomerkin.services.bedrock_agent_service import BedrockAgentService, AutonomousGenomicsAgent
from biomerkin.utils.logging_config import get_logger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)


def test_bedrock_agent_creation():
    """Test creating Bedrock Agents for autonomous genomics analysis."""
    logger.info("Testing Bedrock Agent creation...")
    
    try:
        # Initialize Bedrock Agent service
        bedrock_service = BedrockAgentService()
        
        # Create genomics agent with autonomous capabilities
        agent_id = bedrock_service.create_genomics_agent()
        
        logger.info(f"Successfully created Bedrock Agent: {agent_id}")
        
        # Test agent invocation with sample genomics data
        sample_prompt = """
        Analyze this DNA sequence for clinical significance:
        
        ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
        
        Please autonomously:
        1. Identify any genes or variants
        2. Assess clinical significance
        3. Provide reasoning for your analysis
        4. Suggest next steps
        """
        
        session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        result = bedrock_service.invoke_agent(agent_id, session_id, sample_prompt)
        
        logger.info("Agent invocation successful!")
        logger.info(f"Response: {result.get('response', '')[:200]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing Bedrock Agent creation: {str(e)}")
        return False


def test_autonomous_genomics_workflow():
    """Test the complete autonomous genomics workflow."""
    logger.info("Testing autonomous genomics workflow...")
    
    try:
        # Initialize autonomous genomics agent
        autonomous_agent = AutonomousGenomicsAgent()
        
        # Sample DNA sequence for testing
        sample_dna_sequence = """
        ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
        CGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATC
        GATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
        ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGA
        """
        
        # Sample patient information
        patient_info = {
            'patient_id': 'TEST_PATIENT_001',
            'age': 45,
            'gender': 'Female',
            'family_history': 'Positive for breast cancer',
            'symptoms': ['Fatigue', 'Weight loss'],
            'comorbidities': ['Diabetes']
        }
        
        # Perform autonomous genomics analysis
        result = autonomous_agent.analyze_patient_genome(
            dna_sequence=sample_dna_sequence,
            patient_info=patient_info
        )
        
        logger.info("Autonomous genomics analysis completed!")
        logger.info(f"Analysis type: {result.get('analysis_type', 'Unknown')}")
        logger.info(f"Patient ID: {result.get('patient_id', 'Unknown')}")
        logger.info(f"Sequence length: {result.get('sequence_length', 0)}")
        
        # Check autonomous capabilities
        autonomous_caps = result.get('autonomous_capabilities', {})
        logger.info(f"Reasoning demonstrated: {autonomous_caps.get('reasoning_demonstrated', False)}")
        logger.info(f"Decision making model: {autonomous_caps.get('decision_making_model', 'Unknown')}")
        
        # Display autonomous decisions
        decisions = autonomous_caps.get('autonomous_decisions', [])
        logger.info(f"Autonomous decisions made: {len(decisions)}")
        for i, decision in enumerate(decisions[:3], 1):
            logger.info(f"  {i}. {decision}")
        
        # Display external integrations
        integrations = autonomous_caps.get('external_integrations', [])
        logger.info(f"External integrations: {len(integrations)}")
        for integration in integrations:
            logger.info(f"  - {integration}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing autonomous genomics workflow: {str(e)}")
        return False


def test_reasoning_capabilities():
    """Test advanced reasoning capabilities with complex genomics cases."""
    logger.info("Testing reasoning capabilities...")
    
    try:
        # Initialize autonomous genomics agent
        autonomous_agent = AutonomousGenomicsAgent()
        
        # Create a complex genomics case for reasoning demonstration
        complex_case = {
            'case_id': 'COMPLEX_CASE_001',
            'case_type': 'multi_variant_analysis',
            'complexity_factors': [
                'Multiple variants of uncertain significance',
                'Conflicting literature evidence',
                'Limited population data',
                'Complex inheritance pattern'
            ],
            'genomic_data': {
                'variants': [
                    {
                        'variant': 'c.1234G>A',
                        'gene': 'BRCA1',
                        'classification': 'Uncertain significance',
                        'conflicting_evidence': True
                    },
                    {
                        'variant': 'c.5678C>T',
                        'gene': 'TP53',
                        'classification': 'Likely pathogenic',
                        'population_frequency': 'Rare'
                    }
                ]
            },
            'clinical_context': {
                'patient_age': 52,
                'family_history': 'Strong family history of cancer',
                'current_symptoms': ['Fatigue', 'Weight loss', 'Night sweats']
            }
        }
        
        # Demonstrate reasoning capabilities
        result = autonomous_agent.demonstrate_reasoning_capabilities(complex_case)
        
        logger.info("Reasoning demonstration completed!")
        
        # Check reasoning demonstration
        reasoning_demo = result.get('reasoning_demonstration', {})
        logger.info(f"Case complexity: {reasoning_demo.get('case_complexity', 'Unknown')}")
        logger.info(f"Reasoning model: {reasoning_demo.get('reasoning_model', 'Unknown')}")
        logger.info(f"Decision points: {reasoning_demo.get('decision_points', 0)}")
        logger.info(f"Autonomous actions: {reasoning_demo.get('autonomous_actions', 0)}")
        
        # Display reasoning steps
        reasoning_steps = result.get('reasoning', [])
        logger.info(f"Reasoning steps: {len(reasoning_steps)}")
        for i, step in enumerate(reasoning_steps[:3], 1):
            logger.info(f"  Step {i}: {step}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing reasoning capabilities: {str(e)}")
        return False


def test_lambda_action_groups():
    """Test the Lambda action group executors."""
    logger.info("Testing Lambda action group executors...")
    
    try:
        # Test genomics action group
        genomics_event = {
            'actionGroup': 'GenomicsAnalysis',
            'apiPath': '/analyze-sequence',
            'httpMethod': 'POST',
            'parameters': [],
            'requestBody': {
                'content': {
                    'sequence': 'ATGCGATCGATCGATCGATCGATCGATCGATCGATCG',
                    'reference_genome': 'GRCh38'
                }
            }
        }
        
        # Import and test genomics action
        from lambda_functions.bedrock_genomics_action import handler as genomics_handler
        
        class MockContext:
            aws_request_id = 'test-request-id'
        
        genomics_result = genomics_handler(genomics_event, MockContext())
        
        logger.info("Genomics action group test successful!")
        logger.info(f"Status code: {genomics_result['response']['httpStatusCode']}")
        
        # Test literature action group
        literature_event = {
            'actionGroup': 'LiteratureResearch',
            'apiPath': '/search-literature',
            'httpMethod': 'POST',
            'parameters': [],
            'requestBody': {
                'content': {
                    'genes': ['BRCA1', 'TP53'],
                    'conditions': ['breast cancer'],
                    'max_articles': 10
                }
            }
        }
        
        # Import and test literature action
        from lambda_functions.bedrock_literature_action import handler as literature_handler
        
        literature_result = literature_handler(literature_event, MockContext())
        
        logger.info("Literature action group test successful!")
        logger.info(f"Status code: {literature_result['response']['httpStatusCode']}")
        
        # Test proteomics action group
        proteomics_event = {
            'actionGroup': 'ProteomicsAnalysis',
            'apiPath': '/analyze-protein',
            'httpMethod': 'POST',
            'parameters': [],
            'requestBody': {
                'content': {
                    'protein_sequence': 'MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG',
                    'protein_id': 'P04637'
                }
            }
        }
        
        # Import and test proteomics action
        from lambda_functions.bedrock_proteomics_action import handler as proteomics_handler
        
        proteomics_result = proteomics_handler(proteomics_event, MockContext())
        
        logger.info("Proteomics action group test successful!")
        logger.info(f"Status code: {proteomics_result['response']['httpStatusCode']}")

        # Test drug action group
        drug_event = {
            'actionGroup': 'DrugDiscovery',
            'apiPath': '/find-drug-candidates',
            'httpMethod': 'POST',
            'parameters': [],
            'requestBody': {
                'content': {
                    'target_genes': ['BRCA1', 'TP53'],
                    'condition': 'breast cancer'
                }
            }
        }
        
        # Import and test drug action
        from lambda_functions.bedrock_drug_action import handler as drug_handler
        
        drug_result = drug_handler(drug_event, MockContext())
        
        logger.info("Drug action group test successful!")
        logger.info(f"Status code: {drug_result['response']['httpStatusCode']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing Lambda action groups: {str(e)}")
        return False


def test_bedrock_orchestrator():
    """Test the Bedrock orchestrator for multi-agent coordination."""
    logger.info("Testing Bedrock orchestrator...")
    
    try:
        # Import orchestrator
        from lambda_functions.bedrock_orchestrator import handler as orchestrator_handler
        
        # Create test event
        orchestrator_event = {
            'dna_sequence': 'ATGCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG',
            'patient_info': {
                'patient_id': 'TEST_PATIENT_002',
                'age': 38,
                'gender': 'Male',
                'family_history': 'Positive for cancer'
            },
            'analysis_type': 'comprehensive',
            'autonomous_mode': True
        }
        
        class MockContext:
            aws_request_id = 'test-orchestrator-request'
        
        # Test orchestrator
        result = orchestrator_handler(orchestrator_event, MockContext())
        
        logger.info("Bedrock orchestrator test completed!")
        logger.info(f"Status code: {result['statusCode']}")
        
        if result['statusCode'] == 200:
            body = json.loads(result['body'])
            logger.info(f"Success: {body.get('success', False)}")
            
            # Check hackathon demonstration features
            analysis_results = body.get('analysis_results', {})
            hackathon_demo = analysis_results.get('hackathon_demonstration', {})
            
            logger.info("Hackathon demonstration features:")
            logger.info(f"  Autonomous AI Agent: {hackathon_demo.get('autonomous_ai_agent', False)}")
            logger.info(f"  LLM Reasoning: {hackathon_demo.get('llm_reasoning', False)}")
            logger.info(f"  External API Integration: {hackathon_demo.get('external_api_integration', False)}")
            logger.info(f"  Multi-Agent Coordination: {hackathon_demo.get('multi_agent_coordination', False)}")
            logger.info(f"  Clinical Decision Making: {hackathon_demo.get('clinical_decision_making', False)}")
            
            aws_services = hackathon_demo.get('aws_services_used', [])
            logger.info(f"  AWS Services Used: {len(aws_services)}")
            for service in aws_services:
                logger.info(f"    - {service}")
        
        return result['statusCode'] == 200
        
    except Exception as e:
        logger.error(f"Error testing Bedrock orchestrator: {str(e)}")
        return False


def run_comprehensive_test():
    """Run comprehensive test of all autonomous Bedrock Agent capabilities."""
    logger.info("=" * 80)
    logger.info("AUTONOMOUS BEDROCK AGENTS COMPREHENSIVE TEST")
    logger.info("=" * 80)
    
    test_results = {}
    
    # Test 1: Bedrock Agent Creation
    logger.info("\n" + "=" * 50)
    logger.info("TEST 1: Bedrock Agent Creation")
    logger.info("=" * 50)
    test_results['agent_creation'] = test_bedrock_agent_creation()
    
    # Test 2: Autonomous Genomics Workflow
    logger.info("\n" + "=" * 50)
    logger.info("TEST 2: Autonomous Genomics Workflow")
    logger.info("=" * 50)
    test_results['autonomous_workflow'] = test_autonomous_genomics_workflow()
    
    # Test 3: Reasoning Capabilities
    logger.info("\n" + "=" * 50)
    logger.info("TEST 3: Reasoning Capabilities")
    logger.info("=" * 50)
    test_results['reasoning_capabilities'] = test_reasoning_capabilities()
    
    # Test 4: Lambda Action Groups
    logger.info("\n" + "=" * 50)
    logger.info("TEST 4: Lambda Action Groups")
    logger.info("=" * 50)
    test_results['lambda_actions'] = test_lambda_action_groups()
    
    # Test 5: Bedrock Orchestrator
    logger.info("\n" + "=" * 50)
    logger.info("TEST 5: Bedrock Orchestrator")
    logger.info("=" * 50)
    test_results['orchestrator'] = test_bedrock_orchestrator()
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name.upper()}: {status}")
    
    logger.info(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED! Autonomous Bedrock Agents are ready for hackathon demonstration!")
    else:
        logger.warning(f"⚠️  {total_tests - passed_tests} test(s) failed. Please review the errors above.")
    
    # Hackathon readiness check
    logger.info("\n" + "=" * 80)
    logger.info("AWS HACKATHON READINESS CHECK")
    logger.info("=" * 80)
    
    hackathon_requirements = {
        'Autonomous AI Agent': test_results.get('autonomous_workflow', False),
        'LLM Reasoning': test_results.get('reasoning_capabilities', False),
        'External API Integration': test_results.get('lambda_actions', False),
        'Multi-Agent Coordination': test_results.get('orchestrator', False),
        'AWS Services Integration': test_results.get('agent_creation', False)
    }
    
    for requirement, status in hackathon_requirements.items():
        status_icon = "✅" if status else "❌"
        logger.info(f"{status_icon} {requirement}")
    
    hackathon_ready = all(hackathon_requirements.values())
    if hackathon_ready:
        logger.info("\n🏆 HACKATHON READY! All requirements satisfied.")
    else:
        logger.warning("\n⚠️  Not all hackathon requirements are satisfied.")
    
    return hackathon_ready


if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during testing: {str(e)}")
        sys.exit(1)