"""
Enhanced Session Manager for Practice Flow Persistence
Ensures robust session state management across practice sessions
"""

import logging
import json
from datetime import datetime
from flask import session
from functools import wraps

logger = logging.getLogger(__name__)

class PracticeSessionManager:
    """Manages practice session state with persistence and recovery"""
    
    REQUIRED_KEYS = [
        'exam_type', 'question_ids', 'current_index', 
        'used_questions', 'session_stats', 'show_feedback'
    ]
    
    @staticmethod
    def initialize_session(exam_type, question_ids):
        """Initialize a new practice session with proper state"""
        try:
            session['exam_type'] = exam_type
            session['question_ids'] = question_ids
            session['current_index'] = 0
            session['used_questions'] = session.get('used_questions', [])
            session['show_feedback'] = False
            session['user_answer'] = None
            session['session_stats'] = {
                'questions_answered': 0,
                'correct_answers': 0,
                'session_start': datetime.now().isoformat(),
                'exam_type': exam_type
            }
            
            # Mark session as properly initialized
            session['session_initialized'] = True
            session.permanent = True
            
            logger.info(f"Practice session initialized for {exam_type} with {len(question_ids)} questions")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize practice session: {e}")
            return False
    
    @staticmethod
    def validate_session():
        """Validate that current session has all required data"""
        try:
            if not session.get('session_initialized'):
                return False
                
            for key in PracticeSessionManager.REQUIRED_KEYS:
                if key not in session:
                    logger.warning(f"Missing session key: {key}")
                    return False
            
            # Check that question_ids is valid
            question_ids = session.get('question_ids', [])
            if not question_ids or not isinstance(question_ids, list):
                logger.warning("Invalid question_ids in session")
                return False
                
            # Check current_index is valid
            current_index = session.get('current_index', -1)
            if current_index < 0 or current_index >= len(question_ids):
                logger.warning(f"Invalid current_index: {current_index} for {len(question_ids)} questions")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return False
    
    @staticmethod
    def recover_session():
        """Attempt to recover a corrupted session"""
        try:
            logger.info("Attempting session recovery")
            
            # Keep what we can and reset the rest
            exam_type = session.get('exam_type')
            used_questions = session.get('used_questions', [])
            
            if exam_type:
                logger.info(f"Recovering session for exam type: {exam_type}")
                # Clear corrupted data but keep essentials
                session['current_index'] = 0
                session['show_feedback'] = False
                session['user_answer'] = None
                session['used_questions'] = used_questions
                
                # Reset session stats
                session['session_stats'] = {
                    'questions_answered': 0,
                    'correct_answers': 0,
                    'session_start': datetime.now().isoformat(),
                    'exam_type': exam_type
                }
                
                return True
            else:
                logger.warning("Cannot recover session - no exam type found")
                return False
                
        except Exception as e:
            logger.error(f"Session recovery failed: {e}")
            return False
    
    @staticmethod
    def clear_session():
        """Clear practice session data"""
        try:
            keys_to_clear = [
                'exam_type', 'question_ids', 'current_index', 
                'show_feedback', 'user_answer', 'session_stats',
                'session_initialized'
            ]
            
            for key in keys_to_clear:
                session.pop(key, None)
                
            logger.info("Practice session cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            return False

def require_valid_session(f):
    """Decorator to ensure valid practice session exists"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not PracticeSessionManager.validate_session():
            logger.warning("Invalid session detected, attempting recovery")
            
            if not PracticeSessionManager.recover_session():
                logger.error("Session recovery failed, redirecting to dashboard")
                from flask import flash, redirect, url_for
                flash('Your practice session was interrupted. Please start a new session.', 'warning')
                return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def log_session_state():
    """Debug helper to log current session state"""
    try:
        session_data = {
            'exam_type': session.get('exam_type'),
            'question_count': len(session.get('question_ids', [])),
            'current_index': session.get('current_index'),
            'show_feedback': session.get('show_feedback'),
            'used_questions_count': len(session.get('used_questions', [])),
            'session_initialized': session.get('session_initialized')
        }
        logger.debug(f"Session state: {session_data}")
    except Exception as e:
        logger.error(f"Failed to log session state: {e}")