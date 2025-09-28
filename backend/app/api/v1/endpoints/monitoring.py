"""
API endpoints for monitoring and observability
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from app.services.monitoring_service import (
    MonitoringService, LogLevel, AlertSeverity, MetricType
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

# Initialize monitoring service
monitoring_service = MonitoringService()

# Start monitoring
monitoring_service.start_monitoring()

# Request/Response Models
class LogQuery(BaseModel):
    level: Optional[str] = None
    component: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100

class MetricQuery(BaseModel):
    name: Optional[str] = None
    component: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 1000

class AlertQuery(BaseModel):
    severity: Optional[str] = None
    component: Optional[str] = None
    resolved: Optional[bool] = None
    limit: int = 100

class HealthCheckQuery(BaseModel):
    component: Optional[str] = None
    status: Optional[str] = None
    limit: int = 100

class AlertRuleRequest(BaseModel):
    name: str
    metric_name: str
    threshold: float
    operator: str
    severity: str
    component: Optional[str] = None

class MetricRequest(BaseModel):
    name: str
    value: float
    metric_type: str
    component: str
    tags: Optional[Dict[str, str]] = None

# Logs endpoints
@router.get("/logs")
async def get_logs(
    level: Optional[str] = Query(None, description="Filter by log level"),
    component: Optional[str] = Query(None, description="Filter by component"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    limit: int = Query(100, description="Maximum number of logs to return")
):
    """Get structured logs with filtering"""
    try:
        log_level = LogLevel(level) if level else None
        logs = monitoring_service.logger.get_logs(
            level=log_level,
            component=component,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return {
            "success": True,
            "logs": [
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "level": log.level.value,
                    "service": log.service,
                    "component": log.component,
                    "message": log.message,
                    "context": log.context,
                    "trace_id": log.trace_id,
                    "user_id": log.user_id,
                    "request_id": log.request_id
                }
                for log in logs
            ],
            "count": len(logs)
        }
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logs")
async def create_log(
    level: str,
    component: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None
):
    """Create a new log entry"""
    try:
        log_level = LogLevel(level)
        monitoring_service.logger.log(
            level=log_level,
            component=component,
            message=message,
            context=context or {},
            trace_id=trace_id,
            user_id=user_id,
            request_id=request_id
        )
        
        return {
            "success": True,
            "message": "Log entry created"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid log level: {e}")
    except Exception as e:
        logger.error(f"Error creating log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Metrics endpoints
@router.get("/metrics")
async def get_metrics(
    name: Optional[str] = Query(None, description="Filter by metric name"),
    component: Optional[str] = Query(None, description="Filter by component"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    limit: int = Query(1000, description="Maximum number of metrics to return")
):
    """Get metrics with filtering"""
    try:
        metrics = monitoring_service.metrics_collector.get_metrics(
            name=name,
            component=component,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return {
            "success": True,
            "metrics": [
                {
                    "id": metric.id,
                    "name": metric.name,
                    "value": metric.value,
                    "metric_type": metric.metric_type.value,
                    "timestamp": metric.timestamp.isoformat(),
                    "tags": metric.tags,
                    "service": metric.service,
                    "component": metric.component
                }
                for metric in metrics
            ],
            "count": len(metrics)
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metrics")
async def record_metric(request: MetricRequest):
    """Record a new metric"""
    try:
        metric_type = MetricType(request.metric_type)
        monitoring_service.metrics_collector.record_metric(
            name=request.name,
            value=request.value,
            metric_type=metric_type,
            component=request.component,
            tags=request.tags or {}
        )
        
        return {
            "success": True,
            "message": "Metric recorded"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid metric type: {e}")
    except Exception as e:
        logger.error(f"Error recording metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/{metric_name}/summary")
async def get_metric_summary(
    metric_name: str,
    component: Optional[str] = Query(None, description="Filter by component")
):
    """Get summary statistics for a specific metric"""
    try:
        summary = monitoring_service.metrics_collector.get_metric_summary(
            name=metric_name,
            component=component
        )
        
        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Error getting metric summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metrics/counter/{name}/increment")
async def increment_counter(
    name: str,
    component: str,
    tags: Optional[Dict[str, str]] = None
):
    """Increment a counter metric"""
    try:
        monitoring_service.metrics_collector.increment_counter(
            name=name,
            component=component,
            tags=tags or {}
        )
        
        return {
            "success": True,
            "message": "Counter incremented"
        }
    except Exception as e:
        logger.error(f"Error incrementing counter: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metrics/gauge/{name}")
async def set_gauge(
    name: str,
    value: float,
    component: str,
    tags: Optional[Dict[str, str]] = None
):
    """Set a gauge metric"""
    try:
        monitoring_service.metrics_collector.set_gauge(
            name=name,
            value=value,
            component=component,
            tags=tags or {}
        )
        
        return {
            "success": True,
            "message": "Gauge set"
        }
    except Exception as e:
        logger.error(f"Error setting gauge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Alerts endpoints
@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    component: Optional[str] = Query(None, description="Filter by component"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    limit: int = Query(100, description="Maximum number of alerts to return")
):
    """Get alerts with filtering"""
    try:
        alert_severity = AlertSeverity(severity) if severity else None
        alerts = monitoring_service.alert_manager.get_alerts(
            severity=alert_severity,
            component=component,
            resolved=resolved,
            limit=limit
        )
        
        return {
            "success": True,
            "alerts": [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity.value,
                    "service": alert.service,
                    "component": alert.component,
                    "metric_name": alert.metric_name,
                    "threshold_value": alert.threshold_value,
                    "current_value": alert.current_value,
                    "timestamp": alert.timestamp.isoformat(),
                    "resolved": alert.resolved,
                    "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
                }
                for alert in alerts
            ],
            "count": len(alerts)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid severity: {e}")
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/rules")
async def add_alert_rule(request: AlertRuleRequest):
    """Add a new alert rule"""
    try:
        severity = AlertSeverity(request.severity)
        monitoring_service.alert_manager.add_alert_rule(
            name=request.name,
            metric_name=request.metric_name,
            threshold=request.threshold,
            operator=request.operator,
            severity=severity,
            component=request.component
        )
        
        return {
            "success": True,
            "message": "Alert rule added"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid severity: {e}")
    except Exception as e:
        logger.error(f"Error adding alert rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert"""
    try:
        monitoring_service.alert_manager.resolve_alert(alert_id)
        
        return {
            "success": True,
            "message": "Alert resolved"
        }
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/check")
async def check_alerts():
    """Manually trigger alert checking"""
    try:
        monitoring_service.alert_manager.check_alerts(monitoring_service.metrics_collector)
        
        return {
            "success": True,
            "message": "Alert checking completed"
        }
    except Exception as e:
        logger.error(f"Error checking alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health checks endpoints
@router.get("/health")
async def get_health_checks(
    component: Optional[str] = Query(None, description="Filter by component"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, description="Maximum number of health checks to return")
):
    """Get health checks with filtering"""
    try:
        health_checks = monitoring_service.health_checker.get_health_checks(
            component=component,
            status=status,
            limit=limit
        )
        
        return {
            "success": True,
            "health_checks": [
                {
                    "service": hc.service,
                    "component": hc.component,
                    "status": hc.status,
                    "timestamp": hc.timestamp.isoformat(),
                    "response_time_ms": hc.response_time_ms,
                    "details": hc.details,
                    "error": hc.error
                }
                for hc in health_checks
            ],
            "count": len(health_checks)
        }
    except Exception as e:
        logger.error(f"Error getting health checks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/health/{check_name}")
async def run_health_check(check_name: str):
    """Run a specific health check"""
    try:
        health_check = await monitoring_service.health_checker.run_health_check(check_name)
        
        return {
            "success": True,
            "health_check": {
                "service": health_check.service,
                "component": health_check.component,
                "status": health_check.status,
                "timestamp": health_check.timestamp.isoformat(),
                "response_time_ms": health_check.response_time_ms,
                "details": health_check.details,
                "error": health_check.error
            }
        }
    except Exception as e:
        logger.error(f"Error running health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/health/run-all")
async def run_all_health_checks():
    """Run all health checks"""
    try:
        health_checks = await monitoring_service.health_checker.run_all_health_checks()
        
        return {
            "success": True,
            "health_checks": [
                {
                    "service": hc.service,
                    "component": hc.component,
                    "status": hc.status,
                    "timestamp": hc.timestamp.isoformat(),
                    "response_time_ms": hc.response_time_ms,
                    "details": hc.details,
                    "error": hc.error
                }
                for hc in health_checks
            ],
            "count": len(health_checks)
        }
    except Exception as e:
        logger.error(f"Error running health checks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System status endpoints
@router.get("/status")
async def get_system_status():
    """Get overall system status"""
    try:
        status = monitoring_service.get_system_status()
        
        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
async def get_metrics_dashboard():
    """Get metrics dashboard data"""
    try:
        dashboard = monitoring_service.get_metrics_dashboard()
        
        return {
            "success": True,
            "dashboard": dashboard
        }
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Utility endpoints
@router.get("/log-levels")
async def get_log_levels():
    """Get available log levels"""
    return {
        "success": True,
        "log_levels": [level.value for level in LogLevel]
    }

@router.get("/alert-severities")
async def get_alert_severities():
    """Get available alert severities"""
    return {
        "success": True,
        "alert_severities": [severity.value for severity in AlertSeverity]
    }

@router.get("/metric-types")
async def get_metric_types():
    """Get available metric types"""
    return {
        "success": True,
        "metric_types": [metric_type.value for metric_type in MetricType]
    }

@router.get("/components")
async def get_components():
    """Get list of monitored components"""
    # This would typically come from a configuration or be dynamically discovered
    return {
        "success": True,
        "components": [
            "system",
            "api",
            "analysis",
            "verification",
            "retrieval",
            "fallacy_detection",
            "ai_detection",
            "sag_generation",
            "provenance",
            "collaboration"
        ]
    }

# Cleanup endpoint
@router.delete("/logs")
async def clear_logs():
    """Clear all logs (use with caution)"""
    try:
        monitoring_service.logger.log_entries.clear()
        
        return {
            "success": True,
            "message": "Logs cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/metrics")
async def clear_metrics():
    """Clear all metrics (use with caution)"""
    try:
        monitoring_service.metrics_collector.metrics.clear()
        monitoring_service.metrics_collector.counters.clear()
        monitoring_service.metrics_collector.gauges.clear()
        monitoring_service.metrics_collector.histograms.clear()
        monitoring_service.metrics_collector.timers.clear()
        
        return {
            "success": True,
            "message": "Metrics cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

