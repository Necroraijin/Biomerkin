#!/usr/bin/env python3
"""
Test script for ProteomicsAgent AWS Bedrock Agent.
This script tests the autonomous proteomics analysis capabilities.
"""

import boto3
import json
import logging
import time
import sys
from typing import Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProteomicsAgentTester:
    """Tests the ProteomicsAgent Bedrock Agent functionality."""
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize the tester."""
        self.region = region
        self.bedrock_runtime_client = boto3.client('bedrock-agent-runtime', region_name=region)
        
        # Load deployment info
        try:
            with open('proteomics_agent_deployment_info.json', 'r') as f:
                self.deployment_info = json.load(f)
                self.agent_id = self.deployment_info['bedrock_agent']['agent_id']
                logger.info(f"Loaded ProteomicsAgent ID: {self.agent_id}")
        except FileNotFoundError:
            logger.error("Deployment info not found. Please run deployment script first.")
            sys.exit(1)
    
    def test_protein_analysis(self) -> bool:
        """Test comprehensive protein analysis."""
        logger.info("Testing comprehensive protein analysis...")
        
        # Sample protein sequence (human p53 tumor suppressor)
        test_sequence = """
        MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGP
        DEAPRMPEAAPPVAPAPAAPTPAAPAPAPSWPLSSSVPSQKTYQGSYGFRLGFLHSGTAK
        SVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIYKQSQHMTEVVRRCPHHE
        RCSDSDGLAPPQHLIRVEGNLRVEYLDDRNTFRHSVVVPYEPPEVGSDCTTIHYNYMCNS
        SCMGGMNRRPILTIITLEDSSGNLLGRNSFEVRVCACPGRDRRTEEENLRKKGEPHHELP
        PGSTKRALPNNTSSSPQPKKKPLDGEYFTLQIRGRERFEMFRELNEALELKDAQAGKEPG
        GSRAHSSHLKSKKGQSTSRHKKLMFKTEGPDSD
        """.replace('\n', '').replace(' ', '')
        
        prompt = f"""
        Please analyze this protein sequence for comprehensive proteomics analysis:
        
        Protein Sequence: {test_sequence}
        
        I need you to:
        1. Predict the protein structure and analyze structural features
        2. Identify functional domains and their significance
        3. Predict protein-protein interactions
        4. Assess the clinical significance and disease associations
        5. Evaluate the druggability and therapeutic potential
        6. Provide autonomous insights with reasoning
        
        Please use your autonomous proteomics analysis capabilities to provide a comprehensive assessment.
        """
        
        try:
            response = self.bedrock_runtime_client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId='TSTALIASID',
                sessionId=f'test-session-{int(time.time())}',
                inputText=prompt
            )
            
            # Process response
            response_text = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')
            
            logger.info("✅ Protein analysis test completed")
            logger.info(f"Response length: {len(response_text)} characters")
            
            # Check for key capabilities in response
            capabilities_found = []
            if 'structure' in response_text.lower():
                capabilities_found.append('Structure Analysis')
            if 'domain' in response_text.lower():
                capabilities_found.append('Domain Identification')
            if 'interaction' in response_text.lower():
                capabilities_found.append('Interaction Prediction')
            if 'clinical' in response_text.lower():
                capabilities_found.append('Clinical Assessment')
            if 'drug' in response_text.lower():
                capabilities_found.append('Druggability Assessment')
            
            logger.info(f"Capabilities demonstrated: {', '.join(capabilities_found)}")
            
            return len(capabilities_found) >= 3
            
        except Exception as e:
            logger.error(f"❌ Protein analysis test failed: {str(e)}")
            return False
    
    def test_structure_prediction(self) -> bool:
        """Test protein structure prediction."""
        logger.info("Testing protein structure prediction...")
        
        # Sample sequence for structure prediction
        test_sequence = "MKWVTFISLLLLFSSAYSRGVFRRDTHKSEIAHRFKDLGEEHFKGLVLIAFSQYLQQCPFDEHVKLVNELTEFAKTCVADESHAGCEKSLHTLFGDELCKVASLRETYGDMADCCEKQEPERNECFLSHKDDSPDLPKLKPDPNTLCDEFKADEKKFWGKYLYEIARRHPYFYAPELLYYANKYNGVFQECCQAEDKGACLLPKIETMREKVLASSARQRLRCASIQKFGERALKAWSVARLSQKFPKAEFVEVTKLVTDLTKVHKECCHGDLLECADDRADLAKYICDNQDTISSKLKECCDKPLLEKSHCIAEVEKDAIPENLPPLTADFAEDKDVCKNYQEAKDAFLGSFLYEYSRRHPEYAVSVLLRLAKEYEATLEECCAKDDPHACYSTVFDKLKHLVDEPQNLIKQNCDQFEKLGEYGFQNALIVRYTRKVPQVSTPTLVEVSRSLGKVGTRCCTKPESERMPCTEDYLSLILNRLCVLHEKTPVSEKVTKCCSGSLVERRPCFSALTPDETYVPKAFDEKLFTFHADICTLPDTEKQIKKQTALVELLKHKPKATEEQLKTVMENFVAFVDKCCAADDKEACFAVEGPKLVVSTQTALA"
        
        prompt = f"""
        Please predict the structure of this protein sequence and provide detailed analysis:
        
        Protein Sequence: {test_sequence}
        
        I need you to:
        1. Predict the secondary and tertiary structure
        2. Identify structural motifs and domains
        3. Assess structural stability and quality
        4. Predict binding sites and functional regions
        5. Evaluate the structure for drug design potential
        
        Use your autonomous structure prediction capabilities with reasoning.
        """
        
        try:
            response = self.bedrock_runtime_client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId='TSTALIASID',
                sessionId=f'test-session-structure-{int(time.time())}',
                inputText=prompt
            )
            
            # Process response
            response_text = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')
            
            logger.info("✅ Structure prediction test completed")
            
            # Check for structure-related content
            structure_terms = ['secondary structure', 'tertiary', 'alpha helix', 'beta sheet', 'binding site', 'fold']
            found_terms = [term for term in structure_terms if term in response_text.lower()]
            
            logger.info(f"Structure terms found: {', '.join(found_terms)}")
            
            return len(found_terms) >= 2
            
        except Exception as e:
            logger.error(f"❌ Structure prediction test failed: {str(e)}")
            return False
    
    def test_function_analysis(self) -> bool:
        """Test protein function analysis."""
        logger.info("Testing protein function analysis...")
        
        prompt = """
        Please analyze the function of the BRCA1 protein (breast cancer susceptibility protein 1).
        
        I need you to:
        1. Predict the biological functions and molecular mechanisms
        2. Identify functional domains and their roles
        3. Assess the clinical significance and disease associations
        4. Predict pathway involvement and regulatory mechanisms
        5. Evaluate therapeutic targeting opportunities
        
        Use your autonomous function analysis capabilities with detailed reasoning.
        """
        
        try:
            response = self.bedrock_runtime_client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId='TSTALIASID',
                sessionId=f'test-session-function-{int(time.time())}',
                inputText=prompt
            )
            
            # Process response
            response_text = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')
            
            logger.info("✅ Function analysis test completed")
            
            # Check for function-related content
            function_terms = ['dna repair', 'tumor suppressor', 'homologous recombination', 'cancer', 'brca1']
            found_terms = [term for term in function_terms if term in response_text.lower()]
            
            logger.info(f"Function terms found: {', '.join(found_terms)}")
            
            return len(found_terms) >= 2
            
        except Exception as e:
            logger.error(f"❌ Function analysis test failed: {str(e)}")
            return False
    
    def test_druggability_assessment(self) -> bool:
        """Test druggability assessment."""
        logger.info("Testing druggability assessment...")
        
        prompt = """
        Please assess the druggability of the human epidermal growth factor receptor 2 (HER2/ERBB2) protein.
        
        I need you to:
        1. Evaluate the protein as a therapeutic target
        2. Identify potential binding sites for drug development
        3. Assess the feasibility of different intervention strategies
        4. Analyze the competitive landscape and opportunities
        5. Provide recommendations for drug development approaches
        
        Use your autonomous druggability assessment capabilities with detailed reasoning.
        """
        
        try:
            response = self.bedrock_runtime_client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId='TSTALIASID',
                sessionId=f'test-session-drug-{int(time.time())}',
                inputText=prompt
            )
            
            # Process response
            response_text = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')
            
            logger.info("✅ Druggability assessment test completed")
            
            # Check for druggability-related content
            drug_terms = ['binding site', 'therapeutic target', 'drug development', 'inhibitor', 'antibody', 'small molecule']
            found_terms = [term for term in drug_terms if term in response_text.lower()]
            
            logger.info(f"Druggability terms found: {', '.join(found_terms)}")
            
            return len(found_terms) >= 2
            
        except Exception as e:
            logger.error(f"❌ Druggability assessment test failed: {str(e)}")
            return False
    
    def test_autonomous_reasoning(self) -> bool:
        """Test autonomous reasoning capabilities."""
        logger.info("Testing autonomous reasoning capabilities...")
        
        prompt = """
        I have a protein with the following characteristics:
        - Contains a kinase domain
        - Shows high expression in cancer cells
        - Has multiple phosphorylation sites
        - Interacts with cell cycle proteins
        
        Please use your autonomous reasoning to:
        1. Predict the likely biological function and cellular role
        2. Assess the clinical significance and disease associations
        3. Evaluate the therapeutic potential and intervention strategies
        4. Provide step-by-step reasoning for your conclusions
        5. Suggest next steps for research and development
        
        Demonstrate your autonomous decision-making and reasoning capabilities.
        """
        
        try:
            response = self.bedrock_runtime_client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId='TSTALIASID',
                sessionId=f'test-session-reasoning-{int(time.time())}',
                inputText=prompt
            )
            
            # Process response
            response_text = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        response_text += chunk['bytes'].decode('utf-8')
            
            logger.info("✅ Autonomous reasoning test completed")
            
            # Check for reasoning indicators
            reasoning_terms = ['reasoning', 'analysis', 'conclusion', 'evidence', 'prediction', 'assessment']
            found_terms = [term for term in reasoning_terms if term in response_text.lower()]
            
            logger.info(f"Reasoning indicators found: {', '.join(found_terms)}")
            
            return len(found_terms) >= 3
            
        except Exception as e:
            logger.error(f"❌ Autonomous reasoning test failed: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """Run all ProteomicsAgent tests."""
        logger.info("Starting comprehensive ProteomicsAgent testing...")
        logger.info("=" * 60)
        
        tests = {
            'protein_analysis': self.test_protein_analysis,
            'structure_prediction': self.test_structure_prediction,
            'function_analysis': self.test_function_analysis,
            'druggability_assessment': self.test_druggability_assessment,
            'autonomous_reasoning': self.test_autonomous_reasoning
        }
        
        results = {}
        
        for test_name, test_func in tests.items():
            logger.info(f"\n--- Running {test_name.replace('_', ' ').title()} Test ---")
            try:
                results[test_name] = test_func()
                time.sleep(2)  # Brief pause between tests
            except Exception as e:
                logger.error(f"Test {test_name} failed with exception: {str(e)}")
                results[test_name] = False
        
        return results
    
    def generate_test_report(self, results: Dict[str, bool]) -> None:
        """Generate a comprehensive test report."""
        logger.info("\n" + "=" * 60)
        logger.info("PROTEOMICS AGENT TEST REPORT")
        logger.info("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        success_rate = (passed_tests / total_tests) * 100
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed Tests: {passed_tests}")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        
        logger.info("\nDetailed Results:")
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"  {test_name.replace('_', ' ').title()}: {status}")
        
        logger.info(f"\nOverall Status: {'✅ SUCCESS' if success_rate >= 80 else '⚠️ PARTIAL' if success_rate >= 60 else '❌ FAILED'}")
        
        if success_rate >= 80:
            logger.info("\n🎉 ProteomicsAgent Bedrock Agent is working excellently!")
            logger.info("Autonomous proteomics capabilities verified:")
            logger.info("  • Comprehensive protein analysis")
            logger.info("  • Structure prediction and analysis")
            logger.info("  • Function annotation and assessment")
            logger.info("  • Druggability evaluation")
            logger.info("  • Autonomous reasoning and decision-making")
        elif success_rate >= 60:
            logger.info("\n⚠️ ProteomicsAgent is partially functional")
            logger.info("Some capabilities may need attention")
        else:
            logger.info("\n❌ ProteomicsAgent needs troubleshooting")
            logger.info("Multiple capabilities are not working correctly")


def main():
    """Main testing function."""
    logger.info("AWS Bedrock ProteomicsAgent Testing")
    logger.info("=" * 50)
    
    try:
        # Initialize tester
        tester = ProteomicsAgentTester()
        
        # Run all tests
        results = tester.run_all_tests()
        
        # Generate report
        tester.generate_test_report(results)
        
        # Return success if most tests pass
        success_rate = (sum(results.values()) / len(results)) * 100
        return success_rate >= 80
        
    except Exception as e:
        logger.error(f"Testing failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)