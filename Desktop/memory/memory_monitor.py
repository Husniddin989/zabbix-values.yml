#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SYSTEM MONITOR - Tizim resurslarini kuzatish va Telegram orqali xabar yuborish
Versiya: 1.0.0
Python versiyasi
"""

import os
import sys
import time
import logging
import argparse
import configparser
import subprocess
import platform
import socket
import json
import requests
from datetime import datetime
import psutil

# Default configuration values
DEFAULT_CONFIG_FILE = "/etc/memory-monitor/config.conf"
DEFAULT_LOG_FILE = "/var/log/memory_monitor.log"
DEFAULT_THRESHOLD = 80
DEFAULT_INTERVAL = 60
DEFAULT_LOG_LEVEL = "INFO"

class SystemMonitor:
    def __init__(self, config_file=DEFAULT_CONFIG_FILE):
        """Initialize the SystemMonitor with the given configuration file."""
        self.config_file = config_file
        self.config = self._load_config()
        self._setup_logging()
        self.last_alert_times = {
            'ram': 0,
            'cpu': 0,
            'disk': 0,
            'swap': 0,
            'load': 0,
            'network': 0
        }
        self.logger.info(f"Memory monitoring service boshlandi")
        self.logger.info(f"Konfiguratsiya fayli: {self.config_file}")
        self.logger.debug(f"Monitoring sozlamalari: RAM {self.config['threshold']}%, interval {self.config['check_interval']} sek")
        
        # Test Telegram connection at startup
        self.test_telegram_connection()

    def _load_config(self):
        """Load configuration from file or use defaults."""
        config = {
            'bot_token': "",
            'chat_id': "",
            'log_file': DEFAULT_LOG_FILE,
            'threshold': DEFAULT_THRESHOLD,
            'check_interval': DEFAULT_INTERVAL,
            'log_level': DEFAULT_LOG_LEVEL,
            'alert_message_title': "🛑 SYSTEM MONITOR ALERT",
            'include_top_processes': True,
            'top_processes_count': 10,
            'monitor_cpu': True,
            'cpu_threshold': 90,
            'monitor_disk': True,
            'disk_threshold': 90,
            'disk_path': "/",
            'monitor_swap': True,
            'swap_threshold': 80,
            'monitor_load': True,
            'load_threshold': 5,
            'monitor_network': True,
            'network_interface': "",
            'network_threshold': 90,
            # Database integration settings
            'db_enabled': False,
            'db_type': "sqlite",  # sqlite, mysql, postgresql
            'db_host': "localhost",
            'db_port': 3306,
            'db_name': "system_monitor",
            'db_user': "",
            'db_password': "",
            # Prometheus integration settings
            'prometheus_enabled': False,
            'prometheus_port': 9090
        }
        
        if not os.path.exists(self.config_file):
            print(f"XATO: Konfiguratsiya fayli topilmadi: {self.config_file}")
            print("Standart konfiguratsiya qiymatlari ishlatiladi.")
            return config
        
        try:
            # Read configuration file
            parser = configparser.ConfigParser()
            parser.read(self.config_file)
            
            # General settings
            if 'General' in parser:
                for key in ['bot_token', 'chat_id', 'log_file', 'log_level', 'alert_message_title']:
                    if key in parser['General']:
                        config[key] = parser['General'][key]
                
                for key in ['threshold', 'check_interval', 'top_processes_count']:
                    if key in parser['General']:
                        config[key] = parser['General'].getint(key)
                
                if 'include_top_processes' in parser['General']:
                    config['include_top_processes'] = parser['General'].getboolean('include_top_processes')
            
            # CPU monitoring
            if 'CPU' in parser:
                if 'monitor_cpu' in parser['CPU']:
                    config['monitor_cpu'] = parser['CPU'].getboolean('monitor_cpu')
                if 'cpu_threshold' in parser['CPU']:
                    config['cpu_threshold'] = parser['CPU'].getint('cpu_threshold')
            
            # Disk monitoring
            if 'Disk' in parser:
                if 'monitor_disk' in parser['Disk']:
                    config['monitor_disk'] = parser['Disk'].getboolean('monitor_disk')
                if 'disk_threshold' in parser['Disk']:
                    config['disk_threshold'] = parser['Disk'].getint('disk_threshold')
                if 'disk_path' in parser['Disk']:
                    config['disk_path'] = parser['Disk']['disk_path']
            
            # Swap monitoring
            if 'Swap' in parser:
                if 'monitor_swap' in parser['Swap']:
                    config['monitor_swap'] = parser['Swap'].getboolean('monitor_swap')
                if 'swap_threshold' in parser['Swap']:
                    config['swap_threshold'] = parser['Swap'].getint('swap_threshold')
            
            # Load monitoring
            if 'Load' in parser:
                if 'monitor_load' in parser['Load']:
                    config['monitor_load'] = parser['Load'].getboolean('monitor_load')
                if 'load_threshold' in parser['Load']:
                    config['load_threshold'] = parser['Load'].getint('load_threshold')
            
            # Network monitoring
            if 'Network' in parser:
                if 'monitor_network' in parser['Network']:
                    config['monitor_network'] = parser['Network'].getboolean('monitor_network')
                if 'network_interface' in parser['Network']:
                    config['network_interface'] = parser['Network']['network_interface']
                if 'network_threshold' in parser['Network']:
                    config['network_threshold'] = parser['Network'].getint('network_threshold')
            
            # Database integration
            if 'Database' in parser:
                if 'db_enabled' in parser['Database']:
                    config['db_enabled'] = parser['Database'].getboolean('db_enabled')
                for key in ['db_type', 'db_host', 'db_name', 'db_user', 'db_password']:
                    if key in parser['Database']:
                        config[key] = parser['Database'][key]
                if 'db_port' in parser['Database']:
                    config['db_port'] = parser['Database'].getint('db_port')
            
            # Prometheus integration
            if 'Prometheus' in parser:
                if 'prometheus_enabled' in parser['Prometheus']:
                    config['prometheus_enabled'] = parser['Prometheus'].getboolean('prometheus_enabled')
                if 'prometheus_port' in parser['Prometheus']:
                    config['prometheus_port'] = parser['Prometheus'].getint('prometheus_port')
            
        except Exception as e:
            print(f"Konfiguratsiya faylini o'qishda xatolik: {e}")
            print("Standart konfiguratsiya qiymatlari ishlatiladi.")
        
        # Validate required settings
        if not config['bot_token'] or not config['chat_id']:
            print("XATO: BOT_TOKEN va CHAT_ID konfiguratsiya faylida ko'rsatilishi kerak.")
            sys.exit(1)
        
        # Set default network interface if not specified
        if not config['network_interface']:
            interfaces = psutil.net_if_addrs()
            for interface in interfaces:
                if interface != 'lo':  # Skip loopback
                    config['network_interface'] = interface
                    break
        
        return config

    def _setup_logging(self):
        """Set up logging configuration."""
        log_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR
        }
        
        log_level = log_levels.get(self.config['log_level'], logging.INFO)
        
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(self.config['log_file'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configure logging
        logging.basicConfig(
            filename=self.config['log_file'],
            level=log_level,
            format='%(asctime)s - [%(levelname)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Add console handler for DEBUG and ERROR levels
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
        console.setFormatter(formatter)
        
        # Add the handler to the root logger
        self.logger = logging.getLogger('')
        self.logger.addHandler(console)

    def get_system_info(self):
        """Get system information."""
        hostname = socket.gethostname()
        try:
            server_ip = socket.gethostbyname(socket.gethostname())
        except:
            server_ip = "127.0.0.1"
        
        # Get more detailed IP if available
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            server_ip = s.getsockname()[0]
            s.close()
        except:
            pass
        
        kernel = platform.release()
        os_info = platform.platform()
        
        # Get uptime
        uptime = ""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.readline().split()[0])
                uptime_days = int(uptime_seconds / 86400)
                uptime_hours = int((uptime_seconds % 86400) / 3600)
                uptime_minutes = int((uptime_seconds % 3600) / 60)
                uptime = f"up {uptime_days} days, {uptime_hours} hours, {uptime_minutes} minutes"
        except:
            uptime = "unknown"
        
        # Get CPU info
        cpu_info = platform.processor()
        cpu_cores = psutil.cpu_count(logical=True)
        
        # Get memory info
        mem = psutil.virtual_memory()
        total_memory = f"{mem.total / (1024**3):.1f}G"
        
        # Get disk info
        disk = psutil.disk_usage(self.config['disk_path'])
        total_disk = f"{disk.total / (1024**3):.1f}G"
        
        return {
            "hostname": hostname,
            "ip": server_ip,
            "os": os_info,
            "kernel": kernel,
            "cpu": f"{cpu_info} ({cpu_cores} cores)",
            "uptime": uptime,
            "total_ram": total_memory,
            "total_disk": f"{total_disk} ({self.config['disk_path']})"
        }

    def check_ram_usage(self):
        """Check RAM usage and return usage percentage."""
        mem = psutil.virtual_memory()
        usage_percent = mem.percent
        return usage_percent

    def check_cpu_usage(self):
        """Check CPU usage and return usage percentage."""
        if not self.config['monitor_cpu']:
            return 0
        
        cpu_percent = psutil.cpu_percent(interval=1)
        return cpu_percent

    def check_disk_usage(self):
        """Check disk usage and return usage percentage."""
        if not self.config['monitor_disk']:
            return 0
        
        disk = psutil.disk_usage(self.config['disk_path'])
        return disk.percent

    def check_swap_usage(self):
        """Check swap usage and return usage percentage."""
        if not self.config['monitor_swap']:
            return 0
        
        swap = psutil.swap_memory()
        if swap.total == 0:
            return 0
        
        return swap.percent

    def check_load_average(self):
        """Check load average and return load per core."""
        if not self.config['monitor_load']:
            return 0
        
        cpu_cores = psutil.cpu_count(logical=True)
        load_avg = os.getloadavg()[0]  # 1 minute load average
        load_per_core = load_avg / cpu_cores
        
        return load_per_core * 100  # Convert to percentage for threshold comparison

    def check_network_usage(self):
        """Check network usage and return usage in Mbps."""
        if not self.config['monitor_network']:
            return 0, 0
        
        interface = self.config['network_interface']
        
        # Check if interface exists
        if interface not in psutil.net_if_addrs():
            self.logger.warning(f"Network interfeysi topilmadi: {interface}")
            return 0, 0
        
        # Get initial counters
        net_io_counters_1 = psutil.net_io_counters(pernic=True)
        if interface not in net_io_counters_1:
            self.logger.warning(f"Network interfeysi statistikasi topilmadi: {interface}")
            return 0, 0
        
        rx_bytes_1 = net_io_counters_1[interface].bytes_recv
        tx_bytes_1 = net_io_counters_1[interface].bytes_sent
        
        # Wait 1 second
        time.sleep(1)
        
        # Get counters again
        net_io_counters_2 = psutil.net_io_counters(pernic=True)
        rx_bytes_2 = net_io_counters_2[interface].bytes_recv
        tx_bytes_2 = net_io_counters_2[interface].bytes_sent
        
        # Calculate rates in Mbps
        rx_rate = (rx_bytes_2 - rx_bytes_1) * 8 / 1024 / 1024  # Convert to Mbps
        tx_rate = (tx_bytes_2 - tx_bytes_1) * 8 / 1024 / 1024  # Convert to Mbps
        
        return rx_rate, tx_rate

    def get_top_processes(self, resource_type):
        """Get top processes based on resource type."""
        count = self.config['top_processes_count']
        
        if resource_type == "RAM":
            processes = []
            for proc in psutil.process_iter(['pid', 'ppid', 'name', 'memory_percent', 'cpu_percent']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'ppid': proc.info['ppid'],
                        'name': proc.info['name'],
                        'memory_percent': proc.info['memory_percent'],
                        'cpu_percent': proc.info['cpu_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Sort by memory usage
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            # Format output
            result = "PID PPID COMMAND %MEM% %CPU%\n"
            for proc in processes[:count]:
                result += f"{proc['pid']} {proc['ppid']} {proc['name']} {proc['memory_percent']:.1f}% {proc['cpu_percent']:.1f}%\n"
            
            return result
        
        elif resource_type == "CPU":
            processes = []
            for proc in psutil.process_iter(['pid', 'ppid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'ppid': proc.info['ppid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            # Format output
            result = "PID PPID COMMAND %CPU% %MEM%\n"
            for proc in processes[:count]:
                result += f"{proc['pid']} {proc['ppid']} {proc['name']} {proc['cpu_percent']:.1f}% {proc['memory_percent']:.1f}%\n"
            
            return result
        
        elif resource_type == "Disk":
            try:
                # Use subprocess to get disk usage by directory
                output = subprocess.check_output(
                    f"du -h {self.config
(Content truncated due to size limit. Use line ranges to read in chunks)