"""
Cache decorators and utilities for agent methods.

This module provides convenient decorators and utilities for caching
expensive operations in the Biomerkin multi-agent system.
"""

import functools
import hashlib
import json
import logging
from typing import Any, Callable, Optional, List, Dict

from ..services.cache_manager import get_cache_manager, CacheType


logger = logging.getLogger(__name__)


def cache_api_response(cache_type: CacheType, ttl_seconds: Optional[int] = None,
                      key_generator: Optional[Callable] = None,
                      dependencies: Optional[List[str]] = None):
    """
    Decorator for caching API responses.
    
    Args:
        cache_type: Type of cached data
        ttl_seconds: Time to live in seconds
        key_generator: Custom function to generate cache key
        dependencies: List of dependency keys for invalidation
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = _generate_default_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key, cache_type)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                cache_manager.put(cache_key, result, cache_type, ttl_seconds, dependencies)
                logger.debug(f"Cached result for {func.__name__}: {cache_key}")
                return result
            except Exception as e:
                logger.error(f"Error in cached function {func.__name__}: {str(e)}")
                raise
        
        return wrapper
    return decorator


def cache_computation(cache_type: CacheType, ttl_seconds: Optional[int] = None,
                     key_generator: Optional[Callable] = None,
                     dependencies: Optional[List[str]] = None):
    """
    Decorator for caching expensive computational results.
    
    Args:
        cache_type: Type of cached data
        ttl_seconds: Time to live in seconds
        key_generator: Custom function to generate cache key
        dependencies: List of dependency keys for invalidation
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = _generate_default_key(func.__name__, args, kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key, cache_type)
            if cached_result is not None:
                logger.debug(f"Cache hit for computation {func.__name__}: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                cache_manager.put(cache_key, result, cache_type, ttl_seconds, dependencies)
                logger.debug(f"Cached computation result for {func.__name__}: {cache_key}")
                return result
            except Exception as e:
                logger.error(f"Error in cached computation {func.__name__}: {str(e)}")
                raise
        
        return wrapper
    return decorator


def invalidate_cache_on_update(cache_types: List[CacheType], 
                              dependency_key_generator: Optional[Callable] = None):
    """
    Decorator to invalidate cache entries when data is updated.
    
    Args:
        cache_types: List of cache types to invalidate
        dependency_key_generator: Function to generate dependency keys
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Execute the function first
            result = func(*args, **kwargs)
            
            # Invalidate cache entries
            cache_manager = get_cache_manager()
            
            if dependency_key_generator:
                dependency_key = dependency_key_generator(*args, **kwargs)
                invalidated = cache_manager.invalidate_by_dependency(dependency_key)
                logger.info(f"Invalidated {invalidated} cache entries for dependency: {dependency_key}")
            else:
                # Clear all entries of specified types
                total_invalidated = 0
                for cache_type in cache_types:
                    invalidated = cache_manager.clear_by_type(cache_type)
                    total_invalidated += invalidated
                logger.info(f"Invalidated {total_invalidated} cache entries of types: {[ct.value for ct in cache_types]}")
            
            return result
        
        return wrapper
    return decorator


class CacheKeyGenerator:
    """Utility class for generating cache keys."""
    
    @staticmethod
    def genomics_sequence_key(sequence: str, analysis_type: str = "default") -> str:
        """Generate cache key for genomics sequence analysis."""
        sequence_hash = hashlib.md5(sequence.encode('utf-8')).hexdigest()
        return f"genomics:{analysis_type}:{sequence_hash}"
    
    @staticmethod
    def protein_structure_key(protein_id: str, structure_type: str = "pdb") -> str:
        """Generate cache key for protein structure data."""
        return f"protein_structure:{structure_type}:{protein_id}"
    
    @staticmethod
    def literature_search_key(search_terms: List[str], max_results: int = 10) -> str:
        """Generate cache key for literature search."""
        terms_str = "|".join(sorted(search_terms))
        terms_hash = hashlib.md5(terms_str.encode('utf-8')).hexdigest()
        return f"literature_search:{terms_hash}:{max_results}"
    
    @staticmethod
    def drug_candidate_key(target_genes: List[str], target_proteins: List[str]) -> str:
        """Generate cache key for drug candidate search."""
        targets = sorted(target_genes + target_proteins)
        targets_str = "|".join(targets)
        targets_hash = hashlib.md5(targets_str.encode('utf-8')).hexdigest()
        return f"drug_candidates:{targets_hash}"
    
    @staticmethod
    def api_response_key(api_name: str, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key for API responses."""
        params_str = json.dumps(params, sort_keys=True, default=str)
        params_hash = hashlib.md5(params_str.encode('utf-8')).hexdigest()
        return f"api:{api_name}:{endpoint}:{params_hash}"


def _generate_default_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate default cache key from function name and arguments."""
    # Create a deterministic representation of arguments
    key_data = {
        'function': func_name,
        'args': [_serialize_arg(arg) for arg in args],
        'kwargs': {k: _serialize_arg(v) for k, v in kwargs.items()}
    }
    
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.sha256(key_str.encode('utf-8')).hexdigest()
    
    return f"default:{func_name}:{key_hash[:16]}"


def _serialize_arg(arg: Any) -> Any:
    """Serialize argument for cache key generation."""
    if hasattr(arg, 'to_dict'):
        return arg.to_dict()
    elif hasattr(arg, '__dict__'):
        return arg.__dict__
    elif isinstance(arg, (list, tuple)):
        return [_serialize_arg(item) for item in arg]
    elif isinstance(arg, dict):
        return {k: _serialize_arg(v) for k, v in arg.items()}
    else:
        return arg


# Convenience decorators for specific cache types
def cache_genomics_analysis(ttl_seconds: Optional[int] = None):
    """Decorator for caching genomics analysis results."""
    return cache_computation(
        CacheType.GENOMICS_ANALYSIS,
        ttl_seconds=ttl_seconds or 3600
    )


def cache_protein_structure(ttl_seconds: Optional[int] = None):
    """Decorator for caching protein structure data."""
    return cache_api_response(
        CacheType.PROTEIN_STRUCTURE,
        ttl_seconds=ttl_seconds or 604800  # 1 week
    )


def cache_literature_search(ttl_seconds: Optional[int] = None):
    """Decorator for caching literature search results."""
    return cache_api_response(
        CacheType.LITERATURE_SEARCH,
        ttl_seconds=ttl_seconds or 86400  # 24 hours
    )


def cache_drug_candidates(ttl_seconds: Optional[int] = None):
    """Decorator for caching drug candidate results."""
    return cache_api_response(
        CacheType.DRUG_CANDIDATE,
        ttl_seconds=ttl_seconds or 86400  # 24 hours
    )


def cache_api_call(api_name: str, ttl_seconds: Optional[int] = None):
    """Decorator for caching general API calls."""
    def key_gen(*args, **kwargs):
        return CacheKeyGenerator.api_response_key(api_name, "generic", kwargs)
    
    return cache_api_response(
        CacheType.API_RESPONSE,
        ttl_seconds=ttl_seconds or 3600,
        key_generator=key_gen
    )