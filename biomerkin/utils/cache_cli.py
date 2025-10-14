"""
Command-line interface for cache management.

This module provides CLI tools for managing the cache layer,
including monitoring, clearing, and configuration.
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, Any

from ..services.cache_manager import get_cache_manager, CacheType, clear_cache_manager
from ..services.cache_monitor import get_cache_monitor, clear_cache_monitor
from ..utils.config import get_config


def format_bytes(bytes_value: int) -> str:
    """Format bytes in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{seconds*1000:.1f} ms"
    elif seconds < 60:
        return f"{seconds:.1f} s"
    elif seconds < 3600:
        return f"{seconds/60:.1f} min"
    else:
        return f"{seconds/3600:.1f} h"


class CacheCLI:
    """Command-line interface for cache management."""
    
    def __init__(self):
        """Initialize CLI."""
        self.cache_manager = get_cache_manager()
        self.cache_monitor = get_cache_monitor()
    
    def status(self, args) -> None:
        """Show cache status and metrics."""
        print("=== Cache Status ===")
        
        # Get health status
        health = self.cache_monitor.health_check()
        status_icon = "✅" if health.is_healthy else "❌"
        print(f"Health: {status_icon} {'Healthy' if health.is_healthy else 'Unhealthy'}")
        print(f"Backend: {'Available' if health.backend_available else 'Unavailable'}")
        
        if health.issues:
            print("Issues:")
            for issue in health.issues:
                print(f"  - {issue}")
        
        print(f"\n=== Metrics ===")
        metrics = self.cache_manager.get_metrics()
        print(f"Total Requests: {metrics.total_requests:,}")
        print(f"Cache Hits: {metrics.cache_hits:,}")
        print(f"Cache Misses: {metrics.cache_misses:,}")
        print(f"Hit Rate: {metrics.hit_rate:.1%}")
        print(f"Miss Rate: {metrics.miss_rate:.1%}")
        print(f"Total Entries: {metrics.entries_count:,}")
        print(f"Total Size: {format_bytes(metrics.total_size_bytes)}")
        print(f"Evictions: {metrics.evictions_count:,}")
        
        # Show entries by type
        print(f"\n=== Entries by Type ===")
        for cache_type in CacheType:
            try:
                keys = self.cache_manager.backend.list_keys(cache_type)
                print(f"{cache_type.value}: {len(keys):,} entries")
            except Exception as e:
                print(f"{cache_type.value}: Error - {str(e)}")
    
    def clear(self, args) -> None:
        """Clear cache entries."""
        if args.type:
            # Clear specific type
            try:
                cache_type = CacheType(args.type)
                cleared = self.cache_manager.clear_by_type(cache_type)
                print(f"Cleared {cleared:,} entries of type '{args.type}'")
            except ValueError:
                print(f"Invalid cache type: {args.type}")
                print(f"Valid types: {[ct.value for ct in CacheType]}")
                return
        elif args.all:
            # Clear all entries
            if not args.force:
                response = input("Are you sure you want to clear ALL cache entries? (y/N): ")
                if response.lower() != 'y':
                    print("Operation cancelled")
                    return
            
            cleared = self.cache_manager.clear_all()
            print(f"Cleared {cleared:,} total entries")
        else:
            print("Specify --type <type> or --all to clear cache entries")
    
    def list_keys(self, args) -> None:
        """List cache keys."""
        cache_type = None
        if args.type:
            try:
                cache_type = CacheType(args.type)
            except ValueError:
                print(f"Invalid cache type: {args.type}")
                return
        
        try:
            keys = self.cache_manager.backend.list_keys(cache_type)
            
            if not keys:
                type_str = f" of type '{args.type}'" if args.type else ""
                print(f"No cache keys found{type_str}")
                return
            
            print(f"Found {len(keys):,} cache keys:")
            
            # Limit output if too many keys
            display_keys = keys[:args.limit] if args.limit else keys
            
            for key in display_keys:
                if args.verbose:
                    # Get entry details
                    try:
                        entry = self.cache_manager.backend.get(key)
                        if entry:
                            age = datetime.utcnow() - entry.created_at
                            size = format_bytes(entry.size_bytes)
                            print(f"  {key} ({entry.cache_type.value}, {size}, {format_duration(age.total_seconds())} old, {entry.access_count} accesses)")
                        else:
                            print(f"  {key} (details unavailable)")
                    except Exception as e:
                        print(f"  {key} (error: {str(e)})")
                else:
                    print(f"  {key}")
            
            if args.limit and len(keys) > args.limit:
                print(f"  ... and {len(keys) - args.limit:,} more")
                
        except Exception as e:
            print(f"Error listing keys: {str(e)}")
    
    def get_entry(self, args) -> None:
        """Get details of a specific cache entry."""
        try:
            # Try to find the entry across all types
            entry = None
            found_type = None
            
            for cache_type in CacheType:
                full_key = f"{cache_type.value}:{args.key}"
                entry = self.cache_manager.backend.get(full_key)
                if entry:
                    found_type = cache_type
                    break
            
            if not entry:
                print(f"Cache entry not found: {args.key}")
                return
            
            print(f"=== Cache Entry Details ===")
            print(f"Key: {entry.key}")
            print(f"Type: {entry.cache_type.value}")
            print(f"Created: {entry.created_at}")
            print(f"Last Accessed: {entry.last_accessed}")
            print(f"Access Count: {entry.access_count}")
            print(f"Size: {format_bytes(entry.size_bytes)}")
            print(f"TTL: {entry.ttl_seconds}s" if entry.ttl_seconds else "TTL: None")
            print(f"Expired: {'Yes' if entry.is_expired() else 'No'}")
            
            if entry.dependencies:
                print(f"Dependencies: {', '.join(entry.dependencies)}")
            
            if args.show_value:
                print(f"\n=== Value ===")
                if isinstance(entry.value, (dict, list)):
                    print(json.dumps(entry.value, indent=2, default=str))
                else:
                    print(entry.value)
                    
        except Exception as e:
            print(f"Error getting entry: {str(e)}")
    
    def report(self, args) -> None:
        """Generate performance report."""
        print("=== Cache Performance Report ===")
        
        try:
            report = self.cache_monitor.get_performance_report(hours=args.hours)
            
            print(f"Period: {report.period_start} to {report.period_end}")
            print(f"Duration: {format_duration((report.period_end - report.period_start).total_seconds())}")
            
            print(f"\n=== Request Statistics ===")
            print(f"Total Requests: {report.total_requests:,}")
            print(f"Cache Hits: {report.cache_hits:,}")
            print(f"Cache Misses: {report.cache_misses:,}")
            print(f"Hit Rate: {report.hit_rate:.1%}")
            print(f"Miss Rate: {report.miss_rate:.1%}")
            print(f"Average Response Time: {report.average_response_time_ms:.1f} ms")
            
            print(f"\n=== Cache Operations ===")
            print(f"Evictions: {report.evictions:,}")
            print(f"Errors: {report.errors:,}")
            
            print(f"\n=== Entries by Type ===")
            for cache_type, count in report.entries_by_type.items():
                size = format_bytes(report.size_by_type.get(cache_type, 0))
                print(f"{cache_type}: {count:,} entries ({size})")
            
            if args.json:
                print(f"\n=== JSON Report ===")
                print(json.dumps(report.to_dict(), indent=2, default=str))
                
        except Exception as e:
            print(f"Error generating report: {str(e)}")
    
    def config(self, args) -> None:
        """Show cache configuration."""
        print("=== Cache Configuration ===")
        
        config = get_config()
        
        print(f"Environment: {config.environment}")
        print(f"Caching Enabled: {config.processing.enable_caching}")
        print(f"Backend Type: {type(self.cache_manager.backend).__name__}")
        
        if hasattr(self.cache_manager.backend, 'table_name'):
            print(f"DynamoDB Table: {self.cache_manager.backend.table_name}")
            print(f"AWS Region: {self.cache_manager.backend.region_name}")
        
        print(f"\n=== Default TTL Values ===")
        for cache_type, ttl in self.cache_manager.default_ttls.items():
            print(f"{cache_type.value}: {format_duration(ttl)}")
    
    def test(self, args) -> None:
        """Test cache functionality."""
        print("=== Cache Functionality Test ===")
        
        test_key = "cli_test_key"
        test_value = {"test": True, "timestamp": datetime.utcnow().isoformat()}
        
        try:
            # Test put
            print("Testing cache put...")
            success = self.cache_manager.put(test_key, test_value, CacheType.API_RESPONSE, ttl_seconds=60)
            if success:
                print("✅ Put operation successful")
            else:
                print("❌ Put operation failed")
                return
            
            # Test get
            print("Testing cache get...")
            retrieved = self.cache_manager.get(test_key, CacheType.API_RESPONSE)
            if retrieved == test_value:
                print("✅ Get operation successful")
            else:
                print("❌ Get operation failed - value mismatch")
                return
            
            # Test delete
            print("Testing cache delete...")
            success = self.cache_manager.delete(test_key, CacheType.API_RESPONSE)
            if success:
                print("✅ Delete operation successful")
            else:
                print("❌ Delete operation failed")
                return
            
            # Verify deletion
            print("Verifying deletion...")
            retrieved = self.cache_manager.get(test_key, CacheType.API_RESPONSE)
            if retrieved is None:
                print("✅ Verification successful - entry deleted")
            else:
                print("❌ Verification failed - entry still exists")
                return
            
            print("\n🎉 All cache tests passed!")
            
        except Exception as e:
            print(f"❌ Cache test failed: {str(e)}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Biomerkin Cache Management CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show cache status and metrics')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear cache entries')
    clear_parser.add_argument('--type', help='Cache type to clear')
    clear_parser.add_argument('--all', action='store_true', help='Clear all cache entries')
    clear_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List cache keys')
    list_parser.add_argument('--type', help='Filter by cache type')
    list_parser.add_argument('--limit', type=int, help='Limit number of keys shown')
    list_parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get cache entry details')
    get_parser.add_argument('key', help='Cache key to retrieve')
    get_parser.add_argument('--show-value', action='store_true', help='Show cached value')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate performance report')
    report_parser.add_argument('--hours', type=int, default=24, help='Hours to include in report')
    report_parser.add_argument('--json', action='store_true', help='Output JSON format')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show cache configuration')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test cache functionality')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        cli = CacheCLI()
        command_method = getattr(cli, args.command)
        command_method(args)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()