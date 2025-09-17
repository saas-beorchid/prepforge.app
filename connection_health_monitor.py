"""
Connection Health Monitor
Monitors database connection health and provides real-time status
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from app import app, db
from database_retry_handler import test_connection, refresh_connection

logger = logging.getLogger(__name__)

class ConnectionHealthMonitor:
    """Monitor database connection health and automatically recover"""
    
    def __init__(self):
        self.is_healthy = True
        self.last_check = datetime.now()
        self.failure_count = 0
        self.monitor_thread = None
        self.running = False
        
    def start_monitoring(self):
        """Start the connection health monitoring thread"""
        if self.running:
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Database connection health monitor started")
        
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Database connection health monitor stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                with app.app_context():
                    if test_connection():
                        if not self.is_healthy:
                            logger.info("Database connection recovered")
                            self.is_healthy = True
                            self.failure_count = 0
                    else:
                        self.failure_count += 1
                        if self.is_healthy:
                            logger.warning(f"Database connection failed (failure #{self.failure_count})")
                            self.is_healthy = False
                            
                        # Try to refresh connection after multiple failures
                        if self.failure_count >= 3:
                            logger.info("Attempting connection refresh after multiple failures")
                            refresh_connection()
                            
                    self.last_check = datetime.now()
                    
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                self.is_healthy = False
                
            time.sleep(30)  # Check every 30 seconds
            
    def get_status(self):
        """Get current connection health status"""
        return {
            'healthy': self.is_healthy,
            'last_check': self.last_check,
            'failure_count': self.failure_count,
            'time_since_check': (datetime.now() - self.last_check).total_seconds()
        }

# Global monitor instance
health_monitor = ConnectionHealthMonitor()

def start_health_monitoring():
    """Start database health monitoring"""
    health_monitor.start_monitoring()

def get_connection_status():
    """Get current connection status"""
    return health_monitor.get_status()