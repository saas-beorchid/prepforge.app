#!/usr/bin/env python3
"""
Database migration script for new session persistence tables
Creates PracticeSession and TrialUsage tables
"""

import os
import sys
import logging
from app import app, db
from models import PracticeSession, TrialUsage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_new_tables():
    """Create new tables for session persistence"""
    with app.app_context():
        try:
            # Create tables
            db.create_all()
            
            # Check if tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            
            existing_tables = inspector.get_table_names()
            
            if 'practice_session' in existing_tables:
                logger.info("✅ PracticeSession table created successfully")
            else:
                logger.error("❌ Failed to create PracticeSession table")
                
            if 'trial_usage' in existing_tables:
                logger.info("✅ TrialUsage table created successfully")
            else:
                logger.error("❌ Failed to create TrialUsage table")
            
            # Get column info for verification
            if 'practice_session' in existing_tables:
                columns = [col['name'] for col in inspector.get_columns('practice_session')]
                logger.info(f"PracticeSession columns: {columns}")
                
            if 'trial_usage' in existing_tables:
                columns = [col['name'] for col in inspector.get_columns('trial_usage')]
                logger.info(f"TrialUsage columns: {columns}")
            
            logger.info("🎉 Database migration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    success = create_new_tables()
    if not success:
        sys.exit(1)