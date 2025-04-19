#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Prometheus metrics exporter for System Monitor
Exposes system metrics for Prometheus scraping
"""

import time
import logging
import threading
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

try:
    from prometheus_client import start_http_server, Gauge, Counter, Info
    from prometheus_client.core import CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class PrometheusExporter:
    """Prometheus metrics exporter for System Monitor."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Prometheus exporter with configuration."""
        self.config = config
        self.logger = logging.getLogger('memory_monitor.prometheus')
        self.enabled = config.get('prometheus_enabled', False)
        self.port = config.get('prometheus_port', 9090)
        self.metrics = {}
        self.registry = None
        self.server = None
        self.server_thread = None
        
        # Check if prometheus_client is available
        if not PROMETHEUS_AVAILABLE:
            self.logger.error("Prometheus integration requires prometheus_client package. Install with: pip install prometheus_client")
            self.enabled = False
            return
        
        # Initialize Prometheus metrics if enabled
        if self.enabled:
            self._initialize_metrics()
    
    def _initialize_metrics(self) -> None:
        """Initialize Prometheus metrics."""
        try:
            # Create a registry
            self.registry = CollectorRegistry()
            
            # System information
            self.metrics['system_info'] = Info('system_monitor_info', 'System information', registry=self.registry)
            
            # Resource usage gauges
            self.metrics['ram_usage'] = Gauge('system_monitor_ram_usage_percent', 'RAM usage in percent', registry=self.registry)
            self.metrics['cpu_usage'] = Gauge('system_monitor_cpu_usage_percent', 'CPU usage in percent', registry=self.registry)
            self.metrics['disk_usage'] = Gauge('system_monitor_disk_usage_percent', 'Disk usage in percent', registry=self.registry)
            self.metrics['swap_usage'] = Gauge('system_monitor_swap_usage_percent', 'Swap usage in percent', registry=self.registry)
            self.metrics['load_average'] = Gauge('system_monitor_load_average', 'System load average', registry=self.registry)
            self.metrics['network_rx'] = Gauge('system_monitor_network_rx_mbps', 'Network receive rate in Mbps', registry=self.registry)
            self.metrics['network_tx'] = Gauge('system_monitor_network_tx_mbps', 'Network transmit rate in Mbps', registry=self.registry)
            
            # Alert counters
            self.metrics['ram_alerts'] = Counter('system_monitor_ram_alerts_total', 'Total number of RAM alerts', registry=self.registry)
            self.metrics['cpu_alerts'] = Counter('system_monitor_cpu_alerts_total', 'Total number of CPU alerts', registry=self.registry)
            self.metrics['disk_alerts'] = Counter('system_monitor_disk_alerts_total', 'Total number of disk alerts', registry=self.registry)
            self.metrics['swap_alerts'] = Counter('system_monitor_swap_alerts_total', 'Total number of swap alerts', registry=self.registry)
            self.metrics['load_alerts'] = Counter('system_monitor_load_alerts_total', 'Total number of load alerts', registry=self.registry)
            self.metrics['network_alerts'] = Counter('system_monitor_network_alerts_total', 'Total number of network alerts', registry=self.registry)
            
            # Start the server
            self._start_server()
            self.logger.info(f"Prometheus exporter initialized on port {self.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Prometheus metrics: {str(e)}")
            self.enabled = False
    
    def _start_server(self) -> None:
        """Start Prometheus HTTP server in a separate thread."""
        try:
            # Start the server in a separate thread
            self.server_thread = threading.Thread(
                target=start_http_server,
                args=(self.port,),
                kwargs={'registry': self.registry},
                daemon=True
            )
            self.server_thread.start()
            self.logger.info(f"Prometheus HTTP server started on port {self.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start Prometheus HTTP server: {str(e)}")
            self.enabled = False
    
    def update_metrics(self, metrics: Dict[str, Any], system_info: Dict[str, str]) -> bool:
        """Update Prometheus metrics with current values."""
        if not self.enabled or not PROMETHEUS_AVAILABLE:
            return False
        
        try:
            # Update system info
            self.metrics['system_info'].info({
                'hostname': system_info.get('hostname', 'unknown'),
                'ip': system_info.get('ip', '0.0.0.0'),
                'os': system_info.get('os', 'unknown'),
                'kernel': system_info.get('kernel', 'unknown'),
                'uptime': system_info.get('uptime', 'unknown')
            })
            
            # Update resource usage gauges
            self.metrics['ram_usage'].set(metrics.get('ram', 0))
            self.metrics['cpu_usage'].set(metrics.get('cpu', 0))
            self.metrics['disk_usage'].set(metrics.get('disk', 0))
            self.metrics['swap_usage'].set(metrics.get('swap', 0))
            self.metrics['load_average'].set(metrics.get('load', 0))
            
            # Update network metrics
            if 'network' in metrics and isinstance(metrics['network'], tuple) and len(metrics['network']) == 2:
                rx_rate, tx_rate = metrics['network']
                self.metrics['network_rx'].set(rx_rate)
                self.metrics['network_tx'].set(tx_rate)
            
            self.logger.debug("Prometheus metrics updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update Prometheus metrics: {str(e)}")
            return False
    
    def increment_alert_counter(self, alert_type: str) -> bool:
        """Increment alert counter for the specified type."""
        if not self.enabled or not PROMETHEUS_AVAILABLE:
            return False
        
        try:
            counter_name = f"{alert_type.lower()}_alerts"
            if counter_name in self.metrics:
                self.metrics[counter_name].inc()
                self.logger.debug(f"Prometheus alert counter incremented: {counter_name}")
                return True
            else:
                self.logger.warning(f"Unknown alert type for Prometheus counter: {alert_type}")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to increment Prometheus alert counter: {str(e)}")
            return False
    
    def stop(self) -> None:
        """Stop the Prometheus HTTP server."""
        if self.server_thread and self.server_thread.is_alive():
            # There's no direct way to stop the server in prometheus_client
            # It will be stopped when the process exits
            self.logger.info("Prometheus HTTP server will stop when the process exits")


class GrafanaHandler:
    """Handler for Grafana integration recommendations."""
    
    @staticmethod
    def get_dashboard_json(system_name: str = "System Monitor") -> str:
        """Generate a sample Grafana dashboard JSON for System Monitor."""
        dashboard = {
            "annotations": {
                "list": [
                    {
                        "builtIn": 1,
                        "datasource": "-- Grafana --",
                        "enable": True,
                        "hide": True,
                        "iconColor": "rgba(0, 211, 255, 1)",
                        "name": "Annotations & Alerts",
                        "type": "dashboard"
                    }
                ]
            },
            "editable": True,
            "gnetId": None,
            "graphTooltip": 0,
            "id": None,
            "links": [],
            "panels": [
                {
                    "aliasColors": {},
                    "bars": False,
                    "dashLength": 10,
                    "dashes": False,
                    "datasource": "Prometheus",
                    "fill": 1,
                    "fillGradient": 0,
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 0,
                        "y": 0
                    },
                    "hiddenSeries": False,
                    "id": 1,
                    "legend": {
                        "avg": False,
                        "current": False,
                        "max": False,
                        "min": False,
                        "show": True,
                        "total": False,
                        "values": False
                    },
                    "lines": True,
                    "linewidth": 1,
                    "nullPointMode": "null",
                    "options": {
                        "dataLinks": []
                    },
                    "percentage": False,
                    "pointradius": 2,
                    "points": False,
                    "renderer": "flot",
                    "seriesOverrides": [],
                    "spaceLength": 10,
                    "stack": False,
                    "steppedLine": False,
                    "targets": [
                        {
                            "expr": "system_monitor_ram_usage_percent",
                            "legendFormat": "RAM Usage",
                            "refId": "A"
                        }
                    ],
                    "thresholds": [],
                    "timeFrom": None,
                    "timeRegions": [],
                    "timeShift": None,
                    "title": "RAM Usage",
                    "tooltip": {
                        "shared": True,
                        "sort": 0,
                        "value_type": "individual"
                    },
                    "type": "graph",
                    "xaxis": {
                        "buckets": None,
                        "mode": "time",
                        "name": None,
                        "show": True,
                        "values": []
                    },
                    "yaxes": [
                        {
                            "format": "percent",
                            "label": None,
                            "logBase": 1,
                            "max": "100",
                            "min": "0",
                            "show": True
                        },
                        {
                            "format": "short",
                            "label": None,
                            "logBase": 1,
                            "max": None,
                            "min": None,
                            "show": True
                        }
                    ],
                    "yaxis": {
                        "align": False,
                        "alignLevel": None
                    }
                },
                {
                    "aliasColors": {},
                    "bars": False,
                    "dashLength": 10,
                    "dashes": False,
                    "datasource": "Prometheus",
                    "fill": 1,
                    "fillGradient": 0,
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 12,
                        "y": 0
                    },
                    "hiddenSeries": False,
                    "id": 2,
                    "legend": {
                        "avg": False,
                        "current": False,
                        "max": False,
                        "min": False,
                        "show": True,
                        "total": False,
                        "values": False
                    },
                    "lines": True,
                    "linewidth": 1,
                    "nullPointMode": "null",
                    "options": {
                        "dataLinks": []
                    },
                    "percentage": False,
                    "pointradius": 2,
                    "points": False,
                    "renderer": "flot",
                    "seriesOverrides": [],
                    "spaceLength": 10,
                    "stack": False,
                    "steppedLine": False,
                    "targets": [
                        {
                            "expr": "system_monitor_cpu_usage_percent",
                            "legendFormat": "CPU Usage",
                            "refId": "A"
                        }
                    ],
                    "thresholds": [],
                    "timeFrom": None,
                    "timeRegions": [],
                    "timeShift": None,
                    "title": "CPU Usage",
                    "tooltip": {
                        "shared": True,
                        "sort": 0,
                        "value_type": "individual"
                    },
                    "type": "graph",
                    "xaxis": {
                        "buckets": None,
                        "mode": "time",
                        "name": None,
                        "show": True,
                        "values": []
                    },
                    "yaxes": [
                        {
                            "format": "percent",
                            "label": None,
                            "logBase": 1,
                            "max": "100",
                            "min": "0",
                            "show": True
                        },
                        {
                            "format": "short",
                            "label": None,
                            "logBase": 1,
                            "max": None,
                            "min": None,
                            "show": True
                        }
                    ],
                    "yaxis": {
                        "align": False,
                        "alignLevel": None
                    }
                },
                {
                    "aliasColors": {},
                    "bars": False,
                    "dashLength": 10,
                    "dashes": False,
                    "datasource": "Prometheus",
                    "fill": 1,
                    "fillGradient": 0,
                    "gridPos": {
                        "h": 8,
                        "w": 12,
                        "x": 0,
                        "y": 8
                    },
                    "hiddenSeries": False,
                    "id": 3,
                    "legend": {
                        "avg": False,
                        "current": False,
                        "max": False,
                        "min": False,
                        "show": True,
                        "total": False,
                        "values": False
                    },
                    "lines": True,
                    "linewidth": 1,
                    "nullPointMode": "null",
                    "options": {
                        "dataLinks": []
                    },
                    "percentage": False,
                    "pointradius": 2,
                    "points": False,
                    "renderer": "flot",
                    "seriesOverrid
(Content truncated due to size limit. Use line ranges to read in chunks)