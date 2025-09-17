#!/usr/bin/env python3
"""
Fix Question Database Issues
Ensure all cached questions exist in the main question table to prevent foreign key violations
"""

import logging
from app import app, db
from models import Question, CachedQuestion
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sync_cached_questions_to_main_table():
    """Sync all cached questions to the main question table"""
    
    with app.app_context():
        logger.info("🔄 Starting cached question synchronization...")
        
        try:
            # Get all cached questions
            cached_questions = CachedQuestion.query.all()
            logger.info(f"Found {len(cached_questions)} cached questions")
            
            synced_count = 0
            skipped_count = 0
            
            for cached_q in cached_questions:
                # Check if question already exists in main table
                existing_question = Question.query.filter_by(question_id=cached_q.question_id).first()
                
                if not existing_question:
                    # Create new question in main table
                    new_question = Question()
                    new_question.question_id = cached_q.question_id
                    new_question.exam_type = cached_q.exam_type
                    new_question.question_text = cached_q.question_text
                    new_question.difficulty = cached_q.difficulty
                    
                    # Handle choices - convert to JSON if needed
                    try:
                        if isinstance(cached_q.choices, str):
                            choices = json.loads(cached_q.choices)
                        else:
                            choices = cached_q.choices
                        new_question.choices = json.dumps(choices) if choices else json.dumps(["Option A", "Option B", "Option C", "Option D"])
                    except:
                        new_question.choices = json.dumps(["Option A", "Option B", "Option C", "Option D"])
                    
                    new_question.correct_answer = cached_q.correct_answer
                    new_question.explanation = cached_q.explanation or "Explanation not available"
                    new_question.topic_area = cached_q.topic_area or "General"
                    
                    db.session.add(new_question)
                    synced_count += 1
                    
                    if synced_count % 100 == 0:
                        logger.info(f"Synced {synced_count} questions...")
                        db.session.commit()
                else:
                    skipped_count += 1
            
            # Final commit
            db.session.commit()
            
            logger.info(f"✅ Question synchronization completed")
            logger.info(f"📊 Synced: {synced_count} questions")
            logger.info(f"📊 Skipped (already exists): {skipped_count} questions")
            
            # Verify the sync
            total_main_questions = Question.query.count()
            total_cached_questions = CachedQuestion.query.count()
            
            logger.info(f"📈 Main question table now has: {total_main_questions} questions")
            logger.info(f"📈 Cached question table has: {total_cached_questions} questions")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to sync questions: {e}")
            db.session.rollback()
            return False

def verify_question_integrity():
    """Verify that all cached questions exist in main table"""
    
    with app.app_context():
        logger.info("🔍 Verifying question integrity...")
        
        try:
            # Get sample question IDs from cached table
            sample_cached = CachedQuestion.query.limit(10).all()
            
            missing_count = 0
            for cached_q in sample_cached:
                main_q = Question.query.filter_by(question_id=cached_q.question_id).first()
                if not main_q:
                    missing_count += 1
                    logger.warning(f"Missing question in main table: {cached_q.question_id}")
            
            if missing_count == 0:
                logger.info("✅ All sampled questions exist in main table")
                return True
            else:
                logger.error(f"❌ Found {missing_count} missing questions in main table")
                return False
                
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False

if __name__ == "__main__":
    logger.info("🚀 QUESTION DATABASE SYNCHRONIZATION")
    logger.info("=" * 50)
    
    # First verify current state
    if not verify_question_integrity():
        logger.info("🔧 Starting synchronization...")
        if sync_cached_questions_to_main_table():
            logger.info("🎉 SYNCHRONIZATION SUCCESSFUL")
            verify_question_integrity()
        else:
            logger.error("🚨 SYNCHRONIZATION FAILED")
    else:
        logger.info("✅ Question database is already synchronized")