#!/usr/bin/env python3
"""
Load testing tool for Biomerkin multi-agent system.
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import Dict, Any, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from biomerkin.services.orchestrator import WorkflowOrchestrator
from biomerkin.services.enhanced_orchestrator import get_enhanced_orchestrator
from biomerkin.agents.genomics_agent import GenomicsAgent


class LoadTester:
    """Comprehensive load testing for Biomerkin system."""
    
    def __init__(self):
        self.results = {}
        self.test_data = self._generate_test_data()
    
    def _generate_test_data(self) -> Dict[str, Any]:
        """Generate test data for load testing."""
        return {
            'small_sequence': 'ATGCGTAAGGCTTAGCTAGC' * 5,  # 100 bases
            'medium_sequence': 'ATGCGTAAGGCTTAGCTAGC' * 50,  # 1000 bases
            'large_sequence': 'ATGCGTAAGGCTTAGCTAGC' * 500,  # 10000 bases
            'protein_sequence': 'MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG',
            'search_terms': ['BRCA1', 'cancer', 'genomics', 'mutation', 'therapy'],
            'drug_targets': {
                'genes': ['BRCA1', 'TP53', 'EGFR'],
                'proteins': ['BRCA1_protein', 'p53_protein'],
                'conditions': ['breast cancer', 'lung cancer']
            }
        }
    
    def test_agent_load(self, agent_class, test_data: Dict[str, Any], 
                       num_requests: int = 10, concurrency: int = 5) -> Dict[str, Any]:
        """Test load on individual agent."""
        
        def execute_agent_request(request_id: int) -> Dict[str, Any]:
            """Execute single agent request."""
            start_time = time.time()
            
            try:
                agent = agent_class()
                result = agent.execute_with_error_handling(test_data)
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
                result = None
            
            end_time = time.time()
            
            return {
                'request_id': request_id,
                'success': success,
                'execution_time': end_time - start_time,
                'error': error,
                'timestamp': datetime.now().isoformat()
            }
        
        print(f"   Testing {agent_class.__name__} with {num_requests} requests, {concurrency} concurrent...")
        
        start_time = time.time()
        
        # Execute requests with controlled concurrency
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(execute_agent_request, i) for i in range(num_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        execution_times = [r['execution_time'] for r in successful_results]
        
        return {
            'agent_name': agent_class.__name__,
            'total_requests': num_requests,
            'successful_requests': len(successful_results),
            'failed_requests': len(failed_results),
            'success_rate': len(successful_results) / num_requests,
            'total_time': total_time,
            'throughput': num_requests / total_time,
            'avg_execution_time': statistics.mean(execution_times) if execution_times else 0,
            'min_execution_time': min(execution_times) if execution_times else 0,
            'max_execution_time': max(execution_times) if execution_times else 0,
            'p95_execution_time': statistics.quantiles(execution_times, n=20)[18] if len(execution_times) > 5 else 0,
            'errors': [r['error'] for r in failed_results if r['error']],
            'concurrency_level': concurrency
        }
    
    def test_orchestrator_load(self, num_workflows: int = 20, 
                              concurrency: int = 5) -> Dict[str, Any]:
        """Test load on workflow orchestrator."""
        
        def create_workflow(workflow_id: int) -> Dict[str, Any]:
            """Create single workflow."""
            start_time = time.time()
            
            try:
                orchestrator = WorkflowOrchestrator()
                workflow_id_str = orchestrator.start_analysis(f"test_sequence_{workflow_id}.fasta")
                
                # Get status
                status = orchestrator.get_analysis_status(workflow_id_str)
                
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
                workflow_id_str = None
                status = None
            
            end_time = time.time()
            
            return {
                'workflow_id': workflow_id,
                'workflow_id_str': workflow_id_str,
                'success': success,
                'execution_time': end_time - start_time,
                'error': error,
                'status': status.status.value if status else None,
                'timestamp': datetime.now().isoformat()
            }
        
        print(f"   Testing WorkflowOrchestrator with {num_workflows} workflows, {concurrency} concurrent...")
        
        start_time = time.time()
        
        # Execute workflow creation with controlled concurrency
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(create_workflow, i) for i in range(num_workflows)]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_results = [r for r in results if r['success']]
        failed_results = [r for r in results if not r['success']]
        
        execution_times = [r['execution_time'] for r in successful_results]
        
        return {
            'component': 'WorkflowOrchestrator',
            'total_workflows': num_workflows,
            'successful_workflows': len(successful_results),
            'failed_workflows': len(failed_results),
            'success_rate': len(successful_results) / num_workflows,
            'total_time': total_time,
            'throughput': num_workflows / total_time,
            'avg_execution_time': statistics.mean(execution_times) if execution_times else 0,
            'min_execution_time': min(execution_times) if execution_times else 0,
            'max_execution_time': max(execution_times) if execution_times else 0,
            'p95_execution_time': statistics.quantiles(execution_times, n=20)[18] if len(execution_times) > 5 else 0,
            'errors': [r['error'] for r in failed_results if r['error']],
            'concurrency_level': concurrency
        }
    
    def test_enhanced_orchestrator_load(self, num_requests: int = 10) -> Dict[str, Any]:
        """Test load on enhanced orchestrator."""
        
        print(f"   Testing Enhanced Orchestrator with {num_requests} status requests...")
        
        start_time = time.time()
        execution_times = []
        errors = []
        
        enhanced_orchestrator = get_enhanced_orchestrator()
        
        for i in range(num_requests):
            request_start = time.time()
            
            try:
                status = enhanced_orchestrator.get_enhanced_status()
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
                status = None
            
            request_end = time.time()
            execution_times.append(request_end - request_start)
            
            if error:
                errors.append(error)
        
        total_time = time.time() - start_time
        successful_requests = len([t for t in execution_times if t > 0]) - len(errors)
        
        return {
            'component': 'EnhancedOrchestrator',
            'total_requests': num_requests,
            'successful_requests': successful_requests,
            'failed_requests': len(errors),
            'success_rate': successful_requests / num_requests,
            'total_time': total_time,
            'throughput': num_requests / total_time,
            'avg_execution_time': statistics.mean(execution_times) if execution_times else 0,
            'min_execution_time': min(execution_times) if execution_times else 0,
            'max_execution_time': max(execution_times) if execution_times else 0,
            'errors': errors[:5]  # First 5 errors
        }
    
    def test_memory_under_load(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """Test memory usage under sustained load."""
        
        print(f"   Testing memory usage under load for {duration_seconds} seconds...")
        
        import psutil
        process = psutil.Process()
        
        memory_samples = []
        start_time = time.time()
        
        # Create agents and run continuous load
        agents = []
        
        while time.time() - start_time < duration_seconds:
            # Create new agent every few seconds
            if len(agents) < 10:
                agents.append(GenomicsAgent())
            
            # Execute some work
            try:
                agent = agents[len(agents) % len(agents)] if agents else GenomicsAgent()
                test_data = {
                    'sequence_data': self.test_data['medium_sequence'],
                    'analysis_type': 'basic'
                }
                agent.execute_with_error_handling(test_data)
            except:
                pass  # Ignore errors for memory test
            
            # Sample memory every 5 seconds
            if int(time.time() - start_time) % 5 == 0:
                memory_mb = process.memory_info().rss / 1024 / 1024
                memory_samples.append({
                    'timestamp': time.time() - start_time,
                    'memory_mb': memory_mb
                })
            
            time.sleep(1)  # Small delay
        
        return {
            'test_duration': duration_seconds,
            'memory_samples': memory_samples,
            'initial_memory_mb': memory_samples[0]['memory_mb'] if memory_samples else 0,
            'final_memory_mb': memory_samples[-1]['memory_mb'] if memory_samples else 0,
            'peak_memory_mb': max(s['memory_mb'] for s in memory_samples) if memory_samples else 0,
            'memory_growth_mb': (memory_samples[-1]['memory_mb'] - memory_samples[0]['memory_mb']) if len(memory_samples) > 1 else 0,
            'agents_created': len(agents)
        }
    
    def test_concurrent_scaling(self, max_concurrency: int = 16) -> Dict[str, Any]:
        """Test how system scales with increasing concurrency."""
        
        print(f"   Testing concurrent scaling up to {max_concurrency} workers...")
        
        scaling_results = {}
        
        for concurrency in [1, 2, 4, 8, 16]:
            if concurrency > max_concurrency:
                break
            
            print(f"     Testing concurrency level: {concurrency}")
            
            # Test with genomics agent
            agent_result = self.test_agent_load(
                GenomicsAgent,
                {'sequence_data': self.test_data['medium_sequence'], 'analysis_type': 'basic'},
                num_requests=concurrency * 2,  # 2 requests per worker
                concurrency=concurrency
            )
            
            scaling_results[f"concurrency_{concurrency}"] = {
                'concurrency_level': concurrency,
                'throughput': agent_result['throughput'],
                'avg_execution_time': agent_result['avg_execution_time'],
                'success_rate': agent_result['success_rate'],
                'total_time': agent_result['total_time']
            }
        
        # Calculate scaling efficiency
        baseline_throughput = scaling_results['concurrency_1']['throughput']
        
        for key, result in scaling_results.items():
            if key != 'concurrency_1':
                concurrency = result['concurrency_level']
                expected_throughput = baseline_throughput * concurrency
                actual_throughput = result['throughput']
                result['scaling_efficiency'] = actual_throughput / expected_throughput if expected_throughput > 0 else 0
        
        return scaling_results
    
    def run_comprehensive_load_test(self) -> Dict[str, Any]:
        """Run comprehensive load testing."""
        
        print("🚀 Starting Comprehensive Load Testing")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test individual agents
        print("\n🔬 Testing Individual Agents...")
        agent_results = {}
        
        # Test genomics agent with different data sizes
        for size_name, sequence in [('small', self.test_data['small_sequence']), 
                                   ('medium', self.test_data['medium_sequence']),
                                   ('large', self.test_data['large_sequence'])]:
            test_data = {'sequence_data': sequence, 'analysis_type': 'basic'}
            result = self.test_agent_load(GenomicsAgent, test_data, num_requests=10, concurrency=3)
            agent_results[f'genomics_{size_name}'] = result
        
        # Test orchestrator
        print("\n🎭 Testing Orchestrator...")
        orchestrator_result = self.test_orchestrator_load(num_workflows=15, concurrency=3)
        
        # Test enhanced orchestrator
        enhanced_result = self.test_enhanced_orchestrator_load(num_requests=20)
        
        # Test concurrent scaling
        print("\n⚡ Testing Concurrent Scaling...")
        scaling_result = self.test_concurrent_scaling(max_concurrency=8)
        
        # Test memory under load
        print("\n🧠 Testing Memory Under Load...")
        memory_result = self.test_memory_under_load(duration_seconds=30)
        
        total_time = time.time() - start_time
        
        # Compile results
        results = {
            'test_metadata': {
                'total_test_time': total_time,
                'timestamp': datetime.now().isoformat(),
                'test_version': '1.0.0'
            },
            'agent_load_tests': agent_results,
            'orchestrator_load_test': orchestrator_result,
            'enhanced_orchestrator_test': enhanced_result,
            'concurrent_scaling_test': scaling_result,
            'memory_load_test': memory_result
        }
        
        return results
    
    def generate_load_test_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate load test report with recommendations."""
        
        # Analyze results and generate recommendations
        recommendations = []
        
        # Agent performance analysis
        agent_results = results.get('agent_load_tests', {})
        for test_name, result in agent_results.items():
            if result['success_rate'] < 0.95:
                recommendations.append({
                    'component': test_name,
                    'issue': f"Low success rate: {result['success_rate']:.1%}",
                    'recommendation': 'Investigate error handling and increase timeout values',
                    'priority': 'high'
                })
            
            if result['avg_execution_time'] > 5.0:
                recommendations.append({
                    'component': test_name,
                    'issue': f"Slow execution: {result['avg_execution_time']:.2f}s average",
                    'recommendation': 'Optimize algorithm or increase Lambda memory allocation',
                    'priority': 'medium'
                })
        
        # Orchestrator analysis
        orch_result = results.get('orchestrator_load_test', {})
        if orch_result.get('success_rate', 0) < 0.9:
            recommendations.append({
                'component': 'orchestrator',
                'issue': f"Orchestrator success rate: {orch_result['success_rate']:.1%}",
                'recommendation': 'Improve error handling and add retry logic',
                'priority': 'high'
            })
        
        # Scaling analysis
        scaling_results = results.get('concurrent_scaling_test', {})
        poor_scaling = [k for k, v in scaling_results.items() 
                       if isinstance(v, dict) and v.get('scaling_efficiency', 1) < 0.7]
        
        if poor_scaling:
            recommendations.append({
                'component': 'concurrency',
                'issue': 'Poor scaling efficiency at higher concurrency levels',
                'recommendation': 'Implement connection pooling and optimize thread management',
                'priority': 'medium'
            })
        
        # Memory analysis
        memory_result = results.get('memory_load_test', {})
        if memory_result.get('memory_growth_mb', 0) > 100:
            recommendations.append({
                'component': 'memory',
                'issue': f"High memory growth: {memory_result['memory_growth_mb']:.1f}MB",
                'recommendation': 'Implement memory cleanup and optimize object lifecycle',
                'priority': 'high'
            })
        
        # Performance summary
        summary = {
            'total_tests_run': len(agent_results) + 3,  # agents + orchestrator + enhanced + scaling
            'overall_success_rate': statistics.mean([
                result.get('success_rate', 0) for result in agent_results.values()
            ] + [orch_result.get('success_rate', 0)]),
            'avg_throughput': statistics.mean([
                result.get('throughput', 0) for result in agent_results.values()
            ]),
            'recommendations_count': len(recommendations),
            'performance_grade': 'A' if len(recommendations) == 0 else 'B' if len(recommendations) <= 2 else 'C'
        }
        
        return {
            'summary': summary,
            'recommendations': recommendations,
            'detailed_analysis': {
                'best_performing_agent': max(agent_results.items(), 
                                           key=lambda x: x[1]['throughput'])[0] if agent_results else None,
                'slowest_agent': max(agent_results.items(), 
                                   key=lambda x: x[1]['avg_execution_time'])[0] if agent_results else None,
                'optimal_concurrency': self._find_optimal_concurrency(scaling_results),
                'memory_efficiency': 'good' if memory_result.get('memory_growth_mb', 0) < 50 else 'needs_improvement'
            }
        }
    
    def _find_optimal_concurrency(self, scaling_results: Dict[str, Any]) -> int:
        """Find optimal concurrency level from scaling test results."""
        
        best_efficiency = 0
        optimal_concurrency = 1
        
        for key, result in scaling_results.items():
            if isinstance(result, dict) and 'scaling_efficiency' in result:
                if result['scaling_efficiency'] > best_efficiency:
                    best_efficiency = result['scaling_efficiency']
                    optimal_concurrency = result['concurrency_level']
        
        return optimal_concurrency
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save load test results to file."""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"load_test_results_{timestamp}.json"
        
        filepath = Path("reports") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📊 Load test results saved to: {filepath}")
        return filepath
    
    def print_summary(self, results: Dict[str, Any], report: Dict[str, Any]):
        """Print load test summary."""
        
        print("\n" + "=" * 60)
        print("📊 LOAD TEST SUMMARY")
        print("=" * 60)
        
        summary = report['summary']
        print(f"\n🎯 Overall Performance:")
        print(f"   Tests Run: {summary['total_tests_run']}")
        print(f"   Success Rate: {summary['overall_success_rate']:.1%}")
        print(f"   Avg Throughput: {summary['avg_throughput']:.2f} ops/sec")
        print(f"   Performance Grade: {summary['performance_grade']}")
        
        # Agent performance
        agent_results = results.get('agent_load_tests', {})
        if agent_results:
            print(f"\n🔬 Agent Performance:")
            for test_name, result in agent_results.items():
                print(f"   {test_name:20}: {result['throughput']:.2f} ops/sec, "
                      f"{result['success_rate']:.1%} success, "
                      f"{result['avg_execution_time']:.3f}s avg")
        
        # Orchestrator performance
        orch_result = results.get('orchestrator_load_test', {})
        if orch_result:
            print(f"\n🎭 Orchestrator Performance:")
            print(f"   Throughput: {orch_result['throughput']:.2f} workflows/sec")
            print(f"   Success Rate: {orch_result['success_rate']:.1%}")
            print(f"   Avg Time: {orch_result['avg_execution_time']:.3f}s")
        
        # Scaling analysis
        detailed = report['detailed_analysis']
        print(f"\n⚡ Scaling Analysis:")
        print(f"   Optimal Concurrency: {detailed['optimal_concurrency']} workers")
        print(f"   Memory Efficiency: {detailed['memory_efficiency']}")
        
        # Recommendations
        recommendations = report['recommendations']
        if recommendations:
            print(f"\n💡 Recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations[:3], 1):  # Top 3
                print(f"   {i}. {rec['component']}: {rec['recommendation']}")
                print(f"      Priority: {rec['priority']}")
        
        total_time = results['test_metadata']['total_test_time']
        print(f"\n⏱️ Total Test Time: {total_time:.2f} seconds")
        print("=" * 60)


def main():
    """Main load testing execution."""
    
    print("🧬 Biomerkin Load Testing Tool")
    print("=" * 60)
    
    load_tester = LoadTester()
    
    try:
        # Run comprehensive load test
        results = load_tester.run_comprehensive_load_test()
        
        # Generate report
        report = load_tester.generate_load_test_report(results)
        
        # Combine results and report
        full_results = {**results, 'load_test_report': report}
        
        # Print summary
        load_tester.print_summary(results, report)
        
        # Save results
        report_file = load_tester.save_results(full_results)
        
        print(f"\n🎉 Load testing completed successfully!")
        print(f"📈 Report saved: {report_file}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Load testing failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)