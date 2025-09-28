"""
Cache Service for FailSafe

Provides efficient caching for:
1. API responses
2. Model predictions
3. Embeddings
4. SAG generation
5. Evidence retrieval
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, Optional, Union
from pathlib import Path
import pickle
import gzip

from ..core.config import get_settings


class CacheService:
    """
    High-performance caching service with multiple backends.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.disk_cache_dir = Path("data/cache")
        self.disk_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache configuration
        self.max_memory_items = self.settings.cache.get("max_memory_items", 1000)
        self.memory_ttl = self.settings.cache.get("memory_ttl_seconds", 300)  # 5 minutes
        self.disk_ttl = self.settings.cache.get("disk_ttl_seconds", 3600)    # 1 hour
        self.max_disk_size_mb = self.settings.cache.get("max_disk_size_mb", 100)
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate a cache key from data"""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        hash_obj = hashlib.md5(data_str.encode())
        return f"{prefix}:{hash_obj.hexdigest()}"
    
    def _is_expired(self, timestamp: float, ttl: float) -> bool:
        """Check if cache entry is expired"""
        return time.time() - timestamp > ttl
    
    def _cleanup_memory_cache(self):
        """Clean up expired entries from memory cache"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.memory_cache.items():
            entry_ttl = entry.get("ttl", self.memory_ttl)
            if self._is_expired(entry["timestamp"], entry_ttl):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        # If still too many items, remove oldest
        if len(self.memory_cache) > self.max_memory_items:
            sorted_items = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1]["timestamp"]
            )
            items_to_remove = len(self.memory_cache) - self.max_memory_items
            for key, _ in sorted_items[:items_to_remove]:
                del self.memory_cache[key]
    
    def _get_disk_path(self, key: str) -> Path:
        """Get disk cache file path"""
        return self.disk_cache_dir / f"{key}.cache.gz"
    
    def _cleanup_disk_cache(self):
        """Clean up expired entries from disk cache"""
        current_time = time.time()
        total_size = 0
        
        for cache_file in self.disk_cache_dir.glob("*.cache.gz"):
            try:
                with gzip.open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                
                if self._is_expired(entry["timestamp"], self.disk_ttl):
                    cache_file.unlink()
                    continue
                
                # Check disk size limit
                file_size = cache_file.stat().st_size
                total_size += file_size
                
                if total_size > self.max_disk_size_mb * 1024 * 1024:
                    # Remove oldest files
                    cache_file.unlink()
                    
            except (pickle.PickleError, EOFError, OSError):
                # Corrupted file, remove it
                cache_file.unlink()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        # Try memory cache first
        if key in self.memory_cache:
            entry = self.memory_cache[key]
            entry_ttl = entry.get("ttl", self.memory_ttl)
            if not self._is_expired(entry["timestamp"], entry_ttl):
                return entry["value"]
            else:
                del self.memory_cache[key]
        
        # Try disk cache
        disk_path = self._get_disk_path(key)
        if disk_path.exists():
            try:
                with gzip.open(disk_path, 'rb') as f:
                    entry = pickle.load(f)
                
                entry_ttl = entry.get("ttl", self.disk_ttl)
                if not self._is_expired(entry["timestamp"], entry_ttl):
                    # Promote to memory cache
                    self.memory_cache[key] = entry
                    return entry["value"]
                else:
                    disk_path.unlink()
            except (pickle.PickleError, EOFError, OSError):
                disk_path.unlink()
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache"""
        current_time = time.time()
        cache_ttl = ttl or self.memory_ttl
        
        entry = {
            "value": value,
            "timestamp": current_time,
            "ttl": cache_ttl
        }
        
        # Store in memory cache
        self.memory_cache[key] = entry
        
        # Store in disk cache for larger TTL
        if cache_ttl > self.memory_ttl:
            disk_path = self._get_disk_path(key)
            try:
                with gzip.open(disk_path, 'wb') as f:
                    pickle.dump(entry, f)
            except (OSError, pickle.PickleError):
                pass  # Ignore disk cache errors
        
        # Cleanup if needed
        if len(self.memory_cache) > self.max_memory_items:
            self._cleanup_memory_cache()
    
    def delete(self, key: str) -> None:
        """Delete value from cache"""
        # Remove from memory cache
        self.memory_cache.pop(key, None)
        
        # Remove from disk cache
        disk_path = self._get_disk_path(key)
        if disk_path.exists():
            disk_path.unlink()
    
    def clear(self) -> None:
        """Clear all cache"""
        self.memory_cache.clear()
        
        # Clear disk cache
        for cache_file in self.disk_cache_dir.glob("*.cache.gz"):
            cache_file.unlink()
    
    def get_or_set(self, key: str, factory_func, ttl: Optional[float] = None) -> Any:
        """Get value from cache or set it using factory function"""
        value = self.get(key)
        if value is None:
            value = factory_func()
            self.set(key, value, ttl)
        return value
    
    def cache_result(self, prefix: str, ttl: Optional[float] = None):
        """Decorator for caching function results"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                if args and hasattr(args[0], func.__name__):
                    # Đây là một phương thức, args[1:] là các tham số thực sự
                    cache_args = args[1:]
                else:
                    # Đây là một hàm thông thường
                    cache_args = args

                # Generate cache key from function name and relevant arguments
                cache_key = self._generate_key(
                    f"{prefix}:{func.__name__}",
                    {"args": cache_args, "kwargs": kwargs} # <-- Chỉ dùng cache_args
                )
                
                # Try to get from cache
                result = self.get(cache_key)
                if result is not None:
                    return result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                return result
            
            return wrapper
        return decorator
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        memory_size = len(self.memory_cache)
        disk_files = list(self.disk_cache_dir.glob("*.cache.gz"))
        disk_size = sum(f.stat().st_size for f in disk_files)
        
        return {
            "memory_items": memory_size,
            "disk_files": len(disk_files),
            "disk_size_mb": disk_size / (1024 * 1024),
            "max_memory_items": self.max_memory_items,
            "memory_ttl": self.memory_ttl,
            "disk_ttl": self.disk_ttl
        }


# Global cache instance
_cache_instance: Optional[CacheService] = None


def get_cache() -> CacheService:
    """Get global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance


# Convenience functions
def cache_get(key: str) -> Optional[Any]:
    """Get value from global cache"""
    return get_cache().get(key)


def cache_set(key: str, value: Any, ttl: Optional[float] = None) -> None:
    """Set value in global cache"""
    get_cache().set(key, value, ttl)


def cache_delete(key: str) -> None:
    """Delete value from global cache"""
    get_cache().delete(key)


def cache_clear() -> None:
    """Clear global cache"""
    get_cache().clear()


def cached(prefix: str, ttl: Optional[float] = None):
    """Decorator for caching function results"""
    return get_cache().cache_result(prefix, ttl)
