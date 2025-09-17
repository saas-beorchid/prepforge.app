import sys
import logging
from app import app, db
from models import User
from sqlalchemy import text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_admin_field_to_user():
    """Check if admin field exists in User model, add it if not"""
    with app.app_context():
        # Check if column exists
        try:
            db.session.execute(text('SELECT is_admin FROM "user" LIMIT 1'))
            logger.info("is_admin column already exists in User model")
        except Exception as e:
            logger.info("Adding is_admin column to User model")
            try:
                db.session.execute(text('ALTER TABLE "user" ADD COLUMN is_admin BOOLEAN DEFAULT false'))
                db.session.commit()
                logger.info("Successfully added is_admin column to User model")
            except Exception as e:
                logger.error(f"Failed to add is_admin column: {str(e)}")
                db.session.rollback()
                return False
    return True

def make_first_user_admin():
    """Make the first user an admin"""
    with app.app_context():
        try:
            # Get the first user
            first_user = User.query.order_by(User.id).first()
            if first_user:
                first_user.is_admin = True
                db.session.commit()
                logger.info(f"User {first_user.email} (ID: {first_user.id}) is now an admin")
                return True
            else:
                logger.warning("No users found in the database")
                return False
        except Exception as e:
            logger.error(f"Failed to make first user admin: {str(e)}")
            db.session.rollback()
            return False

def make_user_admin_by_email(email):
    """Make a specific user an admin by email"""
    with app.app_context():
        try:
            user = User.query.filter_by(email=email).first()
            if user:
                user.is_admin = True
                db.session.commit()
                logger.info(f"User {user.email} (ID: {user.id}) is now an admin")
                return True
            else:
                logger.warning(f"No user found with email: {email}")
                return False
        except Exception as e:
            logger.error(f"Failed to make user admin: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    if not add_admin_field_to_user():
        logger.error("Failed to add admin field. Exiting.")
        sys.exit(1)
    
    # If email is provided as argument, make that user admin
    if len(sys.argv) > 1:
        email = sys.argv[1]
        if make_user_admin_by_email(email):
            logger.info(f"Successfully made {email} an admin")
        else:
            logger.error(f"Failed to make {email} an admin")
    # Otherwise make first user admin
    else:
        if make_first_user_admin():
            logger.info("Successfully made first user an admin")
        else:
            logger.error("Failed to make first user an admin")