#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Database handler for System Monitor
Supports SQLite, MySQL, and PostgreSQL databases
"""

import os
import logging
import sqlite3
import datetime
import json
from typing import Dict, Any, Optional, List, Tuple

# Optional imports for MySQL and PostgreSQL
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import psycopg2
    import psycopg2.extras
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False


class DatabaseHandler:
    """Handler for database operations."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize database handler with configuration."""
        self.config = config
        self.logger = logging.getLogger('memory_monitor.database')
        self.connection = None
        self.db_type = config.get('db_type', 'sqlite').lower()
        
        # Initialize database if enabled
        if config.get('db_enabled', False):
            self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize database connection and tables."""
        try:
            if self.db_type == 'sqlite':
                self._initialize_sqlite()
            elif self.db_type == 'mysql':
                if not MYSQL_AVAILABLE:
                    self.logger.error("MySQL support requires mysql-connector-python package. Install with: pip install mysql-connector-python")
                    return
                self._initialize_mysql()
            elif self.db_type == 'postgresql':
                if not POSTGRESQL_AVAILABLE:
                    self.logger.error("PostgreSQL support requires psycopg2 package. Install with: pip install psycopg2-binary")
                    return
                self._initialize_postgresql()
            else:
                self.logger.error(f"Unsupported database type: {self.db_type}")
                return
            
            # Create tables if they don't exist
            self._create_tables()
            self.logger.info(f"Database initialized successfully: {self.db_type}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")
    
    def _initialize_sqlite(self) -> None:
        """Initialize SQLite database."""
        db_path = self.config.get('db_path', '/var/lib/memory-monitor/metrics.db')
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
    
    def _initialize_mysql(self) -> None:
        """Initialize MySQL database."""
        self.connection = mysql.connector.connect(
            host=self.config.get('db_host', 'localhost'),
            port=self.config.get('db_port', 3306),
            user=self.config.get('db_user', ''),
            password=self.config.get('db_password', ''),
            database=self.config.get('db_name', 'system_monitor')
        )
    
    def _initialize_postgresql(self) -> None:
        """Initialize PostgreSQL database."""
        self.connection = psycopg2.connect(
            host=self.config.get('db_host', 'localhost'),
            port=self.config.get('db_port', 5432),
            user=self.config.get('db_user', ''),
            password=self.config.get('db_password', ''),
            dbname=self.config.get('db_name', 'system_monitor')
        )
    
    def _create_tables(self) -> None:
        """Create necessary tables if they don't exist."""
        cursor = self.connection.cursor()
        
        # Create metrics table
        if self.db_type == 'sqlite':
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                hostname TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                ram_usage REAL,
                cpu_usage REAL,
                disk_usage REAL,
                swap_usage REAL,
                load_average REAL,
                network_rx REAL,
                network_tx REAL,
                extra_data TEXT
            )
            ''')
            
            # Create alerts table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                hostname TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                value TEXT NOT NULL,
                message TEXT,
                sent_successfully BOOLEAN
            )
            ''')
            
        elif self.db_type == 'mysql':
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                hostname VARCHAR(255) NOT NULL,
                ip_address VARCHAR(45) NOT NULL,
                ram_usage FLOAT,
                cpu_usage FLOAT,
                disk_usage FLOAT,
                swap_usage FLOAT,
                load_average FLOAT,
                network_rx FLOAT,
                network_tx FLOAT,
                extra_data TEXT
            )
            ''')
            
            # Create alerts table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                hostname VARCHAR(255) NOT NULL,
                alert_type VARCHAR(50) NOT NULL,
                value VARCHAR(100) NOT NULL,
                message TEXT,
                sent_successfully BOOLEAN
            )
            ''')
            
        elif self.db_type == 'postgresql':
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                hostname VARCHAR(255) NOT NULL,
                ip_address VARCHAR(45) NOT NULL,
                ram_usage FLOAT,
                cpu_usage FLOAT,
                disk_usage FLOAT,
                swap_usage FLOAT,
                load_average FLOAT,
                network_rx FLOAT,
                network_tx FLOAT,
                extra_data TEXT
            )
            ''')
            
            # Create alerts table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                hostname VARCHAR(255) NOT NULL,
                alert_type VARCHAR(50) NOT NULL,
                value VARCHAR(100) NOT NULL,
                message TEXT,
                sent_successfully BOOLEAN
            )
            ''')
        
        self.connection.commit()
        cursor.close()
    
    def store_metrics(self, metrics: Dict[str, Any], system_info: Dict[str, str]) -> bool:
        """Store metrics in the database."""
        if not self.config.get('db_enabled', False) or not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Extract network metrics
            network_rx, network_tx = 0.0, 0.0
            if 'network' in metrics and isinstance(metrics['network'], tuple) and len(metrics['network']) == 2:
                network_rx, network_tx = metrics['network']
            
            # Prepare extra data (anything not in standard columns)
            extra_data = {k: v for k, v in metrics.items() if k not in ['ram', 'cpu', 'disk', 'swap', 'load', 'network']}
            if extra_data:
                extra_data_json = json.dumps(extra_data)
            else:
                extra_data_json = None
            
            # Insert metrics
            if self.db_type == 'sqlite':
                cursor.execute('''
                INSERT INTO metrics (
                    timestamp, hostname, ip_address, ram_usage, cpu_usage, disk_usage, 
                    swap_usage, load_average, network_rx, network_tx, extra_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.datetime.now().isoformat(),
                    system_info.get('hostname', 'unknown'),
                    system_info.get('ip', '0.0.0.0'),
                    metrics.get('ram', 0.0),
                    metrics.get('cpu', 0.0),
                    metrics.get('disk', 0.0),
                    metrics.get('swap', 0.0),
                    metrics.get('load', 0.0),
                    network_rx,
                    network_tx,
                    extra_data_json
                ))
            else:  # MySQL and PostgreSQL use %s placeholders
                cursor.execute('''
                INSERT INTO metrics (
                    timestamp, hostname, ip_address, ram_usage, cpu_usage, disk_usage, 
                    swap_usage, load_average, network_rx, network_tx, extra_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    datetime.datetime.now(),
                    system_info.get('hostname', 'unknown'),
                    system_info.get('ip', '0.0.0.0'),
                    metrics.get('ram', 0.0),
                    metrics.get('cpu', 0.0),
                    metrics.get('disk', 0.0),
                    metrics.get('swap', 0.0),
                    metrics.get('load', 0.0),
                    network_rx,
                    network_tx,
                    extra_data_json
                ))
            
            self.connection.commit()
            cursor.close()
            self.logger.debug("Metrics stored in database successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store metrics in database: {str(e)}")
            return False
    
    def store_alert(self, alert_type: str, value: str, message: str, 
                   sent_successfully: bool, system_info: Dict[str, str]) -> bool:
        """Store alert information in the database."""
        if not self.config.get('db_enabled', False) or not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Insert alert
            if self.db_type == 'sqlite':
                cursor.execute('''
                INSERT INTO alerts (
                    timestamp, hostname, alert_type, value, message, sent_successfully
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.datetime.now().isoformat(),
                    system_info.get('hostname', 'unknown'),
                    alert_type,
                    value,
                    message,
                    sent_successfully
                ))
            else:  # MySQL and PostgreSQL use %s placeholders
                cursor.execute('''
                INSERT INTO alerts (
                    timestamp, hostname, alert_type, value, message, sent_successfully
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    datetime.datetime.now(),
                    system_info.get('hostname', 'unknown'),
                    alert_type,
                    value,
                    message,
                    sent_successfully
                ))
            
            self.connection.commit()
            cursor.close()
            self.logger.debug(f"Alert stored in database successfully: {alert_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store alert in database: {str(e)}")
            return False
    
    def get_recent_metrics(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metrics from the last specified hours."""
        if not self.config.get('db_enabled', False) or not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            # Calculate time threshold
            time_threshold = datetime.datetime.now() - datetime.timedelta(hours=hours)
            
            if self.db_type == 'sqlite':
                cursor.execute('''
                SELECT * FROM metrics 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
                ''', (time_threshold.isoformat(),))
                
                # Convert rows to dictionaries
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
            elif self.db_type == 'mysql':
                cursor.execute('''
                SELECT * FROM metrics 
                WHERE timestamp >= %s 
                ORDER BY timestamp DESC
                ''', (time_threshold,))
                
                # Convert rows to dictionaries
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
            elif self.db_type == 'postgresql':
                cursor.execute('''
                SELECT * FROM metrics 
                WHERE timestamp >= %s 
                ORDER BY timestamp DESC
                ''', (time_threshold,))
                
                # Convert rows to dictionaries using DictCursor
                results = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve metrics from database: {str(e)}")
            return []
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alerts from the last specified hours."""
        if not self.config.get('db_enabled', False) or not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            
            # Calculate time threshold
            time_threshold = datetime.datetime.now() - datetime.timedelta(hours=hours)
            
            if self.db_type == 'sqlite':
                cursor.execute('''
                SELECT * FROM alerts 
                WHERE timestamp >= ? 
                ORDER BY timestamp DESC
                ''', (time_threshold.isoformat(),))
                
                # Convert rows to dictionaries
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
            elif self.db_type == 'mysql':
                cursor.execute('''
                SELECT * FROM alerts 
                WHERE timestamp >= %s 
                ORDER BY timestamp DESC
                ''', (time_threshold,))
                
                # Convert rows to dictionaries
                columns = [column[0] for column in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
            elif self.db_type == 'postgresql':
                cursor.execute('''
                SELECT * FROM alerts 
                WHERE timestamp >= %s 
                ORDER BY timestamp DESC
                ''', (time_threshold,))
                
                # Convert rows to dictionaries using DictCursor
                results = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            return results
            
        except Exception as e:
    
(Content truncated due to size limit. Use line ranges to read in chunks)