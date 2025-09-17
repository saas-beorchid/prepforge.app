"""
Question Gate System - Rate limiting for free/pro users
Manages daily question limits and subscription-based access
"""

import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user
from models import db, UserActivity

logger = logging.getLogger(__name__)

def rate_limit(free_limit_per_day=20, pro_limit_per_minute=10):
    """
    Rate limiting decorator for question generation
    
    Args:
        free_limit_per_day: Daily limit for free users (default: 20)
        pro_limit_per_minute: Per-minute limit for pro users (default: 10)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({
                    'error': 'Authentication required',
                    'code': 'auth_required'
                }), 401
            
            user_id = current_user.id
            subscription_plan = getattr(current_user, 'subscription_plan', 'free')
            
            try:
                if subscription_plan == 'pro':
                    # Check per-minute limit for pro users
                    if not check_pro_rate_limit(user_id, pro_limit_per_minute):
                        return jsonify({
                            'error': f'Rate limit exceeded. Pro users can generate up to {pro_limit_per_minute} questions per minute.',
                            'code': 'rate_limit_exceeded',
                            'limit_type': 'pro_per_minute',
                            'limit': pro_limit_per_minute
                        }), 429
                else:
                    # Check daily limit for free users
                    remaining = check_free_daily_limit(user_id, free_limit_per_day)
                    if remaining <= 0:
                        return jsonify({
                            'error': f'Daily limit of {free_limit_per_day} questions reached. Upgrade to Pro for unlimited questions!',
                            'code': 'daily_limit_exceeded',
                            'limit_type': 'free_daily',
                            'limit': free_limit_per_day,
                            'remaining': 0
                        }), 429
                
                # Execute the original function
                result = f(*args, **kwargs)
                
                # Record the activity after successful execution
                record_user_activity(user_id, 'question_generated')
                
                return result
                
            except Exception as e:
                logger.error(f"Rate limit check failed for user {user_id}: {e}")
                # Allow the request to proceed if rate limiting fails
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def check_free_daily_limit(user_id, daily_limit):
    """
    Check daily question limit for free users
    Returns remaining questions count
    """
    try:
        today = datetime.utcnow().date()
        
        # Count questions generated today
        activity = UserActivity.query.filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == 'question_generated',
            db.func.date(UserActivity.created_at) == today
        ).first()
        
        if activity:
            questions_today = activity.count
            remaining = max(0, daily_limit - questions_today)
        else:
            remaining = daily_limit
        
        logger.debug(f"Free user {user_id} has {remaining}/{daily_limit} questions remaining today")
        return remaining
        
    except Exception as e:
        logger.error(f"Error checking daily limit for user {user_id}: {e}")
        return daily_limit  # Default to allowing requests if check fails

def check_pro_rate_limit(user_id, per_minute_limit):
    """
    Check per-minute rate limit for pro users
    Returns True if within limit, False otherwise
    """
    try:
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        
        # Count questions generated in the last minute
        recent_activity = UserActivity.query.filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == 'question_generated',
            UserActivity.created_at >= one_minute_ago
        ).count()
        
        within_limit = recent_activity < per_minute_limit
        logger.debug(f"Pro user {user_id} has generated {recent_activity}/{per_minute_limit} questions in last minute")
        
        return within_limit
        
    except Exception as e:
        logger.error(f"Error checking per-minute limit for user {user_id}: {e}")
        return True  # Default to allowing requests if check fails

def record_user_activity(user_id, activity_type):
    """
    Record user activity for rate limiting
    """
    try:
        today = datetime.utcnow().date()
        
        # Find or create today's activity record
        activity = UserActivity.query.filter(
            UserActivity.user_id == user_id,
            UserActivity.activity_type == activity_type,
            db.func.date(UserActivity.created_at) == today
        ).first()
        
        if activity:
            activity.count += 1
            activity.updated_at = datetime.utcnow()
        else:
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_type,
                count=1
            )
            db.session.add(activity)
        
        db.session.commit()
        logger.debug(f"Recorded {activity_type} for user {user_id}, count: {activity.count}")
        
    except Exception as e:
        logger.error(f"Error recording user activity for user {user_id}: {e}")
        db.session.rollback()

def get_trial_remaining(user_id):
    """
    Get remaining trial questions for a user
    """
    try:
        return check_free_daily_limit(user_id, 20)
    except Exception as e:
        logger.error(f"Error getting trial remaining for user {user_id}: {e}")
        return 20  # Default to full trial

def get_user_activity_stats(user_id, days=7):
    """
    Get user activity statistics for the last N days
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        activities = UserActivity.query.filter(
            UserActivity.user_id == user_id,
            UserActivity.created_at >= cutoff_date
        ).all()
        
        stats = {}
        for activity in activities:
            date_key = activity.created_at.date().isoformat()
            if date_key not in stats:
                stats[date_key] = {}
            stats[date_key][activity.activity_type] = activity.count
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting activity stats for user {user_id}: {e}")
        return {}