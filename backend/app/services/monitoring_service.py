"""
Enhanced Monitoring Service for FailSafe
Provides comprehensive monitoring, logging, and alerting capabilities
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import logging
import psutil
import threading
from collections import defaultdict, deque
import uuid

logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """Log levels for structured logging"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class MetricType(Enum):
    """Types of metrics to collect"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class LogEntry:
    """Structured log entry"""
    id: str
    timestamp: datetime
    level: LogLevel
    service: str
    component: str
    message: str
    context: Dict[str, Any]
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None

@dataclass
class Metric:
    """Metric data structure"""
    id: str
    name: str
    value: Union[float, int]
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str]
    service: str
    component: str

@dataclass
class Alert:
    """Alert data structure"""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    service: str
    component: str
    metric_name: str
    threshold_value: float
    current_value: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class HealthCheck:
    """Health check result"""
    service: str
    component: str
    status: str
    timestamp: datetime
    response_time_ms: float
    details: Dict[str, Any]
    error: Optional[str] = None

class StructuredLogger:
    """Structured logging service"""
    
    def __init__(self, service_name: str = "failsafe"):
        self.service_name = service_name
        self.log_entries = deque(maxlen=10000)  # Keep last 10k entries
        self.logger = logging.getLogger(f"{service_name}.structured")
        
        # Setup structured logging handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log(
        self,
        level: LogLevel,
        component: str,
        message: str,
        context: Dict[str, Any] = None,
        trace_id: str = None,
        user_id: str = None,
        request_id: str = None
    ):
        """Log a structured message"""
        if context is None:
            context = {}
        
        log_entry = LogEntry(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            level=level,
            service=self.service_name,
            component=component,
            message=message,
            context=context,
            trace_id=trace_id,
            user_id=user_id,
            request_id=request_id
        )
        
        # Add to in-memory store
        self.log_entries.append(log_entry)
        
        # Log to standard logger
        log_data = {
            "message": message,
            "context": context,
            "trace_id": trace_id,
            "user_id": user_id,
            "request_id": request_id
        }
        
        if level == LogLevel.DEBUG:
            self.logger.debug(json.dumps(log_data))
        elif level == LogLevel.INFO:
            self.logger.info(json.dumps(log_data))
        elif level == LogLevel.WARNING:
            self.logger.warning(json.dumps(log_data))
        elif level == LogLevel.ERROR:
            self.logger.error(json.dumps(log_data))
        elif level == LogLevel.CRITICAL:
            self.logger.critical(json.dumps(log_data))
    
    def get_logs(
        self,
        level: LogLevel = None,
        component: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100
    ) -> List[LogEntry]:
        """Get filtered log entries"""
        logs = list(self.log_entries)
        
        # Apply filters
        if level:
            logs = [log for log in logs if log.level == level]
        
        if component:
            logs = [log for log in logs if log.component == component]
        
        if start_time:
            logs = [log for log in logs if log.timestamp >= start_time]
        
        if end_time:
            logs = [log for log in logs if log.timestamp <= end_time]
        
        # Sort by timestamp (newest first)
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        return logs[:limit]

class MetricsCollector:
    """Metrics collection service"""
    
    def __init__(self, service_name: str = "failsafe"):
        self.service_name = service_name
        self.metrics = deque(maxlen=50000)  # Keep last 50k metrics
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self.timers = defaultdict(list)
    
    def record_metric(
        self,
        name: str,
        value: Union[float, int],
        metric_type: MetricType,
        component: str,
        tags: Dict[str, str] = None
    ):
        """Record a metric"""
        if tags is None:
            tags = {}
        
        metric = Metric(
            id=str(uuid.uuid4()),
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.now(),
            tags=tags,
            service=self.service_name,
            component=component
        )
        
        self.metrics.append(metric)
        
        # Update in-memory aggregations
        if metric_type == MetricType.COUNTER:
            self.counters[name] += value
        elif metric_type == MetricType.GAUGE:
            self.gauges[name] = value
        elif metric_type == MetricType.HISTOGRAM:
            self.histograms[name].append(value)
        elif metric_type == MetricType.TIMER:
            self.timers[name].append(value)
    
    def increment_counter(self, name: str, component: str, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        self.record_metric(name, 1, MetricType.COUNTER, component, tags)
    
    def set_gauge(self, name: str, value: Union[float, int], component: str, tags: Dict[str, str] = None):
        """Set a gauge metric"""
        self.record_metric(name, value, MetricType.GAUGE, component, tags)
    
    def record_histogram(self, name: str, value: Union[float, int], component: str, tags: Dict[str, str] = None):
        """Record a histogram value"""
        self.record_metric(name, value, MetricType.HISTOGRAM, component, tags)
    
    def record_timer(self, name: str, duration_ms: float, component: str, tags: Dict[str, str] = None):
        """Record a timer metric"""
        self.record_metric(name, duration_ms, MetricType.TIMER, component, tags)
    
    def get_metrics(
        self,
        name: str = None,
        component: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 1000
    ) -> List[Metric]:
        """Get filtered metrics"""
        metrics = list(self.metrics)
        
        # Apply filters
        if name:
            metrics = [m for m in metrics if m.name == name]
        
        if component:
            metrics = [m for m in metrics if m.component == component]
        
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]
        
        # Sort by timestamp (newest first)
        metrics.sort(key=lambda x: x.timestamp, reverse=True)
        
        return metrics[:limit]
    
    def get_metric_summary(self, name: str, component: str = None) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        metrics = self.get_metrics(name=name, component=component)
        
        if not metrics:
            return {"error": "No metrics found"}
        
        values = [m.value for m in metrics]
        
        return {
            "name": name,
            "component": component,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "latest": values[0] if values else None,
            "timestamp": metrics[0].timestamp if metrics else None
        }

class AlertManager:
    """Alert management service"""
    
    def __init__(self, service_name: str = "failsafe"):
        self.service_name = service_name
        self.alerts = deque(maxlen=1000)  # Keep last 1k alerts
        self.alert_rules = {}
        self.alert_handlers = []
    
    def add_alert_rule(
        self,
        name: str,
        metric_name: str,
        threshold: float,
        operator: str,
        severity: AlertSeverity,
        component: str = None
    ):
        """Add an alert rule"""
        self.alert_rules[name] = {
            "metric_name": metric_name,
            "threshold": threshold,
            "operator": operator,  # "gt", "lt", "eq", "gte", "lte"
            "severity": severity,
            "component": component,
            "enabled": True
        }
    
    def check_alerts(self, metrics_collector: MetricsCollector):
        """Check all alert rules against current metrics"""
        for rule_name, rule in self.alert_rules.items():
            if not rule["enabled"]:
                continue
            
            # Get current metric value
            metric_summary = metrics_collector.get_metric_summary(
                rule["metric_name"],
                rule["component"]
            )
            
            if "error" in metric_summary:
                continue
            
            current_value = metric_summary["latest"]
            threshold = rule["threshold"]
            operator = rule["operator"]
            
            # Check if alert should trigger
            should_alert = False
            if operator == "gt" and current_value > threshold:
                should_alert = True
            elif operator == "lt" and current_value < threshold:
                should_alert = True
            elif operator == "eq" and current_value == threshold:
                should_alert = True
            elif operator == "gte" and current_value >= threshold:
                should_alert = True
            elif operator == "lte" and current_value <= threshold:
                should_alert = True
            
            if should_alert:
                # Check if alert already exists and is not resolved
                existing_alert = any(
                    alert.metric_name == rule["metric_name"] and
                    alert.component == rule["component"] and
                    not alert.resolved
                    for alert in self.alerts
                )
                
                if not existing_alert:
                    self.create_alert(
                        title=f"Alert: {rule_name}",
                        message=f"Metric {rule['metric_name']} is {current_value} {operator} {threshold}",
                        severity=rule["severity"],
                        service=self.service_name,
                        component=rule["component"],
                        metric_name=rule["metric_name"],
                        threshold_value=threshold,
                        current_value=current_value
                    )
    
    def create_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        service: str,
        component: str,
        metric_name: str,
        threshold_value: float,
        current_value: float
    ):
        """Create a new alert"""
        alert = Alert(
            id=str(uuid.uuid4()),
            title=title,
            message=message,
            severity=severity,
            service=service,
            component=component,
            metric_name=metric_name,
            threshold_value=threshold_value,
            current_value=current_value,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        
        # Notify alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                break
    
    def get_alerts(
        self,
        severity: AlertSeverity = None,
        component: str = None,
        resolved: bool = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get filtered alerts"""
        alerts = list(self.alerts)
        
        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if component:
            alerts = [a for a in alerts if a.component == component]
        
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x.timestamp, reverse=True)
        
        return alerts[:limit]
    
    def add_alert_handler(self, handler):
        """Add an alert handler function"""
        self.alert_handlers.append(handler)

class HealthChecker:
    """Health check service"""
    
    def __init__(self, service_name: str = "failsafe"):
        self.service_name = service_name
        self.health_checks = deque(maxlen=1000)  # Keep last 1k health checks
        self.check_functions = {}
    
    def add_health_check(self, name: str, check_function, component: str = "system"):
        """Add a health check function"""
        self.check_functions[name] = {
            "function": check_function,
            "component": component
        }
    
    async def run_health_check(self, name: str) -> HealthCheck:
        """Run a specific health check"""
        if name not in self.check_functions:
            return HealthCheck(
                service=self.service_name,
                component="unknown",
                status="error",
                timestamp=datetime.now(),
                response_time_ms=0,
                details={},
                error=f"Health check '{name}' not found"
            )
        
        start_time = time.time()
        try:
            result = await self.check_functions[name]["function"]()
            response_time = (time.time() - start_time) * 1000
            
            health_check = HealthCheck(
                service=self.service_name,
                component=self.check_functions[name]["component"],
                status="healthy" if result.get("healthy", False) else "unhealthy",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details=result.get("details", {}),
                error=result.get("error")
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            health_check = HealthCheck(
                service=self.service_name,
                component=self.check_functions[name]["component"],
                status="error",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details={},
                error=str(e)
            )
        
        self.health_checks.append(health_check)
        return health_check
    
    async def run_all_health_checks(self) -> List[HealthCheck]:
        """Run all health checks"""
        results = []
        for name in self.check_functions:
            result = await self.run_health_check(name)
            results.append(result)
        return results
    
    def get_health_checks(
        self,
        component: str = None,
        status: str = None,
        limit: int = 100
    ) -> List[HealthCheck]:
        """Get filtered health checks"""
        checks = list(self.health_checks)
        
        # Apply filters
        if component:
            checks = [c for c in checks if c.component == component]
        
        if status:
            checks = [c for c in checks if c.status == status]
        
        # Sort by timestamp (newest first)
        checks.sort(key=lambda x: x.timestamp, reverse=True)
        
        return checks[:limit]

class SystemMonitor:
    """System resource monitoring"""
    
    def __init__(self):
        self.monitoring = True
        self.monitor_thread = None
    
    def start_monitoring(self, metrics_collector: MetricsCollector):
        """Start system monitoring in background thread"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(metrics_collector,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self, metrics_collector: MetricsCollector):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                metrics_collector.set_gauge("system.cpu.usage", cpu_percent, "system")
                
                # Memory usage
                memory = psutil.virtual_memory()
                metrics_collector.set_gauge("system.memory.usage", memory.percent, "system")
                metrics_collector.set_gauge("system.memory.available", memory.available, "system")
                
                # Disk usage
                disk = psutil.disk_usage('/')
                metrics_collector.set_gauge("system.disk.usage", disk.percent, "system")
                metrics_collector.set_gauge("system.disk.free", disk.free, "system")
                
                # Network I/O
                net_io = psutil.net_io_counters()
                metrics_collector.set_gauge("system.network.bytes_sent", net_io.bytes_sent, "system")
                metrics_collector.set_gauge("system.network.bytes_recv", net_io.bytes_recv, "system")
                
                # Process count
                process_count = len(psutil.pids())
                metrics_collector.set_gauge("system.processes.count", process_count, "system")
                
            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
            
            time.sleep(10)  # Monitor every 10 seconds

class MonitoringService:
    """Main monitoring service that coordinates all monitoring components"""
    
    def __init__(self, service_name: str = "failsafe"):
        self.service_name = service_name
        self.logger = StructuredLogger(service_name)
        self.metrics_collector = MetricsCollector(service_name)
        self.alert_manager = AlertManager(service_name)
        self.health_checker = HealthChecker(service_name)
        self.system_monitor = SystemMonitor()
        
        # Setup default alert rules
        self._setup_default_alerts()
        
        # Setup default health checks
        self._setup_default_health_checks()
    
    def _setup_default_alerts(self):
        """Setup default alert rules"""
        # CPU usage alerts
        self.alert_manager.add_alert_rule(
            "high_cpu_usage",
            "system.cpu.usage",
            80.0,
            "gt",
            AlertSeverity.HIGH,
            "system"
        )
        
        # Memory usage alerts
        self.alert_manager.add_alert_rule(
            "high_memory_usage",
            "system.memory.usage",
            85.0,
            "gt",
            AlertSeverity.HIGH,
            "system"
        )
        
        # Disk usage alerts
        self.alert_manager.add_alert_rule(
            "high_disk_usage",
            "system.disk.usage",
            90.0,
            "gt",
            AlertSeverity.CRITICAL,
            "system"
        )
    
    def _setup_default_health_checks(self):
        """Setup default health checks"""
        # System health check
        async def system_health():
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                healthy = (
                    cpu_percent < 90 and
                    memory.percent < 95 and
                    disk.percent < 95
                )
                
                return {
                    "healthy": healthy,
                    "details": {
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "disk_percent": disk.percent
                    }
                }
            except Exception as e:
                return {
                    "healthy": False,
                    "error": str(e)
                }
        
        self.health_checker.add_health_check("system", system_health, "system")
    
    def start_monitoring(self):
        """Start all monitoring services"""
        self.system_monitor.start_monitoring(self.metrics_collector)
        self.logger.log(LogLevel.INFO, "monitoring", "Monitoring services started")
    
    def stop_monitoring(self):
        """Stop all monitoring services"""
        self.system_monitor.stop_monitoring()
        self.logger.log(LogLevel.INFO, "monitoring", "Monitoring services stopped")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        # Get latest health checks
        health_checks = self.health_checker.get_health_checks(limit=10)
        
        # Get active alerts
        active_alerts = self.alert_manager.get_alerts(resolved=False, limit=10)
        
        # Get system metrics
        cpu_usage = self.metrics_collector.get_metric_summary("system.cpu.usage", "system")
        memory_usage = self.metrics_collector.get_metric_summary("system.memory.usage", "system")
        disk_usage = self.metrics_collector.get_metric_summary("system.disk.usage", "system")
        
        # Determine overall status
        overall_status = "healthy"
        if active_alerts:
            critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
            if critical_alerts:
                overall_status = "critical"
            else:
                overall_status = "warning"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "health_checks": [asdict(hc) for hc in health_checks],
            "active_alerts": [asdict(alert) for alert in active_alerts],
            "system_metrics": {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage
            }
        }
    
    def get_metrics_dashboard(self) -> Dict[str, Any]:
        """Get metrics for dashboard"""
        # Get recent metrics
        recent_metrics = self.metrics_collector.get_metrics(limit=1000)
        
        # Group by metric name
        metrics_by_name = defaultdict(list)
        for metric in recent_metrics:
            metrics_by_name[metric.name].append(metric)
        
        # Calculate summaries
        dashboard_metrics = {}
        for name, metrics in metrics_by_name.items():
            if not metrics:
                continue
            
            values = [m.value for m in metrics]
            dashboard_metrics[name] = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
                "latest": values[0],
                "trend": self._calculate_trend(values)
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": dashboard_metrics
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend for a series of values"""
        if len(values) < 2:
            return "stable"
        
        # Simple trend calculation
        recent_avg = sum(values[:len(values)//2]) / (len(values)//2)
        older_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"

# Create global monitoring service instance
monitoring_service = MonitoringService("failsafe")

