#!/usr/bin/env python3
"""
Database Migration Script for Strategic AI Framework
Updates database schema to support the 5-layer strategic framework
"""

import logging
from app import app, db
from models import (
    User, Question, CachedQuestion, ExamConfig, QuestionMetrics, 
    UserAbilityProfile, GenerationRequest, QuestionGenerationTemplate,
    ContentOptimization
)

logger = logging.getLogger(__name__)

def run_migration():
    """Run database migration to update schema"""
    with app.app_context():
        try:
            logger.info("Starting database migration for Strategic AI Framework...")
            

            # Add new columns to existing tables
            logger.info("Adding new columns to existing tables...")
            alter_statements = [
                ("exam_config", '''
                    ALTER TABLE exam_config 
                    ADD COLUMN IF NOT EXISTS difficulty_levels TEXT DEFAULT '[1,2,3,4,5]',
                    ADD COLUMN IF NOT EXISTS topic_areas TEXT DEFAULT '[]',
                    ADD COLUMN IF NOT EXISTS question_formats TEXT DEFAULT '["multiple_choice"]',
                    ADD COLUMN IF NOT EXISTS time_limits INTEGER DEFAULT 120,
                    ADD COLUMN IF NOT EXISTS passing_score INTEGER DEFAULT 70,
                    ADD COLUMN IF NOT EXISTS content_weight TEXT DEFAULT '{}';
                '''),
                ("user_ability_profile", '''
                    ALTER TABLE user_ability_profile 
                    ADD COLUMN IF NOT EXISTS current_difficulty FLOAT DEFAULT 3.0,
                    ADD COLUMN IF NOT EXISTS strength_areas TEXT DEFAULT '[]',
                    ADD COLUMN IF NOT EXISTS weak_areas TEXT DEFAULT '[]',
                    ADD COLUMN IF NOT EXISTS question_count INTEGER DEFAULT 0,
                    ADD COLUMN IF NOT EXISTS accuracy_rate FLOAT DEFAULT 0.0;
                '''),
                ("question_metrics", '''
                    ALTER TABLE question_metrics 
                    ADD COLUMN IF NOT EXISTS exam_type VARCHAR(50),
                    ADD COLUMN IF NOT EXISTS difficulty_level INTEGER DEFAULT 3,
                    ADD COLUMN IF NOT EXISTS topic_area VARCHAR(100) DEFAULT 'General',
                    ADD COLUMN IF NOT EXISTS total_attempts INTEGER DEFAULT 0,
                    ADD COLUMN IF NOT EXISTS correct_attempts INTEGER DEFAULT 0,
                    ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                '''),
                ("generation_request", '''
                    ALTER TABLE generation_request 
                    ADD COLUMN IF NOT EXISTS questions_requested INTEGER DEFAULT 1,
                    ADD COLUMN IF NOT EXISTS questions_generated INTEGER DEFAULT 0,
                    ADD COLUMN IF NOT EXISTS request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ADD COLUMN IF NOT EXISTS completion_time TIMESTAMP;
                ''')
            ]
            with db.engine.begin() as connection:
                for table, stmt in alter_statements:
                    try:
                        connection.execute(db.text(stmt))
                    except Exception as e:
                        logger.warning(f"Could not alter table {table}: {e}")

            # Migrate existing data
            logger.info("Migrating existing cached question data...")

            with db.engine.connect() as connection:
                existing_cached = connection.execute(db.text("""
                    SELECT id, choices FROM cached_question 
                    WHERE option_a IS NULL AND choices IS NOT NULL
                """)).fetchall()

                for record in existing_cached:
                    try:
                        choices = record[1] if isinstance(record[1], dict) else {}
                        if choices:
                            connection.execute(db.text("""
                                UPDATE cached_question 
                                SET option_a = :a, option_b = :b, option_c = :c, option_d = :d
                                WHERE id = :id
                            """), {
                                'id': record[0],
                                'a': choices.get('A', ''),
                                'b': choices.get('B', ''),
                                'c': choices.get('C', ''),
                                'd': choices.get('D', '')
                            })
                    except Exception as e:
                        logger.warning(f"Could not migrate cached question {record[0]}: {e}")
                        continue

            # Create all new tables
            logger.info("Creating new tables...")
            db.create_all()
            
            # Commit all changes
            db.session.commit()
            logger.info("Database migration completed successfully!")
            
            return True
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migration()
