"""
Database Connection Retry Handler
Provides robust connection handling with automatic retries for SSL connection issues
"""

import logging
import time
import functools
from sqlalchemy.exc import OperationalError, DisconnectionError
from app import db

logger = logging.getLogger(__name__)

def db_retry(max_retries=3, backoff_factor=1.0):
    """
    Decorator for database operations with automatic retry on connection failures
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DisconnectionError) as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Database operation failed after {max_retries} attempts: {e}")
                        raise
                    
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Database connection failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                    
                    # Try to refresh the connection
                    try:
                        db.session.close()
                        db.engine.dispose()
                    except:
                        pass
                        
            return None
        return wrapper
    return decorator

def test_connection():
    """Test database connection and return status"""
    try:
        db.session.execute('SELECT 1')
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def refresh_connection():
    """Refresh database connection pool"""
    try:
        db.session.close()
        db.engine.dispose()
        logger.info("Database connection pool refreshed")
        return True
    except Exception as e:
        logger.error(f"Failed to refresh connection pool: {e}")
        return False