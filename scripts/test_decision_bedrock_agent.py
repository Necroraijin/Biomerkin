#!/usr/bin/env python3
"""
Test script for DecisionAgent Bedrock Agent.
This script tests the autonomous medical decision-making capabilities of the Bedrock Agent.
"""

import json
import boto3
import time
import logging
from typing import Dict, Any, List
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DecisionBedrockAgentTester:
    """Tester for DecisionAgent Bedrock Agent."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the tester."""
        self.region = region
        self.bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
        
        # Load deployment info
        self.deployment_info = self.load_deployment_info()
        
    def load_deployment_info(self) -> Dict[str, Any]:
        """Load deployment information."""
        try:
            with open('decision_agent_deployment_info.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Deployment info not found. Please deploy the agent first.")
            raise
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive tests of the DecisionAgent Bedrock Agent."""
        logger.info("Starting comprehensive DecisionAgent Bedrock Agent tests...")
        
        test_results = {
            'test_suite': 'DecisionAgent Bedrock Agent Tests',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'agent_id': self.deployment_info['agent_id'],
            'tests': {}
        }
        
        # Test 1: Medical Report Generation
        logger.info("Test 1: Medical Report Generation")
        test_results['tests']['medical_report_generation'] = self.test_medical_report_generation()
        
        # Test 2: Genetic Risk Assessment
        logger.info("Test 2: Genetic Risk Assessment")
        test_results['tests']['genetic_risk_assessment'] = self.test_genetic_risk_assessment()
        
        # Test 3: Treatment Recommendations
        logger.info("Test 3: Treatment Recommendations")
        test_results['tests']['treatment_recommendations'] = self.test_treatment_recommendations()
        
        # Test 4: Clinical Decision Support
        logger.info("Test 4: Clinical Decision Support")
        test_results['tests']['clinical_decision_support'] = self.test_clinical_decision_support()
        
        # Test 5: Monitoring Strategy Development
        logger.info("Test 5: Monitoring Strategy Development")
        test_results['tests']['monitoring_strategy'] = self.test_monitoring_strategy()
        
        # Test 6: Complex Multi-Modal Analysis
        logger.info("Test 6: Complex Multi-Modal Analysis")
        test_results['tests']['complex_analysis'] = self.test_complex_multimodal_analysis()
        
        # Calculate overall success rate
        successful_tests = sum(1 for test in test_results['tests'].values() if test['success'])
        total_tests = len(test_results['tests'])
        test_results['overall_success_rate'] = successful_tests / total_tests
        test_results['summary'] = f"{successful_tests}/{total_tests} tests passed"
        
        logger.info(f"Test suite completed: {test_results['summary']}")
        return test_results
    
    def test_medical_report_generation(self) -> Dict[str, Any]:
        """Test medical report generation capability."""
        try:
            test_data = {
                "patient_id": "TEST_MRG_001",
                "genomics_results": {
                    "genes": [
                        {
                            "id": "BRCA1",
                            "name": "BRCA1",
                            "function": "DNA repair tumor suppressor gene",
                            "confidence": 0.95
                        },
                        {
                            "id": "TP53",
                            "name": "TP53",
                            "function": "Tumor suppressor protein p53",
                            "confidence": 0.88
                        }
                    ],
                    "mutations": [
                        {
                            "gene_id": "BRCA1",
                            "position": 5382,
                            "reference": "C",
                            "alternate": "T",
                            "significance": "Pathogenic"
                        }
                    ],
                    "quality_metrics": {
                        "quality_score": 0.92
                    }
                },
                "proteomics_results": {
                    "functional_annotations": [
                        {
                            "description": "DNA damage response pathway",
                            "confidence": 0.85,
                            "source": "UniProt"
                        }
                    ]
                },
                "literature_results": {
                    "summary": {
                        "key_findings": [
                            "BRCA1 mutations associated with increased breast cancer risk",
                            "DNA repair pathway dysfunction in cancer development"
                        ],
                        "articles_analyzed": 25,
                        "confidence_level": 0.88
                    }
                },
                "drug_results": {
                    "drug_candidates": [
                        {
                            "drug_id": "DB00958",
                            "name": "Carboplatin",
                            "mechanism": "DNA crosslinking agent",
                            "effectiveness": 0.75
                        }
                    ]
                }
            }
            
            prompt = f"""
            Generate a comprehensive medical report for this patient with the following analysis results:
            
            {json.dumps(test_data, indent=2)}
            
            Please provide a detailed medical report including risk assessment, treatment recommendations, 
            and clinical insights based on the genomic, proteomic, literature, and drug discovery data.
            """
            
            response = self.invoke_agent(prompt)
            
            # Validate response
            success = self.validate_medical_report_response(response)
            
            return {
                'success': success,
                'test_name': 'Medical Report Generation',
                'input_data': test_data,
                'response': response,
                'validation_notes': 'Checked for comprehensive report structure and content'
            }
            
        except Exception as e:
            logger.error(f"Medical report generation test failed: {e}")
            return {
                'success': False,
                'test_name': 'Medical Report Generation',
                'error': str(e)
            }
    
    def test_genetic_risk_assessment(self) -> Dict[str, Any]:
        """Test genetic risk assessment capability."""
        try:
            test_data = {
                "genomics_data": {
                    "genes": [
                        {
                            "id": "APOE",
                            "name": "APOE",
                            "function": "Apolipoprotein E",
                            "confidence": 0.92
                        }
                    ],
                    "mutations": [
                        {
                            "gene_id": "APOE",
                            "position": 112,
                            "reference": "C",
                            "alternate": "T",
                            "significance": "Risk factor for Alzheimer's disease"
                        }
                    ]
                },
                "patient_context": {
                    "age": 65,
                    "gender": "female",
                    "family_history": ["Alzheimer's disease in mother"]
                }
            }
            
            prompt = f"""
            Perform a comprehensive genetic risk assessment for this patient:
            
            {json.dumps(test_data, indent=2)}
            
            Please assess genetic risks, identify protective factors, and provide clinical recommendations 
            based on the genetic variants and patient context.
            """
            
            response = self.invoke_agent(prompt)
            
            # Validate response
            success = self.validate_risk_assessment_response(response)
            
            return {
                'success': success,
                'test_name': 'Genetic Risk Assessment',
                'input_data': test_data,
                'response': response,
                'validation_notes': 'Checked for risk factors, recommendations, and confidence metrics'
            }
            
        except Exception as e:
            logger.error(f"Genetic risk assessment test failed: {e}")
            return {
                'success': False,
                'test_name': 'Genetic Risk Assessment',
                'error': str(e)
            }
    
    def test_treatment_recommendations(self) -> Dict[str, Any]:
        """Test treatment recommendation generation capability."""
        try:
            test_data = {
                "patient_profile": {
                    "genetic_profile": {
                        "pharmacogenomic_variants": ["CYP2D6*4", "CYP2C19*2"]
                    },
                    "current_medications": ["Metformin", "Lisinopril"],
                    "allergies": ["Penicillin"]
                },
                "analysis_results": {
                    "genomics": {
                        "genes": [
                            {
                                "id": "CYP2D6",
                                "name": "CYP2D6",
                                "function": "Drug metabolism enzyme",
                                "confidence": 0.95
                            }
                        ]
                    },
                    "drug_discovery": {
                        "drug_candidates": [
                            {
                                "drug_id": "DB00321",
                                "name": "Amitriptyline",
                                "mechanism": "Tricyclic antidepressant",
                                "effectiveness": 0.70
                            }
                        ]
                    }
                },
                "treatment_goals": {
                    "primary_indication": "Depression",
                    "secondary_goals": ["Minimize side effects", "Optimize efficacy"]
                }
            }
            
            prompt = f"""
            Generate personalized treatment recommendations for this patient:
            
            {json.dumps(test_data, indent=2)}
            
            Please provide treatment recommendations considering the genetic profile, current medications, 
            allergies, and treatment goals. Include drug selection rationale and monitoring strategies.
            """
            
            response = self.invoke_agent(prompt)
            
            # Validate response
            success = self.validate_treatment_recommendations_response(response)
            
            return {
                'success': success,
                'test_name': 'Treatment Recommendations',
                'input_data': test_data,
                'response': response,
                'validation_notes': 'Checked for personalized recommendations and safety considerations'
            }
            
        except Exception as e:
            logger.error(f"Treatment recommendations test failed: {e}")
            return {
                'success': False,
                'test_name': 'Treatment Recommendations',
                'error': str(e)
            }
    
    def test_clinical_decision_support(self) -> Dict[str, Any]:
        """Test clinical decision support capability."""
        try:
            test_data = {
                "clinical_scenario": {
                    "patient_presentation": "45-year-old male with family history of cardiac disease",
                    "diagnostic_question": "Risk stratification for cardiovascular disease",
                    "therapeutic_dilemma": "Preventive intervention vs. watchful waiting"
                },
                "available_data": {
                    "genetic_data": {
                        "genes": [
                            {
                                "id": "LDLR",
                                "name": "LDLR",
                                "function": "LDL receptor",
                                "confidence": 0.90
                            }
                        ]
                    },
                    "clinical_data": {
                        "cholesterol": "elevated",
                        "blood_pressure": "borderline high"
                    }
                }
            }
            
            prompt = f"""
            Provide clinical decision support for this scenario:
            
            {json.dumps(test_data, indent=2)}
            
            Please analyze the clinical scenario and available data to provide evidence-based 
            decision recommendations, risk-benefit analysis, and alternative approaches.
            """
            
            response = self.invoke_agent(prompt)
            
            # Validate response
            success = self.validate_decision_support_response(response)
            
            return {
                'success': success,
                'test_name': 'Clinical Decision Support',
                'input_data': test_data,
                'response': response,
                'validation_notes': 'Checked for decision recommendations and evidence analysis'
            }
            
        except Exception as e:
            logger.error(f"Clinical decision support test failed: {e}")
            return {
                'success': False,
                'test_name': 'Clinical Decision Support',
                'error': str(e)
            }
    
    def test_monitoring_strategy(self) -> Dict[str, Any]:
        """Test monitoring strategy development capability."""
        try:
            test_data = {
                "patient_profile": {
                    "genetic_risk_factors": ["BRCA1 mutation", "Lynch syndrome variant"]
                },
                "treatment_plan": {
                    "primary_treatment": "Targeted therapy",
                    "duration": "6 months"
                },
                "risk_factors": ["High genetic risk", "Family history"]
            }
            
            prompt = f"""
            Develop a comprehensive monitoring strategy for this patient:
            
            {json.dumps(test_data, indent=2)}
            
            Please create a monitoring protocol including surveillance schedule, biomarker monitoring, 
            safety parameters, and escalation criteria based on the patient profile and treatment plan.
            """
            
            response = self.invoke_agent(prompt)
            
            # Validate response
            success = self.validate_monitoring_strategy_response(response)
            
            return {
                'success': success,
                'test_name': 'Monitoring Strategy Development',
                'input_data': test_data,
                'response': response,
                'validation_notes': 'Checked for comprehensive monitoring protocol and schedule'
            }
            
        except Exception as e:
            logger.error(f"Monitoring strategy test failed: {e}")
            return {
                'success': False,
                'test_name': 'Monitoring Strategy Development',
                'error': str(e)
            }
    
    def test_complex_multimodal_analysis(self) -> Dict[str, Any]:
        """Test complex multi-modal analysis integration."""
        try:
            test_data = {
                "patient_id": "COMPLEX_001",
                "comprehensive_data": {
                    "genomics": {
                        "genes": ["BRCA1", "TP53", "PTEN", "ATM"],
                        "mutations": [
                            {"gene": "BRCA1", "type": "pathogenic"},
                            {"gene": "TP53", "type": "likely_pathogenic"}
                        ]
                    },
                    "proteomics": {
                        "pathways": ["DNA repair", "Cell cycle control", "Apoptosis"]
                    },
                    "literature": {
                        "evidence_level": "strong",
                        "clinical_trials": 15
                    },
                    "drug_discovery": {
                        "targeted_therapies": ["PARP inhibitors", "Platinum compounds"],
                        "clinical_stage": "Phase III"
                    }
                }
            }
            
            prompt = f"""
            Perform a comprehensive multi-modal analysis and generate integrated clinical recommendations:
            
            {json.dumps(test_data, indent=2)}
            
            Please integrate all available data sources to provide a comprehensive medical assessment, 
            risk stratification, treatment recommendations, and monitoring strategy. Demonstrate 
            autonomous reasoning across all data modalities.
            """
            
            response = self.invoke_agent(prompt)
            
            # Validate response
            success = self.validate_complex_analysis_response(response)
            
            return {
                'success': success,
                'test_name': 'Complex Multi-Modal Analysis',
                'input_data': test_data,
                'response': response,
                'validation_notes': 'Checked for integration across all data modalities and autonomous insights'
            }
            
        except Exception as e:
            logger.error(f"Complex multi-modal analysis test failed: {e}")
            return {
                'success': False,
                'test_name': 'Complex Multi-Modal Analysis',
                'error': str(e)
            }
    
    def invoke_agent(self, prompt: str) -> Dict[str, Any]:
        """Invoke the Bedrock Agent with a prompt."""
        try:
            session_id = f"test-session-{int(time.time())}"
            
            response = self.bedrock_runtime.invoke_agent(
                agentId=self.deployment_info['agent_id'],
                agentAliasId=self.deployment_info['alias_id'],
                sessionId=session_id,
                inputText=prompt
            )
            
            # Process the response
            result = {
                'session_id': session_id,
                'response_text': '',
                'citations': [],
                'trace': []
            }
            
            # Extract response from event stream
            event_stream = response['completion']
            for event in event_stream:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        result['response_text'] += chunk['bytes'].decode('utf-8')
                elif 'trace' in event:
                    result['trace'].append(event['trace'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error invoking agent: {e}")
            raise
    
    def validate_medical_report_response(self, response: Dict[str, Any]) -> bool:
        """Validate medical report generation response."""
        response_text = response.get('response_text', '').lower()
        
        # Check for key components
        required_components = [
            'medical report',
            'genetic',
            'risk',
            'treatment',
            'recommendation'
        ]
        
        return all(component in response_text for component in required_components)
    
    def validate_risk_assessment_response(self, response: Dict[str, Any]) -> bool:
        """Validate genetic risk assessment response."""
        response_text = response.get('response_text', '').lower()
        
        required_components = [
            'risk',
            'genetic',
            'assessment',
            'recommendation'
        ]
        
        return all(component in response_text for component in required_components)
    
    def validate_treatment_recommendations_response(self, response: Dict[str, Any]) -> bool:
        """Validate treatment recommendations response."""
        response_text = response.get('response_text', '').lower()
        
        required_components = [
            'treatment',
            'recommendation',
            'drug',
            'monitoring'
        ]
        
        return all(component in response_text for component in required_components)
    
    def validate_decision_support_response(self, response: Dict[str, Any]) -> bool:
        """Validate clinical decision support response."""
        response_text = response.get('response_text', '').lower()
        
        required_components = [
            'decision',
            'recommendation',
            'evidence',
            'clinical'
        ]
        
        return all(component in response_text for component in required_components)
    
    def validate_monitoring_strategy_response(self, response: Dict[str, Any]) -> bool:
        """Validate monitoring strategy response."""
        response_text = response.get('response_text', '').lower()
        
        required_components = [
            'monitoring',
            'strategy',
            'protocol',
            'schedule'
        ]
        
        return all(component in response_text for component in required_components)
    
    def validate_complex_analysis_response(self, response: Dict[str, Any]) -> bool:
        """Validate complex multi-modal analysis response."""
        response_text = response.get('response_text', '').lower()
        
        required_components = [
            'analysis',
            'genomic',
            'treatment',
            'recommendation',
            'monitoring',
            'risk'
        ]
        
        return all(component in response_text for component in required_components)
    
    def save_test_results(self, test_results: Dict[str, Any]) -> None:
        """Save test results to file."""
        output_file = f"decision_agent_test_results_{int(time.time())}.json"
        
        with open(output_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        logger.info(f"Test results saved to {output_file}")


def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test DecisionAgent Bedrock Agent')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--test', choices=[
        'all', 'medical_report', 'risk_assessment', 'treatment_recommendations',
        'decision_support', 'monitoring_strategy', 'complex_analysis'
    ], default='all', help='Specific test to run')
    
    args = parser.parse_args()
    
    tester = DecisionBedrockAgentTester(region=args.region)
    
    if args.test == 'all':
        test_results = tester.run_comprehensive_tests()
    else:
        # Run specific test
        test_method = getattr(tester, f'test_{args.test}')
        test_result = test_method()
        test_results = {
            'test_suite': f'DecisionAgent {args.test} Test',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'tests': {args.test: test_result}
        }
    
    # Save and display results
    tester.save_test_results(test_results)
    
    print("\n" + "="*80)
    print("DECISION AGENT BEDROCK AGENT TEST RESULTS")
    print("="*80)
    print(f"Test Suite: {test_results['test_suite']}")
    print(f"Timestamp: {test_results['timestamp']}")
    
    if 'overall_success_rate' in test_results:
        print(f"Overall Success Rate: {test_results['overall_success_rate']:.2%}")
        print(f"Summary: {test_results['summary']}")
    
    print("\nIndividual Test Results:")
    for test_name, result in test_results['tests'].items():
        status = "✓ PASS" if result['success'] else "✗ FAIL"
        print(f"  {test_name}: {status}")
        if not result['success'] and 'error' in result:
            print(f"    Error: {result['error']}")
    
    print("="*80)


if __name__ == "__main__":
    main()