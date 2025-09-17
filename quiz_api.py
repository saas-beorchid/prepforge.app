"""
Quiz API endpoints for interactive question practice
Handles question generation, answer submission, and user progress tracking
"""

import os
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user

# Initialize blueprint
quiz_api = Blueprint('quiz_api', __name__)
logger = logging.getLogger(__name__)

def get_user_performance(user_id: int, exam_type: str, topic: str):
    """Get user performance for adaptive difficulty"""
    try:
        from models import UserPerformance
        performance = UserPerformance.query.filter_by(
            user_id=user_id,
            exam_type=exam_type,
            topic=topic
        ).first()
        
        logger.info(f"📊 Retrieved performance for user {user_id}: {exam_type} - {topic} = {performance.score if performance else 'No data'}")
        return performance
        
    except Exception as e:
        logger.error(f"❌ Error retrieving user performance: {e}")
        return None

def update_user_performance(user_id: int, exam_type: str, topic: str, score: float):
    """Update or create user performance record"""
    try:
        from models import db, UserPerformance
        from datetime import datetime
        
        # Get existing record or create new one
        performance = UserPerformance.query.filter_by(
            user_id=user_id,
            exam_type=exam_type,
            topic=topic
        ).first()
        
        if performance:
            # Update existing record - calculate running average
            total_score = (performance.score * performance.attempts) + score
            performance.attempts += 1
            performance.score = total_score / performance.attempts
            performance.last_updated = datetime.utcnow()
            logger.info(f"📊 Updated performance for user {user_id}: {exam_type} - {topic} = {performance.score:.1f}% (attempt {performance.attempts})")
        else:
            # Create new record
            performance = UserPerformance(
                user_id=user_id,
                exam_type=exam_type,
                topic=topic,
                score=score,
                attempts=1,
                last_updated=datetime.utcnow()
            )
            db.session.add(performance)
            logger.info(f"📊 Created new performance record for user {user_id}: {exam_type} - {topic} = {score:.1f}%")
        
        db.session.commit()
        return performance
        
    except Exception as e:
        logger.error(f"❌ Error updating user performance: {e}")
        db.session.rollback()
        return None

def determine_difficulty(score: float) -> str:
    """Determine difficulty level based on user score"""
    if score < 40:
        return 'easy'
    elif score <= 70:
        return 'medium'
    else:
        return 'hard'

def generate_unique_fallback_question(exam_type: str, topic: str, difficulty: str, index: int, timestamp: int):
    """Generate unique fallback question when xAI fails"""
    import random
    import hashlib
    
    # Create unique content based on timestamp and index
    unique_hash = hashlib.md5(f"{timestamp}{index}{exam_type}{topic}".encode()).hexdigest()[:8]
    
    if exam_type == 'GRE' and topic == 'algebra':
        # Generate unique algebraic problems
        a = random.randint(2, 9)
        b = random.randint(1, 8)
        c = random.randint(1, 12)
        
        if difficulty == 'easy':
            question_text = f"Solve for x: {a}x + {b} = {c * a + b}"
            correct_val = c
            # Create numeric options for algebra
            options = [str(correct_val), str(correct_val + 1), str(correct_val - 1), str(correct_val + 2)]
        elif difficulty == 'hard':
            question_text = f"If {a}x² - {b}x + {c} = 0, what is the discriminant?"
            correct_val = b*b - 4*a*c
            # Create numeric options for discriminant
            options = [str(correct_val), str(correct_val + 4), str(correct_val - 4), str(abs(correct_val) + 1)]
        else:  # medium
            question_text = f"What is {a} × {b} + {c}?"
            correct_val = a * b + c
            # Create numeric options for arithmetic
            options = [str(correct_val), str(correct_val + 1), str(correct_val - 1), str(correct_val + 2)]
            
        correct_option = options[0]  # The first option is always correct
        
        # Shuffle the options but track where the correct answer ends up
        import random
        shuffled_options = options.copy()
        random.shuffle(shuffled_options)
        
        # Find the index of the correct answer after shuffling
        correct_index = shuffled_options.index(correct_option)
        correct_letter = chr(65 + correct_index)  # Convert to A, B, C, D
        
        return {
            'id': f"fallback_{unique_hash}_{timestamp}_{index}",
            'question_text': question_text,
            'choices': shuffled_options,  # Clean options without A/B/C/D prefixes
            'correct_answer': correct_letter,  # Letter corresponding to correct option position
            'explanation': f"Unique {exam_type} {topic} question ({difficulty} level) - Generated at {timestamp}",
            'difficulty': difficulty,
            'topic': topic,
            'exam_type': exam_type,
            'source': 'unique_fallback',
            'generation_time': timestamp
        }
    else:
        # Generic unique fallback
        return {
            'id': f"fallback_{unique_hash}_{timestamp}_{index}",
            'question_text': f"Unique {exam_type} {topic} question #{index} - What concept is most important in {topic}? (Generated: {timestamp})",
            'choices': [f"Concept {unique_hash[:2]}", f"Concept {unique_hash[2:4]}", f"Concept {unique_hash[4:6]}", "All concepts"],  # Clean options without prefixes
            'correct_answer': 'D',
            'explanation': f"All concepts in {topic} are important for {exam_type} success. This is a unique question generated at timestamp {timestamp}.",
            'difficulty': difficulty,
            'topic': topic,
            'exam_type': exam_type,
            'source': 'unique_fallback',
            'generation_time': timestamp
        }

def simple_rate_limit():
    """Simple rate limiting decorator with per-exam-type tracking"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            from flask import session, request
            
            # Get exam type from request
            data = request.get_json() or {}
            exam_type = data.get('exam_type', 'GRE')
            
            # Track requests per exam type
            session_key = f'api_requests_{exam_type}'
            request_count = session.get(session_key, 0)
            
            if request_count >= 20:
                return jsonify({
                    'error': f'Daily limit of 20 questions reached for {exam_type}. Upgrade to Pro for unlimited access.',
                    'code': 'rate_limit_exceeded',
                    'limit': 20,
                    'remaining': 0,
                    'exam_type': exam_type
                }), 429
                
            session[session_key] = request_count + 1
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

@quiz_api.route('/api/generate-questions', methods=['POST'])
@login_required
@simple_rate_limit()
def generate_questions():
    """
    Generate unique questions with adaptive difficulty using xAI integration
    """
    try:
        # Import models here to avoid circular imports
        from models import db, UserPerformance
        import uuid
        import time
        
        data = request.get_json() or {}
        exam_type = data.get('exam_type', 'GRE')
        topic = data.get('topic', 'algebra')
        count = min(data.get('count', 1), 5)  # Limit to 5 questions max
        
        logger.info(f"🚀 Generating {count} UNIQUE {exam_type} questions for user {current_user.id}, topic: {topic}")
        
        # Get user performance for adaptive difficulty
        user_performance = get_user_performance(current_user.id, exam_type, topic)
        difficulty = determine_difficulty(user_performance.score if user_performance else 50.0)
        
        logger.info(f"📊 User performance: {user_performance.score if user_performance else 'No data'}, Difficulty: {difficulty}")
        
        # Generate unique questions using xAI
        questions = []
        
        try:
            # Initialize xAI generator
            from xai_question_generator import XAIQuestionGenerator
            xai_generator = XAIQuestionGenerator()
            
            # Create unique system prompt enforcing uniqueness
            timestamp = int(time.time())
            unique_session_id = str(uuid.uuid4())[:8]
            
            system_prompt = f"""Generate UNIQUE {exam_type} {topic} questions that are:
1. NEVER repeated - each question must be completely different from any previous questions
2. Specific to {topic} at {difficulty} difficulty level
3. Educational and challenging
4. Session ID: {unique_session_id} - Use this to ensure uniqueness
5. Current time: {timestamp} - Include time-based variation

IMPORTANT: Generate completely different questions each time. Avoid any repetition of content, numbers, or concepts from previous generations. Make each question unique in topic focus, numbers used, and approach."""
            
            # Generate questions with enforced uniqueness  
            for i in range(count):
                unique_topic_variant = f"{topic}_variant_{i}_{timestamp}"
                
                try:
                    question_data = xai_generator.generate_single_question(
                        exam_type=exam_type,
                        topic=unique_topic_variant,
                        difficulty=difficulty,
                        system_prompt=system_prompt,
                        enforce_uniqueness=True
                    )
                    
                    if question_data:
                        # Ensure clean options without letter prefixes
                        if 'choices' in question_data:
                            import re
                            clean_choices = []
                            for choice in question_data['choices']:
                                if isinstance(choice, str):
                                    # Remove letter prefixes like "A.", "B)", etc.
                                    clean_choice = re.sub(r'^[A-D][.)]\s*', '', choice).strip()
                                    clean_choices.append(clean_choice)
                                else:
                                    clean_choices.append(choice)
                            question_data['choices'] = clean_choices
                        
                        # Add uniqueness markers
                        question_data['id'] = f"xai_{exam_type}_{unique_session_id}_{i}_{timestamp}"
                        question_data['topic'] = topic
                        question_data['difficulty'] = difficulty
                        question_data['source'] = 'xai_unique'
                        question_data['generation_time'] = timestamp
                        question_data['session_id'] = unique_session_id
                        
                        # Enhance explanation with detailed sections
                        if 'explanation' in question_data:
                            original_explanation = question_data['explanation']
                            question_data['explanation'] = {
                                'technical': original_explanation,
                                'simple': f"In simple terms: {original_explanation[:200]}...",
                                'key_concepts': self.extract_key_concepts(original_explanation, exam_type)
                            }
                        else:
                            question_data['explanation'] = {
                                'technical': 'Technical explanation not available.',
                                'simple': 'Simple explanation not available.',
                                'key_concepts': ['Core concepts for this question type']
                            }
                        
                        questions.append(question_data)
                        logger.info(f"✅ Generated unique question {i+1}/{count}: {question_data['id']}")
                    else:
                        logger.warning(f"⚠️ xAI failed to generate question {i+1}, using fallback")
                        # Fallback with unique content
                        fallback_question = generate_unique_fallback_question(exam_type, topic, difficulty, i, timestamp)
                        questions.append(fallback_question)
                        
                except Exception as q_error:
                    logger.warning(f"⚠️ Error generating question {i+1}: {q_error}, using fallback")
                    fallback_question = generate_unique_fallback_question(exam_type, topic, difficulty, i, timestamp)
                    questions.append(fallback_question)
                
                # Small delay to ensure uniqueness
                time.sleep(0.1)
                
        except Exception as xai_error:
            logger.error(f"❌ xAI generation failed: {xai_error}")
            # Generate unique fallback questions
            for i in range(count):
                fallback_question = generate_unique_fallback_question(exam_type, topic, difficulty, i, int(time.time()))
                questions.append(fallback_question)
        
        # Track Mixpanel event
        try:
            if current_app.config.get('MIXPANEL_TOKEN'):
                from analytics import track_mixpanel_event
                track_mixpanel_event(current_user.id, 'Question Generated', {
                    'exam_type': exam_type,
                    'topic': topic,
                    'difficulty': difficulty,
                    'count': len(questions),
                    'source': 'xai_unique'
                })
        except Exception as e:
            logger.warning(f"Mixpanel tracking failed: {e}")
        
        if not questions:
            return jsonify({
                'error': 'Failed to generate questions. Please try again.',
                'code': 'generation_failed'
            }), 500
        
        # Calculate remaining questions for free users per exam type
        from flask import session
        session_key = f'api_requests_{exam_type}'
        remaining = max(0, 20 - session.get(session_key, 0))
        
        return jsonify({
            'success': True,
            'questions': questions,
            'count': len(questions),
            'questions_remaining': remaining,
            'exam_type': exam_type
        })
        
    except Exception as e:
        logger.error(f"Error in generate_questions: {e}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'server_error'
        }), 500

@quiz_api.route('/api/submit-answer', methods=['POST'])
@login_required
def submit_answer():
    """
    Submit answer and get feedback with performance tracking
    """
    try:
        data = request.get_json() or {}
        question_id = data.get('question_id')
        user_answer = data.get('answer', '').upper()
        exam_type = data.get('exam_type', 'GRE')
        question_data = data.get('question_data', {})
        
        if not user_answer:
            return jsonify({
                'error': 'Answer is required',
                'code': 'missing_answer'
            }), 400
        
        # Get correct answer
        correct_answer = question_data.get('correct_answer', '').upper()
        explanation = question_data.get('explanation', 'No explanation available.')
        topic = question_data.get('topic', 'General')
        difficulty = question_data.get('difficulty', 'medium')
        
        # Check if answer is correct
        is_correct = user_answer == correct_answer
        
        # Calculate score (simple scoring: 1 point for correct, 0 for incorrect)
        score = 1.0 if is_correct else 0.0
        
        # Update user performance for adaptive learning
        performance_score = 100.0 if is_correct else 0.0  # Convert to percentage
        updated_performance = update_user_performance(current_user.id, exam_type, topic, performance_score)
        
        # Calculate new overall score for response
        overall_score = updated_performance.score if updated_performance else performance_score
        
        try:
            from models import UserPerformance, db
            from datetime import datetime
            
            # Check if performance record exists (UPSERT logic)
            performance = UserPerformance.query.filter_by(
                user_id=current_user.id,
                exam_type=exam_type,
                topic=topic or 'General'
            ).first()
            
            if performance:
                # Update existing record with rolling average
                new_score = ((performance.score * performance.attempts) + score) / (performance.attempts + 1)
                performance.score = new_score
                performance.attempts += 1
                performance.last_updated = datetime.utcnow()
                logger.debug(f"Updated existing performance for user {current_user.id}: score {new_score:.2f}")
            else:
                # Create new record
                performance = UserPerformance(
                    user_id=current_user.id,
                    exam_type=exam_type,
                    topic=topic or 'General',
                    score=score,
                    attempts=1,
                    last_updated=datetime.utcnow()
                )
                db.session.add(performance)
                logger.debug(f"Created new performance record for user {current_user.id}")
            
            db.session.commit()
            
        except Exception as e:
            logger.warning(f"Failed to update user performance: {e}")
            db.session.rollback()
        
        # Track analytics (simplified)
        logger.debug(f"Would track Mixpanel event: Answer Submitted with properties: {{'user_id': '{current_user.id}', 'exam_type': '{exam_type}', 'topic': '{topic}', 'difficulty': '{difficulty}', 'is_correct': {is_correct}, 'user_answer': '{user_answer}', 'correct_answer': '{correct_answer}', 'timestamp': '{datetime.now().isoformat()}'}}")
        
        logger.info(f"User {current_user.id} answered question: {is_correct} ({user_answer} vs {correct_answer})")
        
        return jsonify({
            'success': True,
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'explanation': explanation,
            'score': score,
            'user_answer': user_answer,
            'questions_remaining': 19  # Placeholder for free trial
        })
        
    except Exception as e:
        logger.error(f"Error in submit_answer: {e}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'server_error'
        }), 500

@quiz_api.route('/api/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """
    Create Stripe checkout session for Pro upgrade
    """
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        if not stripe.api_key:
            return jsonify({
                'error': 'Payment system not configured',
                'code': 'payment_config_error'
            }), 500
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=current_user.email,
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'PrepForge Pro Subscription',
                        'description': 'Unlimited access to all practice questions',
                    },
                    'unit_amount': 2999,  # $29.99
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'cancel',
            metadata={
                'user_id': str(current_user.id),
                'email': current_user.email
            }
        )
        
        # Track analytics
        try:
            track_mixpanel_event('Checkout Started', {
                'user_id': str(current_user.id),
                'checkout_session_id': checkout_session.id,
                'amount': 29.99
            })
        except Exception as e:
            logger.warning(f"Mixpanel tracking failed: {e}")
        
        logger.info(f"Created checkout session for user {current_user.id}: {checkout_session.id}")
        
        return jsonify({
            'success': True,
            'url': checkout_session.url,
            'session_id': checkout_session.id
        })
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        return jsonify({
            'error': 'Failed to create checkout session',
            'code': 'checkout_error'
        }), 500

def get_cached_question(exam_type, topic=None, difficulty=None):
    """
    Get a cached question matching the criteria
    """
    try:
        query = CachedQuestion.query.filter_by(exam_type=exam_type)
        
        if topic:
            query = query.filter(CachedQuestion.topic.ilike(f'%{topic}%'))
            
        if difficulty:
            query = query.filter_by(difficulty=difficulty)
        
        # Get a random question from the filtered results
        question = query.order_by(db.func.random()).first()
        return question
        
    except Exception as e:
        logger.error(f"Error getting cached question: {e}")
        return None

def track_mixpanel_event(event_name, properties):
    """
    Track events to Mixpanel (placeholder for now)
    """
    try:
        mixpanel_token = os.environ.get('MIXPANEL_TOKEN')
        if not mixpanel_token:
            logger.debug("Mixpanel token not configured, skipping tracking")
            return
        
        # Add timestamp
        properties['timestamp'] = datetime.utcnow().isoformat()
        
        logger.debug(f"Would track Mixpanel event: {event_name} with properties: {properties}")
        
        # TODO: Implement actual Mixpanel API call when needed
        # For now, just log the event
        
    except Exception as e:
        logger.warning(f"Mixpanel tracking error: {e}")

# Register error handlers
@quiz_api.errorhandler(429)
def rate_limit_handler(e):
    return jsonify({
        'error': 'Rate limit exceeded',
        'code': 'rate_limit_exceeded'
    }), 429

@quiz_api.errorhandler(500)
def server_error_handler(e):
    return jsonify({
        'error': 'Internal server error',
        'code': 'server_error'
    }), 500

def extract_key_concepts(explanation_text: str, exam_type: str) -> list:
    """Extract key concepts from explanation text"""
    try:
        # Basic concept extraction based on exam type
        if exam_type in ['GRE', 'GMAT']:
            concepts = ['Critical reasoning', 'Logical analysis', 'Problem solving']
        elif exam_type in ['MCAT', 'USMLE_STEP_1', 'USMLE_STEP_2']:
            concepts = ['Medical knowledge', 'Clinical reasoning', 'Diagnostic skills']
        elif exam_type == 'LSAT':
            concepts = ['Legal reasoning', 'Logical deduction', 'Argument analysis']
        else:
            concepts = ['Core knowledge', 'Application skills', 'Critical thinking']
        
        # Try to extract specific concepts from explanation
        if 'formula' in explanation_text.lower():
            concepts.append('Mathematical formulas')
        if 'theorem' in explanation_text.lower():
            concepts.append('Theoretical principles')
        if 'method' in explanation_text.lower():
            concepts.append('Problem-solving methods')
            
        return concepts[:3]  # Limit to 3 key concepts
        
    except Exception as e:
        logger.warning(f"Error extracting key concepts: {e}")
        return ['Core concepts', 'Problem analysis', 'Application skills']