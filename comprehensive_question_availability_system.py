#!/usr/bin/env python3
"""
COMPREHENSIVE QUESTION AVAILABILITY SYSTEM
==========================================

This system ensures ALL 13 exam types ALWAYS have practice questions available
through a 4-tier approach:

TIER 1: JSON File Loading (Immediate)
TIER 2: Emergency AI Generation (On-demand)
TIER 3: Background Batch Generation (Continuous)
TIER 4: Personalized Adaptive Generation (User-specific)

Author: PrepForge Development Team
Date: July 2025
"""

import json
import os
import logging
import threading
import time
from datetime import datetime, timedelta
from sqlalchemy import and_, func
from app import app, db
from models import Question, CachedQuestion, User, UserProgress
from strategic_ai_engine import StrategicAIEngine
from emergency_question_generator import emergency_generator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveQuestionSystem:
    """
    Ensures 100% question availability across all 13 exam types
    """
    
    # All supported exam types
    ALL_EXAM_TYPES = [
        'GMAT', 'GRE', 'MCAT', 'USMLE_STEP_1', 'USMLE_STEP_2', 
        'NCLEX', 'LSAT', 'IELTS', 'TOEFL', 'PMP', 'CFA', 'ACT', 'SAT'
    ]
    
    # Minimum questions required per exam type
    MIN_QUESTIONS_PER_EXAM = 50
    OPTIMAL_QUESTIONS_PER_EXAM = 200
    
    # Currently missing exam types (will be auto-detected)
    PRIORITY_EXAM_TYPES = [
        'NCLEX', 'GRE', 'MCAT', 'USMLE_STEP_1', 
        'USMLE_STEP_2', 'SAT', 'ACT'
    ]
    
    def __init__(self):
        self.ai_engine = StrategicAIEngine()
        self.generation_threads = {}
        self.json_data_path = './questions_data'
        
    def ensure_all_exams_have_questions(self):
        """
        MASTER METHOD: Ensures all 13 exam types have questions
        This is called on app startup and periodically
        """
        logger.info("🎯 COMPREHENSIVE QUESTION AVAILABILITY CHECK STARTED")
        
        with app.app_context():
            for exam_type in self.ALL_EXAM_TYPES:
                try:
                    self._ensure_exam_has_minimum_questions(exam_type)
                except Exception as e:
                    logger.error(f"Failed to ensure questions for {exam_type}: {e}")
                    
        logger.info("✅ COMPREHENSIVE QUESTION AVAILABILITY CHECK COMPLETED")
    
    def _ensure_exam_has_minimum_questions(self, exam_type):
        """
        Ensures a specific exam type has minimum questions through 4-tier approach
        """
        logger.info(f"🔍 Checking question availability for {exam_type}")
        
        # Check current question count
        current_count = self._get_available_question_count(exam_type)
        logger.info(f"📊 {exam_type}: {current_count} questions available")
        
        if current_count >= self.MIN_QUESTIONS_PER_EXAM:
            logger.info(f"✅ {exam_type}: Sufficient questions ({current_count})")
            
            # If below optimal, start background generation
            if current_count < self.OPTIMAL_QUESTIONS_PER_EXAM:
                self._start_background_generation(exam_type)
                
            return current_count
            
        # TIER 1: Load from JSON files first
        loaded_from_json = self._load_from_json_files(exam_type)
        current_count += loaded_from_json
        
        if current_count >= self.MIN_QUESTIONS_PER_EXAM:
            logger.info(f"✅ {exam_type}: JSON loading successful ({current_count} total)")
            return current_count
            
        # TIER 2: Emergency AI Generation
        logger.warning(f"⚡ {exam_type}: Emergency AI generation required")
        needed = self.MIN_QUESTIONS_PER_EXAM - current_count
        generated = self._emergency_ai_generation(exam_type, needed)
        current_count += generated
        
        if current_count >= self.MIN_QUESTIONS_PER_EXAM:
            logger.info(f"✅ {exam_type}: Emergency generation successful ({current_count} total)")
        else:
            logger.error(f"❌ {exam_type}: Still insufficient questions ({current_count})")
            
        # TIER 3: Always start background generation for continuous supply
        self._start_background_generation(exam_type)
        
        return current_count
    
    def _get_available_question_count(self, exam_type):
        """Get total available questions for exam type (cached + database)"""
        try:
            # Count from CachedQuestion (faster access)
            cached_count = CachedQuestion.query.filter_by(exam_type=exam_type).count()
            
            # Count from main Question table
            db_count = Question.query.filter_by(exam_type=exam_type).count()
            
            # Return the maximum (questions might be in both tables)
            return max(cached_count, db_count)
            
        except Exception as e:
            logger.error(f"Error counting questions for {exam_type}: {e}")
            return 0
    
    def _load_from_json_files(self, exam_type):
        """
        TIER 1: Load questions from JSON files in questions_data/
        """
        logger.info(f"📁 TIER 1: Loading {exam_type} from JSON files")
        
        # Map exam types to JSON file names
        json_filename_map = {
            'GRE': 'GRE_Questions.json',
            'GMAT': 'GMAT_Questions.json', 
            'MCAT': 'MCAT_Questions.json',
            'USMLE_STEP_1': 'USMLE_STEP_1_Questions.json',
            'USMLE_STEP_2': 'USMLE_STEP_2_Questions.json',
            'NCLEX': 'NCLEX_Questions.json',
            'LSAT': 'LSAT_Questions.json',
            'IELTS': 'IELTS_Questions.json',
            'TOEFL': 'TOEFL_Questions(Reading).json',
            'PMP': 'PMP_Questions.json',
            'CFA': 'CFA_Questions.json',
            'ACT': 'ACT_Questions.json',
            'SAT': 'SAT_Questions.json'
        }
        
        json_file = json_filename_map.get(exam_type)
        if not json_file:
            logger.warning(f"No JSON mapping found for {exam_type}")
            return 0
            
        json_path = os.path.join(self.json_data_path, json_file)
        
        if not os.path.exists(json_path):
            logger.warning(f"JSON file not found: {json_path}")
            return 0
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
                
            if not questions_data:
                logger.warning(f"Empty JSON file: {json_path}")
                return 0
                
            loaded_count = 0
            
            for i, q_data in enumerate(questions_data):
                try:
                    # Check if this question already exists
                    question_id = f"{exam_type}_json_{i}"
                    if CachedQuestion.query.filter_by(question_id=question_id).first():
                        continue
                        
                    # Create CachedQuestion for immediate availability
                    cached_question = CachedQuestion(
                        question_id=question_id,
                        exam_type=exam_type,
                        difficulty=3,  # Default medium
                        question_text=q_data.get('question_text', q_data.get('question', '')),
                        option_a=self._get_option(q_data, 0),
                        option_b=self._get_option(q_data, 1),
                        option_c=self._get_option(q_data, 2),
                        option_d=self._get_option(q_data, 3),
                        correct_answer=str(q_data.get('correct_answer', 'A')),
                        explanation=q_data.get('explanation', 'No explanation available'),
                        topic_area=q_data.get('topic_area', 'General'),
                        tags='["json_loaded"]'
                    )
                    
                    db.session.add(cached_question)
                    loaded_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to load question {i} from {json_file}: {e}")
                    continue
                    
            db.session.commit()
            logger.info(f"✅ Loaded {loaded_count} questions from {json_file}")
            return loaded_count
            
        except Exception as e:
            logger.error(f"Failed to load JSON file {json_path}: {e}")
            db.session.rollback()
            return 0
    
    def _get_option(self, q_data, index):
        """Extract option from question data safely"""
        options = q_data.get('options', q_data.get('choices', []))
        if isinstance(options, list) and len(options) > index:
            return str(options[index])
        return f"Option {chr(65 + index)}"  # A, B, C, D
    
    def _emergency_ai_generation(self, exam_type, count):
        """
        TIER 2: Emergency AI generation for immediate needs
        """
        logger.info(f"⚡ TIER 2: Emergency AI generation for {exam_type} ({count} questions)")
        
        try:
            questions_data = self.ai_engine.generate_questions(
                exam_type=exam_type,
                difficulty='medium',
                topic_area='general',
                count=min(count, 25)  # Limit to prevent API overload
            )
            
            if not questions_data:
                logger.error(f"AI generation returned no questions for {exam_type}")
                return 0
                
            saved_count = 0
            
            for i, q_data in enumerate(questions_data):
                try:
                    question_id = f"{exam_type}_emergency_{int(time.time())}_{i}"
                    
                    cached_question = CachedQuestion(
                        question_id=question_id,
                        exam_type=exam_type,
                        difficulty=3,
                        question_text=q_data['question_text'],
                        option_a=q_data['options'][0] if len(q_data['options']) > 0 else 'A',
                        option_b=q_data['options'][1] if len(q_data['options']) > 1 else 'B',
                        option_c=q_data['options'][2] if len(q_data['options']) > 2 else 'C',
                        option_d=q_data['options'][3] if len(q_data['options']) > 3 else 'D',
                        correct_answer=str(q_data['correct_answer']),
                        explanation=q_data.get('explanation', 'AI-generated explanation'),
                        topic_area='General',
                        tags='["emergency_generated"]'
                    )
                    
                    db.session.add(cached_question)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to save emergency question {i} for {exam_type}: {e}")
                    continue
                    
            db.session.commit()
            logger.info(f"✅ Emergency generation: {saved_count}/{count} questions saved for {exam_type}")
            return saved_count
            
        except Exception as e:
            logger.error(f"Emergency generation failed for {exam_type}: {e}")
            db.session.rollback()
            return 0
    
    def _start_background_generation(self, exam_type):
        """
        TIER 3: Start continuous background generation
        """
        if exam_type in self.generation_threads:
            logger.info(f"Background generation already running for {exam_type}")
            return
            
        logger.info(f"🔄 TIER 3: Starting background generation for {exam_type}")
        
        thread = threading.Thread(
            target=self._background_generation_worker,
            args=(exam_type,),
            daemon=True,
            name=f"BackgroundGen-{exam_type}"
        )
        
        self.generation_threads[exam_type] = thread
        thread.start()
    
    def _background_generation_worker(self, exam_type):
        """
        Continuous background worker for question generation
        """
        logger.info(f"🔄 Background generation worker started for {exam_type}")
        
        while True:
            try:
                with app.app_context():
                    current_count = self._get_available_question_count(exam_type)
                    
                    if current_count < self.OPTIMAL_QUESTIONS_PER_EXAM:
                        needed = min(25, self.OPTIMAL_QUESTIONS_PER_EXAM - current_count)
                        
                        logger.info(f"🔄 Background generating {needed} questions for {exam_type}")
                        
                        questions_data = self.ai_engine.generate_questions(
                            exam_type=exam_type,
                            difficulty='medium',
                            topic_area='general',
                            count=needed
                        )
                        
                        if questions_data:
                            saved_count = 0
                            for i, q_data in enumerate(questions_data):
                                try:
                                    question_id = f"{exam_type}_bg_{int(time.time())}_{i}"
                                    
                                    cached_question = CachedQuestion(
                                        question_id=question_id,
                                        exam_type=exam_type,
                                        difficulty=3,
                                        question_text=q_data['question_text'],
                                        option_a=q_data['options'][0] if len(q_data['options']) > 0 else 'A',
                                        option_b=q_data['options'][1] if len(q_data['options']) > 1 else 'B',
                                        option_c=q_data['options'][2] if len(q_data['options']) > 2 else 'C',
                                        option_d=q_data['options'][3] if len(q_data['options']) > 3 else 'D',
                                        correct_answer=str(q_data['correct_answer']),
                                        explanation=q_data.get('explanation', 'Background-generated explanation'),
                                        topic_area='General',
                                        tags='["background_generated"]'
                                    )
                                    
                                    db.session.add(cached_question)
                                    saved_count += 1
                                    
                                except Exception as e:
                                    logger.error(f"Failed to save background question {i}: {e}")
                                    continue
                                    
                            db.session.commit()
                            logger.info(f"🔄 Background generation: {saved_count} questions saved for {exam_type}")
                        
                        # Wait before next generation cycle
                        time.sleep(300)  # 5 minutes
                    else:
                        logger.info(f"✅ {exam_type} has optimal questions ({current_count}), sleeping...")
                        time.sleep(1800)  # 30 minutes
                        
            except Exception as e:
                logger.error(f"Background generation error for {exam_type}: {e}")
                time.sleep(60)  # Wait 1 minute before retry
    
    def generate_personalized_questions(self, user_id, exam_type, count=10):
        """
        TIER 4: Personalized question generation based on user performance
        """
        logger.info(f"🎯 TIER 4: Generating personalized questions for user {user_id}, {exam_type}")
        
        with app.app_context():
            try:
                # Analyze user performance
                user_progress = UserProgress.query.filter_by(
                    user_id=user_id,
                    exam_type=exam_type
                ).order_by(UserProgress.answered_at.desc()).limit(20).all()
                
                # Determine weak areas and difficulty adjustment
                weak_topics = self._analyze_weak_areas(user_progress)
                suggested_difficulty = self._calculate_user_difficulty(user_progress)
                
                logger.info(f"User {user_id} weak topics: {weak_topics}, difficulty: {suggested_difficulty}")
                
                # Generate personalized questions
                questions_data = self.ai_engine.generate_questions(
                    exam_type=exam_type,
                    difficulty=suggested_difficulty,
                    topic_area=weak_topics[0] if weak_topics else 'general',
                    count=count,
                    personalization_context={
                        'user_id': user_id,
                        'weak_areas': weak_topics,
                        'recent_accuracy': self._get_recent_accuracy(user_progress)
                    }
                )
                
                if questions_data:
                    saved_count = 0
                    for i, q_data in enumerate(questions_data):
                        try:
                            question_id = f"{exam_type}_personal_{user_id}_{int(time.time())}_{i}"
                            
                            cached_question = CachedQuestion(
                                question_id=question_id,
                                exam_type=exam_type,
                                difficulty=self._difficulty_to_int(suggested_difficulty),
                                question_text=q_data['question_text'],
                                option_a=q_data['options'][0] if len(q_data['options']) > 0 else 'A',
                                option_b=q_data['options'][1] if len(q_data['options']) > 1 else 'B',
                                option_c=q_data['options'][2] if len(q_data['options']) > 2 else 'C',
                                option_d=q_data['options'][3] if len(q_data['options']) > 3 else 'D',
                                correct_answer=str(q_data['correct_answer']),
                                explanation=q_data.get('explanation', 'Personalized explanation'),
                                topic_area=weak_topics[0] if weak_topics else 'General',
                                tags=f'["personalized", "user_{user_id}"]'
                            )
                            
                            db.session.add(cached_question)
                            saved_count += 1
                            
                        except Exception as e:
                            logger.error(f"Failed to save personalized question {i}: {e}")
                            continue
                            
                    db.session.commit()
                    logger.info(f"🎯 Generated {saved_count} personalized questions for user {user_id}")
                    return saved_count
                    
            except Exception as e:
                logger.error(f"Personalized generation failed for user {user_id}: {e}")
                db.session.rollback()
                return 0
                
        return 0
    
    def _analyze_weak_areas(self, user_progress):
        """Analyze user progress to identify weak topic areas"""
        if not user_progress:
            return ['general']
            
        # Simple analysis - can be enhanced
        topic_performance = {}
        for progress in user_progress:
            topic = getattr(progress, 'topic_area', 'general')
            if topic not in topic_performance:
                topic_performance[topic] = {'correct': 0, 'total': 0}
            
            topic_performance[topic]['total'] += 1
            if progress.is_correct:
                topic_performance[topic]['correct'] += 1
        
        # Return topics with lowest accuracy
        weak_topics = []
        for topic, stats in topic_performance.items():
            if stats['total'] > 0:
                accuracy = stats['correct'] / stats['total']
                if accuracy < 0.6:  # Less than 60% accuracy
                    weak_topics.append(topic)
        
        return weak_topics if weak_topics else ['general']
    
    def _calculate_user_difficulty(self, user_progress):
        """Calculate appropriate difficulty for user"""
        if not user_progress:
            return 'medium'
            
        # Calculate recent accuracy
        recent_correct = sum(1 for p in user_progress[-10:] if p.is_correct)
        recent_total = len(user_progress[-10:])
        
        if recent_total == 0:
            return 'medium'
            
        accuracy = recent_correct / recent_total
        
        if accuracy >= 0.8:
            return 'hard'
        elif accuracy >= 0.6:
            return 'medium'
        else:
            return 'easy'
    
    def _get_recent_accuracy(self, user_progress):
        """Get user's recent accuracy percentage"""
        if not user_progress:
            return 0.0
            
        recent_correct = sum(1 for p in user_progress[-10:] if p.is_correct)
        return recent_correct / min(len(user_progress), 10)
    
    def _difficulty_to_int(self, difficulty):
        """Convert difficulty string to integer"""
        mapping = {'easy': 1, 'medium': 3, 'hard': 5}
        return mapping.get(difficulty, 3)
    
    def get_system_status(self):
        """Get comprehensive status of question availability system"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'exam_types': {},
            'total_questions': 0,
            'system_health': 'healthy'
        }
        
        with app.app_context():
            for exam_type in self.ALL_EXAM_TYPES:
                count = self._get_available_question_count(exam_type)
                status['exam_types'][exam_type] = {
                    'available_questions': count,
                    'status': 'healthy' if count >= self.MIN_QUESTIONS_PER_EXAM else 'critical',
                    'background_generation': exam_type in self.generation_threads
                }
                status['total_questions'] += count
        
        # Determine overall system health
        critical_exams = [
            exam for exam, data in status['exam_types'].items() 
            if data['status'] == 'critical'
        ]
        
        if critical_exams:
            status['system_health'] = 'critical'
            status['critical_exam_types'] = critical_exams
        
        return status


# Global instance
question_system = ComprehensiveQuestionSystem()

def initialize_comprehensive_system():
    """Initialize the comprehensive question system on app startup"""
    logger.info("🚀 INITIALIZING COMPREHENSIVE QUESTION AVAILABILITY SYSTEM")
    
    # Start the main availability check
    thread = threading.Thread(
        target=question_system.ensure_all_exams_have_questions,
        daemon=True,
        name="ComprehensiveQuestionSystem"
    )
    thread.start()
    
    logger.info("✅ COMPREHENSIVE QUESTION AVAILABILITY SYSTEM INITIALIZED")

def get_questions_for_practice(exam_type, user_id=None, count=1):
    """
    Get questions for practice with guaranteed availability
    This replaces the old question selection logic
    """
    with app.app_context():
        # Ensure this exam type has questions
        available_count = question_system._get_available_question_count(exam_type)
        
        if available_count < question_system.MIN_QUESTIONS_PER_EXAM:
            logger.warning(f"Insufficient questions for {exam_type}, triggering emergency generation")
            question_system._ensure_exam_has_minimum_questions(exam_type)
        
        # Get questions from cache (prioritizing personalized if available)
        query = CachedQuestion.query.filter_by(exam_type=exam_type)
        
        if user_id:
            # Try to get personalized questions first
            personalized = query.filter(
                CachedQuestion.tags.contains(f'"user_{user_id}"')
            ).limit(count).all()
            
            if len(personalized) >= count:
                return personalized
                
            # Generate more personalized questions if needed
            if len(personalized) < count:
                question_system.generate_personalized_questions(
                    user_id, exam_type, count - len(personalized)
                )
        
        # Get regular questions
        questions = query.order_by(func.random()).limit(count).all()
        
        if not questions:
            # Emergency fallback
            logger.error(f"No questions available for {exam_type} despite system checks!")
            question_system._emergency_ai_generation(exam_type, count)
            questions = query.limit(count).all()
        
        return questions


if __name__ == "__main__":
    # For testing the system
    with app.app_context():
        system = ComprehensiveQuestionSystem()
        status = system.get_system_status()
        print(json.dumps(status, indent=2))