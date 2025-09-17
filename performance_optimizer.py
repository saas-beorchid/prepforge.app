#!/usr/bin/env python3
"""
PERFORMANCE OPTIMIZER FOR PREPFORGE
===================================

Implements aggressive performance optimizations:
1. Question pre-loading and memory caching
2. Database query optimization 
3. Template caching
4. Static asset optimization

Author: PrepForge Development Team
Date: July 22, 2025
"""

import logging
import threading
import time
from flask import g, request
from app import app, db
from models import CachedQuestion
from functools import lru_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global performance cache
PERFORMANCE_CACHE = {
    'questions': {},
    'stats': {},
    'last_update': time.time()
}

class PerformanceOptimizer:
    """
    Aggressive performance optimization system
    """
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def get_cached_questions(exam_type, limit=20):
        """
        Memory-cached question retrieval with LRU caching
        """
        try:
            questions = CachedQuestion.query.filter_by(exam_type=exam_type).limit(limit).all()
            logger.info(f"🚀 Memory cache hit for {exam_type}: {len(questions)} questions")
            return questions
        except Exception as e:
            logger.error(f"Cache retrieval failed for {exam_type}: {e}")
            return []
    
    @staticmethod
    def warm_all_caches():
        """
        Pre-warm all caches for maximum speed
        """
        logger.info("🔥 WARMING ALL PERFORMANCE CACHES")
        
        all_exam_types = [
            'GMAT', 'GRE', 'MCAT', 'USMLE_STEP_1', 'USMLE_STEP_2',
            'NCLEX', 'LSAT', 'IELTS', 'TOEFL', 'PMP', 'CFA', 'ACT', 'SAT'
        ]
        
        with app.app_context():
            for exam_type in all_exam_types:
                # Pre-load into memory cache
                questions = PerformanceOptimizer.get_cached_questions(exam_type, 50)
                PERFORMANCE_CACHE['questions'][exam_type] = questions
                
                # Cache stats
                PERFORMANCE_CACHE['stats'][exam_type] = {
                    'count': len(questions),
                    'cached_at': time.time()
                }
                
            logger.info(f"✅ All caches warmed for {len(all_exam_types)} exam types")
    
    @staticmethod
    def get_ultra_fast_questions(exam_type, count=1):
        """
        Ultra-fast question retrieval using multi-level caching
        """
        # Level 1: Memory cache
        if exam_type in PERFORMANCE_CACHE['questions']:
            cached_questions = PERFORMANCE_CACHE['questions'][exam_type]
            if cached_questions and len(cached_questions) >= count:
                import random
                selected = random.sample(cached_questions, min(count, len(cached_questions)))
                logger.info(f"⚡ ULTRA-FAST L1: {exam_type} questions served from memory")
                return selected
        
        # Level 2: LRU cache
        questions = PerformanceOptimizer.get_cached_questions(exam_type, 20)
        if questions and len(questions) >= count:
            import random
            selected = random.sample(questions, min(count, len(questions)))
            logger.info(f"⚡ FAST L2: {exam_type} questions served from LRU cache")
            return selected
        
        # Level 3: Database (fallback)
        try:
            questions = CachedQuestion.query.filter_by(exam_type=exam_type).limit(count).all()
            logger.info(f"⚡ L3: {exam_type} questions served from database")
            return questions
        except Exception as e:
            logger.error(f"All cache levels failed for {exam_type}: {e}")
            return []

# Background cache warmer
def background_cache_warmer():
    """
    Continuously warm caches in background
    """
    while True:
        try:
            time.sleep(300)  # Every 5 minutes
            PerformanceOptimizer.warm_all_caches()
            PERFORMANCE_CACHE['last_update'] = time.time()
        except Exception as e:
            logger.error(f"Background cache warming failed: {e}")

# Start background warmer
cache_warmer_thread = threading.Thread(target=background_cache_warmer, daemon=True)
cache_warmer_thread.start()

# Initialize on import
with app.app_context():
    try:
        PerformanceOptimizer.warm_all_caches()
    except:
        logger.warning("Initial cache warming failed - will retry in background")