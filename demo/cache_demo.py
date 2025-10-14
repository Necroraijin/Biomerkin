#!/usr/bin/env python3
"""
Cache Layer Demonstration for Biomerkin

This script demonstrates the caching functionality implemented for the
Biomerkin multi-agent system, showing performance improvements and
cache management capabilities.
"""

import time
import json
from datetime import datetime

from biomerkin.services.cache_manager import get_cache_manager, CacheType, clear_cache_manager
from biomerkin.services.cache_monitor import get_cache_monitor, clear_cache_monitor
from biomerkin.utils.cache_decorators import cache_api_response, cache_computation


def simulate_expensive_api_call(query: str, max_results: int = 10) -> dict:
    """Simulate an expensive API call (like PubMed search)."""
    print(f"  🔄 Making API call for query: '{query}' (max_results: {max_results})")
    time.sleep(2)  # Simulate network delay
    
    return {
        "query": query,
        "max_results": max_results,
        "results": [
            {"id": f"article_{i}", "title": f"Research on {query} - Article {i}"}
            for i in range(1, min(max_results + 1, 6))
        ],
        "timestamp": datetime.utcnow().isoformat(),
        "total_found": max_results * 2  # Simulate more results available
    }


def simulate_expensive_computation(sequence: str) -> dict:
    """Simulate expensive genomics computation."""
    print(f"  🧬 Analyzing sequence: {sequence[:20]}...")
    time.sleep(1.5)  # Simulate computation time
    
    return {
        "sequence_length": len(sequence),
        "gc_content": sequence.count('G') + sequence.count('C'),
        "genes_found": len(sequence) // 100,  # Simplified
        "analysis_time": 1.5,
        "timestamp": datetime.utcnow().isoformat()
    }


@cache_api_response(CacheType.LITERATURE_SEARCH, ttl_seconds=300)  # 5 minutes
def cached_literature_search(query: str, max_results: int = 10) -> dict:
    """Cached version of literature search."""
    return simulate_expensive_api_call(query, max_results)


@cache_computation(CacheType.GENOMICS_ANALYSIS, ttl_seconds=600)  # 10 minutes
def cached_genomics_analysis(sequence: str) -> dict:
    """Cached version of genomics analysis."""
    return simulate_expensive_computation(sequence)


def demo_basic_caching():
    """Demonstrate basic caching functionality."""
    print("=" * 60)
    print("🚀 BASIC CACHING DEMONSTRATION")
    print("=" * 60)
    
    # Clear any existing cache
    clear_cache_manager()
    cache_manager = get_cache_manager()
    
    print("\n1. Testing Literature Search Caching")
    print("-" * 40)
    
    # First call - will be slow
    print("First call (no cache):")
    start_time = time.time()
    result1 = cached_literature_search("cancer genomics", 5)
    time1 = time.time() - start_time
    print(f"  ✅ Completed in {time1:.2f} seconds")
    print(f"  📄 Found {len(result1['results'])} articles")
    
    # Second call - should be fast (cached)
    print("\nSecond call (from cache):")
    start_time = time.time()
    result2 = cached_literature_search("cancer genomics", 5)
    time2 = time.time() - start_time
    print(f"  ⚡ Completed in {time2:.2f} seconds")
    print(f"  📄 Found {len(result2['results'])} articles")
    
    speedup = time1/time2 if time2 > 0 else float('inf')
    if speedup == float('inf'):
        print(f"\n🎯 Speedup: ∞ (instant from cache)!")
    else:
        print(f"\n🎯 Speedup: {speedup:.1f}x faster!")
    
    # Show cache metrics
    metrics = cache_manager.get_metrics()
    print(f"📊 Cache hit rate: {metrics.hit_rate:.1%}")


def demo_genomics_caching():
    """Demonstrate genomics analysis caching."""
    print("\n\n2. Testing Genomics Analysis Caching")
    print("-" * 40)
    
    sample_sequence = "ATGCGTAAGGCTTAGCTAGCTAGCTAAGCTAGCTAGCTAAGCTAGCTAGCTAA" * 10
    
    # First analysis - will be slow
    print("First analysis (no cache):")
    start_time = time.time()
    result1 = cached_genomics_analysis(sample_sequence)
    time1 = time.time() - start_time
    print(f"  ✅ Completed in {time1:.2f} seconds")
    print(f"  🧬 Sequence length: {result1['sequence_length']}")
    print(f"  🔬 Genes found: {result1['genes_found']}")
    
    # Second analysis - should be fast (cached)
    print("\nSecond analysis (from cache):")
    start_time = time.time()
    result2 = cached_genomics_analysis(sample_sequence)
    time2 = time.time() - start_time
    print(f"  ⚡ Completed in {time2:.2f} seconds")
    print(f"  🧬 Sequence length: {result2['sequence_length']}")
    print(f"  🔬 Genes found: {result2['genes_found']}")
    
    speedup = time1/time2 if time2 > 0 else float('inf')
    if speedup == float('inf'):
        print(f"\n🎯 Speedup: ∞ (instant from cache)!")
    else:
        print(f"\n🎯 Speedup: {speedup:.1f}x faster!")


def demo_cache_invalidation():
    """Demonstrate cache invalidation."""
    print("\n\n3. Testing Cache Invalidation")
    print("-" * 40)
    
    cache_manager = get_cache_manager()
    
    # Add some cached data
    print("Adding test data to cache...")
    cache_manager.put("test_key_1", {"data": "test1"}, CacheType.API_RESPONSE)
    cache_manager.put("test_key_2", {"data": "test2"}, CacheType.GENOMICS_ANALYSIS)
    cache_manager.put("test_key_3", {"data": "test3"}, CacheType.LITERATURE_SEARCH)
    
    print(f"  📦 Total entries: {cache_manager.get_metrics().entries_count}")
    
    # Clear specific type
    print("\nClearing API response cache...")
    cleared = cache_manager.clear_by_type(CacheType.API_RESPONSE)
    print(f"  🗑️  Cleared {cleared} entries")
    print(f"  📦 Remaining entries: {cache_manager.get_metrics().entries_count}")
    
    # Clear all
    print("\nClearing all cache...")
    total_cleared = cache_manager.clear_all()
    print(f"  🗑️  Cleared {total_cleared} total entries")
    print(f"  📦 Remaining entries: {cache_manager.get_metrics().entries_count}")


def demo_cache_monitoring():
    """Demonstrate cache monitoring capabilities."""
    print("\n\n4. Testing Cache Monitoring")
    print("-" * 40)
    
    clear_cache_monitor()
    monitor = get_cache_monitor()
    
    # Perform some cache operations
    print("Performing cache operations for monitoring...")
    
    # Mix of hits and misses
    cache_manager = get_cache_manager()
    
    # Cache some data
    cache_manager.put("monitor_test_1", {"data": "test1"}, CacheType.API_RESPONSE)
    cache_manager.put("monitor_test_2", {"data": "test2"}, CacheType.GENOMICS_ANALYSIS)
    
    # Generate hits and misses
    cache_manager.get("monitor_test_1", CacheType.API_RESPONSE)  # Hit
    cache_manager.get("monitor_test_2", CacheType.GENOMICS_ANALYSIS)  # Hit
    cache_manager.get("nonexistent_1", CacheType.API_RESPONSE)  # Miss
    cache_manager.get("nonexistent_2", CacheType.LITERATURE_SEARCH)  # Miss
    
    # Health check
    print("\nPerforming health check...")
    health = monitor.health_check()
    print(f"  🏥 Health status: {'✅ Healthy' if health.is_healthy else '❌ Unhealthy'}")
    print(f"  🔌 Backend available: {'✅ Yes' if health.backend_available else '❌ No'}")
    print(f"  📊 Hit rate: {health.hit_rate:.1%}")
    print(f"  📦 Total entries: {health.total_entries}")
    print(f"  💾 Total size: {health.total_size_mb:.2f} MB")
    
    if health.issues:
        print("  ⚠️  Issues:")
        for issue in health.issues:
            print(f"    - {issue}")
    
    # Performance report
    print("\nGenerating performance report...")
    report = monitor.get_performance_report(hours=1)
    print(f"  📈 Total requests: {report.total_requests}")
    print(f"  ✅ Cache hits: {report.cache_hits}")
    print(f"  ❌ Cache misses: {report.cache_misses}")
    print(f"  📊 Hit rate: {report.hit_rate:.1%}")
    print(f"  ⏱️  Average response time: {report.average_response_time_ms:.1f} ms")


def demo_cache_types():
    """Demonstrate different cache types and TTL."""
    print("\n\n5. Testing Different Cache Types and TTL")
    print("-" * 40)
    
    cache_manager = get_cache_manager()
    
    # Test different cache types
    cache_types_data = [
        (CacheType.API_RESPONSE, {"api": "pubmed", "query": "test"}),
        (CacheType.GENOMICS_ANALYSIS, {"sequence": "ATCG", "genes": 5}),
        (CacheType.LITERATURE_SEARCH, {"articles": ["article1", "article2"]}),
        (CacheType.PROTEIN_STRUCTURE, {"protein_id": "1ABC", "structure": "alpha_helix"}),
        (CacheType.DRUG_CANDIDATE, {"drug": "aspirin", "target": "COX2"}),
    ]
    
    print("Adding entries of different types...")
    for cache_type, data in cache_types_data:
        key = f"test_{cache_type.value}"
        cache_manager.put(key, data, cache_type, ttl_seconds=60)
        print(f"  📝 Added {cache_type.value}: {key}")
    
    # Show entries by type
    print(f"\nCache contents by type:")
    for cache_type in CacheType:
        keys = cache_manager.backend.list_keys(cache_type)
        print(f"  {cache_type.value}: {len(keys)} entries")
    
    # Test TTL expiration (shortened for demo)
    print(f"\nTesting TTL expiration...")
    cache_manager.put("short_ttl_test", {"data": "expires_soon"}, CacheType.API_RESPONSE, ttl_seconds=2)
    
    # Should be available immediately
    result = cache_manager.get("short_ttl_test", CacheType.API_RESPONSE)
    print(f"  ✅ Immediately after creation: {'Found' if result else 'Not found'}")
    
    # Wait for expiration
    print("  ⏳ Waiting 3 seconds for expiration...")
    time.sleep(3)
    
    # Should be expired now
    result = cache_manager.get("short_ttl_test", CacheType.API_RESPONSE)
    print(f"  ⏰ After expiration: {'Found' if result else 'Not found (expired)'}")


def main():
    """Run all cache demonstrations."""
    print("🎯 BIOMERKIN CACHE LAYER DEMONSTRATION")
    print("=" * 60)
    print("This demo shows the caching functionality implemented for")
    print("the Biomerkin multi-agent bioinformatics system.")
    print("=" * 60)
    
    try:
        # Run all demonstrations
        demo_basic_caching()
        demo_genomics_caching()
        demo_cache_invalidation()
        demo_cache_monitoring()
        demo_cache_types()
        
        print("\n" + "=" * 60)
        print("🎉 CACHE DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        # Final metrics
        cache_manager = get_cache_manager()
        final_metrics = cache_manager.get_metrics()
        
        print(f"\n📊 Final Cache Statistics:")
        print(f"  Total Requests: {final_metrics.total_requests}")
        print(f"  Cache Hits: {final_metrics.cache_hits}")
        print(f"  Cache Misses: {final_metrics.cache_misses}")
        print(f"  Overall Hit Rate: {final_metrics.hit_rate:.1%}")
        print(f"  Total Entries: {final_metrics.entries_count}")
        print(f"  Total Size: {final_metrics.total_size_bytes} bytes")
        
        print(f"\n✨ The caching layer provides significant performance")
        print(f"   improvements for expensive operations in the")
        print(f"   Biomerkin multi-agent system!")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        clear_cache_manager()
        clear_cache_monitor()


if __name__ == "__main__":
    main()