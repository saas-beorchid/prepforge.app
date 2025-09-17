#!/usr/bin/env python3
"""
Bulk Question Generator for O'Study Platform
Generates 25 questions for each exam type and caches them for immediate use
"""

import logging
import time
from app import app, db
from models import Question, CachedQuestion
from strategic_ai_engine import StrategicAIEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BulkQuestionGenerator:
    def __init__(self):
        self.engine = StrategicAIEngine()
        self.target_exam_types = [
            'GRE', 'NCLEX', 'MCAT', 'SAT', 'ACT', 
            'USMLE_STEP_1', 'USMLE_STEP_2'
        ]
        
    def generate_and_cache_questions(self, exam_type, count=25):
        """Generate questions and save them to both Question and CachedQuestion tables"""
        logger.info(f"Generating {count} questions for {exam_type}")
        
        try:
            # Generate questions using Strategic AI Engine
            questions_data = self.engine.generate_questions(
                exam_type=exam_type,
                difficulty='medium',
                topic_area='general',
                count=count
            )
            
            if not questions_data:
                logger.error(f"No questions generated for {exam_type}")
                return False
                
            saved_count = 0
            
            for q_data in questions_data:
                try:
                    # Save to main Question table (using correct field names from models.py)
                    question = Question(
                        id=f"{exam_type}_{int(time.time())}_{saved_count}",  # Generate unique ID
                        exam_type=exam_type,
                        difficulty=q_data.get('difficulty', 'medium'),
                        question_text=q_data['question_text'],
                        choices=q_data['options'],  # Using 'choices' not 'options'
                        correct_answer=str(q_data['correct_answer']),  # Convert to string
                        explanation=q_data['explanation'],
                        is_generated=True,
                        generation_source='strategic_ai_engine'
                    )
                    db.session.add(question)
                    db.session.flush()  # Get the ID
                    
                    # Save to CachedQuestion table for faster access (using correct field names)
                    cached_question = CachedQuestion(
                        question_id=question.id,
                        exam_type=exam_type,
                        difficulty=3,  # Default medium difficulty
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
                    logger.error(f"Failed to save question for {exam_type}: {e}")
                    db.session.rollback()
                    continue
            
            db.session.commit()
            logger.info(f"Successfully saved {saved_count}/{count} questions for {exam_type}")
            return saved_count > 0
            
        except Exception as e:
            logger.error(f"Bulk generation failed for {exam_type}: {e}")
            db.session.rollback()
            return False
    
    def run_bulk_generation(self):
        """Generate questions for all target exam types"""
        logger.info("Starting bulk question generation for all exam types")
        
        results = {}
        total_start_time = time.time()
        
        for exam_type in self.target_exam_types:
            start_time = time.time()
            success = self.generate_and_cache_questions(exam_type, 25)
            end_time = time.time()
            
            results[exam_type] = {
                'success': success,
                'duration': end_time - start_time
            }
            
            logger.info(f"Completed {exam_type} in {end_time - start_time:.2f}s")
            
            # Small delay to prevent API rate limiting
            time.sleep(2)
        
        total_end_time = time.time()
        
        # Summary report
        logger.info("=== BULK GENERATION SUMMARY ===")
        successful = sum(1 for r in results.values() if r['success'])
        total_duration = total_end_time - total_start_time
        
        logger.info(f"Successfully generated questions for {successful}/{len(self.target_exam_types)} exam types")
        logger.info(f"Total duration: {total_duration:.2f} seconds")
        
        for exam_type, result in results.items():
            status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
            logger.info(f"{exam_type}: {status} ({result['duration']:.2f}s)")
        
        return results

def main():
    """Main function to run bulk question generation"""
    with app.app_context():
        generator = BulkQuestionGenerator()
        results = generator.run_bulk_generation()
        return results

if __name__ == "__main__":
    main()