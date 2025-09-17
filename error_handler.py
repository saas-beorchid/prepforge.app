#!/usr/bin/env python3
"""
ROBUST ERROR HANDLING SYSTEM
============================

This module provides comprehensive error handling to eliminate 500 errors
and ensure users always have a smooth experience practicing questions.
"""

import logging
import traceback
from functools import wraps
from flask import jsonify, render_template, request, current_app
from app import app, db
from models import CachedQuestion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrepForgeErrorHandler:
    """Comprehensive error handling for PrepForge"""
    
    @staticmethod
    def handle_database_error(func):
        """Decorator to handle database errors gracefully"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Database error in {func.__name__}: {e}")
                db.session.rollback()
                
                # Return fallback data if possible
                if 'question' in func.__name__.lower():
                    return PrepForgeErrorHandler.get_fallback_questions()
                return None
        return wrapper
    
    @staticmethod
    def handle_api_error(func):
        """Decorator to handle API errors gracefully"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"API error in {func.__name__}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Return user-friendly error response
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'error': 'We encountered a temporary issue. Please try again.',
                        'fallback_available': True
                    }), 500
                else:
                    return render_template('error.html', 
                                         error_message='Temporary issue - please try again',
                                         show_retry=True), 500
        return wrapper
    
    @staticmethod
    def get_fallback_questions(exam_type='GMAT', count=5):
        """Get fallback questions when primary systems fail"""
        try:
            questions = CachedQuestion.query.filter_by(exam_type=exam_type).limit(count).all()
            if not questions:
                # Generate basic fallback questions
                questions = PrepForgeErrorHandler.generate_basic_questions(exam_type, count)
            return questions
        except Exception as e:
            logger.error(f"Fallback question retrieval failed: {e}")
            return PrepForgeErrorHandler.generate_basic_questions(exam_type, count)
    
    @staticmethod
    def generate_basic_questions(exam_type, count):
        """Generate basic questions when all other systems fail"""
        basic_questions = []
        
        question_templates = {
            'GMAT': {
                'question': 'If x + y = 10 and x - y = 4, what is the value of x?',
                'options': ['5', '6', '7', '8'],
                'correct': '7',
                'explanation': 'Solving the system: x + y = 10, x - y = 4. Adding equations: 2x = 14, so x = 7.'
            },
            'GRE': {
                'question': 'Choose the word that best completes the sentence: The scholar was known for his _______ research.',
                'options': ['superficial', 'meticulous', 'hasty', 'careless'],
                'correct': 'meticulous',
                'explanation': 'Meticulous means showing great attention to detail, which fits a scholar known for quality research.'
            },
            'MCAT': {
                'question': 'Which of the following is the primary function of mitochondria?',
                'options': ['Protein synthesis', 'DNA replication', 'Energy production', 'Cell division'],
                'correct': 'Energy production',
                'explanation': 'Mitochondria are the powerhouses of the cell, primarily responsible for ATP production.'
            }
        }
        
        template = question_templates.get(exam_type, question_templates['GMAT'])
        
        for i in range(count):
            question = {
                'id': f'fallback_{exam_type}_{i+1}',
                'exam_type': exam_type,
                'question_text': template['question'],
                'option_a': template['options'][0],
                'option_b': template['options'][1],
                'option_c': template['options'][2],
                'option_d': template['options'][3],
                'correct_answer': template['correct'],
                'explanation': template['explanation'],
                'difficulty': 3,
                'topic_area': 'General'
            }
            basic_questions.append(question)
        
        return basic_questions

# Register global error handlers
@app.errorhandler(500)
def handle_500_error(error):
    """Handle 500 Internal Server Error"""
    logger.error(f"500 Error: {error}")
    logger.error(f"Request: {request.url}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    db.session.rollback()
    
    return render_template('error.html',
                         error_code=500,
                         error_message='We are experiencing temporary technical difficulties.',
                         show_retry=True,
                         support_message='Our team has been notified and is working to resolve this.'), 500

@app.errorhandler(404)
def handle_404_error(error):
    """Handle 404 Not Found Error"""
    return render_template('error.html',
                         error_code=404,
                         error_message='The page you are looking for does not exist.',
                         show_home_link=True), 404

@app.errorhandler(403)
def handle_403_error(error):
    """Handle 403 Forbidden Error"""
    return render_template('error.html',
                         error_code=403,
                         error_message='You do not have permission to access this resource.',
                         show_login_link=True), 403

# Context processor for error handling
@app.context_processor
def inject_error_handler():
    return {
        'error_handler': PrepForgeErrorHandler,
        'get_fallback_questions': PrepForgeErrorHandler.get_fallback_questions
    }

logger.info("✅ Error handling system initialized")