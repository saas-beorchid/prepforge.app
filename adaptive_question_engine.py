"""
Adaptive Question Engine for PrepForge
Implements user performance tracking and adaptive difficulty adjustment using xAI API
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from flask import current_app

logger = logging.getLogger(__name__)

class AdaptiveQuestionEngine:
    """Engine for adaptive question generation based on user performance"""
    
    def __init__(self):
        """Initialize the adaptive engine with xAI generator"""
        from xai_question_generator import XAIQuestionGenerator
        self.xai_generator = XAIQuestionGenerator()
        
    def get_user_performance(self, user_id: int, exam_type: str, topic: str):
        """Get user performance for specific exam type and topic"""
        try:
            from models import UserPerformance
            performance = UserPerformance.query.filter_by(
                user_id=user_id,
                exam_type=exam_type,
                topic=topic
            ).first()
            
            logger.info(f"📊 Retrieved performance for user {user_id}: {exam_type} - {topic}")
            return performance
            
        except Exception as e:
            logger.error(f"❌ Error retrieving user performance: {e}")
            return None
    
    def calculate_user_score(self, user_id: int, exam_type: str, topic: str) -> float:
        """Calculate user's current score percentage for a topic"""
        try:
            from models import UserProgress
            # Get recent progress records for this topic
            progress_records = UserProgress.query.filter_by(
                user_id=user_id,
                exam_type=exam_type
            ).order_by(UserProgress.answered_at.desc()).limit(10).all()
            
            if not progress_records:
                logger.info(f"📊 No progress records found for user {user_id} - {exam_type} - {topic}")
                return 50.0  # Default score for new users
            
            # Filter by topic if possible (check question metadata)
            topic_records = []
            for record in progress_records:
                # For now, include all records since we don't have topic filtering
                # In production, you'd check question.topics or question.subject
                topic_records.append(record)
            
            if not topic_records:
                return 50.0
            
            # Calculate percentage correct
            correct_count = sum(1 for record in topic_records if record.answered_correctly)
            total_count = len(topic_records)
            score = (correct_count / total_count) * 100
            
            logger.info(f"📊 Calculated score for user {user_id}: {score:.1f}% ({correct_count}/{total_count})")
            return score
            
        except Exception as e:
            logger.error(f"❌ Error calculating user score: {e}")
            return 50.0  # Default fallback
    
    def update_user_performance(self, user_id: int, exam_type: str, topic: str, score: float):
        """Update or create user performance record"""
        try:
            from models import db, UserPerformance
            # Get existing record or create new one
            performance = UserPerformance.query.filter_by(
                user_id=user_id,
                exam_type=exam_type,
                topic=topic
            ).first()
            
            if performance:
                # Update existing record
                performance.score = score
                performance.attempts += 1
                performance.last_updated = datetime.utcnow()
                logger.info(f"📊 Updated performance for user {user_id}: {exam_type} - {topic} = {score:.1f}%")
            else:
                # Create new record
                performance = UserPerformance(
                    user_id=user_id,
                    exam_type=exam_type,
                    topic=topic,
                    score=score,
                    attempts=1,
                    last_updated=datetime.utcnow()
                )
                db.session.add(performance)
                logger.info(f"📊 Created new performance record for user {user_id}: {exam_type} - {topic} = {score:.1f}%")
            
            db.session.commit()
            return performance
            
        except Exception as e:
            logger.error(f"❌ Error updating user performance: {e}")
            db.session.rollback()
            raise
    
    def determine_difficulty(self, score: float) -> str:
        """Determine difficulty level based on user score"""
        if score < 40:
            return 'easy'
        elif score <= 70:
            return 'medium'
        else:
            return 'hard'
    
    def generate_adaptive_questions(self, user_id: int, exam_type: str, topic: str, count: int = 1) -> List[Dict]:
        """Generate adaptive questions based on user performance"""
        try:
            # Calculate current user score
            current_score = self.calculate_user_score(user_id, exam_type, topic)
            
            # Update performance record
            performance = self.update_user_performance(user_id, exam_type, topic, current_score)
            
            # Determine difficulty level
            difficulty = self.determine_difficulty(current_score)
            
            logger.info(f"🎯 Generating {difficulty} {exam_type} questions for user {user_id} (score: {current_score:.1f}%)")
            
            # Track adaptation in Mixpanel
            self._track_question_adaptation(user_id, exam_type, topic, difficulty, current_score)
            
            # Generate questions with xAI using adaptive prompts
            questions = self.xai_generator.generate_adaptive_questions(
                exam_type=exam_type,
                topic=topic,
                difficulty=difficulty,
                user_score=current_score,
                count=count
            )
            
            logger.info(f"✅ Generated {len(questions)} adaptive {difficulty} questions")
            return questions
            
        except Exception as e:
            logger.error(f"❌ Error generating adaptive questions: {e}")
            raise
    
    def _track_question_adaptation(self, user_id: int, exam_type: str, topic: str, difficulty: str, score: float):
        """Track question adaptation in Mixpanel"""
        try:
            from subscription_gate import track_mixpanel_event
            
            properties = {
                'exam_type': exam_type,
                'topic': topic,
                'difficulty': difficulty,
                'score': score,
                'adaptation_engine': 'xai_adaptive'
            }
            
            track_mixpanel_event('Question Adapted', user_id, properties)
            logger.info(f"📊 Tracked adaptation: user={user_id}, {exam_type}-{topic}, {difficulty} (score: {score:.1f}%)")
            
        except Exception as e:
            logger.warning(f"⚠️ Mixpanel tracking failed: {e}")

# Global instance
adaptive_engine = AdaptiveQuestionEngine()