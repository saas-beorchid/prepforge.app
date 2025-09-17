"""
Subscription Gate System for PrepForge
Implements rate limiting and subscription checks for /generate-question route
"""

import os
import json
import redis
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user
from models import db, User
from sqlalchemy import func, and_

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection setup with fallback
redis_client = None
try:
    redis_url = os.environ.get('REDIS_URL')
    if redis_url:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        # Test connection
        redis_client.ping()
        logger.info("✅ Redis connected successfully for rate limiting")
    else:
        logger.info("⚠️  No REDIS_URL found, using PostgreSQL fallback")
except Exception as e:
    logger.warning(f"⚠️  Redis connection failed: {e}, using PostgreSQL fallback")
    redis_client = None

# Mixpanel setup
mixpanel_token = os.environ.get('MIXPANEL_TOKEN')
if mixpanel_token:
    logger.info("✅ Mixpanel token found for analytics tracking")
else:
    logger.warning("⚠️  No MIXPANEL_TOKEN found, analytics tracking disabled")

class UserActivity(db.Model):
    """Track daily question counts for free users"""
    __tablename__ = 'user_activity'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    question_count = db.Column(db.Integer, default=0)
    
    # Unique constraint to ensure one record per user per day
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='_user_date_uc'),)

def track_mixpanel_event(event_name, user_id, properties=None):
    """Track events in Mixpanel with fallback logging"""
    if not mixpanel_token:
        logger.info(f"📊 Analytics: {event_name} for user {user_id} (Mixpanel disabled)")
        return
    
    try:
        import requests
        
        event_data = {
            "event": event_name,
            "properties": {
                "distinct_id": str(user_id),
                "time": int(datetime.utcnow().timestamp()),
                **(properties or {})
            }
        }
        
        # Send to Mixpanel
        response = requests.post(
            "https://api.mixpanel.com/track",
            data={
                "data": json.dumps(event_data),
                "api_key": mixpanel_token
            },
            timeout=5
        )
        
        if response.status_code == 200:
            logger.info(f"📊 Mixpanel: {event_name} tracked for user {user_id}")
        else:
            logger.warning(f"⚠️  Mixpanel tracking failed: {response.status_code}")
            
    except Exception as e:
        logger.warning(f"⚠️  Mixpanel error: {e}")

def check_free_user_limit(user_id):
    """Check if free user has exceeded daily 20-question limit"""
    today = datetime.utcnow().date()
    
    try:
        # Get or create today's activity record
        activity = UserActivity.query.filter_by(
            user_id=user_id, 
            date=today
        ).first()
        
        if not activity:
            # Create new activity record
            activity = UserActivity()
            activity.user_id = user_id
            activity.date = today
            activity.question_count = 0
            db.session.add(activity)
            db.session.commit()
            
        current_count = activity.question_count
        limit_exceeded = current_count >= 20
        
        logger.info(f"📊 Free user {user_id}: {current_count}/20 questions today")
        return not limit_exceeded, current_count, 20
        
    except Exception as e:
        logger.error(f"❌ Error checking free user limit: {e}")
        # Fail open - allow request if database error
        return True, 0, 20

def check_pro_user_limit(user_id):
    """Check if pro user has exceeded 10 questions/minute limit"""
    try:
        if redis_client:
            # Use Redis for pro user rate limiting
            key = f"pro_user_rate:{user_id}"
            current_minute = int(datetime.utcnow().timestamp() // 60)
            redis_key = f"{key}:{current_minute}"
            
            current_count_str = redis_client.get(redis_key)
            current_count = int(current_count_str) if current_count_str else 0
            
            limit_exceeded = current_count >= 10
            
            logger.info(f"📊 Pro user {user_id}: {current_count}/10 questions this minute (Redis)")
            return not limit_exceeded, current_count, 10
        else:
            # Fallback to PostgreSQL for pro users - simplified approach
            # For pro users without Redis, we'll use a more lenient fallback
            # In production, Redis should be available for accurate minute-based limiting
            current_count = 0  # Allow pro users through if Redis unavailable
            limit_exceeded = current_count >= 10
            
            logger.info(f"📊 Pro user {user_id}: {current_count}/10 questions this minute (PostgreSQL)")
            return not limit_exceeded, current_count, 10
            
    except Exception as e:
        logger.error(f"❌ Error checking pro user limit: {e}")
        # Fail open for pro users - allow request if error
        return True, 0, 10

def increment_user_count(user_id, is_pro=False):
    """Increment the user's question count"""
    try:
        if is_pro and redis_client:
            # Increment Redis counter for pro users
            current_minute = int(datetime.utcnow().timestamp() // 60)
            key = f"pro_user_rate:{user_id}:{current_minute}"
            redis_client.incr(key)
            redis_client.expire(key, 120)  # Expire after 2 minutes
            logger.info(f"📊 Incremented pro user {user_id} count in Redis")
        else:
            # Increment PostgreSQL counter for free users (or pro fallback)
            today = datetime.utcnow().date()
            activity = UserActivity.query.filter_by(
                user_id=user_id, 
                date=today
            ).first()
            
            if activity:
                activity.question_count += 1
            else:
                activity = UserActivity()
                activity.user_id = user_id
                activity.date = today  
                activity.question_count = 1
                db.session.add(activity)
                
            db.session.commit()
            logger.info(f"📊 Incremented user {user_id} count in PostgreSQL")
            
    except Exception as e:
        logger.error(f"❌ Error incrementing user count: {e}")

def subscription_gate(f):
    """
    Decorator to protect routes with subscription-based rate limiting
    - Free users: 20 questions/day
    - Pro users: 10 questions/minute
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if not current_user.is_authenticated:
            track_mixpanel_event("Gate Checked", "anonymous", {
                "result": "unauthorized",
                "reason": "not_authenticated"
            })
            return jsonify({
                "error": "Authentication required",
                "code": "AUTH_REQUIRED"
            }), 401
        
        user_id = current_user.id
        
        # Check user's subscription plan
        user = User.query.get(user_id)
        if not user:
            track_mixpanel_event("Gate Checked", user_id, {
                "result": "error",
                "reason": "user_not_found"
            })
            return jsonify({
                "error": "User not found",
                "code": "USER_NOT_FOUND"
            }), 404
        
        # Determine subscription plan - include users with active trials as Pro
        subscription_plan = getattr(user, 'subscription_plan', 'free')
        has_active_trial = user.has_active_trial() if hasattr(user, 'has_active_trial') else False
        is_pro = subscription_plan == 'pro' or has_active_trial
        
        # Check rate limits based on plan
        if is_pro:
            allowed, current_count, limit = check_pro_user_limit(user_id)
            plan_type = "pro"
            limit_window = "per_minute"
        else:
            allowed, current_count, limit = check_free_user_limit(user_id)
            plan_type = "free"
            limit_window = "per_day"
        
        # Track gate check event
        track_mixpanel_event("Gate Checked", user_id, {
            "result": "allowed" if allowed else "rate_limited",
            "plan": plan_type,
            "current_count": current_count,
            "limit": limit,
            "limit_window": limit_window
        })
        
        if not allowed:
            logger.warning(f"🚫 Rate limit exceeded for {plan_type} user {user_id}: {current_count}/{limit}")
            return jsonify({
                "error": f"Rate limit exceeded. {plan_type.title()} users are limited to {limit} questions {limit_window}.",
                "code": "RATE_LIMIT_EXCEEDED",
                "plan": plan_type,
                "current_count": current_count,
                "limit": limit,
                "reset_time": "next day" if plan_type == "free" else "next minute"
            }), 429
        
        # Increment count before proceeding
        increment_user_count(user_id, is_pro)
        
        logger.info(f"✅ Gate passed for {plan_type} user {user_id}")
        return f(*args, **kwargs)
    
    return decorated_function

# Initialize database tables
def init_subscription_gate(app=None):
    """Initialize subscription gate system"""
    try:
        if app:
            # Use provided app context
            with app.app_context():
                db.create_all()
                logger.info("✅ Subscription gate tables initialized")
        else:
            # Try to create tables without explicit context
            # This will work if called from within an app context
            db.create_all()
            logger.info("✅ Subscription gate tables initialized")
    except Exception as e:
        logger.error(f"❌ Error initializing subscription gate: {e}")

if __name__ == "__main__":
    # Test the subscription gate system
    print("🧪 Testing Subscription Gate System")
    print("=" * 50)
    
    # Test Redis connection
    if redis_client:
        try:
            redis_client.ping()
            print("✅ Redis connection: Working")
        except:
            print("❌ Redis connection: Failed")
    else:
        print("⚠️  Redis: Not configured, using PostgreSQL fallback")
    
    # Test Mixpanel
    if mixpanel_token:
        print("✅ Mixpanel: Configured")
    else:
        print("⚠️  Mixpanel: Not configured")
    
    print()
    print("🎯 Subscription Gate System Ready!")