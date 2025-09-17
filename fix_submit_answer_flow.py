#!/usr/bin/env python3
"""
Fix Submit Answer Flow
Ensure cached questions can be used in submit_answer without foreign key violations
"""

import logging
from app import app, db
from models import Question, CachedQuestion, UserProgress
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_cached_to_main_questions():
    """Migrate cached questions to main question table with correct schema"""
    
    with app.app_context():
        logger.info("🔄 Migrating cached questions to main question table...")
        
        try:
            # Get all cached questions
            cached_questions = CachedQuestion.query.all()
            logger.info(f"Found {len(cached_questions)} cached questions to migrate")
            
            migrated_count = 0
            skipped_count = 0
            
            for cached_q in cached_questions:
                # Use the cached question_id or generate one if missing
                question_id = cached_q.question_id or f"cached_{cached_q.exam_type}_{cached_q.id}"
                
                # Check if question already exists in main table
                existing_question = Question.query.filter_by(id=question_id).first()
                
                if not existing_question:
                    # Create new question in main table
                    new_question = Question()
                    new_question.id = question_id  # Use id as primary key
                    new_question.exam_type = cached_q.exam_type
                    new_question.question_text = cached_q.question_text
                    new_question.difficulty = str(cached_q.difficulty) if cached_q.difficulty else "3"
                    
                    # Build choices array from individual options
                    choices = [
                        cached_q.option_a,
                        cached_q.option_b, 
                        cached_q.option_c,
                        cached_q.option_d
                    ]
                    new_question.choices = choices  # Store as JSON array
                    
                    new_question.correct_answer = cached_q.correct_answer
                    new_question.explanation = cached_q.explanation or "Explanation not available"
                    new_question.subject = cached_q.topic_area or "General"
                    new_question.is_generated = True
                    new_question.generation_source = "cached_migration"
                    
                    db.session.add(new_question)
                    migrated_count += 1
                    
                    if migrated_count % 100 == 0:
                        logger.info(f"Migrated {migrated_count} questions...")
                        db.session.commit()
                else:
                    skipped_count += 1
            
            # Final commit
            db.session.commit()
            
            logger.info(f"✅ Question migration completed")
            logger.info(f"📊 Migrated: {migrated_count} questions")
            logger.info(f"📊 Skipped (already exists): {skipped_count} questions")
            
            # Verify the migration
            total_main_questions = Question.query.count()
            total_cached_questions = CachedQuestion.query.count()
            
            logger.info(f"📈 Main question table now has: {total_main_questions} questions")
            logger.info(f"📈 Cached question table has: {total_cached_questions} questions")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate questions: {e}")
            db.session.rollback()
            return False

def update_cached_question_ids():
    """Update cached questions with proper question_id values"""
    
    with app.app_context():
        logger.info("🔄 Updating cached question IDs...")
        
        try:
            # Get cached questions without proper question_id
            cached_questions = CachedQuestion.query.filter(
                (CachedQuestion.question_id == None) | (CachedQuestion.question_id == "")
            ).all()
            
            logger.info(f"Found {len(cached_questions)} cached questions to update")
            
            updated_count = 0
            for cached_q in cached_questions:
                # Generate a proper question_id
                cached_q.question_id = f"cached_{cached_q.exam_type}_{cached_q.id}"
                updated_count += 1
                
                if updated_count % 100 == 0:
                    logger.info(f"Updated {updated_count} question IDs...")
                    db.session.commit()
            
            db.session.commit()
            logger.info(f"✅ Updated {updated_count} cached question IDs")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update question IDs: {e}")
            db.session.rollback()
            return False

def test_submit_answer_flow():
    """Test the submit answer flow with sample data"""
    
    with app.app_context():
        logger.info("🧪 Testing submit answer flow...")
        
        try:
            # Get a sample cached question
            sample_cached = CachedQuestion.query.first()
            if not sample_cached:
                logger.error("No cached questions found for testing")
                return False
            
            logger.info(f"Testing with question: {sample_cached.question_id}")
            
            # Check if corresponding main question exists
            main_question = Question.query.filter_by(id=sample_cached.question_id).first()
            if not main_question:
                logger.error(f"Main question not found for ID: {sample_cached.question_id}")
                return False
            
            logger.info("✅ Submit answer flow should work - main question exists")
            return True
            
        except Exception as e:
            logger.error(f"❌ Submit answer flow test failed: {e}")
            return False

if __name__ == "__main__":
    logger.info("🚀 FIXING SUBMIT ANSWER FLOW")
    logger.info("=" * 50)
    
    # Step 1: Update cached question IDs
    logger.info("Step 1: Updating cached question IDs...")
    if update_cached_question_ids():
        logger.info("✅ Cached question IDs updated")
    else:
        logger.error("❌ Failed to update cached question IDs")
        exit(1)
    
    # Step 2: Migrate cached questions to main table
    logger.info("Step 2: Migrating cached questions to main table...")
    if migrate_cached_to_main_questions():
        logger.info("✅ Questions migrated successfully")
    else:
        logger.error("❌ Failed to migrate questions")
        exit(1)
    
    # Step 3: Test the submit answer flow
    logger.info("Step 3: Testing submit answer flow...")
    if test_submit_answer_flow():
        logger.info("✅ Submit answer flow ready")
    else:
        logger.error("❌ Submit answer flow still has issues")
        exit(1)
    
    logger.info("🎉 SUBMIT ANSWER FLOW FIXED SUCCESSFULLY")