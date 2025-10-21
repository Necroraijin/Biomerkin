#!/usr/bin/env python3
"""
Test script for DrugAgent Bedrock Agent with autonomous capabilities.
This script tests the autonomous drug discovery and clinical analysis capabilities
of the DrugAgent Bedrock Agent.
"""

import json
import boto3
import logging
import time
import sys
import os
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DrugBedrockAgentTester:
    """Tester for DrugAgent Bedrock Agent autonomous capabilities."""
    
    def __init__(self, agent_id: str, region: str = 'us-east-1'):
        """Initialize the tester."""
        self.agent_id = agent_id
        self.region = region
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
        
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive tests of DrugAgent autonomous capabilities.
        
        Returns:
            Dictionary containing test results
        """
        logger.info("Starting comprehensive DrugAgent Bedrock Agent tests...")
        
        test_results = {
            'agent_id': self.agent_id,
            'test_timestamp': time.time(),
            'tests': {}
        }
        
        # Test 1: Drug candidate identification
        logger.info("Testing autonomous drug candidate identification...")
        test_results['tests']['drug_discovery'] = self._test_drug_discovery()
        
        # Test 2: Clinical trial analysis
        logger.info("Testing autonomous clinical trial analysis...")
        test_results['tests']['clinical_trials'] = self._test_clinical_trial_analysis()
        
        # Test 3: Drug interaction assessment
        logger.info("Testing autonomous drug interaction assessment...")
        test_results['tests']['drug_interactions'] = self._test_drug_interactions()
        
        # Test 4: Therapeutic potential evaluation
        logger.info("Testing autonomous therapeutic evaluation...")
        test_results['tests']['therapeutic_evaluation'] = self._test_therapeutic_evaluation()
        
        # Test 5: Treatment plan generation
        logger.info("Testing autonomous treatment plan generation...")
        test_results['tests']['treatment_planning'] = self._test_treatment_planning()
        
        # Calculate overall success rate
        successful_tests = sum(1 for test in test_results['tests'].values() if test.get('success', False))
        total_tests = len(test_results['tests'])
        test_results['overall_success_rate'] = successful_tests / total_tests if total_tests > 0 else 0
        
        logger.info(f"Tests completed. Success rate: {test_results['overall_success_rate']:.2%}")
        
        return test_results
    
    def _test_drug_discovery(self) -> Dict[str, Any]:
        """Test autonomous drug candidate identification."""
        try:
            # Test with cancer-related genes
            test_input = """
            I need to find drug candidates for a patient with mutations in BRCA1 and TP53 genes. 
            The patient has breast cancer and we're looking for targeted therapy options. 
            Please identify and prioritize drug candidates using your autonomous reasoning capabilities.
            """
            
            response = self._invoke_agent(test_input)
            
            # Analyze response for autonomous capabilities
            analysis = self._analyze_drug_discovery_response(response)
            
            return {
                'success': analysis['has_drug_candidates'],
                'response_length': len(response),
                'autonomous_features': analysis['autonomous_features'],
                'drug_candidates_found': analysis['drug_count'],
                'reasoning_quality': analysis['reasoning_score'],
                'raw_response': response[:500] + "..." if len(response) > 500 else response
            }
            
        except Exception as e:
            logger.error(f"Drug discovery test failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'test_type': 'drug_discovery'
            }
    
    def _test_clinical_trial_analysis(self) -> Dict[str, Any]:
        """Test autonomous clinical trial analysis."""
        try:
            test_input = """
            Analyze clinical trials for trastuzumab (Herceptin) and pembrolizumab (Keytruda) 
            in breast cancer treatment. Use your autonomous reasoning to assess trial design quality, 
            success probability, and regulatory outlook. Provide insights on the evidence strength.
            """
            
            response = self._invoke_agent(test_input)
            
            # Analyze response for clinical trial insights
            analysis = self._analyze_clinical_trial_response(response)
            
            return {
                'success': analysis['has_trial_analysis'],
                'response_length': len(response),
                'autonomous_features': analysis['autonomous_features'],
                'trials_analyzed': analysis['trial_count'],
                'insights_quality': analysis['insights_score'],
                'raw_response': response[:500] + "..." if len(response) > 500 else response
            }
            
        except Exception as e:
            logger.error(f"Clinical trial analysis test failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'test_type': 'clinical_trials'
            }
    
    def _test_drug_interactions(self) -> Dict[str, Any]:
        """Test autonomous drug interaction assessment."""
        try:
            test_input = """
            Assess drug interactions between warfarin, aspirin, and metformin for a 65-year-old 
            patient with diabetes and atrial fibrillation. Use autonomous reasoning to evaluate 
            clinical significance and provide safety recommendations with monitoring strategies.
            """
            
            response = self._invoke_agent(test_input)
            
            # Analyze response for interaction assessment
            analysis = self._analyze_interaction_response(response)
            
            return {
                'success': analysis['has_interaction_analysis'],
                'response_length': len(response),
                'autonomous_features': analysis['autonomous_features'],
                'interactions_found': analysis['interaction_count'],
                'safety_recommendations': analysis['safety_score'],
                'raw_response': response[:500] + "..." if len(response) > 500 else response
            }
            
        except Exception as e:
            logger.error(f"Drug interaction test failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'test_type': 'drug_interactions'
            }
    
    def _test_therapeutic_evaluation(self) -> Dict[str, Any]:
        """Test autonomous therapeutic potential evaluation."""
        try:
            test_input = """
            Evaluate the therapeutic potential of CAR-T cell therapy and checkpoint inhibitors 
            for a patient with relapsed B-cell lymphoma. Consider efficacy, safety, and 
            patient-specific factors. Use autonomous reasoning to provide personalized recommendations.
            """
            
            response = self._invoke_agent(test_input)
            
            # Analyze response for therapeutic evaluation
            analysis = self._analyze_therapeutic_response(response)
            
            return {
                'success': analysis['has_therapeutic_analysis'],
                'response_length': len(response),
                'autonomous_features': analysis['autonomous_features'],
                'therapies_evaluated': analysis['therapy_count'],
                'personalization_quality': analysis['personalization_score'],
                'raw_response': response[:500] + "..." if len(response) > 500 else response
            }
            
        except Exception as e:
            logger.error(f"Therapeutic evaluation test failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'test_type': 'therapeutic_evaluation'
            }
    
    def _test_treatment_planning(self) -> Dict[str, Any]:
        """Test autonomous treatment plan generation."""
        try:
            test_input = """
            Generate a comprehensive treatment plan for a 45-year-old patient with HER2-positive 
            breast cancer, considering neoadjuvant therapy, surgery, and adjuvant treatment. 
            Use autonomous reasoning to optimize drug selection, sequencing, and monitoring strategies.
            """
            
            response = self._invoke_agent(test_input)
            
            # Analyze response for treatment planning
            analysis = self._analyze_treatment_plan_response(response)
            
            return {
                'success': analysis['has_treatment_plan'],
                'response_length': len(response),
                'autonomous_features': analysis['autonomous_features'],
                'plan_completeness': analysis['completeness_score'],
                'optimization_quality': analysis['optimization_score'],
                'raw_response': response[:500] + "..." if len(response) > 500 else response
            }
            
        except Exception as e:
            logger.error(f"Treatment planning test failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'test_type': 'treatment_planning'
            }
    
    def _invoke_agent(self, input_text: str) -> str:
        """Invoke the Bedrock Agent with input text."""
        try:
            response = self.bedrock_runtime.invoke_agent(
                agentId=self.agent_id,
                agentAliasId='TSTALIASID',  # Test alias
                sessionId=f"test-session-{int(time.time())}",
                inputText=input_text
            )
            
            # Extract response text
            response_text = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error invoking agent: {str(e)}")
            raise
    
    def _analyze_drug_discovery_response(self, response: str) -> Dict[str, Any]:
        """Analyze drug discovery response for autonomous capabilities."""
        response_lower = response.lower()
        
        # Check for drug candidates
        has_drug_candidates = any(term in response_lower for term in [
            'drug candidate', 'therapeutic', 'treatment', 'medication', 'compound'
        ])
        
        # Count drug mentions
        drug_count = sum(response_lower.count(term) for term in [
            'drug', 'therapy', 'treatment', 'medication'
        ])
        
        # Check for autonomous features
        autonomous_features = []
        if 'reasoning' in response_lower or 'analysis' in response_lower:
            autonomous_features.append('reasoning')
        if 'prioritiz' in response_lower or 'rank' in response_lower:
            autonomous_features.append('prioritization')
        if 'recommend' in response_lower:
            autonomous_features.append('recommendations')
        
        # Score reasoning quality
        reasoning_score = len(autonomous_features) / 3.0
        
        return {
            'has_drug_candidates': has_drug_candidates,
            'drug_count': min(drug_count, 10),  # Cap at 10
            'autonomous_features': autonomous_features,
            'reasoning_score': reasoning_score
        }
    
    def _analyze_clinical_trial_response(self, response: str) -> Dict[str, Any]:
        """Analyze clinical trial response for autonomous capabilities."""
        response_lower = response.lower()
        
        # Check for trial analysis
        has_trial_analysis = any(term in response_lower for term in [
            'clinical trial', 'study', 'phase', 'efficacy', 'safety'
        ])
        
        # Count trial mentions
        trial_count = sum(response_lower.count(term) for term in [
            'trial', 'study', 'phase'
        ])
        
        # Check for autonomous features
        autonomous_features = []
        if 'success probability' in response_lower or 'likelihood' in response_lower:
            autonomous_features.append('success_prediction')
        if 'design quality' in response_lower or 'methodology' in response_lower:
            autonomous_features.append('quality_assessment')
        if 'regulatory' in response_lower:
            autonomous_features.append('regulatory_analysis')
        
        # Score insights quality
        insights_score = len(autonomous_features) / 3.0
        
        return {
            'has_trial_analysis': has_trial_analysis,
            'trial_count': min(trial_count, 10),
            'autonomous_features': autonomous_features,
            'insights_score': insights_score
        }
    
    def _analyze_interaction_response(self, response: str) -> Dict[str, Any]:
        """Analyze drug interaction response for autonomous capabilities."""
        response_lower = response.lower()
        
        # Check for interaction analysis
        has_interaction_analysis = any(term in response_lower for term in [
            'interaction', 'contraindication', 'safety', 'monitoring'
        ])
        
        # Count interactions
        interaction_count = response_lower.count('interaction')
        
        # Check for autonomous features
        autonomous_features = []
        if 'safety' in response_lower or 'risk' in response_lower:
            autonomous_features.append('safety_assessment')
        if 'monitor' in response_lower:
            autonomous_features.append('monitoring_strategy')
        if 'recommend' in response_lower:
            autonomous_features.append('recommendations')
        
        # Score safety recommendations
        safety_score = len(autonomous_features) / 3.0
        
        return {
            'has_interaction_analysis': has_interaction_analysis,
            'interaction_count': min(interaction_count, 5),
            'autonomous_features': autonomous_features,
            'safety_score': safety_score
        }
    
    def _analyze_therapeutic_response(self, response: str) -> Dict[str, Any]:
        """Analyze therapeutic evaluation response for autonomous capabilities."""
        response_lower = response.lower()
        
        # Check for therapeutic analysis
        has_therapeutic_analysis = any(term in response_lower for term in [
            'therapeutic', 'efficacy', 'treatment', 'therapy'
        ])
        
        # Count therapies
        therapy_count = sum(response_lower.count(term) for term in [
            'therapy', 'treatment'
        ])
        
        # Check for autonomous features
        autonomous_features = []
        if 'personalized' in response_lower or 'patient-specific' in response_lower:
            autonomous_features.append('personalization')
        if 'efficacy' in response_lower and 'safety' in response_lower:
            autonomous_features.append('risk_benefit_analysis')
        if 'recommend' in response_lower:
            autonomous_features.append('recommendations')
        
        # Score personalization quality
        personalization_score = len(autonomous_features) / 3.0
        
        return {
            'has_therapeutic_analysis': has_therapeutic_analysis,
            'therapy_count': min(therapy_count, 5),
            'autonomous_features': autonomous_features,
            'personalization_score': personalization_score
        }
    
    def _analyze_treatment_plan_response(self, response: str) -> Dict[str, Any]:
        """Analyze treatment plan response for autonomous capabilities."""
        response_lower = response.lower()
        
        # Check for treatment plan
        has_treatment_plan = any(term in response_lower for term in [
            'treatment plan', 'protocol', 'regimen', 'schedule'
        ])
        
        # Check for autonomous features
        autonomous_features = []
        if 'sequencing' in response_lower or 'timing' in response_lower:
            autonomous_features.append('sequencing_optimization')
        if 'monitoring' in response_lower:
            autonomous_features.append('monitoring_strategy')
        if 'dosing' in response_lower or 'dose' in response_lower:
            autonomous_features.append('dosing_optimization')
        
        # Score completeness
        completeness_score = len(autonomous_features) / 3.0
        
        # Score optimization quality
        optimization_score = 1.0 if 'optim' in response_lower else 0.5
        
        return {
            'has_treatment_plan': has_treatment_plan,
            'autonomous_features': autonomous_features,
            'completeness_score': completeness_score,
            'optimization_score': optimization_score
        }


def main():
    """Main testing function."""
    if len(sys.argv) != 2:
        print("Usage: python test_drug_bedrock_agent.py <agent_id>")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    
    try:
        tester = DrugBedrockAgentTester(agent_id)
        test_results = tester.run_comprehensive_tests()
        
        # Save test results
        timestamp = int(time.time())
        results_file = f"drug_agent_test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print("\n" + "="*60)
        print("DRUGAGENT BEDROCK AGENT TEST RESULTS")
        print("="*60)
        print(f"Agent ID: {agent_id}")
        print(f"Overall Success Rate: {test_results['overall_success_rate']:.2%}")
        print("\nTest Results:")
        
        for test_name, result in test_results['tests'].items():
            status = "✓ PASS" if result.get('success', False) else "✗ FAIL"
            print(f"  {test_name}: {status}")
            
            if 'autonomous_features' in result:
                features = ", ".join(result['autonomous_features'])
                print(f"    Autonomous Features: {features}")
        
        print(f"\nDetailed results saved to: {results_file}")
        print("="*60)
        
        return test_results
        
    except Exception as e:
        print(f"\nTesting failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()