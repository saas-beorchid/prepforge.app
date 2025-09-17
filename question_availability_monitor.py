#!/usr/bin/env python3
"""
QUESTION AVAILABILITY MONITOR
============================

Real-time monitoring and maintenance system for question availability.
Ensures all 13 exam types always have practice questions available.
"""

import logging
import threading
import time
from datetime import datetime
from flask import Blueprint
from app import app, db
from models import CachedQuestion
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

monitor_bp = Blueprint('monitor', __name__)

class QuestionAvailabilityMonitor:
    """Real-time monitor for question availability across all exam types"""
    
    ALL_EXAM_TYPES = [
        'GMAT', 'GRE', 'MCAT', 'USMLE_STEP_1', 'USMLE_STEP_2', 
        'NCLEX', 'LSAT', 'IELTS', 'TOEFL', 'PMP', 'CFA', 'ACT', 'SAT'
    ]
    
    MIN_QUESTIONS_THRESHOLD = 10  # Minimum questions required per exam
    LOW_QUESTIONS_THRESHOLD = 25  # Trigger more generation
    
    def __init__(self):
        self.monitoring = True
        self.monitor_thread = None
        self.last_check = None
        self.status = {}
        
    def start_monitoring(self):
        """Start the continuous monitoring system"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.info("Monitor already running")
            return
            
        logger.info("🔍 Starting Question Availability Monitor")
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="QuestionAvailabilityMonitor"
        )
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop the monitoring system"""
        logger.info("⏹️ Stopping Question Availability Monitor")
        self.monitoring = False
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("🔄 Question Availability Monitor started")
        
        while self.monitoring:
            try:
                with app.app_context():
                    self._check_all_exam_types()
                    self.last_check = datetime.now()
                    
                # Check every 5 minutes
                time.sleep(300)
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(60)  # Wait 1 minute before retry
                
        logger.info("🔄 Question Availability Monitor stopped")
    
    def _check_all_exam_types(self):
        """Check question availability for all exam types"""
        critical_exams = []
        low_exams = []
        
        for exam_type in self.ALL_EXAM_TYPES:
            count = self._get_question_count(exam_type)
            
            self.status[exam_type] = {
                'count': count,
                'status': 'healthy' if count >= self.MIN_QUESTIONS_THRESHOLD else 'critical',
                'last_checked': datetime.now().isoformat()
            }
            
            if count < self.MIN_QUESTIONS_THRESHOLD:
                critical_exams.append(exam_type)
                logger.error(f"🚨 CRITICAL: {exam_type} has only {count} questions")
                self._trigger_emergency_generation(exam_type)
                
            elif count < self.LOW_QUESTIONS_THRESHOLD:
                low_exams.append(exam_type)
                logger.warning(f"⚠️ LOW: {exam_type} has {count} questions")
                self._trigger_background_generation(exam_type)
        
        if critical_exams:
            logger.error(f"🚨 CRITICAL EXAM TYPES: {critical_exams}")
        
        if low_exams:
            logger.warning(f"⚠️ LOW QUESTION EXAM TYPES: {low_exams}")
            
        if not critical_exams and not low_exams:
            logger.info("✅ All exam types have sufficient questions")
    
    def _get_question_count(self, exam_type):
        """Get current question count for exam type"""
        try:
            return CachedQuestion.query.filter_by(exam_type=exam_type).count()
        except Exception as e:
            logger.error(f"Error counting questions for {exam_type}: {e}")
            return 0
    
    def _trigger_emergency_generation(self, exam_type):
        """Trigger emergency question generation for critical exam types"""
        logger.info(f"⚡ Triggering emergency generation for {exam_type}")
        
        # Try to load from JSON first (fastest)
        try:
            from instant_question_loader import load_exam_questions
            loaded = load_exam_questions(exam_type)
            if loaded > 0:
                logger.info(f"✅ Emergency JSON loading successful for {exam_type}: {loaded} questions")
                return
        except Exception as e:
            logger.error(f"Emergency JSON loading failed for {exam_type}: {e}")
        
        # Fallback to AI generation
        try:
            self._ai_emergency_generation(exam_type)
        except Exception as e:
            logger.error(f"Emergency AI generation failed for {exam_type}: {e}")
    
    def _ai_emergency_generation(self, exam_type):
        """Emergency AI generation when JSON loading fails"""
        try:
            from strategic_ai_engine import StrategicAIEngine
            
            logger.info(f"🤖 Emergency AI generation for {exam_type}")
            
            engine = StrategicAIEngine()
            questions_data = engine.generate_questions(
                exam_type=exam_type,
                difficulty=3,
                topic_area='general',
                count=15  # Generate 15 questions for immediate use
            )
            
            if questions_data:
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
                            explanation=q_data.get('explanation', 'Emergency generated explanation'),
                            topic_area='General',
                            tags='["emergency_ai"]'
                        )
                        
                        db.session.add(cached_question)
                        saved_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to save emergency question {i}: {e}")
                        continue
                
                db.session.commit()
                logger.info(f"✅ Emergency AI generation complete for {exam_type}: {saved_count} questions")
                
        except Exception as e:
            logger.error(f"Emergency AI generation failed for {exam_type}: {e}")
            db.session.rollback()
    
    def _trigger_background_generation(self, exam_type):
        """Trigger background generation for low-question exam types"""
        logger.info(f"🔄 Triggering background generation for {exam_type}")
        
        # Start background generation in separate thread
        thread = threading.Thread(
            target=self._background_generation_worker,
            args=(exam_type,),
            daemon=True,
            name=f"BackgroundGen-{exam_type}"
        )
        thread.start()
    
    def _background_generation_worker(self, exam_type):
        """Background worker for generating more questions"""
        try:
            with app.app_context():
                from strategic_ai_engine import StrategicAIEngine
                
                engine = StrategicAIEngine()
                questions_data = engine.generate_questions(
                    exam_type=exam_type,
                    difficulty=3,
                    topic_area='general',
                    count=25
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
                                explanation=q_data.get('explanation', 'Background generated explanation'),
                                topic_area='General',
                                tags='["background_generated"]'
                            )
                            
                            db.session.add(cached_question)
                            saved_count += 1
                            
                        except Exception as e:
                            logger.error(f"Failed to save background question {i}: {e}")
                            continue
                    
                    db.session.commit()
                    logger.info(f"🔄 Background generation complete for {exam_type}: {saved_count} questions")
                    
        except Exception as e:
            logger.error(f"Background generation failed for {exam_type}: {e}")
            db.session.rollback()
    
    def get_status(self):
        """Get current status of all exam types"""
        with app.app_context():
            current_status = {}
            
            for exam_type in self.ALL_EXAM_TYPES:
                count = self._get_question_count(exam_type)
                current_status[exam_type] = {
                    'count': count,
                    'status': 'healthy' if count >= self.MIN_QUESTIONS_THRESHOLD else 'critical',
                    'level': 'high' if count >= self.LOW_QUESTIONS_THRESHOLD else 'low' if count >= self.MIN_QUESTIONS_THRESHOLD else 'critical'
                }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'exam_types': current_status,
                'total_questions': sum(data['count'] for data in current_status.values()),
                'healthy_exams': sum(1 for data in current_status.values() if data['status'] == 'healthy'),
                'critical_exams': [exam for exam, data in current_status.items() if data['status'] == 'critical'],
                'monitoring_active': self.monitoring,
                'last_check': self.last_check.isoformat() if self.last_check else None
            }

# Global monitor instance
question_monitor = QuestionAvailabilityMonitor()

@monitor_bp.route('/admin/question-status')
def question_status():
    """API endpoint to get question availability status"""
    status = question_monitor.get_status()
    return json.dumps(status, indent=2)

def initialize_monitor():
    """Initialize the question availability monitor"""
    logger.info("🚀 Initializing Question Availability Monitor")
    question_monitor.start_monitoring()
    logger.info("✅ Question Availability Monitor initialized")

def ensure_immediate_availability():
    """Ensure all exam types have questions available right now"""
    logger.info("🎯 ENSURING IMMEDIATE QUESTION AVAILABILITY")
    
    missing_exams = []
    
    with app.app_context():
        for exam_type in question_monitor.ALL_EXAM_TYPES:
            count = question_monitor._get_question_count(exam_type)
            
            if count < question_monitor.MIN_QUESTIONS_THRESHOLD:
                logger.warning(f"⚠️ {exam_type} needs immediate attention ({count} questions)")
                missing_exams.append(exam_type)
                question_monitor._trigger_emergency_generation(exam_type)
    
    if missing_exams:
        logger.info(f"🔄 Triggered emergency generation for: {missing_exams}")
    else:
        logger.info("✅ All exam types have sufficient questions")
    
    return len(missing_exams) == 0

if __name__ == "__main__":
    # For testing
    with app.app_context():
        # Run immediate availability check
        all_good = ensure_immediate_availability()
        
        # Get and display status
        status = question_monitor.get_status()
        print(json.dumps(status, indent=2))
        
        # Start monitoring
        initialize_monitor()
        
        # Keep running for testing
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            question_monitor.stop_monitoring()