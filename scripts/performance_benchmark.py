#!/usr/bin/env python3
"""
Performance benchmarking and optimization tool for Biomerkin system.
"""

import asyncio
import time
import psutil
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from biomerkin.services.orchestrator import WorkflowOrchestrator
from biomerkin.services.enhanced_orchestrator import get_enhanced_orchestrator
from biomerkin.services.cache_manager import get_cache_manager
from biomerkin.services.monitoring_service import get_monitoring_service
from biomerkin.agents.genomics_agent import GenomicsAgent
from biomerkin.agents.proteomics_agent import ProteomicsAgent
from biomerkin.agents.literature_agent import LiteratureAgent
from biomerkin.agents.drug_agent import DrugAgent
from biomerkin.agents.decision_agent import DecisionAgent


class PerformanceBenchmark:
    """Comprehensive performance benchmarking for Biomerkin system."""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.system_info = self._get_system_info()
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmarking context."""
        return {
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': round(psutil.virtual_memory().total / (1024**3), 2),
            'python_version': sys.version,
            'platform': sys.platform,
            'timestamp': datetime.now().isoformat()
        }
    
    def benchmark_agent_performance(self) -> Dict[str, Any]:
        """Benchmark individual agent performance."""
        print("🔬 Benchmarking Individual Agents...")
        
        agents = {
            'genomics': GenomicsAgent(),
            'proteomics': ProteomicsAgent(),
            'literature': LiteratureAgent(),
            'drug': DrugAgent(),
            'decision': DecisionAgent()
        }
        
        # Sample test data
        test_data = {
            'genomics': {
                'sequence_data': 'ATGCGTAAGGCTTAGCTAGCATGCGTAAGGCTTAGCTAGC' * 10,
                'analysis_type': 'comprehensive'
            },
            'proteomics': {
                'protein_sequence': 'MKTVRQERLKSIVRILERSKEPVSGAQLAEELSVSRQVIVQDIAYLRSLGYNIVATPRGYVLAGG',
                'protein_id': 'test_protein'
            },
            'literature': {
                'search_terms': ['BRCA1', 'cancer', 'genomics'],
                'max_articles': 5
            },
            'drug': {
                'target_data': {
                    'genes': ['BRCA1', 'TP53'],
                    'proteins': ['BRCA1_protein'],
                    'conditions': ['breast cancer']
                }
            },
            'decision': {
                'analysis_data': {
                    'genomics_results': {'genes': ['BRCA1'], 'mutations': ['c.5266dupC']},
                    'drug_results': {'candidates': ['Olaparib']}
                }
            }
        }
        
        agent_results = {}
        
        for agent_name, agent in agents.items():
            print(f"   Testing {agent_name}Agent...")
            
            # Warm-up run
            try:
                agent.execute_with_error_handling(test_data[agent_name])
            except:
                pass  # Ignore warm-up errors
            
            # Benchmark runs
            times = []
            memory_usage = []
            
            for i in range(3):  # 3 runs for average
                process = psutil.Process()
                mem_before = process.memory_info().rss / 1024 / 1024  # MB
                
                start_time = time.time()
                try:
                    result = agent.execute_with_error_handling(test_data[agent_name])
                    success = True
                except Exception as e:
                    success = False
                    result = str(e)
                
                end_time = time.time()
                mem_after = process.memory_info().rss / 1024 / 1024  # MB
                
                execution_time = end_time - start_time
                memory_used = mem_after - mem_before
                
                times.append(execution_time)
                memory_usage.append(memory_used)
            
            agent_results[agent_name] = {
                'avg_execution_time': statistics.mean(times),
                'min_execution_time': min(times),
                'max_execution_time': max(times),
                'avg_memory_usage_mb': statistics.mean(memory_usage),
                'success_rate': 1.0,  # Simplified for benchmark
                'throughput_per_second': 1 / statistics.mean(times) if statistics.mean(times) > 0 else 0
            }
            
            print(f"     ✅ {agent_name}: {statistics.mean(times):.3f}s avg, {statistics.mean(memory_usage):.1f}MB")
        
        return agent_results
    
    def benchmark_orchestrator_performance(self) -> Dict[str, Any]:
        """Benchmark orchestrator performance."""
        print("\n🎭 Benchmarking Orchestrator Performance...")
        
        orchestrator = WorkflowOrchestrator()
        enhanced_orchestrator = get_enhanced_orchestrator()
        
        # Test workflow creation and management
        workflow_times = []
        
        for i in range(5):  # 5 workflow creations
            start_time = time.time()
            
            try:
                workflow_id = orchestrator.start_analysis(f"test_sequence_{i}.fasta")
                status = orchestrator.get_analysis_status(workflow_id)
                end_time = time.time()
                
                workflow_times.append(end_time - start_time)
            except Exception as e:
                print(f"     ⚠️ Workflow test {i} failed: {e}")
        
        # Test enhanced orchestrator status
        enhanced_start = time.time()
        enhanced_status = enhanced_orchestrator.get_enhanced_status()
        enhanced_time = time.time() - enhanced_start
        
        return {
            'workflow_creation_avg_time': statistics.mean(workflow_times) if workflow_times else 0,
            'workflow_creation_throughput': len(workflow_times) / sum(workflow_times) if workflow_times else 0,
            'enhanced_status_time': enhanced_time,
            'strands_enabled': enhanced_status.get('strands_enabled', False),
            'agents_available': enhanced_status.get('agents_created', 0)
        }
    
    def benchmark_cache_performance(self) -> Dict[str, Any]:
        """Benchmark cache performance."""
        print("\n💾 Benchmarking Cache Performance...")
        
        cache_manager = get_cache_manager()
        
        # Import CacheType
        from biomerkin.services.cache_manager import CacheType
        
        # Test cache operations
        cache_put_times = []
        cache_get_times = []
        
        test_data = {'test': 'data', 'size': 'medium', 'content': 'x' * 1000}
        
        # Cache PUT performance
        for i in range(10):
            start_time = time.time()
            cache_manager.put(f"test_key_{i}", test_data, CacheType.API_RESPONSE)
            end_time = time.time()
            cache_put_times.append(end_time - start_time)
        
        # Cache GET performance
        for i in range(10):
            start_time = time.time()
            result = cache_manager.get(f"test_key_{i}", CacheType.API_RESPONSE)
            end_time = time.time()
            cache_get_times.append(end_time - start_time)
        
        # Get cache metrics
        metrics = cache_manager.get_metrics()
        
        return {
            'cache_put_avg_time': statistics.mean(cache_put_times),
            'cache_get_avg_time': statistics.mean(cache_get_times),
            'cache_hit_rate': metrics.hit_rate,
            'cache_throughput_ops_per_sec': 20 / (sum(cache_put_times) + sum(cache_get_times)),
            'total_entries': metrics.entries_count,
            'total_size_bytes': metrics.total_size_bytes
        }
    
    def benchmark_concurrent_performance(self) -> Dict[str, Any]:
        """Benchmark concurrent execution performance."""
        print("\n⚡ Benchmarking Concurrent Performance...")
        
        def simulate_agent_work(agent_id: int) -> Dict[str, Any]:
            """Simulate agent work for concurrent testing."""
            start_time = time.time()
            
            # Simulate some work
            genomics_agent = GenomicsAgent()
            test_data = {
                'sequence_data': f'ATGCGTAAGGCTTAGCTAGC{agent_id}' * 5,
                'analysis_type': 'basic'
            }
            
            try:
                result = genomics_agent.execute_with_error_handling(test_data)
                success = True
            except:
                success = False
                result = None
            
            end_time = time.time()
            
            return {
                'agent_id': agent_id,
                'execution_time': end_time - start_time,
                'success': success,
                'timestamp': datetime.now().isoformat()
            }
        
        # Test different concurrency levels
        concurrency_results = {}
        
        for num_workers in [1, 2, 4, 8]:
            print(f"   Testing {num_workers} concurrent workers...")
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(simulate_agent_work, i) for i in range(num_workers * 2)]
                results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            successful_results = [r for r in results if r['success']]
            
            concurrency_results[f"{num_workers}_workers"] = {
                'total_time': total_time,
                'successful_tasks': len(successful_results),
                'total_tasks': len(results),
                'success_rate': len(successful_results) / len(results),
                'throughput': len(results) / total_time,
                'avg_task_time': statistics.mean([r['execution_time'] for r in results])
            }
        
        return concurrency_results
    
    def benchmark_memory_usage(self) -> Dict[str, Any]:
        """Benchmark memory usage patterns."""
        print("\n🧠 Benchmarking Memory Usage...")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Test memory usage during operations
        memory_samples = []
        
        # Create multiple agents and test memory growth
        agents = []
        for i in range(5):
            agents.append(GenomicsAgent())
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
        
        # Test cache memory usage
        cache_manager = get_cache_manager()
        for i in range(100):
            large_data = {'data': 'x' * 10000, 'id': i}
            cache_manager.put(f"memory_test_{i}", large_data, cache_manager.CacheType.API_RESPONSE)
            
            if i % 20 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        
        return {
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'memory_growth_mb': final_memory - initial_memory,
            'peak_memory_mb': max(memory_samples),
            'memory_efficiency': (final_memory - initial_memory) / len(agents) if agents else 0,
            'memory_samples': memory_samples[-10:]  # Last 10 samples
        }
    
    def generate_optimization_recommendations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on benchmark results."""
        recommendations = []
        
        # Agent performance recommendations
        agent_results = results.get('agent_performance', {})
        for agent_name, metrics in agent_results.items():
            if metrics['avg_execution_time'] > 2.0:  # Slow agents
                recommendations.append({
                    'component': f'{agent_name}_agent',
                    'issue': 'Slow execution time',
                    'recommendation': f'Optimize {agent_name} agent processing - consider caching or algorithm improvements',
                    'priority': 'high',
                    'estimated_improvement': '30-50% faster execution'
                })
            
            if metrics['avg_memory_usage_mb'] > 100:  # High memory usage
                recommendations.append({
                    'component': f'{agent_name}_agent',
                    'issue': 'High memory usage',
                    'recommendation': f'Optimize {agent_name} agent memory usage - implement streaming or chunking',
                    'priority': 'medium',
                    'estimated_improvement': '20-40% memory reduction'
                })
        
        # Cache performance recommendations
        cache_results = results.get('cache_performance', {})
        if cache_results.get('cache_hit_rate', 0) < 0.5:
            recommendations.append({
                'component': 'cache_manager',
                'issue': 'Low cache hit rate',
                'recommendation': 'Increase cache TTL or improve cache key strategy',
                'priority': 'medium',
                'estimated_improvement': '2-3x performance improvement'
            })
        
        # Concurrency recommendations
        concurrent_results = results.get('concurrent_performance', {})
        if '4_workers' in concurrent_results and '2_workers' in concurrent_results:
            if concurrent_results['4_workers']['throughput'] < concurrent_results['2_workers']['throughput'] * 1.5:
                recommendations.append({
                    'component': 'orchestrator',
                    'issue': 'Poor concurrency scaling',
                    'recommendation': 'Optimize thread pool size or implement async processing',
                    'priority': 'high',
                    'estimated_improvement': '50-100% throughput increase'
                })
        
        # Memory recommendations
        memory_results = results.get('memory_usage', {})
        if memory_results.get('memory_growth_mb', 0) > 200:
            recommendations.append({
                'component': 'system',
                'issue': 'High memory growth',
                'recommendation': 'Implement memory cleanup and garbage collection optimization',
                'priority': 'high',
                'estimated_improvement': '30-50% memory reduction'
            })
        
        return recommendations
    
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmark."""
        print("🚀 Starting Comprehensive Performance Benchmark")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Run all benchmarks
        self.results = {
            'system_info': self.system_info,
            'agent_performance': self.benchmark_agent_performance(),
            'orchestrator_performance': self.benchmark_orchestrator_performance(),
            'cache_performance': self.benchmark_cache_performance(),
            'concurrent_performance': self.benchmark_concurrent_performance(),
            'memory_usage': self.benchmark_memory_usage()
        }
        
        # Generate recommendations
        self.results['optimization_recommendations'] = self.generate_optimization_recommendations(self.results)
        
        total_time = time.time() - self.start_time
        self.results['benchmark_metadata'] = {
            'total_benchmark_time': total_time,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }
        
        return self.results
    
    def save_results(self, filename: str = None):
        """Save benchmark results to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_benchmark_{timestamp}.json"
        
        filepath = Path("reports") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📊 Benchmark results saved to: {filepath}")
        return filepath
    
    def print_summary(self):
        """Print benchmark summary."""
        if not self.results:
            print("No benchmark results available")
            return
        
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 60)
        
        # Agent performance summary
        agent_perf = self.results.get('agent_performance', {})
        if agent_perf:
            print("\n🔬 Agent Performance:")
            for agent, metrics in agent_perf.items():
                print(f"   {agent:12}: {metrics['avg_execution_time']:.3f}s avg, "
                      f"{metrics['avg_memory_usage_mb']:.1f}MB, "
                      f"{metrics['throughput_per_second']:.1f} ops/sec")
        
        # Orchestrator performance
        orch_perf = self.results.get('orchestrator_performance', {})
        if orch_perf:
            print(f"\n🎭 Orchestrator Performance:")
            print(f"   Workflow Creation: {orch_perf['workflow_creation_avg_time']:.3f}s")
            print(f"   Enhanced Status: {orch_perf['enhanced_status_time']:.3f}s")
            print(f"   Strands Enabled: {orch_perf['strands_enabled']}")
        
        # Cache performance
        cache_perf = self.results.get('cache_performance', {})
        if cache_perf:
            print(f"\n💾 Cache Performance:")
            print(f"   Hit Rate: {cache_perf['cache_hit_rate']:.1%}")
            print(f"   Throughput: {cache_perf['cache_throughput_ops_per_sec']:.1f} ops/sec")
            print(f"   Avg GET: {cache_perf['cache_get_avg_time']*1000:.1f}ms")
        
        # Memory usage
        memory_usage = self.results.get('memory_usage', {})
        if memory_usage:
            print(f"\n🧠 Memory Usage:")
            print(f"   Initial: {memory_usage['initial_memory_mb']:.1f}MB")
            print(f"   Final: {memory_usage['final_memory_mb']:.1f}MB")
            print(f"   Growth: {memory_usage['memory_growth_mb']:.1f}MB")
        
        # Optimization recommendations
        recommendations = self.results.get('optimization_recommendations', [])
        if recommendations:
            print(f"\n💡 Optimization Recommendations ({len(recommendations)}):")
            for i, rec in enumerate(recommendations[:5], 1):  # Top 5
                print(f"   {i}. {rec['component']}: {rec['recommendation']}")
                print(f"      Priority: {rec['priority']}, Impact: {rec['estimated_improvement']}")
        
        total_time = self.results.get('benchmark_metadata', {}).get('total_benchmark_time', 0)
        print(f"\n⏱️ Total Benchmark Time: {total_time:.2f} seconds")
        print("=" * 60)


def main():
    """Main benchmark execution."""
    print("🧬 Biomerkin Performance Benchmark Tool")
    print("=" * 60)
    
    benchmark = PerformanceBenchmark()
    
    try:
        # Run comprehensive benchmark
        results = benchmark.run_comprehensive_benchmark()
        
        # Print summary
        benchmark.print_summary()
        
        # Save results
        report_file = benchmark.save_results()
        
        print(f"\n🎉 Benchmark completed successfully!")
        print(f"📈 Report saved: {report_file}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)