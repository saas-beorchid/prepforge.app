"""
Enhanced Session Persistence System for PrepForge
Ensures 100% session continuity across logins, trial limits, and subscription upgrades
"""

import uuid
import logging
from datetime import datetime, timedelta
from flask import session, current_app
from models import db, PracticeSession, TrialUsage, UserProgress
from flask_login import current_user

logger = logging.getLogger(__name__)

class SessionPersistenceManager:
    """Comprehensive session management for seamless user experience"""
    
    @staticmethod
    def save_session_to_db():
        """Save current Flask session to database for persistence"""
        if not current_user.is_authenticated:
            return None
            
        try:
            # Generate unique session ID if not exists
            session_id = session.get('persistent_session_id')
            if not session_id:
                session_id = f"sess_{uuid.uuid4().hex[:16]}"
                session['persistent_session_id'] = session_id
            
            # Get current session data
            exam_type = session.get('exam_type')
            question_ids = session.get('question_ids', [])
            current_index = session.get('current_index', 0)
            
            if not exam_type or not question_ids:
                return None
                
            # Check if session already exists
            practice_session = PracticeSession.query.filter_by(
                id=session_id,
                user_id=current_user.id
            ).first()
            
            if not practice_session:
                practice_session = PracticeSession(
                    id=session_id,
                    user_id=current_user.id,
                    exam_type=exam_type,
                    question_ids=question_ids,
                    current_index=current_index,
                    session_stats=session.get('session_stats', {}),
                    questions_in_session=len([q for q in question_ids[:current_index] if q])
                )
                db.session.add(practice_session)
            else:
                # Update existing session
                practice_session.exam_type = exam_type
                practice_session.question_ids = question_ids
                practice_session.current_index = current_index
                practice_session.session_stats = session.get('session_stats', {})
                practice_session.updated_at = datetime.utcnow()
                practice_session.questions_in_session = len([q for q in question_ids[:current_index] if q])
            
            db.session.commit()
            logger.info(f"Session {session_id} saved for user {current_user.id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def restore_session_from_db():
        """Restore session from database if available"""
        if not current_user.is_authenticated:
            return False
            
        try:
            # Find most recent incomplete session
            practice_session = PracticeSession.query.filter_by(
                user_id=current_user.id,
                completed=False
            ).order_by(PracticeSession.updated_at.desc()).first()
            
            if not practice_session:
                return False
                
            # Check if session is recent (within 7 days)
            days_old = (datetime.utcnow() - practice_session.updated_at).days
            if days_old > 7:
                logger.info(f"Session {practice_session.id} too old ({days_old} days), not restoring")
                return False
            
            # Restore session data
            session['persistent_session_id'] = practice_session.id
            session['exam_type'] = practice_session.exam_type
            session['question_ids'] = practice_session.question_ids
            session['current_index'] = practice_session.current_index
            session['session_stats'] = practice_session.session_stats or {}
            session['session_initialized'] = True
            session['show_feedback'] = False
            
            logger.info(f"Restored session {practice_session.id} for user {current_user.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore session: {e}")
            return False
    
    @staticmethod
    def mark_session_completed():
        """Mark current session as completed"""
        session_id = session.get('persistent_session_id')
        if not session_id:
            return
            
        try:
            practice_session = PracticeSession.query.filter_by(id=session_id).first()
            if practice_session:
                practice_session.completed = True
                practice_session.updated_at = datetime.utcnow()
                db.session.commit()
                logger.info(f"Session {session_id} marked as completed")
                
        except Exception as e:
            logger.error(f"Failed to mark session completed: {e}")
            db.session.rollback()
    
    @staticmethod
    def get_trial_status(exam_type):
        """Get comprehensive trial status for exam type"""
        if not current_user.is_authenticated:
            return {'is_premium': False, 'questions_remaining': 0, 'can_start_session': False}
            
        # Check if user is premium
        is_premium = current_user.subscription and current_user.subscription.active
        if is_premium:
            return {
                'is_premium': True,
                'questions_remaining': float('inf'),
                'can_start_session': True,
                'session_allowed': True
            }
        
        # Get trial usage
        trial_usage = TrialUsage.query.filter_by(
            user_id=current_user.id,
            exam_type=exam_type
        ).first()
        
        if not trial_usage:
            # New trial user
            return {
                'is_premium': False,
                'questions_remaining': 20,
                'can_start_session': True,
                'session_allowed': True,
                'is_new_trial': True
            }
        
        questions_used = trial_usage.questions_used
        questions_remaining = max(0, 20 - questions_used)
        
        # Allow new session if user has enough questions remaining (minimum 5 per session)
        can_start_session = questions_remaining >= 5
        
        return {
            'is_premium': False,
            'questions_used': questions_used,
            'questions_remaining': questions_remaining,
            'can_start_session': can_start_session,
            'session_allowed': questions_remaining > 0,
            'trial_completed': trial_usage.trial_completed
        }
    
    @staticmethod
    def update_trial_usage(exam_type, questions_answered):
        """Update trial usage tracking"""
        if not current_user.is_authenticated:
            return
            
        # Skip if user is premium
        if current_user.subscription and current_user.subscription.active:
            return
            
        try:
            trial_usage = TrialUsage.query.filter_by(
                user_id=current_user.id,
                exam_type=exam_type
            ).first()
            
            if not trial_usage:
                trial_usage = TrialUsage(
                    user_id=current_user.id,
                    exam_type=exam_type,
                    questions_used=questions_answered,
                    sessions_completed=1
                )
                db.session.add(trial_usage)
            else:
                trial_usage.questions_used += questions_answered
                trial_usage.sessions_completed += 1
                trial_usage.last_session_date = datetime.utcnow()
                
                # Mark trial as completed if limit reached
                if trial_usage.questions_used >= 20:
                    trial_usage.trial_completed = True
            
            db.session.commit()
            logger.info(f"Updated trial usage for {current_user.id}: {exam_type} - {trial_usage.questions_used}/20")
            
        except Exception as e:
            logger.error(f"Failed to update trial usage: {e}")
            db.session.rollback()
    
    @staticmethod
    def get_incomplete_sessions():
        """Get list of incomplete sessions for user"""
        if not current_user.is_authenticated:
            return []
            
        try:
            sessions = PracticeSession.query.filter_by(
                user_id=current_user.id,
                completed=False
            ).order_by(PracticeSession.updated_at.desc()).limit(5).all()
            
            session_data = []
            for ps in sessions:
                # Check if session is recent (within 7 days)
                days_old = (datetime.utcnow() - ps.updated_at).days
                if days_old <= 7:
                    progress = f"{ps.current_index + 1}/{len(ps.question_ids)}"
                    session_data.append({
                        'id': ps.id,
                        'exam_type': ps.exam_type,
                        'progress': progress,
                        'questions_remaining': len(ps.question_ids) - ps.current_index - 1,
                        'updated_at': ps.updated_at.strftime('%b %d at %I:%M %p'),
                        'days_old': days_old
                    })
            
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to get incomplete sessions: {e}")
            return []
    
    @staticmethod
    def cleanup_old_sessions():
        """Clean up sessions older than 30 days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            old_sessions = PracticeSession.query.filter(
                PracticeSession.updated_at < cutoff_date
            ).all()
            
            for session in old_sessions:
                db.session.delete(session)
            
            db.session.commit()
            logger.info(f"Cleaned up {len(old_sessions)} old sessions")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            db.session.rollback()