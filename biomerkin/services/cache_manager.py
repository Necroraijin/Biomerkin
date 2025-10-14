"""
Cache Manager for Biomerkin multi-agent system.

This module provides a comprehensive caching layer for API responses and
expensive computational results with intelligent cache invalidation strategies,
performance metrics, and monitoring capabilities.
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from decimal import Decimal

from ..utils.config import get_config


class CacheType(Enum):
    """Types of cached data."""
    API_RESPONSE = "api_response"
    COMPUTATION_RESULT = "computation_result"
    LITERATURE_SEARCH = "literature_search"
    PROTEIN_STRUCTURE = "protein_structure"
    DRUG_CANDIDATE = "drug_candidate"
    GENOMICS_ANALYSIS = "genomics_analysis"


class CacheStrategy(Enum):
    """Cache invalidation strategies."""
    TTL = "time_to_live"
    LRU = "least_recently_used"
    MANUAL = "manual"
    DEPENDENCY = "dependency_based"


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    key: str
    value: Any
    cache_type: CacheType
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: Optional[int]
    dependencies: List[str]
    size_bytes: int
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        if self.ttl_seconds is None:
            return False
        
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'key': self.key,
            'value': self.value,
            'cache_type': self.cache_type.value,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'ttl_seconds': self.ttl_seconds,
            'dependencies': self.dependencies,
            'size_bytes': self.size_bytes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary."""
        return cls(
            key=data['key'],
            value=data['value'],
            cache_type=CacheType(data['cache_type']),
            created_at=datetime.fromisoformat(data['created_at']),
            last_accessed=datetime.fromisoformat(data['last_accessed']),
            access_count=data['access_count'],
            ttl_seconds=data.get('ttl_seconds'),
            dependencies=data.get('dependencies', []),
            size_bytes=data.get('size_bytes', 0)
        )


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_size_bytes: int = 0
    entries_count: int = 0
    evictions_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_requests == 0:
            return 0.0
        return self.cache_hits / self.total_requests
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate."""
        return 1.0 - self.hit_rate
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_requests': self.total_requests,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': self.hit_rate,
            'miss_rate': self.miss_rate,
            'total_size_bytes': self.total_size_bytes,
            'entries_count': self.entries_count,
            'evictions_count': self.evictions_count
        }


class InMemoryCacheBackend:
    """In-memory cache backend for development and testing."""
    
    def __init__(self, max_size: int = 1000):
        """Initialize in-memory cache."""
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.logger = logging.getLogger(__name__)
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get cache entry by key."""
        return self.cache.get(key)
    
    def put(self, entry: CacheEntry) -> bool:
        """Store cache entry."""
        # Implement LRU eviction if at capacity
        if len(self.cache) >= self.max_size and entry.key not in self.cache:
            self._evict_lru()
        
        self.cache[entry.key] = entry
        return True
    
    def delete(self, key: str) -> bool:
        """Delete cache entry by key."""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def list_keys(self, cache_type: Optional[CacheType] = None) -> List[str]:
        """List all cache keys, optionally filtered by type."""
        if cache_type:
            return [key for key, entry in self.cache.items() 
                   if entry.cache_type == cache_type]
        return list(self.cache.keys())
    
    def clear_by_type(self, cache_type: CacheType) -> int:
        """Clear all entries of a specific type."""
        keys_to_delete = [key for key, entry in self.cache.items() 
                         if entry.cache_type == cache_type]
        
        for key in keys_to_delete:
            del self.cache[key]
        
        return len(keys_to_delete)
    
    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self.cache:
            return
        
        lru_key = min(self.cache.keys(), 
                     key=lambda k: self.cache[k].last_accessed)
        del self.cache[lru_key]


class DynamoDBCacheBackend:
    """DynamoDB-based cache backend."""
    
    def __init__(self, table_name: str, region_name: str):
        """Initialize DynamoDB cache backend."""
        self.table_name = table_name
        self.region_name = region_name
        self.logger = logging.getLogger(__name__)
        
        try:
            self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
            self.table = self.dynamodb.Table(table_name)
            self._ensure_table_exists()
        except NoCredentialsError:
            self.logger.warning("AWS credentials not found. Cache will be disabled.")
            self.dynamodb = None
            self.table = None
        except Exception as e:
            self.logger.error(f"Failed to initialize DynamoDB cache backend: {str(e)}")
            self.dynamodb = None
            self.table = None
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """Get cache entry by key."""
        if not self.table:
            return None
        
        try:
            response = self.table.get_item(Key={'cache_key': key})
            if 'Item' not in response:
                return None
            
            item = response['Item']
            return CacheEntry.from_dict({
                'key': item['cache_key'],
                'value': json.loads(item['value']),
                'cache_type': item['cache_type'],
                'created_at': item['created_at'],
                'last_accessed': item['last_accessed'],
                'access_count': int(item['access_count']),
                'ttl_seconds': int(item['ttl_seconds']) if item.get('ttl_seconds') else None,
                'dependencies': item.get('dependencies', []),
                'size_bytes': int(item.get('size_bytes', 0))
            })
        except Exception as e:
            self.logger.error(f"Error getting cache entry: {str(e)}")
            return None
    
    def put(self, entry: CacheEntry) -> bool:
        """Store cache entry."""
        if not self.table:
            return False
        
        try:
            item = {
                'cache_key': entry.key,
                'value': json.dumps(entry.value, default=str),
                'cache_type': entry.cache_type.value,
                'created_at': entry.created_at.isoformat(),
                'last_accessed': entry.last_accessed.isoformat(),
                'access_count': entry.access_count,
                'size_bytes': entry.size_bytes
            }
            
            if entry.ttl_seconds:
                item['ttl_seconds'] = entry.ttl_seconds
                # Set DynamoDB TTL
                item['ttl'] = int((entry.created_at + timedelta(seconds=entry.ttl_seconds)).timestamp())
            
            if entry.dependencies:
                item['dependencies'] = entry.dependencies
            
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            self.logger.error(f"Error storing cache entry: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete cache entry by key."""
        if not self.table:
            return False
        
        try:
            self.table.delete_item(Key={'cache_key': key})
            return True
        except Exception as e:
            self.logger.error(f"Error deleting cache entry: {str(e)}")
            return False
    
    def list_keys(self, cache_type: Optional[CacheType] = None) -> List[str]:
        """List all cache keys, optionally filtered by type."""
        if not self.table:
            return []
        
        try:
            scan_kwargs = {}
            if cache_type:
                scan_kwargs['FilterExpression'] = 'cache_type = :cache_type'
                scan_kwargs['ExpressionAttributeValues'] = {':cache_type': cache_type.value}
            
            response = self.table.scan(**scan_kwargs)
            return [item['cache_key'] for item in response.get('Items', [])]
        except Exception as e:
            self.logger.error(f"Error listing cache keys: {str(e)}")
            return []
    
    def clear_by_type(self, cache_type: CacheType) -> int:
        """Clear all entries of a specific type."""
        keys = self.list_keys(cache_type)
        cleared = 0
        
        for key in keys:
            if self.delete(key):
                cleared += 1
        
        return cleared
    
    def _ensure_table_exists(self):
        """Ensure the cache table exists."""
        try:
            self.table.load()
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                self._create_table()
            else:
                raise
    
    def _create_table(self):
        """Create the cache table."""
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'cache_key', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'cache_key', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST',
                TimeToLiveSpecification={
                    'AttributeName': 'ttl',
                    'Enabled': True
                }
            )
            table.wait_until_exists()
            self.logger.info(f"Created cache table: {self.table_name}")
        except Exception as e:
            self.logger.error(f"Failed to create cache table: {str(e)}")
            raise


class CacheManager:
    """
    Comprehensive cache manager with intelligent invalidation strategies,
    performance metrics, and monitoring capabilities.
    """
    
    def __init__(self, backend: Optional[Union[DynamoDBCacheBackend, InMemoryCacheBackend]] = None):
        """Initialize cache manager."""
        self.logger = logging.getLogger(__name__)
        self.config = get_config()
        self.metrics = CacheMetrics()
        
        # Check if caching is enabled
        if not self.config.cache.enabled:
            self.logger.info("Caching is disabled in configuration")
            self.backend = InMemoryCacheBackend(max_size=0)  # Disabled cache
            self.default_ttls = {}
            return
        
        # Initialize backend
        if backend:
            self.backend = backend
        elif self.config.cache.backend_type == 'dynamodb':
            dynamodb_backend = DynamoDBCacheBackend(
                self.config.cache.dynamodb_table_name, 
                self.config.aws.region
            )
            # Fall back to in-memory if DynamoDB is not available
            if dynamodb_backend.table is None:
                self.logger.warning("DynamoDB not available, falling back to in-memory cache")
                self.backend = InMemoryCacheBackend(max_size=self.config.cache.memory_max_size)
            else:
                self.backend = dynamodb_backend
        else:
            self.backend = InMemoryCacheBackend(max_size=self.config.cache.memory_max_size)
        
        # Default TTL values by cache type from configuration
        self.default_ttls = {
            CacheType.API_RESPONSE: self.config.cache.api_response_ttl,
            CacheType.COMPUTATION_RESULT: self.config.cache.computation_result_ttl,
            CacheType.LITERATURE_SEARCH: self.config.cache.literature_search_ttl,
            CacheType.PROTEIN_STRUCTURE: self.config.cache.protein_structure_ttl,
            CacheType.DRUG_CANDIDATE: self.config.cache.drug_candidate_ttl,
            CacheType.GENOMICS_ANALYSIS: self.config.cache.genomics_analysis_ttl,
        }
    
    def get(self, key: str, cache_type: CacheType) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            cache_type: Type of cached data
            
        Returns:
            Cached value if found and valid, None otherwise
        """
        self.metrics.total_requests += 1
        
        # Generate full cache key
        full_key = self._generate_key(key, cache_type)
        
        # Get from backend
        entry = self.backend.get(full_key)
        
        if entry is None:
            self.metrics.cache_misses += 1
            self.logger.debug(f"Cache miss for key: {full_key}")
            return None
        
        # Check if expired
        if entry.is_expired():
            self.backend.delete(full_key)
            self.metrics.cache_misses += 1
            self.logger.debug(f"Cache entry expired for key: {full_key}")
            return None
        
        # Update access metadata
        entry.last_accessed = datetime.utcnow()
        entry.access_count += 1
        self.backend.put(entry)
        
        self.metrics.cache_hits += 1
        self.logger.debug(f"Cache hit for key: {full_key}")
        
        return entry.value
    
    def put(self, key: str, value: Any, cache_type: CacheType, 
            ttl_seconds: Optional[int] = None, dependencies: Optional[List[str]] = None) -> bool:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            cache_type: Type of cached data
            ttl_seconds: Time to live in seconds (uses default if None)
            dependencies: List of dependency keys for invalidation
            
        Returns:
            True if stored successfully, False otherwise
        """
        # Generate full cache key
        full_key = self._generate_key(key, cache_type)
        
        # Use default TTL if not specified
        if ttl_seconds is None:
            ttl_seconds = self.default_ttls.get(cache_type, 3600)
        
        # Calculate size
        size_bytes = len(json.dumps(value, default=str).encode('utf-8'))
        
        # Create cache entry
        entry = CacheEntry(
            key=full_key,
            value=value,
            cache_type=cache_type,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=0,
            ttl_seconds=ttl_seconds,
            dependencies=dependencies or [],
            size_bytes=size_bytes
        )
        
        # Store in backend
        success = self.backend.put(entry)
        
        if success:
            self.metrics.entries_count += 1
            self.metrics.total_size_bytes += size_bytes
            self.logger.debug(f"Cached value for key: {full_key}")
        else:
            self.logger.warning(f"Failed to cache value for key: {full_key}")
        
        return success
    
    def delete(self, key: str, cache_type: CacheType) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            cache_type: Type of cached data
            
        Returns:
            True if deleted successfully, False otherwise
        """
        full_key = self._generate_key(key, cache_type)
        success = self.backend.delete(full_key)
        
        if success:
            self.metrics.entries_count = max(0, self.metrics.entries_count - 1)
            self.logger.debug(f"Deleted cache entry: {full_key}")
        
        return success
    
    def invalidate_by_dependency(self, dependency_key: str) -> int:
        """
        Invalidate all cache entries that depend on a specific key.
        
        Args:
            dependency_key: The dependency key to invalidate
            
        Returns:
            Number of entries invalidated
        """
        invalidated = 0
        
        # This is a simplified implementation
        # In a production system, you might want to maintain a dependency index
        for cache_type in CacheType:
            keys = self.backend.list_keys(cache_type)
            for key in keys:
                entry = self.backend.get(key)
                if entry and dependency_key in entry.dependencies:
                    if self.backend.delete(key):
                        invalidated += 1
        
        self.logger.info(f"Invalidated {invalidated} cache entries for dependency: {dependency_key}")
        return invalidated
    
    def clear_by_type(self, cache_type: CacheType) -> int:
        """
        Clear all cache entries of a specific type.
        
        Args:
            cache_type: Type of cached data to clear
            
        Returns:
            Number of entries cleared
        """
        cleared = self.backend.clear_by_type(cache_type)
        self.metrics.entries_count = max(0, self.metrics.entries_count - cleared)
        self.metrics.evictions_count += cleared
        
        self.logger.info(f"Cleared {cleared} cache entries of type: {cache_type.value}")
        return cleared
    
    def clear_all(self) -> int:
        """
        Clear all cache entries.
        
        Returns:
            Number of entries cleared
        """
        total_cleared = 0
        for cache_type in CacheType:
            cleared = self.clear_by_type(cache_type)
            total_cleared += cleared
        
        return total_cleared
    
    def get_metrics(self) -> CacheMetrics:
        """Get current cache metrics."""
        return self.metrics
    
    def reset_metrics(self) -> None:
        """Reset cache metrics."""
        self.metrics = CacheMetrics()
    
    def _generate_key(self, key: str, cache_type: CacheType) -> str:
        """Generate full cache key with type prefix."""
        return f"{cache_type.value}:{key}"
    
    def _hash_key(self, key: str) -> str:
        """Generate hash of key for consistent key generation."""
        return hashlib.sha256(key.encode('utf-8')).hexdigest()


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def clear_cache_manager():
    """Clear the global cache manager instance (useful for testing)."""
    global _cache_manager
    _cache_manager = None