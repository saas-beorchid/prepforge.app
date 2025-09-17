#!/usr/bin/env python3
"""
INSTANT QUESTION LOADER - Immediate Solution
===========================================

This script loads questions from JSON files for the 7 missing exam types
and ensures they're immediately available for practice.

Run this script to fix the immediate problem while the comprehensive system starts up.
"""

import json
import os
import logging
from app import app, db
from models import CachedQuestion
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# The 7 exam types that need immediate attention
PRIORITY_EXAMS = ['NCLEX', 'GRE', 'MCAT', 'USMLE_STEP_1', 'USMLE_STEP_2', 'SAT', 'ACT']

# JSON file mapping
JSON_FILES = {
    'GRE': 'GRE_Questions.json',
    'MCAT': 'MCAT_Questions.json',
    'USMLE_STEP_1': 'USMLE_STEP_1_Questions.json',
    'USMLE_STEP_2': 'USMLE_STEP_2_Questions.json',
    'NCLEX': 'NCLEX_Questions.json',
    'ACT': 'ACT_Questions.json',
    'SAT': 'SAT_Questions.json'
}

def load_exam_questions(exam_type):
    """Load questions for a specific exam type from JSON"""
    logger.info(f"🔄 Loading questions for {exam_type}")
    
    # Check if we already have questions
    existing = CachedQuestion.query.filter_by(exam_type=exam_type).count()
    if existing > 0:
        logger.info(f"✅ {exam_type} already has {existing} questions")
        return existing
    
    json_file = JSON_FILES.get(exam_type)
    if not json_file:
        logger.error(f"❌ No JSON file mapping for {exam_type}")
        return 0
        
    json_path = os.path.join('./questions_data', json_file)
    
    if not os.path.exists(json_path):
        logger.error(f"❌ JSON file not found: {json_path}")
        return 0
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            questions_data = json.load(f)
            
        if not questions_data:
            logger.warning(f"⚠️ Empty JSON file: {json_path}")
            return 0
            
        loaded_count = 0
        
        for i, q_data in enumerate(questions_data[:50]):  # Load first 50 questions
            try:
                question_id = f"{exam_type}_instant_{i}"
                
                # Create CachedQuestion for immediate availability
                cached_question = CachedQuestion(
                    question_id=question_id,
                    exam_type=exam_type,
                    difficulty=3,  # Default medium
                    question_text=q_data.get('question_text', q_data.get('question', 'Question text missing')),
                    option_a=_get_option(q_data, 0),
                    option_b=_get_option(q_data, 1),
                    option_c=_get_option(q_data, 2),
                    option_d=_get_option(q_data, 3),
                    correct_answer=str(q_data.get('correct_answer', 'A')),
                    explanation=q_data.get('explanation', f'Answer explanation for {exam_type} question'),
                    topic_area=q_data.get('topic_area', 'General'),
                    tags='["instant_loaded"]'
                )
                
                db.session.add(cached_question)
                loaded_count += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to load question {i} for {exam_type}: {e}")
                continue
                
        db.session.commit()
        logger.info(f"✅ Loaded {loaded_count} questions for {exam_type}")
        return loaded_count
        
    except Exception as e:
        logger.error(f"❌ Failed to load JSON file {json_path}: {e}")
        db.session.rollback()
        return 0

def _get_option(q_data, index):
    """Extract option from question data safely"""
    options = q_data.get('options', q_data.get('choices', []))
    if isinstance(options, list) and len(options) > index:
        return str(options[index])
    return f"Option {chr(65 + index)}"  # A, B, C, D

def load_all_priority_exams():
    """Load questions for all priority exam types"""
    logger.info("🚀 INSTANT QUESTION LOADING STARTED")
    
    total_loaded = 0
    success_count = 0
    
    for exam_type in PRIORITY_EXAMS:
        try:
            count = load_exam_questions(exam_type)
            total_loaded += count
            if count > 0:
                success_count += 1
                
        except Exception as e:
            logger.error(f"❌ Failed to load {exam_type}: {e}")
            continue
    
    logger.info(f"🎯 INSTANT LOADING COMPLETE: {success_count}/{len(PRIORITY_EXAMS)} exam types, {total_loaded} total questions")
    return total_loaded

def verify_all_exams_have_questions():
    """Verify all 13 exam types have at least some questions"""
    ALL_EXAMS = [
        'GMAT', 'GRE', 'MCAT', 'USMLE_STEP_1', 'USMLE_STEP_2', 
        'NCLEX', 'LSAT', 'IELTS', 'TOEFL', 'PMP', 'CFA', 'ACT', 'SAT'
    ]
    
    logger.info("🔍 VERIFYING ALL EXAM TYPES")
    
    results = {}
    all_good = True
    
    for exam_type in ALL_EXAMS:
        count = CachedQuestion.query.filter_by(exam_type=exam_type).count()
        results[exam_type] = count
        status = "✅" if count > 0 else "❌"
        logger.info(f"{status} {exam_type}: {count} questions")
        
        if count == 0:
            all_good = False
    
    if all_good:
        logger.info("🎉 ALL 13 EXAM TYPES HAVE QUESTIONS AVAILABLE!")
    else:
        missing = [exam for exam, count in results.items() if count == 0]
        logger.warning(f"⚠️ Missing questions for: {missing}")
    
    return results

if __name__ == "__main__":
    with app.app_context():
        # Step 1: Load priority exams
        total_loaded = load_all_priority_exams()
        
        # Step 2: Verify all exams
        results = verify_all_exams_have_questions()
        
        # Step 3: Report status
        print("\n" + "="*60)
        print("QUESTION AVAILABILITY STATUS")
        print("="*60)
        
        for exam_type, count in results.items():
            status = "READY" if count > 0 else "NEEDS ATTENTION"
            print(f"{exam_type:15} | {count:3d} questions | {status}")
        
        total_questions = sum(results.values())
        ready_exams = sum(1 for count in results.values() if count > 0)
        
        print("="*60)
        print(f"SUMMARY: {ready_exams}/13 exam types ready, {total_questions} total questions")
        print("="*60)
        
        if ready_exams == 13:
            print("🎉 ALL EXAM TYPES ARE NOW READY FOR PRACTICE!")
        else:
            missing = [exam for exam, count in results.items() if count == 0]
            print(f"⚠️ Still need questions for: {', '.join(missing)}")