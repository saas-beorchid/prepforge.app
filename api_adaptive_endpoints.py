"""
Additional API endpoints for adaptive question generation
Integrates with existing ai_question_api.py
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from adaptive_question_engine import adaptive_engine
from subscription_gate import subscription_gate
import logging

logger = logging.getLogger(__name__)

adaptive_api = Blueprint('adaptive_api', __name__)

@adaptive_api.route('/api/generate-adaptive-questions', methods=['POST'])
@login_required
@subscription_gate
def generate_adaptive_questions():
    """Generate adaptive questions based on user performance"""
    try:
        data = request.get_json()
        exam_type = data.get('exam_type')
        topic = data.get('topic')
        count = min(data.get('count', 1), 5)  # Limit for adaptive generation
        
        if not exam_type or not topic:
            return jsonify({'error': 'Both exam_type and topic are required'}), 400
            
        # Validate exam type
        valid_exams = [
            'GMAT', 'GRE', 'MCAT', 'USMLE_STEP_1', 'USMLE_STEP_2', 
            'NCLEX', 'LSAT', 'IELTS', 'TOEFL', 'PMP', 'CFA', 'ACT', 'SAT'
        ]
        
        if exam_type not in valid_exams:
            return jsonify({'error': f'Invalid exam type. Must be one of: {valid_exams}'}), 400
            
        logger.info(f"🎯 Generating adaptive {exam_type} questions on {topic} for user {current_user.id}")
        
        # Generate adaptive questions
        questions = adaptive_engine.generate_adaptive_questions(
            user_id=current_user.id,
            exam_type=exam_type,
            topic=topic,
            count=count
        )
        
        if not questions:
            logger.error("❌ No adaptive questions generated")
            return jsonify({'error': 'Failed to generate adaptive questions'}), 500
            
        # Get user performance for response
        performance = adaptive_engine.get_user_performance(current_user.id, exam_type, topic)
        
        response_data = {
            'success': True,
            'questions': questions,
            'count': len(questions),
            'exam_type': exam_type,
            'topic': topic,
            'adaptive': True,
            'user_performance': {
                'score': performance.score if performance else None,
                'difficulty_level': performance.difficulty_level if performance else 'medium',
                'attempts': performance.attempts if performance else 0
            },
            'generated_by': 'adaptive_xai_engine',
            'timestamp': adaptive_engine.datetime.utcnow().isoformat()
        }
        
        logger.info(f"✅ Generated {len(questions)} adaptive questions for user {current_user.id}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Error in adaptive question generation: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@adaptive_api.route('/api/user-performance/<exam_type>/<topic>', methods=['GET'])
@login_required
def get_user_performance(exam_type, topic):
    """Get user performance for specific exam type and topic"""
    try:
        performance = adaptive_engine.get_user_performance(current_user.id, exam_type, topic)
        
        if not performance:
            return jsonify({
                'exam_type': exam_type,
                'topic': topic,
                'score': None,
                'difficulty_level': 'medium',
                'attempts': 0,
                'message': 'No performance data available'
            })
        
        return jsonify({
            'exam_type': exam_type,
            'topic': topic,
            'score': performance.score,
            'difficulty_level': performance.difficulty_level,
            'attempts': performance.attempts,
            'last_updated': performance.last_updated.isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error retrieving user performance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@adaptive_api.route('/api/update-performance', methods=['POST'])
@login_required
def update_performance():
    """Update user performance after answering questions"""
    try:
        data = request.get_json()
        exam_type = data.get('exam_type')
        topic = data.get('topic')
        score = data.get('score')
        
        if not all([exam_type, topic, score is not None]):
            return jsonify({'error': 'exam_type, topic, and score are required'}), 400
            
        if not isinstance(score, (int, float)) or score < 0 or score > 100:
            return jsonify({'error': 'Score must be a number between 0 and 100'}), 400
            
        # Update performance
        performance = adaptive_engine.update_user_performance(
            user_id=current_user.id,
            exam_type=exam_type,
            topic=topic,
            score=float(score)
        )
        
        return jsonify({
            'success': True,
            'updated_performance': {
                'exam_type': exam_type,
                'topic': topic,
                'score': performance.score,
                'difficulty_level': performance.difficulty_level,
                'attempts': performance.attempts,
                'last_updated': performance.last_updated.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error updating user performance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500