import math
import random
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from models import Question, UserProgress, QuestionMetrics, db
import logging

logger = logging.getLogger(__name__)

class QuestionSelector:
    """Adaptive question selection using Item Response Theory (IRT) principles"""
    
    def __init__(self, user_id, exam_type):
        self.user_id = user_id
        self.exam_type = exam_type
        self.user_ability = None
        
    def calculate_user_ability(self):
        """Calculate user's current ability estimate using IRT"""
        recent_progress = UserProgress.query.filter_by(
            user_id=self.user_id,
            exam_type=self.exam_type
        ).filter(
            UserProgress.timestamp >= datetime.utcnow() - timedelta(days=30)
        ).order_by(desc(UserProgress.timestamp)).limit(50).all()
        
        if not recent_progress:
            # Default ability for new users
            self.user_ability = 0.0
            return self.user_ability
        
        # Calculate weighted accuracy with time decay
        total_weighted_score = 0
        total_weight = 0
        
        for progress in recent_progress:
            # Time decay factor (more recent = higher weight)
            days_ago = (datetime.utcnow() - progress.timestamp).days
            time_weight = math.exp(-days_ago / 10.0)  # Exponential decay
            
            # Difficulty adjustment
            difficulty_modifier = self.get_question_difficulty_rating(progress.question_id)
            
            # Performance score
            performance = 1.0 if progress.answered_correctly else 0.0
            
            # Adjust for response time (faster correct answers = higher ability)
            if progress.response_time and progress.response_time > 0:
                expected_time = 120  # 2 minutes default
                time_factor = max(0.5, min(1.5, expected_time / progress.response_time))
                performance *= time_factor
            
            weighted_score = performance * time_weight * (1 + difficulty_modifier)
            total_weighted_score += weighted_score
            total_weight += time_weight
        
        if total_weight > 0:
            accuracy = total_weighted_score / total_weight
            # Convert to IRT scale (-3 to +3)
            self.user_ability = (accuracy - 0.5) * 6
        else:
            self.user_ability = 0.0
            
        # Clamp to reasonable bounds
        self.user_ability = max(-3.0, min(3.0, self.user_ability))
        
        logger.info(f"User {self.user_id} ability calculated: {self.user_ability:.2f}")
        return self.user_ability
    
    def get_question_difficulty_rating(self, question_id):
        """Get or estimate question difficulty rating"""
        metrics = QuestionMetrics.query.filter_by(question_id=question_id).first()
        
        if metrics and metrics.times_answered > 5:
            # Use actual performance data
            difficulty = -math.log(max(0.01, metrics.correct_percentage / 100.0))
            return max(-2.0, min(2.0, difficulty))
        else:
            # Estimate from question metadata
            question = Question.query.get(question_id)
            if question:
                difficulty_map = {
                    'easy': -1.0,
                    'medium': 0.0,
                    'hard': 1.0,
                    'expert': 2.0
                }
                return difficulty_map.get(question.difficulty.lower(), 0.0)
        
        return 0.0
    
    def calculate_response_probability(self, user_ability, question_difficulty, discrimination=1.0):
        """Calculate probability of correct response using IRT 2PL model"""
        try:
            exponent = discrimination * (user_ability - question_difficulty)
            # Prevent overflow
            exponent = max(-10, min(10, exponent))
            probability = 1.0 / (1.0 + math.exp(-exponent))
            return probability
        except (OverflowError, ValueError):
            return 0.5
    
    def select_next_question(self, target_accuracy=0.75, exclude_recent=True):
        """Select the optimal next question for the user"""
        if self.user_ability is None:
            self.calculate_user_ability()
        
        # Get available questions
        query = Question.query.filter_by(exam_type=self.exam_type)
        
        # Exclude recently answered questions
        if exclude_recent:
            recent_questions = UserProgress.query.filter_by(
                user_id=self.user_id,
                exam_type=self.exam_type
            ).filter(
                UserProgress.timestamp >= datetime.utcnow() - timedelta(hours=24)
            ).with_entities(UserProgress.question_id).all()
            
            recent_ids = [q[0] for q in recent_questions]
            if recent_ids:
                query = query.filter(~Question.id.in_(recent_ids))
        
        available_questions = query.all()
        
        if not available_questions:
            # If no questions available, relax the recent filter
            available_questions = Question.query.filter_by(exam_type=self.exam_type).all()
        
        if not available_questions:
            return None
        
        # Find optimal question
        best_question = None
        best_score = float('inf')
        
        for question in available_questions:
            difficulty = self.get_question_difficulty_rating(question.id)
            probability = self.calculate_response_probability(self.user_ability, difficulty)
            
            # Score based on how close to target accuracy
            score = abs(probability - target_accuracy)
            
            # Add some randomization to prevent predictable patterns
            score += random.uniform(0, 0.1)
            
            # Prefer questions that haven't been asked much
            metrics = QuestionMetrics.query.filter_by(question_id=question.id).first()
            if not metrics or metrics.times_answered < 10:
                score *= 0.9  # Slight preference for less-asked questions
            
            if score < best_score:
                best_score = score
                best_question = question
        
        if best_question:
            logger.info(f"Selected question {best_question.id} with difficulty {self.get_question_difficulty_rating(best_question.id):.2f}")
        
        return best_question
    
    def update_question_metrics(self, question_id, is_correct, response_time=None):
        """Update question metrics after user response"""
        metrics = QuestionMetrics.query.filter_by(question_id=question_id).first()
        
        if not metrics:
            metrics = QuestionMetrics(question_id=question_id)
            db.session.add(metrics)
        
        # Update basic stats
        metrics.times_answered += 1
        
        # Update accuracy
        if metrics.times_answered == 1:
            metrics.correct_percentage = 100.0 if is_correct else 0.0
        else:
            # Exponential moving average
            alpha = 0.1  # Learning rate
            new_accuracy = 100.0 if is_correct else 0.0
            metrics.correct_percentage = (1 - alpha) * metrics.correct_percentage + alpha * new_accuracy
        
        # Update average time
        if response_time:
            if metrics.average_time == 0:
                metrics.average_time = response_time
            else:
                alpha = 0.2
                metrics.average_time = (1 - alpha) * metrics.average_time + alpha * response_time
        
        # Update difficulty rating using IRT
        if metrics.correct_percentage > 0:
            metrics.difficulty_rating = -math.log(max(0.01, metrics.correct_percentage / 100.0))
            metrics.difficulty_rating = max(-2.0, min(2.0, metrics.difficulty_rating))
        
        # Update discrimination index (simplified)
        if metrics.times_answered > 20:
            # Calculate based on variance in user performance
            metrics.discrimination_index = min(2.0, metrics.times_answered / 50.0)
        
        metrics.last_updated = datetime.utcnow()
        
        try:
            db.session.commit()
            logger.info(f"Updated metrics for question {question_id}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating question metrics: {e}")
    
    def get_topic_recommendations(self):
        """Get personalized topic recommendations based on performance"""
        # Get user's performance by topic
        topic_performance = {}
        
        progress_records = UserProgress.query.filter_by(
            user_id=self.user_id,
            exam_type=self.exam_type
        ).join(Question).filter(
            UserProgress.timestamp >= datetime.utcnow() - timedelta(days=14)
        ).all()
        
        for record in progress_records:
            question = Question.query.get(record.question_id)
            if question and question.topics:
                for topic in question.topics:
                    if topic not in topic_performance:
                        topic_performance[topic] = {'correct': 0, 'total': 0}
                    
                    topic_performance[topic]['total'] += 1
                    if record.answered_correctly:
                        topic_performance[topic]['correct'] += 1
        
        # Calculate accuracy per topic and identify weak areas
        weak_topics = []
        for topic, stats in topic_performance.items():
            if stats['total'] >= 3:  # Minimum questions for reliable stats
                accuracy = stats['correct'] / stats['total']
                if accuracy < 0.7:  # Below 70% accuracy
                    weak_topics.append({
                        'topic': topic,
                        'accuracy': accuracy,
                        'questions_answered': stats['total']
                    })
        
        # Sort by accuracy (weakest first)
        weak_topics.sort(key=lambda x: x['accuracy'])
        
        return weak_topics[:5]  # Top 5 weak topics
    
    def get_difficulty_progression(self):
        """Get recommended difficulty progression for user"""
        if self.user_ability is None:
            self.calculate_user_ability()
        
        # Map ability to difficulty preferences
        if self.user_ability < -1.5:
            return ['easy', 'easy', 'medium']  # Mostly easy questions
        elif self.user_ability < -0.5:
            return ['easy', 'medium', 'medium']  # Mixed easy/medium
        elif self.user_ability < 0.5:
            return ['medium', 'medium', 'hard']  # Mostly medium
        elif self.user_ability < 1.5:
            return ['medium', 'hard', 'hard']  # Mixed medium/hard
        else:
            return ['hard', 'hard', 'expert']  # Advanced questions
    
    def estimate_exam_readiness(self):
        """Estimate user's readiness for the actual exam"""
        if self.user_ability is None:
            self.calculate_user_ability()
        
        # Get recent performance stats
        recent_progress = UserProgress.query.filter_by(
            user_id=self.user_id,
            exam_type=self.exam_type
        ).filter(
            UserProgress.timestamp >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        if len(recent_progress) < 10:
            return {
                'readiness_score': 0,
                'confidence': 'low',
                'recommendation': 'Practice more questions to get a reliable assessment'
            }
        
        # Calculate various metrics
        accuracy = sum(1 for p in recent_progress if p.answered_correctly) / len(recent_progress)
        avg_time = sum(p.response_time for p in recent_progress if p.response_time) / len(recent_progress)
        
        # Readiness score (0-100)
        readiness_score = max(0, min(100, (self.user_ability + 3) * 100 / 6))
        
        # Confidence levels
        if readiness_score >= 80:
            confidence = 'high'
            recommendation = 'You appear ready for the exam! Focus on review and time management.'
        elif readiness_score >= 60:
            confidence = 'medium'
            recommendation = 'Good progress! Focus on weak topics and practice timing.'
        else:
            confidence = 'low'
            recommendation = 'More practice needed. Focus on fundamentals and building consistency.'
        
        return {
            'readiness_score': int(readiness_score),
            'confidence': confidence,
            'recommendation': recommendation,
            'accuracy': accuracy,
            'avg_response_time': avg_time
        }