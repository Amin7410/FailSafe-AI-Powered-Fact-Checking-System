"""
Unit tests for PerformanceService

Tests:
1. Performance metrics collection
2. System resource monitoring
3. Health status checks
4. Optimization suggestions
5. Context managers
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch
from app.services.performance_service import PerformanceService, get_performance_service


class TestPerformanceService:
    """Test suite for PerformanceService"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.service = PerformanceService()
        # Stop background monitoring for testing
        self.service.stop_monitoring.set()
    
    def teardown_method(self):
        """Cleanup test fixtures"""
        self.service.stop()
    
    def test_service_initialization(self):
        """Test performance service initialization"""
        assert self.service is not None
        assert hasattr(self.service, 'metrics')
        assert hasattr(self.service, 'monitoring_enabled')
        assert hasattr(self.service, 'time_operation')
        assert hasattr(self.service, 'time_model_inference')
    
    def test_time_operation_context_manager(self):
        """Test time_operation context manager"""
        with self.service.time_operation("test_operation"):
            time.sleep(0.1)  # Simulate work
        
        # Check that response time was recorded
        assert len(self.service.metrics.response_times) > 0
        assert self.service.metrics.response_times[-1] >= 0.1
    
    def test_time_model_inference_context_manager(self):
        """Test time_model_inference context manager"""
        model_name = "test_model"
        
        with self.service.time_model_inference(model_name):
            time.sleep(0.05)  # Simulate model inference
        
        # Check that model inference time was recorded
        assert model_name in self.service.metrics.model_inference_times
        assert len(self.service.metrics.model_inference_times[model_name]) > 0
        assert self.service.metrics.model_inference_times[model_name][-1] >= 0.05
    
    def test_cache_hit_miss_recording(self):
        """Test cache hit/miss recording"""
        # Record cache hits and misses
        self.service.record_cache_hit()
        self.service.record_cache_hit()
        self.service.record_cache_miss()
        
        assert self.service.metrics.cache_hits == 2
        assert self.service.metrics.cache_misses == 1
    
    def test_error_recording(self):
        """Test error recording"""
        self.service.record_error()
        self.service.record_error()
        
        assert self.service.metrics.error_count == 2
    
    def test_request_recording(self):
        """Test request recording"""
        self.service.record_request()
        self.service.record_request()
        self.service.record_request()
        
        assert self.service.metrics.request_count == 3
    
    def test_performance_stats(self):
        """Test performance statistics generation"""
        # Add some test data
        self.service.record_request()
        self.service.record_request()
        self.service.record_error()
        self.service.record_cache_hit()
        self.service.record_cache_miss()
        
        with self.service.time_operation("test"):
            time.sleep(0.01)
        
        stats = self.service.get_performance_stats()
        
        assert "timestamp" in stats
        assert "request_count" in stats
        assert "error_count" in stats
        assert "error_rate" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "cache_hit_rate" in stats
        
        assert stats["request_count"] == 2
        assert stats["error_count"] == 1
        assert stats["error_rate"] == 0.5
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["cache_hit_rate"] == 0.5
    
    def test_health_status_healthy(self):
        """Test health status when system is healthy"""
        # Add some normal metrics
        self.service.record_request()
        self.service.record_cache_hit()
        
        with self.service.time_operation("fast_operation"):
            time.sleep(0.01)  # Fast operation
        
        health = self.service.get_health_status()
        
        assert "status" in health
        assert "warnings" in health
        assert "stats" in health
        assert "timestamp" in health
        
        # Should be healthy with normal metrics
        assert health["status"] in ["healthy", "degraded"]
        assert isinstance(health["warnings"], list)
    
    def test_health_status_degraded(self):
        """Test health status when system is degraded"""
        # Add metrics that indicate degraded performance
        self.service.record_request()
        self.service.record_error()
        self.service.record_error()  # High error rate
        
        with self.service.time_operation("slow_operation"):
            time.sleep(0.1)  # Slow operation
        
        health = self.service.get_health_status()
        
        # Should detect degraded performance
        assert health["status"] in ["degraded", "unhealthy"]
    
    def test_optimization_suggestions(self):
        """Test optimization suggestions"""
        # Add metrics that should trigger suggestions
        self.service.record_request()
        self.service.record_cache_miss()
        self.service.record_cache_miss()  # Low cache hit rate
        
        with self.service.time_operation("slow_operation"):
            time.sleep(0.1)  # Slow operation
        
        suggestions = self.service.optimize_performance()
        
        assert "suggestions" in suggestions
        assert "total_suggestions" in suggestions
        assert "high_priority" in suggestions
        assert "timestamp" in suggestions
        
        assert isinstance(suggestions["suggestions"], list)
        assert suggestions["total_suggestions"] >= 0
        assert suggestions["high_priority"] >= 0
    
    def test_memory_usage_tracking(self):
        """Test memory usage tracking"""
        # Clear existing data first
        self.service.metrics.memory_usage.clear()
        
        # Manually add memory usage data
        self.service.metrics.add_memory_usage(100.0)  # 100MB
        self.service.metrics.add_memory_usage(200.0)  # 200MB
        self.service.metrics.add_memory_usage(150.0)  # 150MB
        
        stats = self.service.get_performance_stats()
        
        assert "memory_usage_mb" in stats
        memory_stats = stats["memory_usage_mb"]
        
        assert "avg" in memory_stats
        assert "min" in memory_stats
        assert "max" in memory_stats
        assert "current" in memory_stats
        
        assert abs(memory_stats["avg"] - 150.0) < 0.1
        assert memory_stats["min"] == 100.0
        assert memory_stats["max"] == 200.0
        assert memory_stats["current"] == 150.0
    
    def test_cpu_usage_tracking(self):
        """Test CPU usage tracking"""
        # Manually add CPU usage data
        self.service.metrics.add_cpu_usage(50.0)  # 50%
        self.service.metrics.add_cpu_usage(75.0)  # 75%
        self.service.metrics.add_cpu_usage(60.0)  # 60%
        
        stats = self.service.get_performance_stats()
        
        assert "cpu_usage_percent" in stats
        cpu_stats = stats["cpu_usage_percent"]
        
        assert "avg" in cpu_stats
        assert "min" in cpu_stats
        assert "max" in cpu_stats
        assert "current" in cpu_stats
        
        assert abs(cpu_stats["avg"] - 61.67) < 0.1
        assert cpu_stats["min"] == 50.0
        assert cpu_stats["max"] == 75.0
        assert cpu_stats["current"] == 60.0
    
    def test_model_inference_timing(self):
        """Test model inference timing statistics"""
        model_name = "test_model"
        
        # Add multiple inference times
        self.service.metrics.add_model_inference_time(model_name, 0.5)
        self.service.metrics.add_model_inference_time(model_name, 1.0)
        self.service.metrics.add_model_inference_time(model_name, 0.8)
        
        stats = self.service.get_performance_stats()
        
        assert "model_inference_times" in stats
        model_stats = stats["model_inference_times"]
        
        assert model_name in model_stats
        model_times = model_stats[model_name]
        
        assert "avg" in model_times
        assert "min" in model_times
        assert "max" in model_times
        assert "count" in model_times
        
        assert abs(model_times["avg"] - 0.77) < 0.1
        assert model_times["min"] == 0.5
        assert model_times["max"] == 1.0
        assert model_times["count"] == 3
    
    def test_global_performance_service(self):
        """Test global performance service instance"""
        service1 = get_performance_service()
        service2 = get_performance_service()
        
        # Should return the same instance
        assert service1 is service2
    
    def test_service_stop(self):
        """Test service stop functionality"""
        # Create a new service for this test
        test_service = PerformanceService()
        
        # Stop the service
        test_service.stop()
        
        # Should not raise any exceptions
        assert test_service.monitoring_enabled == False
    
    def test_metrics_initialization(self):
        """Test metrics initialization"""
        from app.services.performance_service import PerformanceMetrics
        
        metrics = PerformanceMetrics()
        
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.error_count == 0
        assert metrics.request_count == 0
        assert len(metrics.response_times) == 0
        assert len(metrics.memory_usage) == 0
        assert len(metrics.cpu_usage) == 0
        assert len(metrics.model_inference_times) == 0
    
    def test_metrics_add_methods(self):
        """Test metrics add methods"""
        from app.services.performance_service import PerformanceMetrics
        
        metrics = PerformanceMetrics()
        
        # Test adding data
        metrics.add_response_time(1.5)
        metrics.add_memory_usage(256.0)
        metrics.add_cpu_usage(75.0)
        metrics.add_model_inference_time("model1", 0.8)
        
        assert len(metrics.response_times) == 1
        assert len(metrics.memory_usage) == 1
        assert len(metrics.cpu_usage) == 1
        assert len(metrics.model_inference_times["model1"]) == 1
        
        assert metrics.response_times[0] == 1.5
        assert metrics.memory_usage[0] == 256.0
        assert metrics.cpu_usage[0] == 75.0
        assert metrics.model_inference_times["model1"][0] == 0.8


if __name__ == "__main__":
    pytest.main([__file__])
