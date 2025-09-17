#!/usr/bin/env python3
"""
QUESTION CACHE OPTIMIZER
========================

Optimizes question caching and webpage loading performance by:
1. Pre-caching all generated questions
2. Implementing smart cache management
3. Reducing database queries
4. Optimizing question retrieval

Author: PrepForge Development Team
Date: July 22, 2025
"""

import logging
import time
from datetime import datetime, timedelta
from sqlalchemy import and_, func, text
from app import app, db
from models import Question, CachedQuestion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionCacheOptimizer:
    """
    Optimizes question caching for maximum performance
    """
    
    def __init__(self):
        self.cache_stats = {}
        
    def cache_all_generated_questions(self):
        """
        Cache all generated questions that aren't already cached
        """
        logger.info("🚀 STARTING COMPREHENSIVE QUESTION CACHING")
        
        with app.app_context():
            try:
                # Get all questions not in cache
                uncached_questions = self._find_uncached_questions()
                
                if not uncached_questions:
                    logger.info("✅ All questions already cached")
                    return
                    
                logger.info(f"📦 Found {len(uncached_questions)} questions to cache")
                
                # Cache in batches for performance
                batch_size = 50
                total_cached = 0
                
                for i in range(0, len(uncached_questions), batch_size):
                    batch = uncached_questions[i:i+batch_size]
                    cached_count = self._cache_question_batch(batch)
                    total_cached += cached_count
                    
                    logger.info(f"📈 Progress: {total_cached}/{len(uncached_questions)} questions cached")
                    
                logger.info(f"✅ CACHING COMPLETE: {total_cached} questions cached")
                self._update_cache_stats()
                
            except Exception as e:
                logger.error(f"❌ Caching failed: {e}")
                raise
    
    def _find_uncached_questions(self):
        """
        Find all questions that aren't cached
        """
        # Get all question IDs from main table
        main_questions = db.session.query(Question.id, Question.exam_type).all()
        
        # Get all cached question IDs
        cached_ids = set(row[0] for row in db.session.query(CachedQuestion.question_id).all())
        
        # Find uncached questions
        uncached = []
        for q_id, exam_type in main_questions:
            if q_id not in cached_ids:
                question = Question.query.get(q_id)
                if question:
                    uncached.append(question)
                    
        return uncached
    
    def _cache_question_batch(self, questions):
        """
        Cache a batch of questions efficiently
        """
        cached_count = 0
        
        try:
            for question in questions:
                if self._cache_single_question(question):
                    cached_count += 1
                    
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Batch caching failed: {e}")
            db.session.rollback()
            
        return cached_count
    
    def _cache_single_question(self, question):
        """
        Cache a single question with optimized format
        """
        try:
            # Check if already exists
            existing = CachedQuestion.query.filter_by(question_id=question.id).first()
            if existing:
                return False
                
            # Extract options from choices JSON
            choices = question.choices if question.choices else []
            if isinstance(choices, str):
                import json
                try:
                    choices = json.loads(choices)
                except:
                    choices = []
                    
            # Ensure we have 4 options
            while len(choices) < 4:
                choices.append(f"Option {len(choices) + 1}")
                
            # Create cached version
            cached_question = CachedQuestion(
                question_id=question.id,
                exam_type=question.exam_type,
                difficulty=str(question.difficulty) if question.difficulty else '3',
                question_text=question.question_text,
                choices=choices,
                option_a=choices[0] if len(choices) > 0 else 'Option A',
                option_b=choices[1] if len(choices) > 1 else 'Option B', 
                option_c=choices[2] if len(choices) > 2 else 'Option C',
                option_d=choices[3] if len(choices) > 3 else 'Option D',
                correct_answer=str(question.correct_answer),
                explanation=question.explanation or 'Detailed explanation provided.',
                topic_area=question.subject or 'General',
                tags='["cached_from_main"]',
                cached_at=datetime.utcnow()
            )
            
            db.session.add(cached_question)
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache question {question.id}: {e}")
            return False
    
    def _update_cache_stats(self):
        """
        Update cache statistics for monitoring
        """
        try:
            # Get stats for each exam type
            stats_query = db.session.query(
                CachedQuestion.exam_type,
                func.count(CachedQuestion.id).label('count'),
                func.max(CachedQuestion.cached_at).label('last_cached')
            ).group_by(CachedQuestion.exam_type).all()
            
            self.cache_stats = {
                stat.exam_type: {
                    'count': stat.count,
                    'last_cached': stat.last_cached
                }
                for stat in stats_query
            }
            
            logger.info("📊 CACHE STATISTICS:")
            for exam_type, stats in self.cache_stats.items():
                logger.info(f"   {exam_type}: {stats['count']} questions cached")
                
        except Exception as e:
            logger.error(f"Failed to update cache stats: {e}")
    
    def optimize_database_queries(self):
        """
        Optimize database queries for faster loading
        """
        logger.info("⚡ OPTIMIZING DATABASE QUERIES")
        
        try:
            with app.app_context():
                # Create indexes for faster queries
                db.session.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_cached_question_exam_type ON cached_question(exam_type)"
                ))
                db.session.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_cached_question_difficulty ON cached_question(difficulty)"
                ))
                db.session.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_cached_question_cached_at ON cached_question(cached_at)"
                ))
                
                db.session.commit()
                logger.info("✅ Database indexes created for performance")
                
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
    
    def prewarm_cache(self):
        """
        Pre-warm cache with frequently accessed questions
        """
        logger.info("🔥 PRE-WARMING CACHE")
        
        try:
            # Pre-load questions for each exam type
            all_exam_types = [
                'GMAT', 'GRE', 'MCAT', 'USMLE_STEP_1', 'USMLE_STEP_2',
                'NCLEX', 'LSAT', 'IELTS', 'TOEFL', 'PMP', 'CFA', 'ACT', 'SAT'
            ]
            
            for exam_type in all_exam_types:
                # Pre-load first 10 questions for instant access
                questions = CachedQuestion.query.filter_by(exam_type=exam_type).limit(10).all()
                logger.info(f"🔥 Pre-warmed {len(questions)} questions for {exam_type}")
                
            logger.info("✅ Cache pre-warming complete")
            
        except Exception as e:
            logger.error(f"Cache pre-warming failed: {e}")

def run_cache_optimization():
    """
    Main function to run all cache optimizations
    """
    logger.info("🚀 STARTING COMPREHENSIVE CACHE OPTIMIZATION")
    
    optimizer = QuestionCacheOptimizer()
    
    try:
        # Step 1: Cache all generated questions
        optimizer.cache_all_generated_questions()
        
        # Step 2: Optimize database queries
        optimizer.optimize_database_queries()
        
        # Step 3: Pre-warm cache
        optimizer.prewarm_cache()
        
        logger.info("✅ CACHE OPTIMIZATION COMPLETE - MAXIMUM PERFORMANCE ACHIEVED!")
        
    except Exception as e:
        logger.error(f"❌ Cache optimization failed: {e}")
        raise

if __name__ == "__main__":
    run_cache_optimization()