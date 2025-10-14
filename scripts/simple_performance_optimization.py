#!/usr/bin/env python3
"""
Simple performance optimization and benchmarking for Biomerkin system.
"""

import time
import json
import psutil
import statistics
from datetime import datetime
from pathlib import Path
import sys

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def benchmark_system_performance():
    """Run simple system performance benchmark."""
    
    print("🚀 Biomerkin Performance Optimization")
    print("=" * 50)
    
    # System information
    print("\n💻 System Information:")
    print(f"   CPU Cores: {psutil.cpu_count()}")
    print(f"   Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    print(f"   Platform: {sys.platform}")
    
    # Test imports and basic functionality
    print("\n🔍 Testing Core Components:")
    
    import_tests = [
        ("biomerkin.agents.genomics_agent", "GenomicsAgent"),
        ("biomerkin.services.orchestrator", "WorkflowOrchestrator"),
        ("biomerkin.services.enhanced_orchestrator", "get_enhanced_orchestrator"),
        ("biomerkin.services.cache_manager", "get_cache_manager"),
        ("biomerkin.services.monitoring_service", "get_monitoring_service"),
    ]
    
    performance_results = {}
    
    for module_name, class_name in import_tests:
        start_time = time.time()
        try:
            module = __import__(module_name, fromlist=[class_name])
            component = getattr(module, class_name)
            
            # Test instantiation
            if callable(component):
                if 'get_' in class_name:
                    instance = component()
                else:
                    instance = component()
            
            import_time = time.time() - start_time
            print(f"   ✅ {class_name}: {import_time:.3f}s")
            
            performance_results[class_name] = {
                'import_time': import_time,
                'status': 'success'
            }
            
        except Exception as e:
            import_time = time.time() - start_time
            print(f"   ❌ {class_name}: {import_time:.3f}s - {str(e)[:50]}...")
            
            performance_results[class_name] = {
                'import_time': import_time,
                'status': 'failed',
                'error': str(e)
            }
    
    # Test cache performance
    print("\n💾 Testing Cache Performance:")
    try:
        from biomerkin.services.cache_manager import get_cache_manager, CacheType
        
        cache_manager = get_cache_manager()
        
        # Simple cache test
        test_data = {'test': 'performance', 'timestamp': datetime.now().isoformat()}
        
        # PUT test
        put_start = time.time()
        cache_manager.put('perf_test', test_data, CacheType.API_RESPONSE, ttl_seconds=60)
        put_time = time.time() - put_start
        
        # GET test
        get_start = time.time()
        result = cache_manager.get('perf_test', CacheType.API_RESPONSE)
        get_time = time.time() - get_start
        
        print(f"   ✅ Cache PUT: {put_time*1000:.1f}ms")
        print(f"   ✅ Cache GET: {get_time*1000:.1f}ms")
        print(f"   ✅ Cache Hit: {'Yes' if result else 'No'}")
        
        performance_results['cache'] = {
            'put_time_ms': put_time * 1000,
            'get_time_ms': get_time * 1000,
            'cache_hit': result is not None
        }
        
    except Exception as e:
        print(f"   ❌ Cache test failed: {e}")
        performance_results['cache'] = {'status': 'failed', 'error': str(e)}
    
    # Test enhanced orchestrator
    print("\n🚀 Testing Enhanced Orchestrator:")
    try:
        from biomerkin.services.enhanced_orchestrator import get_enhanced_orchestrator
        
        orchestrator = get_enhanced_orchestrator()
        
        status_start = time.time()
        status = orchestrator.get_enhanced_status()
        status_time = time.time() - status_start
        
        print(f"   ✅ Status Check: {status_time*1000:.1f}ms")
        print(f"   ✅ Strands Enabled: {status.get('strands_enabled', False)}")
        print(f"   ✅ Agents Available: {status.get('agents_created', 0)}")
        
        performance_results['enhanced_orchestrator'] = {
            'status_time_ms': status_time * 1000,
            'strands_enabled': status.get('strands_enabled', False),
            'agents_available': status.get('agents_created', 0)
        }
        
    except Exception as e:
        print(f"   ❌ Enhanced orchestrator test failed: {e}")
        performance_results['enhanced_orchestrator'] = {'status': 'failed', 'error': str(e)}
    
    # Memory usage test
    print("\n🧠 Memory Usage Analysis:")
    process = psutil.Process()
    memory_info = process.memory_info()
    
    print(f"   📊 Current Memory: {memory_info.rss / 1024 / 1024:.1f} MB")
    print(f"   📊 Virtual Memory: {memory_info.vms / 1024 / 1024:.1f} MB")
    
    performance_results['memory'] = {
        'rss_mb': memory_info.rss / 1024 / 1024,
        'vms_mb': memory_info.vms / 1024 / 1024
    }
    
    return performance_results


def generate_optimization_recommendations(results):
    """Generate optimization recommendations based on results."""
    
    recommendations = []
    
    # Import time recommendations
    slow_imports = [name for name, data in results.items() 
                   if isinstance(data, dict) and data.get('import_time', 0) > 1.0]
    
    if slow_imports:
        recommendations.append({
            'component': 'imports',
            'issue': f'Slow imports detected: {", ".join(slow_imports)}',
            'recommendation': 'Consider lazy loading or optimizing import dependencies',
            'priority': 'medium',
            'estimated_improvement': '20-30% faster startup'
        })
    
    # Cache performance recommendations
    cache_data = results.get('cache', {})
    if cache_data.get('put_time_ms', 0) > 100:
        recommendations.append({
            'component': 'cache',
            'issue': f'Slow cache PUT operations: {cache_data.get("put_time_ms", 0):.1f}ms',
            'recommendation': 'Optimize cache backend or reduce data size',
            'priority': 'medium',
            'estimated_improvement': '50% faster cache operations'
        })
    
    # Memory recommendations
    memory_data = results.get('memory', {})
    if memory_data.get('rss_mb', 0) > 500:
        recommendations.append({
            'component': 'memory',
            'issue': f'High memory usage: {memory_data.get("rss_mb", 0):.1f}MB',
            'recommendation': 'Implement memory cleanup and optimize object lifecycle',
            'priority': 'high',
            'estimated_improvement': '30-40% memory reduction'
        })
    
    # Enhanced orchestrator recommendations
    orch_data = results.get('enhanced_orchestrator', {})
    if not orch_data.get('strands_enabled', False):
        recommendations.append({
            'component': 'strands',
            'issue': 'Strands agents not enabled',
            'recommendation': 'Configure AWS credentials to enable Strands functionality',
            'priority': 'high',
            'estimated_improvement': 'Enable advanced multi-agent capabilities'
        })
    
    return recommendations


def generate_lambda_optimization_config():
    """Generate optimized Lambda configuration."""
    
    lambda_configs = {
        'biomerkin-genomics-agent': {
            'memory_mb': 1024,
            'timeout_seconds': 300,
            'environment_variables': {
                'PYTHONPATH': '/var/task',
                'BIOPYTHON_CACHE_SIZE': '100'
            }
        },
        'biomerkin-literature-agent': {
            'memory_mb': 512,
            'timeout_seconds': 180,
            'environment_variables': {
                'PYTHONPATH': '/var/task',
                'BEDROCK_TIMEOUT': '60'
            }
        },
        'biomerkin-drug-agent': {
            'memory_mb': 512,
            'timeout_seconds': 180,
            'environment_variables': {
                'PYTHONPATH': '/var/task',
                'DRUGBANK_API_TIMEOUT': '30'
            }
        },
        'biomerkin-decision-agent': {
            'memory_mb': 1024,
            'timeout_seconds': 300,
            'environment_variables': {
                'PYTHONPATH': '/var/task',
                'BEDROCK_TIMEOUT': '120'
            }
        },
        'biomerkin-orchestrator': {
            'memory_mb': 768,
            'timeout_seconds': 900,
            'environment_variables': {
                'PYTHONPATH': '/var/task',
                'MAX_CONCURRENT_AGENTS': '4'
            }
        }
    }
    
    return lambda_configs


def save_optimization_report(results, recommendations, lambda_configs):
    """Save optimization report to file."""
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'performance_results': results,
        'optimization_recommendations': recommendations,
        'lambda_configurations': lambda_configs,
        'summary': {
            'total_components_tested': len(results),
            'successful_components': len([r for r in results.values() 
                                        if isinstance(r, dict) and r.get('status') != 'failed']),
            'recommendations_count': len(recommendations),
            'optimization_score': max(0, 100 - len(recommendations) * 10)
        }
    }
    
    # Create reports directory
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"performance_optimization_{timestamp}.json"
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    return report_file


def main():
    """Main optimization execution."""
    
    try:
        # Run performance benchmark
        results = benchmark_system_performance()
        
        # Generate recommendations
        recommendations = generate_optimization_recommendations(results)
        
        # Generate Lambda configurations
        lambda_configs = generate_lambda_optimization_config()
        
        # Print recommendations
        print("\n💡 Optimization Recommendations:")
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec['component']}: {rec['recommendation']}")
                print(f"      Priority: {rec['priority']}, Impact: {rec['estimated_improvement']}")
        else:
            print("   ✅ No optimization recommendations - system is well optimized!")
        
        # Print Lambda configurations
        print(f"\n⚡ Lambda Optimization Configurations:")
        print(f"   Generated configs for {len(lambda_configs)} Lambda functions")
        print(f"   Total memory allocation: {sum(c['memory_mb'] for c in lambda_configs.values())} MB")
        
        # Save report
        report_file = save_optimization_report(results, recommendations, lambda_configs)
        
        print(f"\n📊 Performance Report:")
        print(f"   Components Tested: {len(results)}")
        print(f"   Recommendations: {len(recommendations)}")
        print(f"   Optimization Score: {max(0, 100 - len(recommendations) * 10)}/100")
        print(f"   Report Saved: {report_file}")
        
        print(f"\n🎉 Performance optimization completed!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Performance optimization failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)