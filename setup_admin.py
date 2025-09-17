import psycopg2
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_admin_role():
    """Set up admin role in the database"""
    DATABASE_URL = os.environ.get("DATABASE_URL")
    
    if not DATABASE_URL:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Check if is_admin column exists
        try:
            cursor.execute('SELECT column_name FROM information_schema.columns WHERE table_name=\'user\' AND column_name=\'is_admin\'')
            if cursor.fetchone():
                logger.info("is_admin column already exists")
            else:
                # Add is_admin column
                cursor.execute('ALTER TABLE "user" ADD COLUMN is_admin BOOLEAN DEFAULT false')
                conn.commit()
                logger.info("Added is_admin column to user table")
        except Exception as e:
            logger.error(f"Error checking/adding is_admin column: {str(e)}")
            conn.rollback()
            return False
        
        # Make the first user an admin
        try:
            cursor.execute('UPDATE "user" SET is_admin = true WHERE id = (SELECT MIN(id) FROM "user")')
            rows_updated = cursor.rowcount
            if rows_updated > 0:
                conn.commit()
                logger.info(f"Successfully made first user an admin")
            else:
                logger.warning("No users found to make admin")
                conn.rollback()
        except Exception as e:
            logger.error(f"Error making first user admin: {str(e)}")
            conn.rollback()
            return False
        
        cursor.close()
        conn.close()
        return True
    
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return False

if __name__ == "__main__":
    if setup_admin_role():
        logger.info("Admin role setup completed successfully")
    else:
        logger.error("Admin role setup failed")