"""
Tests for the cache manager and caching functionality.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from biomerkin.services.cache_manager import (
    CacheManager, CacheEntry, CacheType, CacheStrategy, CacheMetrics,
    InMemoryCacheBackend, DynamoDBCacheBackend, get_cache_manager, clear_cache_manager
)
from biomerkin.utils.cache_decorators import (
    cache_api_response, cache_computation, CacheKeyGenerator,
    cache_genomics_analysis, cache_protein_structure
)
from biomerkin.services.cache_monitor import CacheMonitor, get_cache_monitor, clear_cache_monitor


class TestCacheEntry:
    """Test CacheEntry functionality."""
    
    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            key="test_key",
            value={"data": "test"},
            cache_type=CacheType.API_RESPONSE,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=0,
            ttl_seconds=3600,
            dependencies=[],
            size_bytes=100
        )
        
        assert entry.key == "test_key"
        assert entry.value == {"data": "test"}
        assert entry.cache_type == CacheType.API_RESPONSE
        assert entry.ttl_seconds == 3600
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration logic."""
        # Create expired entry
        old_time = datetime.utcnow() - timedelta(hours=2)
        expired_entry = CacheEntry(
            key="expired_key",
            value={"data": "test"},
            cache_type=CacheType.API_RESPONSE,
            created_at=old_time,
            last_accessed=old_time,
            access_count=0,
            ttl_seconds=3600,  # 1 hour TTL
            dependencies=[],
            size_bytes=100
        )
        
        assert expired_entry.is_expired()
        
        # Create non-expired entry
        recent_time = datetime.utcnow() - timedelta(minutes=30)
        fresh_entry = CacheEntry(
            key="fresh_key",
            value={"data": "test"},
            cache_type=CacheType.API_RESPONSE,
            created_at=recent_time,
            last_accessed=recent_time,
            access_count=0,
            ttl_seconds=3600,  # 1 hour TTL
            dependencies=[],
            size_bytes=100
        )
        
        assert not fresh_entry.is_expired()
    
    def test_cache_entry_serialization(self):
        """Test cache entry to/from dict conversion."""
        entry = CacheEntry(
            key="test_key",
            value={"data": "test"},
            cache_type=CacheType.API_RESPONSE,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=5,
            ttl_seconds=3600,
            dependencies=["dep1", "dep2"],
            size_bytes=100
        )
        
        entry_dict = entry.to_dict()
        restored_entry = CacheEntry.from_dict(entry_dict)
        
        assert restored_entry.key == entry.key
        assert restored_entry.value == entry.value
        assert restored_entry.cache_type == entry.cache_type
        assert restored_entry.access_count == entry.access_count
        assert restored_entry.dependencies == entry.dependencies


class TestInMemoryCacheBackend:
    """Test in-memory cache backend."""
    
    def test_basic_operations(self):
        """Test basic cache operations."""
        backend = InMemoryCacheBackend(max_size=10)
        
        entry = CacheEntry(
            key="test_key",
            value={"data": "test"},
            cache_type=CacheType.API_RESPONSE,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=0,
            ttl_seconds=3600,
            dependencies=[],
            size_bytes=100
        )
        
        # Test put and get
        assert backend.put(entry)
        retrieved = backend.get("test_key")
        assert retrieved is not None
        assert retrieved.value == {"data": "test"}
        
        # Test delete
        assert backend.delete("test_key")
        assert backend.get("test_key") is None
        assert not backend.delete("nonexistent_key")
    
    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        backend = InMemoryCacheBackend(max_size=2)
        
        # Add entries to fill cache
        for i in range(3):
            entry = CacheEntry(
                key=f"key_{i}",
                value={"data": f"test_{i}"},
                cache_type=CacheType.API_RESPONSE,
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow() - timedelta(seconds=i),  # Different access times
                access_count=0,
                ttl_seconds=3600,
                dependencies=[],
                size_bytes=100
            )
            backend.put(entry)
        
        # First entry should be evicted (oldest access time)
        assert backend.get("key_0") is None
        assert backend.get("key_1") is not None
        assert backend.get("key_2") is not None
    
    def test_list_keys_by_type(self):
        """Test listing keys by cache type."""
        backend = InMemoryCacheBackend()
        
        # Add entries of different types
        api_entry = CacheEntry(
            key="api_key",
            value={"data": "api"},
            cache_type=CacheType.API_RESPONSE,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=0,
            ttl_seconds=3600,
            dependencies=[],
            size_bytes=100
        )
        
        comp_entry = CacheEntry(
            key="comp_key",
            value={"data": "computation"},
            cache_type=CacheType.COMPUTATION_RESULT,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=0,
            ttl_seconds=3600,
            dependencies=[],
            size_bytes=100
        )
        
        backend.put(api_entry)
        backend.put(comp_entry)
        
        api_keys = backend.list_keys(CacheType.API_RESPONSE)
        comp_keys = backend.list_keys(CacheType.COMPUTATION_RESULT)
        all_keys = backend.list_keys()
        
        assert "api_key" in api_keys
        assert "comp_key" not in api_keys
        assert "comp_key" in comp_keys
        assert "api_key" not in comp_keys
        assert len(all_keys) == 2


class TestCacheManager:
    """Test CacheManager functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        clear_cache_manager()
        self.backend = InMemoryCacheBackend()
        self.cache_manager = CacheManager(backend=self.backend)
    
    def test_basic_cache_operations(self):
        """Test basic cache operations."""
        # Test put and get
        success = self.cache_manager.put("test_key", {"data": "test"}, CacheType.API_RESPONSE)
        assert success
        
        result = self.cache_manager.get("test_key", CacheType.API_RESPONSE)
        assert result == {"data": "test"}
        
        # Test cache miss
        result = self.cache_manager.get("nonexistent_key", CacheType.API_RESPONSE)
        assert result is None
        
        # Test delete
        success = self.cache_manager.delete("test_key", CacheType.API_RESPONSE)
        assert success
        
        result = self.cache_manager.get("test_key", CacheType.API_RESPONSE)
        assert result is None
    
    def test_ttl_expiration(self):
        """Test TTL-based expiration."""
        # Put entry with short TTL
        self.cache_manager.put("short_ttl_key", {"data": "test"}, 
                              CacheType.API_RESPONSE, ttl_seconds=1)
        
        # Should be available immediately
        result = self.cache_manager.get("short_ttl_key", CacheType.API_RESPONSE)
        assert result == {"data": "test"}
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Should be expired now
        result = self.cache_manager.get("short_ttl_key", CacheType.API_RESPONSE)
        assert result is None
    
    def test_cache_metrics(self):
        """Test cache metrics tracking."""
        # Initial metrics
        metrics = self.cache_manager.get_metrics()
        assert metrics.total_requests == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        
        # Cache miss
        result = self.cache_manager.get("nonexistent", CacheType.API_RESPONSE)
        assert result is None
        
        metrics = self.cache_manager.get_metrics()
        assert metrics.total_requests == 1
        assert metrics.cache_misses == 1
        assert metrics.hit_rate == 0.0
        
        # Cache put and hit
        self.cache_manager.put("test_key", {"data": "test"}, CacheType.API_RESPONSE)
        result = self.cache_manager.get("test_key", CacheType.API_RESPONSE)
        assert result == {"data": "test"}
        
        metrics = self.cache_manager.get_metrics()
        assert metrics.total_requests == 2
        assert metrics.cache_hits == 1
        assert metrics.cache_misses == 1
        assert metrics.hit_rate == 0.5
    
    def test_dependency_invalidation(self):
        """Test dependency-based cache invalidation."""
        # Put entries with dependencies
        self.cache_manager.put("entry1", {"data": "test1"}, CacheType.API_RESPONSE, 
                              dependencies=["dep1"])
        self.cache_manager.put("entry2", {"data": "test2"}, CacheType.API_RESPONSE, 
                              dependencies=["dep1", "dep2"])
        self.cache_manager.put("entry3", {"data": "test3"}, CacheType.API_RESPONSE, 
                              dependencies=["dep2"])
        
        # Verify entries exist
        assert self.cache_manager.get("entry1", CacheType.API_RESPONSE) is not None
        assert self.cache_manager.get("entry2", CacheType.API_RESPONSE) is not None
        assert self.cache_manager.get("entry3", CacheType.API_RESPONSE) is not None
        
        # Invalidate by dependency
        invalidated = self.cache_manager.invalidate_by_dependency("dep1")
        assert invalidated == 2  # entry1 and entry2
        
        # Check invalidation results
        assert self.cache_manager.get("entry1", CacheType.API_RESPONSE) is None
        assert self.cache_manager.get("entry2", CacheType.API_RESPONSE) is None
        assert self.cache_manager.get("entry3", CacheType.API_RESPONSE) is not None
    
    def test_clear_by_type(self):
        """Test clearing cache entries by type."""
        # Add entries of different types
        self.cache_manager.put("api_key", {"data": "api"}, CacheType.API_RESPONSE)
        self.cache_manager.put("comp_key", {"data": "comp"}, CacheType.COMPUTATION_RESULT)
        self.cache_manager.put("lit_key", {"data": "lit"}, CacheType.LITERATURE_SEARCH)
        
        # Clear API responses
        cleared = self.cache_manager.clear_by_type(CacheType.API_RESPONSE)
        assert cleared == 1
        
        # Verify only API response was cleared
        assert self.cache_manager.get("api_key", CacheType.API_RESPONSE) is None
        assert self.cache_manager.get("comp_key", CacheType.COMPUTATION_RESULT) is not None
        assert self.cache_manager.get("lit_key", CacheType.LITERATURE_SEARCH) is not None


class TestCacheDecorators:
    """Test cache decorators."""
    
    def setup_method(self):
        """Set up test environment."""
        clear_cache_manager()
        self.backend = InMemoryCacheBackend()
        self.cache_manager = CacheManager(backend=self.backend)
    
    def test_cache_api_response_decorator(self):
        """Test API response caching decorator."""
        call_count = 0
        
        @cache_api_response(CacheType.API_RESPONSE, ttl_seconds=3600)
        def mock_api_call(param1, param2=None):
            nonlocal call_count
            call_count += 1
            return {"result": f"{param1}_{param2}", "call_count": call_count}
        
        # First call should execute function
        result1 = mock_api_call("test", param2="value")
        assert result1["result"] == "test_value"
        assert result1["call_count"] == 1
        assert call_count == 1
        
        # Second call should return cached result
        result2 = mock_api_call("test", param2="value")
        assert result2["result"] == "test_value"
        assert result2["call_count"] == 1  # Same as first call
        assert call_count == 1  # Function not called again
        
        # Different parameters should execute function again
        result3 = mock_api_call("different", param2="value")
        assert result3["result"] == "different_value"
        assert result3["call_count"] == 2
        assert call_count == 2
    
    def test_cache_computation_decorator(self):
        """Test computation caching decorator."""
        call_count = 0
        
        @cache_computation(CacheType.COMPUTATION_RESULT, ttl_seconds=3600)
        def expensive_computation(n):
            nonlocal call_count
            call_count += 1
            return {"result": n * n, "call_count": call_count}
        
        # First call
        result1 = expensive_computation(5)
        assert result1["result"] == 25
        assert call_count == 1
        
        # Second call with same parameter should be cached
        result2 = expensive_computation(5)
        assert result2["result"] == 25
        assert result2["call_count"] == 1  # Same as first call
        assert call_count == 1  # Function not called again
    
    def test_genomics_analysis_decorator(self):
        """Test genomics analysis caching decorator."""
        call_count = 0
        
        @cache_genomics_analysis(ttl_seconds=3600)
        def analyze_sequence(sequence):
            nonlocal call_count
            call_count += 1
            return {"genes": len(sequence), "call_count": call_count}
        
        # Test caching
        result1 = analyze_sequence("ATCGATCG")
        assert result1["genes"] == 8
        assert call_count == 1
        
        result2 = analyze_sequence("ATCGATCG")
        assert result2["call_count"] == 1  # Cached result
        assert call_count == 1


class TestCacheKeyGenerator:
    """Test cache key generation utilities."""
    
    def test_genomics_sequence_key(self):
        """Test genomics sequence key generation."""
        key1 = CacheKeyGenerator.genomics_sequence_key("ATCGATCG", "mutation_analysis")
        key2 = CacheKeyGenerator.genomics_sequence_key("ATCGATCG", "mutation_analysis")
        key3 = CacheKeyGenerator.genomics_sequence_key("ATCGATCG", "gene_identification")
        key4 = CacheKeyGenerator.genomics_sequence_key("GCTAGCTA", "mutation_analysis")
        
        # Same sequence and analysis type should generate same key
        assert key1 == key2
        
        # Different analysis type should generate different key
        assert key1 != key3
        
        # Different sequence should generate different key
        assert key1 != key4
        
        # Keys should have expected format
        assert key1.startswith("genomics:mutation_analysis:")
    
    def test_protein_structure_key(self):
        """Test protein structure key generation."""
        key1 = CacheKeyGenerator.protein_structure_key("1ABC", "pdb")
        key2 = CacheKeyGenerator.protein_structure_key("1ABC", "pdb")
        key3 = CacheKeyGenerator.protein_structure_key("1ABC", "alphafold")
        
        assert key1 == key2
        assert key1 != key3
        assert key1 == "protein_structure:pdb:1ABC"
    
    def test_literature_search_key(self):
        """Test literature search key generation."""
        terms1 = ["cancer", "mutation", "BRCA1"]
        terms2 = ["BRCA1", "cancer", "mutation"]  # Same terms, different order
        terms3 = ["cancer", "mutation", "BRCA2"]
        
        key1 = CacheKeyGenerator.literature_search_key(terms1, max_results=10)
        key2 = CacheKeyGenerator.literature_search_key(terms2, max_results=10)
        key3 = CacheKeyGenerator.literature_search_key(terms3, max_results=10)
        key4 = CacheKeyGenerator.literature_search_key(terms1, max_results=20)
        
        # Same terms (different order) should generate same key
        assert key1 == key2
        
        # Different terms should generate different key
        assert key1 != key3
        
        # Different max_results should generate different key
        assert key1 != key4
    
    def test_api_response_key(self):
        """Test API response key generation."""
        params1 = {"query": "test", "limit": 10}
        params2 = {"limit": 10, "query": "test"}  # Same params, different order
        params3 = {"query": "test", "limit": 20}
        
        key1 = CacheKeyGenerator.api_response_key("pubmed", "search", params1)
        key2 = CacheKeyGenerator.api_response_key("pubmed", "search", params2)
        key3 = CacheKeyGenerator.api_response_key("pubmed", "search", params3)
        key4 = CacheKeyGenerator.api_response_key("drugbank", "search", params1)
        
        # Same params (different order) should generate same key
        assert key1 == key2
        
        # Different params should generate different key
        assert key1 != key3
        
        # Different API should generate different key
        assert key1 != key4


class TestCacheMonitor:
    """Test cache monitoring functionality."""
    
    def setup_method(self):
        """Set up test environment."""
        clear_cache_manager()
        clear_cache_monitor()
        self.backend = InMemoryCacheBackend()
        self.cache_manager = CacheManager(backend=self.backend)
        self.monitor = CacheMonitor()
    
    def test_health_check(self):
        """Test cache health check."""
        health_status = self.monitor.health_check()
        
        assert isinstance(health_status.is_healthy, bool)
        assert isinstance(health_status.backend_available, bool)
        assert isinstance(health_status.hit_rate, float)
        assert isinstance(health_status.total_entries, int)
        assert isinstance(health_status.issues, list)
    
    def test_performance_report(self):
        """Test performance report generation."""
        # Add some cache activity
        self.cache_manager.put("test1", {"data": "test1"}, CacheType.API_RESPONSE)
        self.cache_manager.get("test1", CacheType.API_RESPONSE)
        self.cache_manager.get("nonexistent", CacheType.API_RESPONSE)
        
        report = self.monitor.get_performance_report(hours=1)
        
        assert isinstance(report.total_requests, int)
        assert isinstance(report.cache_hits, int)
        assert isinstance(report.cache_misses, int)
        assert isinstance(report.hit_rate, float)
        assert isinstance(report.entries_by_type, dict)
    
    def test_request_time_recording(self):
        """Test request time recording."""
        self.monitor.record_request_time(0.1)
        self.monitor.record_request_time(0.2)
        self.monitor.record_request_time(0.15)
        
        stats = self.monitor.get_cache_statistics()
        assert stats['request_times_count'] == 3
    
    def test_error_recording(self):
        """Test error recording."""
        initial_errors = self.monitor.error_count
        
        self.monitor.record_error()
        self.monitor.record_error()
        
        assert self.monitor.error_count == initial_errors + 2


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB for testing."""
    with patch('boto3.resource') as mock_resource:
        mock_table = Mock()
        mock_resource.return_value.Table.return_value = mock_table
        mock_table.load.return_value = None
        yield mock_table


class TestDynamoDBCacheBackend:
    """Test DynamoDB cache backend."""
    
    def test_initialization_with_mock(self, mock_dynamodb):
        """Test DynamoDB backend initialization."""
        backend = DynamoDBCacheBackend("test-table", "us-east-1")
        assert backend.table_name == "test-table"
        assert backend.region_name == "us-east-1"
    
    def test_put_and_get_with_mock(self, mock_dynamodb):
        """Test put and get operations with mocked DynamoDB."""
        backend = DynamoDBCacheBackend("test-table", "us-east-1")
        
        entry = CacheEntry(
            key="test_key",
            value={"data": "test"},
            cache_type=CacheType.API_RESPONSE,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=0,
            ttl_seconds=3600,
            dependencies=[],
            size_bytes=100
        )
        
        # Mock successful put
        mock_dynamodb.put_item.return_value = {}
        success = backend.put(entry)
        assert success
        
        # Mock successful get
        mock_response = {
            'Item': {
                'cache_key': 'test_key',
                'value': '{"data": "test"}',
                'cache_type': 'api_response',
                'created_at': entry.created_at.isoformat(),
                'last_accessed': entry.last_accessed.isoformat(),
                'access_count': 0,
                'size_bytes': 100
            }
        }
        mock_dynamodb.get_item.return_value = mock_response
        
        retrieved = backend.get("test_key")
        assert retrieved is not None
        assert retrieved.key == "test_key"
        assert retrieved.value == {"data": "test"}


if __name__ == "__main__":
    pytest.main([__file__])