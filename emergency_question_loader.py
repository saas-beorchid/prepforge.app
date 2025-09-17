#!/usr/bin/env python3
"""
Emergency Question Loader - Immediately populate questions for missing exam types
"""

from app import app, db
from models import CachedQuestion
from strategic_ai_engine import StrategicAIEngine
import logging
import time

def load_questions_for_exam(exam_type, count=10):
    """Load questions immediately for an exam type"""
    with app.app_context():
        # Check if we already have questions
        existing = CachedQuestion.query.filter_by(exam_type=exam_type).count()
        if existing > 0:
            print(f"{exam_type} already has {existing} questions")
            return existing
            
        print(f"Generating {count} questions for {exam_type}...")
        
        engine = StrategicAIEngine()
        
        try:
            questions_data = engine.generate_questions(
                exam_type=exam_type,
                difficulty='medium',
                topic_area='general',
                count=count
            )
            
            if not questions_data:
                print(f"No questions generated for {exam_type}")
                return 0
                
            saved_count = 0
            for i, q_data in enumerate(questions_data):
                try:
                    cached_question = CachedQuestion(
                        question_id=f"{exam_type}_emergency_{int(time.time())}_{i}",
                        exam_type=exam_type,
                        difficulty=3,
                        question_text=q_data['question_text'],
                        option_a=q_data['options'][0] if len(q_data['options']) > 0 else 'A',
                        option_b=q_data['options'][1] if len(q_data['options']) > 1 else 'B', 
                        option_c=q_data['options'][2] if len(q_data['options']) > 2 else 'C',
                        option_d=q_data['options'][3] if len(q_data['options']) > 3 else 'D',
                        correct_answer=str(q_data['correct_answer']),
                        explanation=q_data.get('explanation', 'No explanation available'),
                        topic_area='General',
                        tags='[]'
                    )
                    db.session.add(cached_question)
                    saved_count += 1
                    
                except Exception as e:
                    print(f"Failed to save question {i} for {exam_type}: {e}")
                    continue
            
            db.session.commit()
            print(f"Successfully saved {saved_count}/{count} questions for {exam_type}")
            return saved_count
            
        except Exception as e:
            print(f"Generation failed for {exam_type}: {e}")
            db.session.rollback()
            return 0

def main():
    """Load questions for all missing exam types"""
    missing_exams = ['GRE', 'NCLEX', 'MCAT', 'SAT', 'ACT', 'USMLE_STEP_1', 'USMLE_STEP_2']
    
    print("=== EMERGENCY QUESTION LOADING ===")
    
    total_loaded = 0
    for exam_type in missing_exams:
        count = load_questions_for_exam(exam_type, 10)
        total_loaded += count
        
        # Small delay to prevent API rate limiting
        if count > 0:
            time.sleep(2)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total questions loaded: {total_loaded}")
    
    # Verify final state
    with app.app_context():
        for exam_type in missing_exams:
            count = CachedQuestion.query.filter_by(exam_type=exam_type).count()
            print(f"{exam_type}: {count} questions available")

if __name__ == "__main__":
    main()