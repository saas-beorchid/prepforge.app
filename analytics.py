import math
import numpy as np
from datetime import datetime, timedelta, date
from sqlalchemy import func, desc, and_
from models import UserProgress, Question, QuestionMetrics, StudyGoal, User, db
import logging

logger = logging.getLogger(__name__)

class UserAnalytics:
    """Advanced analytics for user performance and learning patterns"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        
    def calculate_topic_mastery(self, exam_type, days_back=30):
        """Calculate user's mastery level for each topic"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get user progress with question topics
        progress_query = db.session.query(
            UserProgress, Question
        ).join(
            Question, UserProgress.question_id == Question.id
        ).filter(
            UserProgress.user_id == self.user_id,
            UserProgress.exam_type == exam_type,
            UserProgress.timestamp >= cutoff_date
        ).all()
        
        topic_stats = {}
        
        for progress, question in progress_query:
            if not question.topics:
                continue
                
            for topic in question.topics:
                if topic not in topic_stats:
                    topic_stats[topic] = {
                        'total_questions': 0,
                        'correct_answers': 0,
                        'total_time': 0,
                        'recent_accuracy': [],
                        'difficulty_levels': {}
                    }
                
                stats = topic_stats[topic]
                stats['total_questions'] += 1
                
                if progress.answered_correctly:
                    stats['correct_answers'] += 1
                    
                if progress.response_time:
                    stats['total_time'] += progress.response_time
                
                # Track recent performance (last 10 questions)
                stats['recent_accuracy'].append(1 if progress.answered_correctly else 0)
                if len(stats['recent_accuracy']) > 10:
                    stats['recent_accuracy'] = stats['recent_accuracy'][-10:]
                
                # Track difficulty distribution
                difficulty = question.difficulty or 'medium'
                if difficulty not in stats['difficulty_levels']:
                    stats['difficulty_levels'][difficulty] = {'total': 0, 'correct': 0}
                
                stats['difficulty_levels'][difficulty]['total'] += 1
                if progress.answered_correctly:
                    stats['difficulty_levels'][difficulty]['correct'] += 1
        
        # Calculate mastery scores
        topic_mastery = {}
        for topic, stats in topic_stats.items():
            if stats['total_questions'] < 3:  # Need minimum questions
                continue
                
            overall_accuracy = stats['correct_answers'] / stats['total_questions']
            recent_accuracy = sum(stats['recent_accuracy']) / len(stats['recent_accuracy']) if stats['recent_accuracy'] else overall_accuracy
            
            # Weight recent performance more heavily
            weighted_accuracy = (overall_accuracy * 0.4) + (recent_accuracy * 0.6)
            
            # Adjust for difficulty progression
            difficulty_bonus = 0
            for difficulty, diff_stats in stats['difficulty_levels'].items():
                if diff_stats['total'] >= 2:
                    diff_accuracy = diff_stats['correct'] / diff_stats['total']
                    multiplier = {'easy': 1.0, 'medium': 1.2, 'hard': 1.5, 'expert': 2.0}.get(difficulty, 1.0)
                    difficulty_bonus += (diff_accuracy * multiplier * diff_stats['total'])
            
            difficulty_bonus = difficulty_bonus / stats['total_questions'] if stats['total_questions'] > 0 else 0
            
            # Final mastery score (0-100)
            mastery_score = min(100, (weighted_accuracy * 70) + (difficulty_bonus * 30))
            
            topic_mastery[topic] = {
                'mastery_score': round(mastery_score, 2),
                'accuracy': round(overall_accuracy * 100, 2),
                'recent_accuracy': round(recent_accuracy * 100, 2),
                'questions_practiced': stats['total_questions'],
                'avg_time_per_question': round(stats['total_time'] / stats['total_questions']) if stats['total_questions'] > 0 else 0,
                'difficulty_distribution': stats['difficulty_levels']
            }
        
        return topic_mastery
    
    def predict_exam_score(self, exam_type, confidence_interval=0.95):
        """Predict user's likely exam score with confidence intervals"""
        # Get recent performance data
        recent_progress = UserProgress.query.filter_by(
            user_id=self.user_id,
            exam_type=self.exam_type
        ).filter(
            UserProgress.timestamp >= datetime.utcnow() - timedelta(days=14)
        ).order_by(desc(UserProgress.timestamp)).limit(100).all()
        
        if len(recent_progress) < 10:
            return {
                'predicted_score': None,
                'confidence_interval': None,
                'data_insufficient': True,
                'message': 'Need at least 10 recent questions for reliable prediction'
            }
        
        # Calculate performance metrics
        accuracies = []
        response_times = []
        difficulty_adjustments = []
        
        for progress in recent_progress:
            question = Question.query.get(progress.question_id)
            if not question:
                continue
                
            accuracy = 1.0 if progress.answered_correctly else 0.0
            accuracies.append(accuracy)
            
            if progress.response_time:
                response_times.append(progress.response_time)
            
            # Difficulty adjustment
            difficulty_map = {'easy': 0.8, 'medium': 1.0, 'hard': 1.3, 'expert': 1.6}
            multiplier = difficulty_map.get(question.difficulty, 1.0)
            difficulty_adjustments.append(accuracy * multiplier)
        
        # Basic prediction using weighted accuracy
        overall_accuracy = sum(accuracies) / len(accuracies)
        difficulty_adjusted_accuracy = sum(difficulty_adjustments) / len(difficulty_adjustments)
        
        # Time factor (penalize very slow responses)
        avg_time = sum(response_times) / len(response_times) if response_times else 120
        time_factor = max(0.7, min(1.2, 120 / avg_time))  # Optimal around 2 minutes
        
        # Learning velocity (trend analysis)
        if len(accuracies) >= 20:
            first_half = sum(accuracies[:len(accuracies)//2]) / (len(accuracies)//2)
            second_half = sum(accuracies[len(accuracies)//2:]) / (len(accuracies) - len(accuracies)//2)
            learning_velocity = (second_half - first_half) * 0.1  # Small adjustment
        else:
            learning_velocity = 0
        
        # Final prediction
        predicted_accuracy = min(1.0, difficulty_adjusted_accuracy * time_factor + learning_velocity)
        
        # Convert to exam score (varies by exam type)
        score_mappings = {
            'GMAT': {'min': 200, 'max': 800, 'pass': 650},
            'MCAT': {'min': 472, 'max': 528, 'pass': 500},
            'GRE': {'min': 260, 'max': 340, 'pass': 300},
            'LSAT': {'min': 120, 'max': 180, 'pass': 150},
            'SAT': {'min': 400, 'max': 1600, 'pass': 1000},
            'ACT': {'min': 1, 'max': 36, 'pass': 21}
        }
        
        mapping = score_mappings.get(exam_type, {'min': 0, 'max': 100, 'pass': 70})
        score_range = mapping['max'] - mapping['min']
        predicted_score = mapping['min'] + (predicted_accuracy * score_range)
        
        # Calculate confidence interval
        accuracy_std = np.std(accuracies) if len(accuracies) > 1 else 0.1
        margin_of_error = 1.96 * accuracy_std * score_range  # 95% confidence
        
        return {
            'predicted_score': round(predicted_score),
            'confidence_interval': {
                'lower': max(mapping['min'], round(predicted_score - margin_of_error)),
                'upper': min(mapping['max'], round(predicted_score + margin_of_error))
            },
            'accuracy': round(predicted_accuracy * 100, 2),
            'data_points': len(recent_progress),
            'passing_threshold': mapping['pass'],
            'likely_to_pass': predicted_score >= mapping['pass']
        }
    
    def generate_study_recommendations(self, exam_type):
        """Generate personalized study recommendations"""
        topic_mastery = self.calculate_topic_mastery(exam_type)
        
        # Identify weak areas
        weak_topics = [
            (topic, data) for topic, data in topic_mastery.items()
            if data['mastery_score'] < 70
        ]
        weak_topics.sort(key=lambda x: x[1]['mastery_score'])
        
        # Identify strong areas
        strong_topics = [
            (topic, data) for topic, data in topic_mastery.items()
            if data['mastery_score'] >= 85
        ]
        
        recommendations = []
        
        # Focus areas
        if weak_topics:
            recommendations.append({
                'type': 'focus_areas',
                'priority': 'high',
                'title': 'Topics requiring immediate attention',
                'topics': [topic for topic, _ in weak_topics[:3]],
                'strategy': 'Practice fundamentals and build consistency'
            })
        
        # Time management
        avg_times = [data['avg_time_per_question'] for _, data in topic_mastery.items()]
        if avg_times:
            avg_time = sum(avg_times) / len(avg_times)
            if avg_time > 150:  # More than 2.5 minutes
                recommendations.append({
                    'type': 'time_management',
                    'priority': 'medium',
                    'title': 'Improve response speed',
                    'strategy': 'Practice timed questions and learn to eliminate wrong answers quickly'
                })
        
        # Difficulty progression
        difficulty_distribution = self.get_difficulty_distribution(exam_type)
        if difficulty_distribution.get('hard', 0) < 0.2:  # Less than 20% hard questions
            recommendations.append({
                'type': 'difficulty_progression',
                'priority': 'medium',
                'title': 'Challenge yourself with harder questions',
                'strategy': 'Gradually increase difficulty to build confidence'
            })
        
        # Maintenance for strong areas
        if strong_topics:
            recommendations.append({
                'type': 'maintenance',
                'priority': 'low',
                'title': 'Maintain strengths',
                'topics': [topic for topic, _ in strong_topics],
                'strategy': 'Light review to prevent knowledge decay'
            })
        
        return recommendations
    
    def get_difficulty_distribution(self, exam_type):
        """Get user's question difficulty distribution"""
        recent_progress = UserProgress.query.filter_by(
            user_id=self.user_id,
            exam_type=exam_type
        ).filter(
            UserProgress.timestamp >= datetime.utcnow() - timedelta(days=14)
        ).join(Question).all()
        
        distribution = {'easy': 0, 'medium': 0, 'hard': 0, 'expert': 0}
        total = len(recent_progress)
        
        for progress in recent_progress:
            question = Question.query.get(progress.question_id)
            if question and question.difficulty:
                distribution[question.difficulty] = distribution.get(question.difficulty, 0) + 1
        
        # Convert to percentages
        if total > 0:
            distribution = {k: v/total for k, v in distribution.items()}
        
        return distribution
    
    def track_learning_velocity(self, exam_type, time_window_days=30):
        """Track user's learning improvement rate over time"""
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
        
        progress_records = UserProgress.query.filter_by(
            user_id=self.user_id,
            exam_type=exam_type
        ).filter(
            UserProgress.timestamp >= cutoff_date
        ).order_by(UserProgress.timestamp).all()
        
        if len(progress_records) < 20:
            return {
                'velocity': 0,
                'trend': 'insufficient_data',
                'improvement_rate': 0
            }
        
        # Split into time chunks and calculate accuracy for each
        chunk_size = max(5, len(progress_records) // 6)  # 6 time periods
        chunks = []
        
        for i in range(0, len(progress_records), chunk_size):
            chunk = progress_records[i:i+chunk_size]
            if len(chunk) >= 3:
                accuracy = sum(1 for p in chunk if p.answered_correctly) / len(chunk)
                chunks.append(accuracy)
        
        if len(chunks) < 3:
            return {
                'velocity': 0,
                'trend': 'insufficient_data',
                'improvement_rate': 0
            }
        
        # Calculate trend using linear regression
        x = list(range(len(chunks)))
        y = chunks
        
        n = len(chunks)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        # Slope of the trend line
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Determine trend
        if slope > 0.02:
            trend = 'improving'
        elif slope < -0.02:
            trend = 'declining'
        else:
            trend = 'stable'
        
        # Velocity as percentage improvement per week
        velocity = slope * 7 * 100  # Convert to weekly percentage change
        
        return {
            'velocity': round(velocity, 2),
            'trend': trend,
            'improvement_rate': round(slope * 100, 2),
            'current_accuracy': round(chunks[-1] * 100, 2),
            'starting_accuracy': round(chunks[0] * 100, 2)
        }
    
    def get_study_streak_analytics(self):
        """Analyze user's study consistency and streaks"""
        # Get all study days in the last 90 days
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        study_days = db.session.query(
            func.date(UserProgress.timestamp).label('study_date'),
            func.count(UserProgress.id).label('questions_count')
        ).filter(
            UserProgress.user_id == self.user_id,
            UserProgress.timestamp >= cutoff_date
        ).group_by(
            func.date(UserProgress.timestamp)
        ).order_by(
            func.date(UserProgress.timestamp)
        ).all()
        
        if not study_days:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'study_frequency': 0,
                'average_daily_questions': 0
            }
        
        # Calculate streaks
        study_dates = [day.study_date for day in study_days]
        current_streak = 0
        longest_streak = 0
        current_streak_count = 0
        
        # Check for current streak (from today backwards)
        today = date.today()
        check_date = today
        
        while check_date in study_dates:
            current_streak += 1
            check_date -= timedelta(days=1)
        
        # Calculate longest streak
        for i, study_date in enumerate(study_dates):
            if i == 0:
                current_streak_count = 1
            else:
                prev_date = study_dates[i-1]
                if (study_date - prev_date).days == 1:
                    current_streak_count += 1
                else:
                    longest_streak = max(longest_streak, current_streak_count)
                    current_streak_count = 1
        
        longest_streak = max(longest_streak, current_streak_count)
        
        # Study frequency
        total_days = (study_dates[-1] - study_dates[0]).days + 1 if len(study_dates) > 1 else 1
        study_frequency = len(study_dates) / total_days
        
        # Average questions per day
        total_questions = sum(day.questions_count for day in study_days)
        avg_daily_questions = total_questions / len(study_days)
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'study_frequency': round(study_frequency * 100, 2),
            'average_daily_questions': round(avg_daily_questions, 1),
            'total_study_days': len(study_days),
            'days_analyzed': total_days
        }
    
    def generate_performance_report(self, exam_type):
        """Generate comprehensive performance report"""
        topic_mastery = self.calculate_topic_mastery(exam_type)
        score_prediction = self.predict_exam_score(exam_type)
        learning_velocity = self.track_learning_velocity(exam_type)
        streak_analytics = self.get_study_streak_analytics()
        recommendations = self.generate_study_recommendations(exam_type)
        
        # Overall performance grade
        if score_prediction['predicted_score']:
            pass_threshold = score_prediction['passing_threshold']
            predicted_score = score_prediction['predicted_score']
            
            if predicted_score >= pass_threshold * 1.2:
                performance_grade = 'A'
            elif predicted_score >= pass_threshold * 1.1:
                performance_grade = 'B'
            elif predicted_score >= pass_threshold:
                performance_grade = 'C'
            elif predicted_score >= pass_threshold * 0.9:
                performance_grade = 'D'
            else:
                performance_grade = 'F'
        else:
            performance_grade = 'Incomplete'
        
        return {
            'exam_type': exam_type,
            'performance_grade': performance_grade,
            'topic_mastery': topic_mastery,
            'score_prediction': score_prediction,
            'learning_velocity': learning_velocity,
            'streak_analytics': streak_analytics,
            'recommendations': recommendations,
            'generated_at': datetime.utcnow().isoformat()
        }