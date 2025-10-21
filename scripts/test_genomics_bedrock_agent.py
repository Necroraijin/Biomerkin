#!/usr/bin/env python3
"""
Test script for GenomicsAgent Bedrock Agent implementation.
This script tests the autonomous genomics analysis capabilities.
"""

import json
import logging
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lambda_functions.bedrock_genomics_action import (
    analyze_sequence_action,
    interpret_variant_action,
    identify_genes_action,
    detect_mutations_action
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GenomicsBedrockAgentTester:
    """Test class for GenomicsAgent Bedrock Agent capabilities."""
    
    def __init__(self):
        """Initialize the tester."""
        self.test_results = []
        
    def run_all_tests(self):
        """Run all test cases for GenomicsAgent Bedrock Agent."""
        logger.info("Starting GenomicsAgent Bedrock Agent Tests")
        logger.info("=" * 60)
        
        # Test 1: Sequence Analysis
        self.test_sequence_analysis()
        
        # Test 2: Variant Interpretation
        self.test_variant_interpretation()
        
        # Test 3: Gene Identification
        self.test_gene_identification()
        
        # Test 4: Mutation Detection
        self.test_mutation_detection()
        
        # Generate test report
        self.generate_test_report()
        
    def test_sequence_analysis(self):
        """Test autonomous sequence analysis capabilities."""
        logger.info("Testing Autonomous Sequence Analysis...")
        
        try:
            # Sample DNA sequence for testing
            test_sequence = (
                "ATGGCGGCGCTGAGCGGTGGCGAGCAGCTGAGCGAGCTGCAGCGCCTGCAGCGCCTG"
                "CAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAG"
                "CGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGC"
                "CTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTG"
                "CAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAG"
            )
            
            request_body = {
                'content': {
                    'sequence': test_sequence,
                    'reference_genome': 'GRCh38',
                    'patient_context': {
                        'age': 45,
                        'gender': 'female',
                        'family_history': 'breast cancer',
                        'ethnicity': 'caucasian'
                    }
                }
            }
            
            result = analyze_sequence_action(request_body, {})
            
            # Validate results
            assert 'analysis_type' in result
            assert 'autonomous_reasoning' in result
            assert 'clinical_decisions' in result
            assert 'llm_insights' in result
            
            self.test_results.append({
                'test': 'Sequence Analysis',
                'status': 'PASSED',
                'details': f"Analyzed sequence of {len(test_sequence)} nucleotides"
            })
            
            logger.info("✓ Sequence Analysis Test PASSED")
            
        except Exception as e:
            self.test_results.append({
                'test': 'Sequence Analysis',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error(f"✗ Sequence Analysis Test FAILED: {str(e)}")    

    def test_variant_interpretation(self):
        """Test autonomous variant interpretation capabilities."""
        logger.info("Testing Autonomous Variant Interpretation...")
        
        try:
            request_body = {
                'content': {
                    'variant': 'c.1234G>A',
                    'gene': 'BRCA1',
                    'patient_context': {
                        'family_history': 'breast and ovarian cancer',
                        'age': 35,
                        'ethnicity': 'ashkenazi jewish'
                    }
                }
            }
            
            result = interpret_variant_action(request_body, {})
            
            # Validate results
            assert 'classification' in result
            assert 'autonomous_reasoning' in result
            assert 'recommendations' in result
            
            self.test_results.append({
                'test': 'Variant Interpretation',
                'status': 'PASSED',
                'details': f"Interpreted variant {request_body['content']['variant']}"
            })
            
            logger.info("✓ Variant Interpretation Test PASSED")
            
        except Exception as e:
            self.test_results.append({
                'test': 'Variant Interpretation',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error(f"✗ Variant Interpretation Test FAILED: {str(e)}")
    
    def test_gene_identification(self):
        """Test autonomous gene identification capabilities."""
        logger.info("Testing Autonomous Gene Identification...")
        
        try:
            test_sequence = (
                "ATGGCGGCGCTGAGCGGTGGCGAGCAGCTGAGCGAGCTGCAGCGCCTGCAGCGCCTG"
                "CAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAG"
                "CGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGC"
                "CTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTG"
            )
            
            request_body = {
                'content': {
                    'sequence': test_sequence,
                    'analysis_context': {
                        'organism': 'human',
                        'tissue_type': 'breast',
                        'disease_context': 'cancer'
                    }
                }
            }
            
            result = identify_genes_action(request_body, {})
            
            # Validate results
            assert 'genes_identified' in result
            assert 'autonomous_analysis' in result
            assert 'clinical_prioritization' in result
            
            self.test_results.append({
                'test': 'Gene Identification',
                'status': 'PASSED',
                'details': f"Identified genes in sequence of {len(test_sequence)} nucleotides"
            })
            
            logger.info("✓ Gene Identification Test PASSED")
            
        except Exception as e:
            self.test_results.append({
                'test': 'Gene Identification',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error(f"✗ Gene Identification Test FAILED: {str(e)}")
    
    def test_mutation_detection(self):
        """Test autonomous mutation detection capabilities."""
        logger.info("Testing Autonomous Mutation Detection...")
        
        try:
            test_sequence = (
                "ATGGCGGCGCTGAGCGGTGGCGAGCAGCTGAGCGAGCTGCAGCGCCTGCAGCGCCTG"
                "CAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAG"
            )
            
            reference_sequence = (
                "ATGGCGGCGCTGAGCGGTGGCGAGCAGCTGAGCGAGCTGCAGCGCCTGCAGCGCCTG"
                "CAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAGCGCCTGCAG"
            )
            
            # Introduce a mutation for testing
            mutated_sequence = test_sequence[:50] + "T" + test_sequence[51:]
            
            request_body = {
                'content': {
                    'sequence': mutated_sequence,
                    'reference_sequence': reference_sequence,
                    'patient_context': {
                        'age': 40,
                        'family_history': 'cancer',
                        'clinical_presentation': 'tumor'
                    }
                }
            }
            
            result = detect_mutations_action(request_body, {})
            
            # Validate results
            assert 'mutations_detected' in result
            assert 'autonomous_analysis' in result
            assert 'clinical_interpretation' in result
            
            self.test_results.append({
                'test': 'Mutation Detection',
                'status': 'PASSED',
                'details': f"Detected mutations in sequence comparison"
            })
            
            logger.info("✓ Mutation Detection Test PASSED")
            
        except Exception as e:
            self.test_results.append({
                'test': 'Mutation Detection',
                'status': 'FAILED',
                'error': str(e)
            })
            logger.error(f"✗ Mutation Detection Test FAILED: {str(e)}")
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        logger.info("\n" + "=" * 60)
        logger.info("GENOMICS BEDROCK AGENT TEST REPORT")
        logger.info("=" * 60)
        
        passed_tests = len([t for t in self.test_results if t['status'] == 'PASSED'])
        total_tests = len(self.test_results)
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        logger.info("\nDetailed Results:")
        for result in self.test_results:
            status_symbol = "✓" if result['status'] == 'PASSED' else "✗"
            logger.info(f"{status_symbol} {result['test']}: {result['status']}")
            if 'details' in result:
                logger.info(f"   Details: {result['details']}")
            if 'error' in result:
                logger.info(f"   Error: {result['error']}")
        
        # Save test report
        report = {
            'test_timestamp': datetime.now().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'test_results': self.test_results
        }
        
        with open('genomics_bedrock_agent_test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"\nTest report saved to: genomics_bedrock_agent_test_report.json")
        
        return passed_tests == total_tests


def main():
    """Main test function."""
    logger.info("GenomicsAgent Bedrock Agent Testing Suite")
    logger.info("Testing autonomous genomics analysis capabilities")
    
    try:
        tester = GenomicsBedrockAgentTester()
        success = tester.run_all_tests()
        
        if success:
            logger.info("\n🎉 All tests passed! GenomicsAgent Bedrock Agent is ready.")
            return True
        else:
            logger.error("\n❌ Some tests failed. Please review the test report.")
            return False
            
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)