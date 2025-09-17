#!/usr/bin/env python3
"""
Asynchronous Question Generator for O'Study Platform
Runs in background to populate question cache without blocking UI
"""

import logging
import time
import threading
from app import app, db
from models import Question, CachedQuestion
from strategic_ai_engine import StrategicAIEngine

class AsyncQuestionGenerator:
    def __init__(self):
        self.engine = StrategicAIEngine()
        self.running_tasks = set()
        
    def start_generation_for_exam(self, exam_type, count=25):
        """Start background generation for specific exam type"""
        if exam_type in self.running_tasks:
            logging.info(f"Generation already running for {exam_type}")
            return
            
        self.running_tasks.add(exam_type)
        thread = threading.Thread(
            target=self._generate_in_background,
            args=(exam_type, count),
            daemon=True
        )
        thread.start()
        logging.info(f"Started background generation thread for {exam_type}")
        
    def _generate_in_background(self, exam_type, count):
        """Background generation with error handling and batching"""
        try:
            with app.app_context():
                logging.info(f"Background generation starting for {exam_type} ({count} questions)")
                
                # Check existing count
                existing = CachedQuestion.query.filter_by(exam_type=exam_type).count()
                if existing >= 50:  # Already have enough
                    logging.info(f"Sufficient questions exist for {exam_type} ({existing})")
                    return
                
                # Generate in small batches
                batch_size = 5
                total_saved = 0
                
                for batch_start in range(0, count, batch_size):
                    batch_count = min(batch_size, count - batch_start)
                    
                    try:
                        questions_data = self.engine.generate_questions(
                            exam_type=exam_type,
                            difficulty='medium', 
                            topic_area='general',
                            count=batch_count
                        )
                        
                        if questions_data:
                            saved_in_batch = self._save_questions_to_db(exam_type, questions_data)
                            total_saved += saved_in_batch
                            logging.info(f"Batch complete for {exam_type}: {saved_in_batch}/{batch_count} saved")
                        else:
                            logging.warning(f"No questions returned for {exam_type} batch")
                            
                        # Prevent API rate limiting
                        time.sleep(2)
                        
                    except Exception as e:
                        logging.error(f"Batch failed for {exam_type}: {e}")
                        continue
                
                logging.info(f"Background generation complete for {exam_type}: {total_saved} questions saved")
                
        except Exception as e:
            logging.error(f"Background generation failed for {exam_type}: {e}")
        finally:
            self.running_tasks.discard(exam_type)
            
    def _save_questions_to_db(self, exam_type, questions_data):
        """Save generated questions to database"""
        saved_count = 0
        
        try:
            for i, q_data in enumerate(questions_data):
                try:
                    # Generate unique ID
                    unique_id = f"{exam_type}_{int(time.time())}_{i}"
                    
                    # Save to main Question table
                    question = Question(
                        id=unique_id,
                        exam_type=exam_type,
                        difficulty=q_data.get('difficulty', 'medium'),
                        question_text=q_data['question_text'],
                        choices=q_data['options'],
                        correct_answer=str(q_data['correct_answer']),
                        explanation=q_data['explanation'],
                        is_generated=True,
                        generation_source='async_generator'
                    )
                    db.session.add(question)
                    db.session.flush()
                    
                    # Save to CachedQuestion table
                    cached_question = CachedQuestion(
                        question_id=question.id,
                        exam_type=exam_type,
                        difficulty=3,  # Medium difficulty
                        question_text=q_data['question_text'],
                        option_a=q_data['options'][0],
                        option_b=q_data['options'][1],
                        option_c=q_data['options'][2],
                        option_d=q_data['options'][3],
                        correct_answer=str(q_data['correct_answer']),
                        explanation=q_data['explanation']
                    )
                    db.session.add(cached_question)
                    saved_count += 1
                    
                except Exception as e:
                    logging.error(f"Failed to save question {i} for {exam_type}: {e}")
                    db.session.rollback()
                    continue
            
            if saved_count > 0:
                db.session.commit()
                
        except Exception as e:
            logging.error(f"Database save failed for {exam_type}: {e}")
            db.session.rollback()
        
        return saved_count

# Global instance
async_generator = AsyncQuestionGenerator()

def start_async_generation(exam_type, count=25):
    """Public interface to start async generation"""
    async_generator.start_generation_for_exam(exam_type, count)