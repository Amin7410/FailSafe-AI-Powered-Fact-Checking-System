"""
Performance Monitoring Service for FailSafe

Provides lightweight performance monitoring and optimization:
1. Response time tracking
2. Memory usage monitoring
3. CPU usage tracking
4. Model inference timing
5. Cache hit/miss ratios
6. Performance metrics collection
"""

from __future__ import annotations

import time
import psutil
import threading
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from contextlib import contextmanager
import json

from ..core.config import get_settings


class PerformanceMetrics:
    """Container for performance metrics"""
    
    def __init__(self):
        self.response_times: deque = deque(maxlen=1000)
        self.memory_usage: deque = deque(maxlen=1000)
        self.cpu_usage: deque = deque(maxlen=1000)
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.model_inference_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.error_count: int = 0
        self.request_count: int = 0
        self.last_updated: datetime = datetime.now()
    
    def add_response_time(self, duration: float):
        """Add response time measurement"""
        self.response_times.append(duration)
        self.last_updated = datetime.now()
    
    def add_memory_usage(self, memory_mb: float):
        """Add memory usage measurement"""
        self.memory_usage.append(memory_mb)
    
    def add_cpu_usage(self, cpu_percent: float):
        """Add CPU usage measurement"""
        self.cpu_usage.append(cpu_percent)
    
    def add_model_inference_time(self, model_name: str, duration: float):
        """Add model inference time"""
        self.model_inference_times[model_name].append(duration)
    
    def increment_cache_hit(self):
        """Increment cache hit counter"""
        self.cache_hits += 1
    
    def increment_cache_miss(self):
        """Increment cache miss counter"""
        self.cache_misses += 1
    
    def increment_error(self):
        """Increment error counter"""
        self.error_count += 1
    
    def increment_request(self):
        """Increment request counter"""
        self.request_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        stats = {
            "timestamp": self.last_updated.isoformat(),
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self.cache_hits / max(self.cache_hits + self.cache_misses, 1),
        }
        
        # Response time statistics
        if self.response_times:
            response_times = list(self.response_times)
            stats["response_time"] = {
                "avg": sum(response_times) / len(response_times),
                "min": min(response_times),
                "max": max(response_times),
                "p95": sorted(response_times)[int(len(response_times) * 0.95)],
                "count": len(response_times)
            }
        
        # Memory usage statistics
        if self.memory_usage:
            memory_usage = list(self.memory_usage)
            stats["memory_usage_mb"] = {
                "avg": sum(memory_usage) / len(memory_usage),
                "min": min(memory_usage),
                "max": max(memory_usage),
                "current": memory_usage[-1] if memory_usage else 0
            }
        
        # CPU usage statistics
        if self.cpu_usage:
            cpu_usage = list(self.cpu_usage)
            stats["cpu_usage_percent"] = {
                "avg": sum(cpu_usage) / len(cpu_usage),
                "min": min(cpu_usage),
                "max": max(cpu_usage),
                "current": cpu_usage[-1] if cpu_usage else 0
            }
        
        # Model inference time statistics
        model_stats = {}
        for model_name, times in self.model_inference_times.items():
            if times:
                times_list = list(times)
                model_stats[model_name] = {
                    "avg": sum(times_list) / len(times_list),
                    "min": min(times_list),
                    "max": max(times_list),
                    "count": len(times_list)
                }
        stats["model_inference_times"] = model_stats
        
        return stats


class PerformanceService:
    """Performance monitoring and optimization service"""
    
    def __init__(self):
        self.settings = get_settings()
        self.metrics = PerformanceMetrics()
        self.monitoring_enabled = True
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_monitoring = threading.Event()
        
        # Start background monitoring
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start background performance monitoring"""
        if not self.monitoring_enabled:
            return
        
        self.monitor_thread = threading.Thread(
            target=self._monitor_system_resources,
            daemon=True
        )
        self.monitor_thread.start()
    
    def _monitor_system_resources(self):
        """Monitor system resources in background"""
        while not self.stop_monitoring.is_set():
            try:
                # Get memory usage
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.metrics.add_memory_usage(memory_mb)
                
                # Get CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics.add_cpu_usage(cpu_percent)
                
            except Exception:
                pass  # Ignore monitoring errors
            
            # Sleep for 5 seconds
            self.stop_monitoring.wait(5)
    
    @contextmanager
    def time_operation(self, operation_name: str):
        """Context manager for timing operations"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.metrics.add_response_time(duration)
    
    @contextmanager
    def time_model_inference(self, model_name: str):
        """Context manager for timing model inference"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.metrics.add_model_inference_time(model_name, duration)
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.metrics.increment_cache_hit()
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.metrics.increment_cache_miss()
    
    def record_error(self):
        """Record error occurrence"""
        self.metrics.increment_error()
    
    def record_request(self):
        """Record request"""
        self.metrics.increment_request()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        return self.metrics.get_stats()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        stats = self.get_performance_stats()
        
        # Determine health status
        health_status = "healthy"
        warnings = []
        
        # Check response time
        if "response_time" in stats:
            avg_response_time = stats["response_time"]["avg"]
            if avg_response_time > 5.0:  # 5 seconds
                health_status = "degraded"
                warnings.append(f"High response time: {avg_response_time:.2f}s")
        
        # Check error rate
        error_rate = stats.get("error_rate", 0)
        if error_rate > 0.05:  # 5% error rate
            health_status = "unhealthy"
            warnings.append(f"High error rate: {error_rate:.2%}")
        
        # Check memory usage
        if "memory_usage_mb" in stats:
            current_memory = stats["memory_usage_mb"]["current"]
            if current_memory > 1000:  # 1GB
                health_status = "degraded"
                warnings.append(f"High memory usage: {current_memory:.1f}MB")
        
        # Check CPU usage
        if "cpu_usage_percent" in stats:
            current_cpu = stats["cpu_usage_percent"]["current"]
            if current_cpu > 80:  # 80% CPU
                health_status = "degraded"
                warnings.append(f"High CPU usage: {current_cpu:.1f}%")
        
        return {
            "status": health_status,
            "warnings": warnings,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def optimize_performance(self) -> Dict[str, Any]:
        """Suggest performance optimizations"""
        stats = self.get_performance_stats()
        suggestions = []
        
        # Cache optimization suggestions
        cache_hit_rate = stats.get("cache_hit_rate", 0)
        if cache_hit_rate < 0.7:  # 70% cache hit rate
            suggestions.append({
                "type": "cache_optimization",
                "priority": "medium",
                "description": f"Low cache hit rate ({cache_hit_rate:.1%}). Consider increasing cache TTL or improving cache keys.",
                "action": "Review cache configuration and key generation"
            })
        
        # Response time optimization
        if "response_time" in stats:
            avg_response_time = stats["response_time"]["avg"]
            if avg_response_time > 2.0:  # 2 seconds
                suggestions.append({
                    "type": "response_time_optimization",
                    "priority": "high",
                    "description": f"High average response time ({avg_response_time:.2f}s). Consider caching or model optimization.",
                    "action": "Implement response caching or optimize model inference"
                })
        
        # Memory optimization
        if "memory_usage_mb" in stats:
            current_memory = stats["memory_usage_mb"]["current"]
            if current_memory > 500:  # 500MB
                suggestions.append({
                    "type": "memory_optimization",
                    "priority": "medium",
                    "description": f"High memory usage ({current_memory:.1f}MB). Consider model quantization or memory cleanup.",
                    "action": "Implement model quantization or memory management"
                })
        
        # Model optimization
        for model_name, model_stats in stats.get("model_inference_times", {}).items():
            avg_time = model_stats["avg"]
            if avg_time > 1.0:  # 1 second
                suggestions.append({
                    "type": "model_optimization",
                    "priority": "high",
                    "description": f"Slow model inference for {model_name} ({avg_time:.2f}s). Consider model optimization.",
                    "action": f"Optimize {model_name} model or implement caching"
                })
        
        return {
            "suggestions": suggestions,
            "total_suggestions": len(suggestions),
            "high_priority": len([s for s in suggestions if s["priority"] == "high"]),
            "timestamp": datetime.now().isoformat()
        }
    
    def stop(self):
        """Stop performance monitoring"""
        self.monitoring_enabled = False
        if self.monitor_thread:
            self.stop_monitoring.set()
            self.monitor_thread.join(timeout=5)


# Global performance service instance
_performance_instance: Optional[PerformanceService] = None


def get_performance_service() -> PerformanceService:
    """Get global performance service instance"""
    global _performance_instance
    if _performance_instance is None:
        _performance_instance = PerformanceService()
    return _performance_instance


# Convenience functions
def time_operation(operation_name: str):
    """Context manager for timing operations"""
    return get_performance_service().time_operation(operation_name)


def time_model_inference(model_name: str):
    """Context manager for timing model inference"""
    return get_performance_service().time_model_inference(model_name)


def record_cache_hit():
    """Record cache hit"""
    get_performance_service().record_cache_hit()


def record_cache_miss():
    """Record cache miss"""
    get_performance_service().record_cache_miss()


def record_error():
    """Record error"""
    get_performance_service().record_error()


def record_request():
    """Record request"""
    get_performance_service().record_request()
