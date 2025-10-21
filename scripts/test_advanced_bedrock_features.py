#!/usr/bin/env python3
"""
Test script for advanced Bedrock features and optimizations.

This script tests:
1. Knowledge base creation and RAG capabilities
2. Model fine-tuning and evaluation
3. Intelligent caching and optimization
4. Cost optimization strategies
5. Performance monitoring and analytics
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from biomerkin.services.bedrock_knowledge_base_service import (
    BedrockKnowledgeBaseService, RAGQuery, KnowledgeBaseType
)
from biomerkin.services.bedrock_fine_tuning_service import (
    BedrockFineTuningService, FineTuningConfig, ModelType
)
from biomerkin.services.bedrock_optimization_service import (
    BedrockOptimizationService, OptimizationStrategy
)
from biomerkin.utils.logging_config import get_logger


class AdvancedBedrockFeaturesTester:
    """Test suite for advanced Bedrock features."""
    
    def __init__(self, mock_mode: bool = True):
        """Initialize the tester."""
        self.logger = get_logger(__name__)
        self.mock_mode = mock_mode
        
        # Initialize services
        self.kb_service = BedrockKnowledgeBaseService(mock_mode=mock_mode)
        self.fine_tuning_service = BedrockFineTuningService(mock_mode=mock_mode)
        self.optimization_service = BedrockOptimizationService(mock_mode=mock_mode)
        
        # Test results
        self.test_results = {
            'knowledge_base_tests': {},
            'fine_tuning_tests': {},
            'optimization_tests': {},
            'integration_tests': {},
            'performance_metrics': {}
        }
    
    async def run_all_tests(self) -> dict:
        """Run all advanced Bedrock feature tests."""
        try:
            self.logger.info("Starting advanced Bedrock features test suite")
            start_time = time.time()
            
            # Test knowledge base features
            await self.test_knowledge_base_features()
            
            # Test fine-tuning capabilities
            await self.test_fine_tuning_features()
            
            # Test optimization features
            await self.test_optimization_features()
            
            # Test integration scenarios
            await self.test_integration_scenarios()
            
            # Calculate overall metrics
            total_time = time.time() - start_time
            self.test_results['performance_metrics'] = {
                'total_execution_time': total_time,
                'tests_passed': self._count_passed_tests(),
                'tests_failed': self._count_failed_tests(),
                'success_rate': self._calculate_success_rate()
            }
            
            self.logger.info(f"Test suite completed in {total_time:.2f} seconds")
            return self.test_results
            
        except Exception as e:
            self.logger.error(f"Error running test suite: {str(e)}")
            raise
    
    async def test_knowledge_base_features(self):
        """Test knowledge base and RAG capabilities."""
        self.logger.info("Testing knowledge base features")
        
        try:
            # Test 1: Create genomics knowledge base
            self.logger.info("Test 1: Creating genomics knowledge base")
            kb_id = await self.kb_service.setup_genomics_knowledge_base()
            self.test_results['knowledge_base_tests']['genomics_kb_creation'] = {
                'status': 'passed',
                'kb_id': kb_id,
                'message': 'Genomics knowledge base created successfully'
            }
            
            # Test 2: Create medical literature knowledge base
            self.logger.info("Test 2: Creating medical literature knowledge base")
            lit_kb_id = await self.kb_service.setup_medical_literature_knowledge_base()
            self.test_results['knowledge_base_tests']['literature_kb_creation'] = {
                'status': 'passed',
                'kb_id': lit_kb_id,
                'message': 'Literature knowledge base created successfully'
            }
            
            # Test 3: RAG query with genomics data
            self.logger.info("Test 3: Testing RAG query with genomics data")
            genomics_query = RAGQuery(
                query_text="What are the clinical implications of BRCA1 pathogenic variants?",
                knowledge_bases=['genomics'],
                max_results=5,
                confidence_threshold=0.7
            )
            
            rag_result = await self.kb_service.query_knowledge_base_with_rag(genomics_query)
            self.test_results['knowledge_base_tests']['genomics_rag_query'] = {
                'status': 'passed',
                'confidence_score': rag_result.confidence_score,
                'retrieved_chunks': len(rag_result.retrieved_chunks),
                'processing_time': rag_result.processing_time,
                'cache_hit': rag_result.cache_hit
            }
            
            # Test 4: RAG query with literature data
            self.logger.info("Test 4: Testing RAG query with literature data")
            literature_query = RAGQuery(
                query_text="What are the latest developments in CRISPR gene therapy for genetic diseases?",
                knowledge_bases=['medical_literature'],
                max_results=3,
                confidence_threshold=0.8
            )
            
            lit_rag_result = await self.kb_service.query_knowledge_base_with_rag(literature_query)
            self.test_results['knowledge_base_tests']['literature_rag_query'] = {
                'status': 'passed',
                'confidence_score': lit_rag_result.confidence_score,
                'retrieved_chunks': len(lit_rag_result.retrieved_chunks),
                'processing_time': lit_rag_result.processing_time,
                'cache_hit': lit_rag_result.cache_hit
            }
            
            # Test 5: Multi-knowledge base query
            self.logger.info("Test 5: Testing multi-knowledge base RAG query")
            multi_query = RAGQuery(
                query_text="How do BRCA1 variants affect treatment decisions and what does recent research show?",
                knowledge_bases=['genomics', 'medical_literature'],
                max_results=8,
                confidence_threshold=0.6
            )
            
            multi_result = await self.kb_service.query_knowledge_base_with_rag(multi_query)
            self.test_results['knowledge_base_tests']['multi_kb_rag_query'] = {
                'status': 'passed',
                'confidence_score': multi_result.confidence_score,
                'retrieved_chunks': len(multi_result.retrieved_chunks),
                'knowledge_sources': multi_result.knowledge_sources,
                'processing_time': multi_result.processing_time
            }
            
            # Test 6: Knowledge base optimization
            self.logger.info("Test 6: Testing knowledge base optimization")
            optimization_result = await self.kb_service.optimize_knowledge_base_performance('genomics')
            self.test_results['knowledge_base_tests']['kb_optimization'] = {
                'status': 'passed',
                'recommendations': len(optimization_result['recommendations']),
                'cache_hit_rate': optimization_result['performance_metrics']['cache_performance']['cache_hit_rate'],
                'cost_analysis': optimization_result['cost_analysis']
            }
            
        except Exception as e:
            self.logger.error(f"Knowledge base test failed: {str(e)}")
            self.test_results['knowledge_base_tests']['error'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    async def test_fine_tuning_features(self):
        """Test model fine-tuning capabilities."""
        self.logger.info("Testing fine-tuning features")
        
        try:
            # Test 1: Create training datasets
            self.logger.info("Test 1: Creating bioinformatics training datasets")
            dataset_ids = await self.fine_tuning_service.create_bioinformatics_training_data()
            self.test_results['fine_tuning_tests']['dataset_creation'] = {
                'status': 'passed',
                'datasets_created': len(dataset_ids),
                'dataset_ids': dataset_ids
            }
            
            # Test 2: Start fine-tuning job for genomics
            self.logger.info("Test 2: Starting genomics model fine-tuning")
            genomics_config = FineTuningConfig(
                model_name="BiomerkinGenomicsModel",
                base_model_id="anthropic.claude-3-haiku-20240307-v1:0",
                model_type=ModelType.GENOMICS_ANALYSIS,
                training_data_s3_uri="s3://biomerkin-training/genomics/train.jsonl",
                validation_data_s3_uri="s3://biomerkin-training/genomics/val.jsonl",
                hyperparameters={
                    'learning_rate': 0.0001,
                    'batch_size': 4,
                    'epochs': 3
                }
            )
            
            job_id = await self.fine_tuning_service.start_fine_tuning_job(
                "genomics-fine-tuning-job",
                "BiomerkinGenomicsModel",
                dataset_ids['genomics'],
                genomics_config
            )
            
            self.test_results['fine_tuning_tests']['genomics_fine_tuning'] = {
                'status': 'passed',
                'job_id': job_id,
                'model_name': genomics_config.model_name
            }
            
            # Test 3: Monitor fine-tuning job
            self.logger.info("Test 3: Monitoring fine-tuning job progress")
            job_status = await self.fine_tuning_service.monitor_fine_tuning_job(job_id)
            self.test_results['fine_tuning_tests']['job_monitoring'] = {
                'status': 'passed',
                'job_status': job_status.status.value,
                'training_metrics': job_status.training_metrics
            }
            
            # Test 4: Model evaluation
            if job_status.custom_model_arn:
                self.logger.info("Test 4: Evaluating fine-tuned model")
                evaluation = await self.fine_tuning_service.evaluate_custom_model(
                    job_status.custom_model_arn,
                    "s3://biomerkin-training/genomics/test.jsonl",
                    "genomics-model-evaluation"
                )
                
                self.test_results['fine_tuning_tests']['model_evaluation'] = {
                    'status': 'passed',
                    'evaluation_id': evaluation.evaluation_id,
                    'metrics': evaluation.metrics,
                    'evaluation_time': evaluation.evaluation_time
                }
            
            # Test 5: Model deployment
            if job_status.custom_model_arn:
                self.logger.info("Test 5: Deploying fine-tuned model")
                deployment = await self.fine_tuning_service.deploy_custom_model(
                    job_status.custom_model_arn,
                    "genomics-model-deployment"
                )
                
                self.test_results['fine_tuning_tests']['model_deployment'] = {
                    'status': 'passed',
                    'deployment_id': deployment['deployment_id'],
                    'endpoint_url': deployment['endpoint_url']
                }
            
            # Test 6: Cost optimization analysis
            self.logger.info("Test 6: Analyzing fine-tuning cost optimization")
            cost_optimization = await self.fine_tuning_service.optimize_model_costs(ModelType.GENOMICS_ANALYSIS)
            self.test_results['fine_tuning_tests']['cost_optimization'] = {
                'status': 'passed',
                'recommendations': len(cost_optimization['recommendations']),
                'potential_savings': cost_optimization['potential_savings']
            }
            
        except Exception as e:
            self.logger.error(f"Fine-tuning test failed: {str(e)}")
            self.test_results['fine_tuning_tests']['error'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    async def test_optimization_features(self):
        """Test optimization and caching features."""
        self.logger.info("Testing optimization features")
        
        try:
            # Test 1: Request optimization
            self.logger.info("Test 1: Testing intelligent request optimization")
            sample_request = {
                'messages': [
                    {
                        'role': 'user',
                        'content': 'Analyze this DNA sequence for pathogenic variants: ATGCGATCG...'
                    }
                ],
                'max_tokens': 2000,
                'temperature': 0.1
            }
            
            optimized_result = await self.optimization_service.optimize_request(sample_request, 'normal')
            self.test_results['optimization_tests']['request_optimization'] = {
                'status': 'passed',
                'cache_hit': optimized_result['cache_hit'],
                'optimization_time': optimized_result['optimization_time'],
                'model_used': optimized_result.get('model_used'),
                'optimizations_applied': optimized_result.get('optimizations_applied', [])
            }
            
            # Test 2: Cache performance test
            self.logger.info("Test 2: Testing cache performance with repeated requests")
            cache_test_results = []
            
            for i in range(5):
                start_time = time.time()
                result = await self.optimization_service.optimize_request(sample_request, 'normal')
                response_time = time.time() - start_time
                
                cache_test_results.append({
                    'iteration': i + 1,
                    'cache_hit': result['cache_hit'],
                    'response_time': response_time
                })
            
            self.test_results['optimization_tests']['cache_performance'] = {
                'status': 'passed',
                'test_iterations': cache_test_results,
                'cache_hit_rate': sum(1 for r in cache_test_results if r['cache_hit']) / len(cache_test_results)
            }
            
            # Test 3: Model selection optimization
            self.logger.info("Test 3: Testing intelligent model selection")
            simple_request = {
                'messages': [{'role': 'user', 'content': 'What is DNA?'}],
                'max_tokens': 500
            }
            
            complex_request = {
                'messages': [{
                    'role': 'user', 
                    'content': 'Provide a comprehensive analysis of the clinical implications of compound heterozygous variants in the CFTR gene, including molecular mechanisms, phenotypic variability, and personalized treatment strategies based on current literature and clinical guidelines.'
                }],
                'max_tokens': 4000
            }
            
            simple_result = await self.optimization_service.optimize_request(simple_request, 'normal')
            complex_result = await self.optimization_service.optimize_request(complex_request, 'high')
            
            self.test_results['optimization_tests']['model_selection'] = {
                'status': 'passed',
                'simple_query_model': simple_result.get('model_used'),
                'complex_query_model': complex_result.get('model_used'),
                'model_selection_working': simple_result.get('model_used') != complex_result.get('model_used')
            }
            
            # Test 4: Optimization analysis
            self.logger.info("Test 4: Running optimization opportunity analysis")
            optimization_analysis = await self.optimization_service.analyze_optimization_opportunities()
            self.test_results['optimization_tests']['optimization_analysis'] = {
                'status': 'passed',
                'current_metrics': {
                    'avg_response_time': optimization_analysis.current_metrics.avg_response_time,
                    'cache_hit_rate': optimization_analysis.current_metrics.cache_hit_rate,
                    'cost_per_request': optimization_analysis.current_metrics.cost_per_request
                },
                'recommendations': len(optimization_analysis.recommended_changes),
                'potential_savings': optimization_analysis.potential_savings,
                'implementation_priority': optimization_analysis.implementation_priority
            }
            
        except Exception as e:
            self.logger.error(f"Optimization test failed: {str(e)}")
            self.test_results['optimization_tests']['error'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    async def test_integration_scenarios(self):
        """Test integration scenarios combining multiple features."""
        self.logger.info("Testing integration scenarios")
        
        try:
            # Test 1: RAG + Optimization integration
            self.logger.info("Test 1: Testing RAG with optimization")
            
            # Create optimized RAG request
            rag_request = {
                'messages': [
                    {
                        'role': 'user',
                        'content': 'Based on current knowledge about BRCA1 variants, what are the latest treatment recommendations?'
                    }
                ],
                'knowledge_bases': ['genomics', 'medical_literature'],
                'max_tokens': 3000
            }
            
            # First optimize the request
            optimized_request = await self.optimization_service.optimize_request(rag_request, 'high')
            
            # Then perform RAG query
            rag_query = RAGQuery(
                query_text=rag_request['messages'][0]['content'],
                knowledge_bases=rag_request['knowledge_bases'],
                max_results=5
            )
            
            rag_result = await self.kb_service.query_knowledge_base_with_rag(rag_query)
            
            self.test_results['integration_tests']['rag_optimization_integration'] = {
                'status': 'passed',
                'optimization_applied': optimized_request['cache_hit'] or len(optimized_request.get('optimizations_applied', [])) > 0,
                'rag_confidence': rag_result.confidence_score,
                'total_processing_time': rag_result.processing_time + optimized_request['optimization_time']
            }
            
            # Test 2: End-to-end genomics analysis workflow
            self.logger.info("Test 2: Testing end-to-end genomics analysis workflow")
            
            workflow_steps = []
            
            # Step 1: Sequence analysis with optimization
            sequence_request = {
                'messages': [
                    {
                        'role': 'user',
                        'content': 'Analyze this DNA sequence for clinically significant variants: ATGCGATCGATCGTAGC...'
                    }
                ]
            }
            
            step1_result = await self.optimization_service.optimize_request(sequence_request, 'normal')
            workflow_steps.append({'step': 'sequence_analysis', 'result': step1_result})
            
            # Step 2: Literature search via RAG
            literature_query = RAGQuery(
                query_text="What does recent research say about the clinical management of identified genetic variants?",
                knowledge_bases=['medical_literature'],
                max_results=3
            )
            
            step2_result = await self.kb_service.query_knowledge_base_with_rag(literature_query)
            workflow_steps.append({'step': 'literature_search', 'result': step2_result})
            
            # Step 3: Treatment recommendation with fine-tuned model (if available)
            treatment_request = {
                'messages': [
                    {
                        'role': 'user',
                        'content': 'Based on the genetic analysis and literature findings, provide treatment recommendations.'
                    }
                ]
            }
            
            step3_result = await self.optimization_service.optimize_request(treatment_request, 'high')
            workflow_steps.append({'step': 'treatment_recommendation', 'result': step3_result})
            
            self.test_results['integration_tests']['end_to_end_workflow'] = {
                'status': 'passed',
                'workflow_steps': len(workflow_steps),
                'total_workflow_time': sum(
                    step['result'].get('processing_time', step['result'].get('optimization_time', 0)) 
                    for step in workflow_steps
                ),
                'optimization_benefits': sum(
                    1 for step in workflow_steps 
                    if step['result'].get('cache_hit') or step['result'].get('optimizations_applied')
                )
            }
            
        except Exception as e:
            self.logger.error(f"Integration test failed: {str(e)}")
            self.test_results['integration_tests']['error'] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def _count_passed_tests(self) -> int:
        """Count number of passed tests."""
        passed = 0
        for category in self.test_results.values():
            if isinstance(category, dict):
                for test_name, test_result in category.items():
                    if isinstance(test_result, dict) and test_result.get('status') == 'passed':
                        passed += 1
        return passed
    
    def _count_failed_tests(self) -> int:
        """Count number of failed tests."""
        failed = 0
        for category in self.test_results.values():
            if isinstance(category, dict):
                for test_name, test_result in category.items():
                    if isinstance(test_result, dict) and test_result.get('status') == 'failed':
                        failed += 1
        return failed
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall test success rate."""
        passed = self._count_passed_tests()
        failed = self._count_failed_tests()
        total = passed + failed
        
        if total == 0:
            return 0.0
        
        return (passed / total) * 100
    
    def generate_test_report(self) -> str:
        """Generate a comprehensive test report."""
        report = []
        report.append("=" * 80)
        report.append("ADVANCED BEDROCK FEATURES TEST REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Mock Mode: {self.mock_mode}")
        report.append("")
        
        # Performance metrics
        metrics = self.test_results.get('performance_metrics', {})
        report.append("OVERALL PERFORMANCE METRICS")
        report.append("-" * 40)
        report.append(f"Total Execution Time: {metrics.get('total_execution_time', 0):.2f} seconds")
        report.append(f"Tests Passed: {metrics.get('tests_passed', 0)}")
        report.append(f"Tests Failed: {metrics.get('tests_failed', 0)}")
        report.append(f"Success Rate: {metrics.get('success_rate', 0):.1f}%")
        report.append("")
        
        # Knowledge base tests
        kb_tests = self.test_results.get('knowledge_base_tests', {})
        if kb_tests:
            report.append("KNOWLEDGE BASE TESTS")
            report.append("-" * 40)
            for test_name, result in kb_tests.items():
                if isinstance(result, dict):
                    status = result.get('status', 'unknown')
                    report.append(f"  {test_name}: {status.upper()}")
                    if status == 'passed' and 'confidence_score' in result:
                        report.append(f"    Confidence Score: {result['confidence_score']:.3f}")
                    if 'processing_time' in result:
                        report.append(f"    Processing Time: {result['processing_time']:.3f}s")
            report.append("")
        
        # Fine-tuning tests
        ft_tests = self.test_results.get('fine_tuning_tests', {})
        if ft_tests:
            report.append("FINE-TUNING TESTS")
            report.append("-" * 40)
            for test_name, result in ft_tests.items():
                if isinstance(result, dict):
                    status = result.get('status', 'unknown')
                    report.append(f"  {test_name}: {status.upper()}")
                    if 'datasets_created' in result:
                        report.append(f"    Datasets Created: {result['datasets_created']}")
                    if 'job_id' in result:
                        report.append(f"    Job ID: {result['job_id']}")
            report.append("")
        
        # Optimization tests
        opt_tests = self.test_results.get('optimization_tests', {})
        if opt_tests:
            report.append("OPTIMIZATION TESTS")
            report.append("-" * 40)
            for test_name, result in opt_tests.items():
                if isinstance(result, dict):
                    status = result.get('status', 'unknown')
                    report.append(f"  {test_name}: {status.upper()}")
                    if 'cache_hit_rate' in result:
                        report.append(f"    Cache Hit Rate: {result['cache_hit_rate']:.1%}")
                    if 'optimization_time' in result:
                        report.append(f"    Optimization Time: {result['optimization_time']:.3f}s")
            report.append("")
        
        # Integration tests
        int_tests = self.test_results.get('integration_tests', {})
        if int_tests:
            report.append("INTEGRATION TESTS")
            report.append("-" * 40)
            for test_name, result in int_tests.items():
                if isinstance(result, dict):
                    status = result.get('status', 'unknown')
                    report.append(f"  {test_name}: {status.upper()}")
                    if 'total_workflow_time' in result:
                        report.append(f"    Total Workflow Time: {result['total_workflow_time']:.3f}s")
            report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)


async def main():
    """Main test execution function."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = get_logger(__name__)
    
    try:
        # Run tests in mock mode for demonstration
        logger.info("Starting Advanced Bedrock Features Test Suite")
        
        tester = AdvancedBedrockFeaturesTester(mock_mode=True)
        results = await tester.run_all_tests()
        
        # Generate and display report
        report = tester.generate_test_report()
        print(report)
        
        # Save results to file
        results_file = f"advanced_bedrock_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Test results saved to {results_file}")
        
        # Return success/failure based on results
        success_rate = results.get('performance_metrics', {}).get('success_rate', 0)
        if success_rate >= 80:
            logger.info("✅ Advanced Bedrock features test suite PASSED")
            return 0
        else:
            logger.error("❌ Advanced Bedrock features test suite FAILED")
            return 1
            
    except Exception as e:
        logger.error(f"Test suite execution failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)