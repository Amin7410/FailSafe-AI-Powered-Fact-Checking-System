"""
Performance Monitoring API Endpoints

Provides endpoints for:
1. Performance statistics
2. Health status
3. Cache statistics
4. System metrics
5. Performance optimization suggestions
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services.monitoring_service import monitoring_service
# from app.services.cache_service import get_cache

router = APIRouter(prefix="/monitor")


@router.get("/health")
def get_health_status() -> Dict[str, Any]:
    """Get system health status"""
    try:
        performance_service = get_performance_service()
        return performance_service.get_health_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/performance")
def get_performance_stats() -> Dict[str, Any]:
    """Get performance statistics"""
    try:
        performance_service = get_performance_service()
        return performance_service.get_performance_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance stats failed: {str(e)}")


@router.get("/cache")
def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    try:
        cache_service = get_cache()
        return cache_service.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache stats failed: {str(e)}")


@router.get("/optimization")
def get_optimization_suggestions() -> Dict[str, Any]:
    """Get performance optimization suggestions"""
    try:
        performance_service = get_performance_service()
        return performance_service.optimize_performance()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization suggestions failed: {str(e)}")


@router.get("/metrics")
def get_all_metrics() -> Dict[str, Any]:
    """Get all monitoring metrics"""
    try:
        performance_service = get_performance_service()
        cache_service = get_cache()
        
        return {
            "health": performance_service.get_health_status(),
            "performance": performance_service.get_performance_stats(),
            "cache": cache_service.get_stats(),
            "optimization": performance_service.optimize_performance()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics collection failed: {str(e)}")


@router.post("/cache/clear")
def clear_cache() -> Dict[str, str]:
    """Clear all cache"""
    try:
        cache_service = get_cache()
        cache_service.clear()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")


@router.get("/status")
def get_system_status() -> Dict[str, Any]:
    """Get overall system status"""
    try:
        performance_service = get_performance_service()
        cache_service = get_cache()
        
        health = performance_service.get_health_status()
        performance = performance_service.get_performance_stats()
        cache = cache_service.get_stats()
        
        # Determine overall status
        overall_status = "healthy"
        if health["status"] == "unhealthy":
            overall_status = "unhealthy"
        elif health["status"] == "degraded":
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": health["timestamp"],
            "services": {
                "performance_monitoring": "active",
                "caching": "active",
                "health_checks": "active"
            },
            "summary": {
                "total_requests": performance.get("request_count", 0),
                "error_rate": performance.get("error_rate", 0),
                "cache_hit_rate": performance.get("cache_hit_rate", 0),
                "avg_response_time": performance.get("response_time", {}).get("avg", 0)
            },
            "warnings": health.get("warnings", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System status failed: {str(e)}")
