"""
Unit tests for CacheService

Tests:
1. Basic cache operations
2. TTL functionality
3. Memory and disk cache
4. Cache cleanup
5. Performance
"""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from app.services.cache_service import CacheService, get_cache, cache_get, cache_set, cache_delete, cache_clear


class TestCacheService:
    """Test suite for CacheService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        # Create temporary directory for disk cache
        self.temp_dir = tempfile.mkdtemp()
        self.cache = CacheService()
        # Override disk cache directory for testing
        self.cache.disk_cache_dir = Path(self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_initialization(self):
        """Test cache service initialization"""
        assert self.cache is not None
        assert hasattr(self.cache, 'get')
        assert hasattr(self.cache, 'set')
        assert hasattr(self.cache, 'delete')
        assert hasattr(self.cache, 'clear')
        assert hasattr(self.cache, 'get_or_set')
    
    def test_basic_cache_operations(self):
        """Test basic cache operations"""
        key = "test_key"
        value = "test_value"
        
        # Test set and get
        self.cache.set(key, value)
        result = self.cache.get(key)
        assert result == value
        
        # Test delete
        self.cache.delete(key)
        result = self.cache.get(key)
        assert result is None
    
    def test_cache_ttl(self):
        """Test cache TTL functionality"""
        key = "ttl_test"
        value = "ttl_value"
        
        # Set with short TTL
        self.cache.set(key, value, ttl=0.1)  # 100ms
        result = self.cache.get(key)
        assert result == value
        
        # Wait for expiration
        time.sleep(0.2)
        result = self.cache.get(key)
        assert result is None
    
    def test_cache_get_or_set(self):
        """Test get_or_set functionality"""
        key = "get_or_set_test"
        call_count = 0
        
        def factory_func():
            nonlocal call_count
            call_count += 1
            return f"generated_value_{call_count}"
        
        # First call should execute factory function
        result1 = self.cache.get_or_set(key, factory_func)
        assert result1 == "generated_value_1"
        assert call_count == 1
        
        # Second call should return cached value
        result2 = self.cache.get_or_set(key, factory_func)
        assert result2 == "generated_value_1"
        assert call_count == 1  # Should not be called again
    
    def test_cache_with_complex_data(self):
        """Test cache with complex data structures"""
        key = "complex_data"
        value = {
            "string": "test",
            "number": 42,
            "list": [1, 2, 3],
            "nested": {"key": "value"}
        }
        
        self.cache.set(key, value)
        result = self.cache.get(key)
        assert result == value
        assert result["nested"]["key"] == "value"
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        prefix = "test_prefix"
        data1 = {"key": "value1"}
        data2 = {"key": "value2"}
        
        key1 = self.cache._generate_key(prefix, data1)
        key2 = self.cache._generate_key(prefix, data2)
        
        assert key1 != key2
        assert key1.startswith(prefix)
        assert key2.startswith(prefix)
        
        # Same data should generate same key
        key1_again = self.cache._generate_key(prefix, data1)
        assert key1 == key1_again
    
    def test_cache_cleanup(self):
        """Test cache cleanup functionality"""
        # Set multiple items
        for i in range(5):
            self.cache.set(f"key_{i}", f"value_{i}", ttl=0.1)
        
        # Wait for expiration
        time.sleep(0.2)
        
        # Trigger cleanup
        self.cache._cleanup_memory_cache()
        
        # All items should be expired
        for i in range(5):
            result = self.cache.get(f"key_{i}")
            assert result is None
    
    def test_cache_limit(self):
        """Test cache size limits"""
        # Set more items than the limit
        max_items = 3
        self.cache.max_memory_items = max_items
        
        for i in range(5):
            self.cache.set(f"key_{i}", f"value_{i}")
        
        # Should only keep the most recent items
        assert len(self.cache.memory_cache) <= max_items
        
        # Check that some items are still accessible
        result = self.cache.get("key_4")
        assert result == "value_4"
    
    def test_disk_cache(self):
        """Test disk cache functionality"""
        key = "disk_test"
        value = "disk_value"
        
        # Set with long TTL to trigger disk storage
        self.cache.set(key, value, ttl=3600)  # 1 hour
        
        # Check that disk file was created
        disk_path = self.cache._get_disk_path(key)
        assert disk_path.exists()
        
        # Clear memory cache and test disk retrieval
        self.cache.memory_cache.clear()
        result = self.cache.get(key)
        assert result == value
    
    def test_cache_decorator(self):
        """Test cache decorator functionality"""
        call_count = 0
        
        @self.cache.cache_result("test_decorator", ttl=60)
        def test_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # First call
        result1 = test_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # Second call should use cache
        result2 = test_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # Should not be called again
        
        # Different arguments should call function
        result3 = test_function(2, 3)
        assert result3 == 5
        assert call_count == 2
    
    def test_cache_clear(self):
        """Test cache clear functionality"""
        # Set some items
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        # Clear cache
        self.cache.clear()
        
        # All items should be gone
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None
        assert len(self.cache.memory_cache) == 0
    
    def test_cache_stats(self):
        """Test cache statistics"""
        # Set some items
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        
        stats = self.cache.get_stats()
        
        assert "memory_items" in stats
        assert "disk_files" in stats
        assert "disk_size_mb" in stats
        assert stats["memory_items"] >= 2
    
    def test_global_cache_functions(self):
        """Test global cache convenience functions"""
        key = "global_test"
        value = "global_value"
        
        # Test global functions
        cache_set(key, value)
        result = cache_get(key)
        assert result == value
        
        cache_delete(key)
        result = cache_get(key)
        assert result is None
    
    def test_global_cache_clear(self):
        """Test global cache clear"""
        # Set some items
        cache_set("key1", "value1")
        cache_set("key2", "value2")
        
        # Clear cache
        cache_clear()
        
        # All items should be gone
        assert cache_get("key1") is None
        assert cache_get("key2") is None
    
    def test_cache_error_handling(self):
        """Test cache error handling"""
        # Test with invalid data
        key = "error_test"
        value = object()  # Non-serializable object
        
        # Should not raise exception
        self.cache.set(key, value)
        result = self.cache.get(key)
        # Result might be None due to serialization issues
        assert result is None or result == value
    
    def test_cache_performance(self):
        """Test cache performance"""
        # Test cache performance with many operations
        start_time = time.time()
        
        for i in range(100):
            self.cache.set(f"perf_key_{i}", f"perf_value_{i}")
        
        for i in range(100):
            result = self.cache.get(f"perf_key_{i}")
            assert result == f"perf_value_{i}"
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time (1 second)
        assert duration < 1.0


if __name__ == "__main__":
    pytest.main([__file__])
