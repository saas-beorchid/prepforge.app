"""
Strategic AI Engine - Complete 5-Layer Framework Implementation
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import func

logger = logging.getLogger(__name__)

class StrategicAIEngine:
    """5-Layer Strategic Framework for AI-Powered Question Generation"""
    
    def __init__(self):
        self.quality_thresholds = {
            'minimum_score': 6.0,
            'content_relevance': 0.8,
            'explanation_quality': 0.7,
            'option_distinctiveness': 0.6
        }
        
    # LAYER 1: CONTENT FRAMEWORK
    def get_content_standards(self, exam_type: str) -> Dict[str, Any]:
        """Get content standards for exam type"""
        standards_map = {
            'GMAT': {
                'difficulty_levels': [1, 2, 3, 4, 5],
                'topics': ['Quantitative Reasoning', 'Verbal Reasoning', 'Data Sufficiency'],
                'question_types': ['multiple_choice', 'data_sufficiency'],
                'time_limits': {'per_question': 120, 'total': 187}
            },
            'GRE': {
                'difficulty_levels': [1, 2, 3, 4, 5],
                'topics': ['Verbal Reasoning', 'Quantitative Reasoning', 'Analytical Writing'],
                'question_types': ['multiple_choice', 'numeric_entry'],
                'time_limits': {'per_question': 105, 'total': 206}
            },
            'MCAT': {
                'difficulty_levels': [1, 2, 3, 4, 5],
                'topics': ['Biology', 'Chemistry', 'Physics', 'Psychology'],
                'question_types': ['multiple_choice'],
                'time_limits': {'per_question': 95, 'total': 390}
            },
            'USMLE_STEP_1': {
                'difficulty_levels': [1, 2, 3, 4, 5],
                'topics': ['Anatomy', 'Physiology', 'Pathology', 'Pharmacology'],
                'question_types': ['multiple_choice'],
                'time_limits': {'per_question': 90, 'total': 480}
            },
            'NCLEX': {
                'difficulty_levels': [1, 2, 3, 4, 5],
                'topics': ['Safe Practice', 'Health Promotion', 'Psychosocial Integrity'],
                'question_types': ['multiple_choice', 'select_all'],
                'time_limits': {'per_question': 75, 'total': 300}
            }
        }
        
        return standards_map.get(exam_type, {
            'difficulty_levels': [1, 2, 3, 4, 5],
            'topics': ['General Knowledge'],
            'question_types': ['multiple_choice'],
            'time_limits': {'per_question': 90, 'total': 300}
        })
    
    # LAYER 2: AI GENERATION ENGINE
    def generate_questions(self, exam_type: str, difficulty: int, topic_area: str, count: int = 1) -> List[Dict[str, Any]]:
        """Generate questions using OpenAI API"""
        try:
            from openai import OpenAI
            
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                logger.error("OpenAI API key not found")
                return []
            
            client = OpenAI(api_key=api_key)
            standards = self.get_content_standards(exam_type)
            
            # Create generation prompt
            prompt = self._create_generation_prompt(exam_type, difficulty, topic_area, count, standards)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert test question generator. Create high-quality, accurate questions with detailed explanations."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            
            # Parse and validate response
            generated_data = json.loads(response.choices[0].message.content)
            questions = generated_data.get('questions', [])
            
            # Enhance questions with metadata
            enhanced_questions = []
            for question in questions:
                enhanced = {
                    **question,
                    'exam_type': exam_type,
                    'difficulty': difficulty,
                    'topic_area': topic_area,
                    'generated_at': datetime.utcnow().isoformat(),
                    'generation_source': 'strategic_ai_engine'
                }
                enhanced_questions.append(enhanced)
            
            return enhanced_questions
            
        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            return []
    
    def _create_generation_prompt(self, exam_type: str, difficulty: int, topic_area: str, count: int, standards: Dict) -> str:
        """Create detailed prompt for question generation"""
        return f"""
Generate {count} high-quality {exam_type} practice question(s) with the following specifications:

EXAM TYPE: {exam_type}
DIFFICULTY: {difficulty}/5 (where 1=beginner, 5=expert)
TOPIC: {topic_area}
QUESTION FORMAT: Multiple choice with 4 options

REQUIREMENTS:
1. Questions must be authentic and realistic for {exam_type}
2. Difficulty level {difficulty} appropriate for the exam
3. Focus specifically on {topic_area}
4. Include detailed explanations for correct answers
5. Ensure options are plausible and distinct

OUTPUT FORMAT (JSON):
{{
    "questions": [
        {{
            "question_text": "Clear, concise question text",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0,
            "explanation": "Detailed explanation of why the correct answer is right and others are wrong",
            "difficulty": {difficulty},
            "topic_area": "{topic_area}"
        }}
    ]
}}

Generate exactly {count} question(s) following this format.
"""
    
    # LAYER 3: QUALITY VALIDATION
    def validate_question(self, question: Dict[str, Any], exam_type: str) -> Dict[str, Any]:
        """Validate question quality and standards compliance"""
        try:
            issues = []
            quality_score = 10.0
            
            # Check required fields
            required_fields = ['question_text', 'options', 'correct_answer', 'explanation']
            for field in required_fields:
                if field not in question or not question[field]:
                    issues.append(f"Missing required field: {field}")
                    quality_score -= 2.5
            
            # Validate question text
            if 'question_text' in question:
                text = question['question_text']
                if len(text) < 10:
                    issues.append("Question text too short")
                    quality_score -= 1.0
                elif len(text) > 1000:
                    issues.append("Question text too long")
                    quality_score -= 0.5
            
            # Validate options
            if 'options' in question:
                options = question['options']
                if not isinstance(options, list) or len(options) != 4:
                    issues.append("Must have exactly 4 options")
                    quality_score -= 2.0
                else:
                    # Check for empty or duplicate options
                    option_texts = [str(opt).strip() for opt in options]
                    if len(set(option_texts)) != 4:
                        issues.append("Options must be unique")
                        quality_score -= 1.5
                    
                    for i, option in enumerate(option_texts):
                        if not option:
                            issues.append(f"Option {i+1} is empty")
                            quality_score -= 1.0
            
            # Validate correct answer
            if 'correct_answer' in question:
                correct = question['correct_answer']
                if not isinstance(correct, int) or correct not in [0, 1, 2, 3]:
                    issues.append("Correct answer must be 0, 1, 2, or 3")
                    quality_score -= 2.0
            
            # Validate explanation
            if 'explanation' in question:
                explanation = question['explanation']
                if len(explanation) < 20:
                    issues.append("Explanation too brief")
                    quality_score -= 1.0
                elif len(explanation) > 500:
                    issues.append("Explanation too verbose")
                    quality_score -= 0.3
            
            return {
                'is_valid': quality_score >= self.quality_thresholds['minimum_score'],
                'quality_score': max(0, quality_score),
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"Error validating question: {str(e)}")
            return {
                'is_valid': False,
                'quality_score': 0.0,
                'issues': [f"Validation error: {str(e)}"]
            }
    
    # LAYER 4: ADAPTIVE PERSONALIZATION
    def personalize_for_user(self, questions: List[Dict[str, Any]], user_id: int, exam_type: str) -> List[Dict[str, Any]]:
        """Personalize questions based on user ability profile"""
        try:
            from app import app
            from models import UserAbilityProfile, UserProgress
            
            with app.app_context():
                # Get user profile
                profile = UserAbilityProfile.query.filter_by(
                    user_id=user_id, 
                    exam_type=exam_type
                ).first()
                
                if not profile:
                    return questions  # Return as-is if no profile
                
                # Get recent performance
                recent_progress = UserProgress.query.filter_by(
                    user_id=user_id,
                    exam_type=exam_type
                ).order_by(UserProgress.created_at.desc()).limit(10).all()
                
                # Calculate personalization factors
                recent_accuracy = self._calculate_recent_accuracy(recent_progress)
                difficulty_adjustment = self._calculate_difficulty_adjustment(
                    recent_accuracy, profile.learning_velocity
                )
                
                # Personalize each question
                personalized = []
                for question in questions:
                    original_difficulty = question.get('difficulty', 3)
                    adjusted_difficulty = max(1, min(5, original_difficulty + difficulty_adjustment))
                    
                    personalized_question = {
                        **question,
                        'personalized_difficulty': adjusted_difficulty,
                        'user_strength_match': self._calculate_strength_match(question, profile),
                        'recommended_time': self._calculate_recommended_time(question, profile),
                        'personalization_applied': True,
                        'personalization_factors': {
                            'recent_accuracy': recent_accuracy,
                            'difficulty_adjustment': difficulty_adjustment,
                            'learning_velocity': profile.learning_velocity
                        }
                    }
                    
                    personalized.append(personalized_question)
                
                return personalized
                
        except Exception as e:
            logger.error(f"Error personalizing questions: {str(e)}")
            return questions
    
    def _calculate_recent_accuracy(self, progress_records: List) -> float:
        """Calculate recent accuracy from progress records"""
        if not progress_records:
            return 0.5  # Default accuracy
        
        correct = sum(1 for p in progress_records if p.is_correct)
        total = len(progress_records)
        return correct / total if total > 0 else 0.5
    
    def _calculate_difficulty_adjustment(self, accuracy: float, learning_velocity: float) -> int:
        """Calculate difficulty adjustment based on performance"""
        if accuracy > 0.8:
            return 1  # Increase difficulty
        elif accuracy < 0.6:
            return -1  # Decrease difficulty
        else:
            return 0  # Keep same difficulty
    
    def _calculate_strength_match(self, question: Dict, profile) -> float:
        """Calculate how well question matches user strengths"""
        try:
            strength_areas = json.loads(profile.strength_areas or '[]')
            question_topic = question.get('topic_area', '').lower()
            
            for strength in strength_areas:
                if strength.lower() in question_topic:
                    return 0.8
            
            return 0.3  # Low match
        except:
            return 0.5  # Default match
    
    def _calculate_recommended_time(self, question: Dict, profile) -> int:
        """Calculate recommended time for question"""
        base_time = 90  # seconds
        difficulty = question.get('difficulty', 3)
        learning_velocity = profile.learning_velocity
        
        # Adjust based on difficulty and user velocity
        adjusted_time = base_time * (difficulty / 3) * (1 / learning_velocity)
        return max(30, min(300, int(adjusted_time)))
    
    # LAYER 5: CONTINUOUS LEARNING
    def update_learning_model(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update learning model based on performance data"""
        try:
            from app import app, db
            from models import UserAbilityProfile, LearningSession
            
            with app.app_context():
                user_id = performance_data['user_id']
                exam_type = performance_data['exam_type']
                
                # Update or create ability profile
                profile = UserAbilityProfile.query.filter_by(
                    user_id=user_id,
                    exam_type=exam_type
                ).first()
                
                if not profile:
                    profile = UserAbilityProfile(
                        user_id=user_id,
                        exam_type=exam_type,
                        current_difficulty=3,
                        strength_areas='[]',
                        weak_areas='[]',
                        learning_velocity=1.0,
                        accuracy_rate=0.0
                    )
                    db.session.add(profile)
                
                # Calculate new metrics
                questions_answered = performance_data.get('questions_answered', 0)
                correct_answers = performance_data.get('correct_answers', 0)
                accuracy = correct_answers / max(1, questions_answered)
                
                # Update profile
                profile.accuracy_rate = (profile.accuracy_rate * 0.7) + (accuracy * 0.3)
                profile.current_difficulty = self._calculate_new_difficulty(
                    accuracy, profile.current_difficulty
                )
                profile.learning_velocity = self._calculate_learning_velocity(
                    performance_data, profile.learning_velocity
                )
                profile.last_updated = datetime.utcnow()
                
                # Update strength/weakness areas
                if 'topic_performance' in performance_data:
                    self._update_topic_areas(profile, performance_data['topic_performance'])
                
                # Create learning session
                session = LearningSession(
                    user_id=user_id,
                    exam_type=exam_type,
                    questions_answered=questions_answered,
                    correct_answers=correct_answers,
                    total_time_spent=performance_data.get('time_spent', 0),
                    topic_performance=performance_data.get('topic_performance', {}),
                    learning_velocity=profile.learning_velocity
                )
                db.session.add(session)
                db.session.commit()
                
                # Generate recommendations
                recommendations = self._generate_learning_recommendations(profile, performance_data)
                
                return {
                    'updated': True,
                    'recommendations': recommendations,
                    'new_difficulty': profile.current_difficulty,
                    'learning_velocity': profile.learning_velocity,
                    'accuracy_rate': profile.accuracy_rate
                }
                
        except Exception as e:
            logger.error(f"Error updating learning model: {str(e)}")
            return {
                'updated': False,
                'error': str(e),
                'recommendations': []
            }
    
    def _calculate_new_difficulty(self, accuracy: float, current_difficulty: int) -> int:
        """Calculate new difficulty based on accuracy"""
        if accuracy > 0.85:
            return min(5, current_difficulty + 1)
        elif accuracy < 0.65:
            return max(1, current_difficulty - 1)
        else:
            return current_difficulty
    
    def _calculate_learning_velocity(self, performance_data: Dict, current_velocity: float) -> float:
        """Calculate learning velocity adjustment"""
        time_spent = performance_data.get('time_spent', 0)
        questions_answered = performance_data.get('questions_answered', 1)
        
        if time_spent > 0:
            avg_time_per_question = time_spent / questions_answered
            target_time = 90  # seconds per question
            
            if avg_time_per_question < target_time * 0.8:
                return min(2.0, current_velocity * 1.1)  # Faster learner
            elif avg_time_per_question > target_time * 1.5:
                return max(0.5, current_velocity * 0.9)  # Needs more time
        
        return current_velocity
    
    def _update_topic_areas(self, profile, topic_performance: Dict):
        """Update strength and weakness areas"""
        strong_topics = [topic for topic, perf in topic_performance.items() if perf > 0.8]
        weak_topics = [topic for topic, perf in topic_performance.items() if perf < 0.6]
        
        profile.strength_areas = json.dumps(strong_topics)
        profile.weak_areas = json.dumps(weak_topics)
    
    def _generate_learning_recommendations(self, profile, performance_data: Dict) -> List[str]:
        """Generate learning recommendations"""
        recommendations = []
        
        accuracy = profile.accuracy_rate
        weak_areas = json.loads(profile.weak_areas or '[]')
        
        if accuracy < 0.6:
            recommendations.append("Focus on fundamental concepts before advancing")
        elif accuracy > 0.8:
            recommendations.append("Ready for more challenging material")
        
        if weak_areas:
            recommendations.append(f"Extra practice needed in: {', '.join(weak_areas[:3])}")
        
        if profile.learning_velocity < 0.8:
            recommendations.append("Take more time to review each question thoroughly")
        elif profile.learning_velocity > 1.5:
            recommendations.append("Consider tackling more advanced topics")
        
        return recommendations
    
    # ANALYTICS AND REPORTING
    def get_user_analytics(self, user_id: int, exam_type: str) -> Dict[str, Any]:
        """Get comprehensive user analytics"""
        try:
            from app import app
            from models import UserAbilityProfile, LearningSession
            
            with app.app_context():
                profile = UserAbilityProfile.query.filter_by(
                    user_id=user_id,
                    exam_type=exam_type
                ).first()
                
                if not profile:
                    return self._default_analytics()
                
                # Get session data
                recent_sessions = LearningSession.query.filter_by(
                    user_id=user_id,
                    exam_type=exam_type
                ).order_by(LearningSession.created_at.desc()).limit(10).all()
                
                total_questions = sum(s.questions_answered for s in recent_sessions)
                
                return {
                    'current_level': profile.current_difficulty,
                    'accuracy_rate': profile.accuracy_rate,
                    'questions_answered': total_questions,
                    'learning_velocity': profile.learning_velocity,
                    'improvement_areas': json.loads(profile.weak_areas or '[]'),
                    'strength_areas': json.loads(profile.strength_areas or '[]'),
                    'last_updated': profile.last_updated.isoformat() if profile.last_updated else None
                }
                
        except Exception as e:
            logger.error(f"Error getting user analytics: {str(e)}")
            return self._default_analytics()
    
    def _default_analytics(self) -> Dict[str, Any]:
        """Default analytics for new users"""
        return {
            'current_level': 1,
            'accuracy_rate': 0.0,
            'questions_answered': 0,
            'learning_velocity': 1.0,
            'improvement_areas': [],
            'strength_areas': []
        }
    
    def optimize_content_strategy(self) -> Dict[str, Any]:
        """System-wide content optimization"""
        try:
            from app import app
            from models import QuestionMetrics, UserProgress
            
            with app.app_context():
                # Get system metrics
                total_questions = QuestionMetrics.query.count()
                if total_questions < 100:
                    return {
                        'status': 'insufficient_data',
                        'message': 'Need more questions for optimization'
                    }
                
                # Calculate system performance
                avg_accuracy = db.session.query(func.avg(QuestionMetrics.average_accuracy)).scalar() or 0.0
                problem_questions = QuestionMetrics.query.filter(
                    QuestionMetrics.average_accuracy < 0.3
                ).count()
                
                # Generate optimization recommendations
                optimizations = []
                if avg_accuracy < 0.6:
                    optimizations.append("Review question difficulty calibration")
                if problem_questions > total_questions * 0.1:
                    optimizations.append("Identify and improve low-performing questions")
                
                return {
                    'status': 'optimized' if optimizations else 'no_action_needed',
                    'total_questions_served': total_questions,
                    'average_accuracy': avg_accuracy,
                    'problem_questions': problem_questions,
                    'changes': {
                        'optimizations_applied': optimizations,
                        'analysis_timestamp': datetime.utcnow().isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error optimizing content strategy: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }