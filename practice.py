import logging
import json
import random
from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import RadioField, HiddenField
from wtforms.validators import DataRequired
from models import Question, UserProgress, CachedQuestion, db, Streak, Badge, UserBadge, AIExplanation, ExamConfig, QuestionMetrics
from random import sample
from sqlalchemy import desc, func
import threading
import time
import re
from datetime import date
from app import app
from ai_explanations import get_dual_explanations
from database_retry_handler import db_retry, test_connection, refresh_connection
from session_manager import PracticeSessionManager, require_valid_session, log_session_state
from buddy import get_encouraging_message, get_random_study_tip

# Performance optimization: Pre-load frequently used queries
CACHE_WARMUP_ENABLED = True
CACHED_QUESTIONS_PER_EXAM = {}
try:
    from question_selector import QuestionSelector
    from analytics import UserAnalytics
except ImportError as e:
    logging.warning(f"Optional modules not available: {e}")
    QuestionSelector = None
    UserAnalytics = None

practice = Blueprint('practice', __name__)

def preload_questions_cache():
    """
    Pre-load questions for faster access
    """
    if not CACHE_WARMUP_ENABLED:
        return
        
    try:
        all_exam_types = [
            'GMAT', 'GRE', 'MCAT', 'USMLE_STEP_1', 'USMLE_STEP_2',
            'NCLEX', 'LSAT', 'IELTS', 'TOEFL', 'PMP', 'CFA', 'ACT', 'SAT'
        ]
        
        for exam_type in all_exam_types:
            # Pre-load 20 questions for instant access
            questions = CachedQuestion.query.filter_by(exam_type=exam_type).limit(20).all()
            CACHED_QUESTIONS_PER_EXAM[exam_type] = questions
            
        logging.info(f"🚀 Pre-loaded questions for {len(CACHED_QUESTIONS_PER_EXAM)} exam types")
        
    except Exception as e:
        logging.error(f"Question pre-loading failed: {e}")

# Pre-load questions on module import
try:
    preload_questions_cache()
except:
    pass  # Fail silently if database not ready

def background_generate_questions(exam_type, count=25):
    """Background task to generate questions without blocking the UI"""
    try:
        with app.app_context():
            from comprehensive_question_availability_system import get_questions_for_practice
            
            logging.info(f"Using comprehensive system for {exam_type}")
            
            # The new system handles everything automatically
            questions = get_questions_for_practice(exam_type, user_id=None, count=1)
            if questions:
                logging.info(f"Comprehensive system ensured questions available for {exam_type}")
            else:
                logging.error(f"Comprehensive system failed for {exam_type}")
                
    except ImportError:
        # Fallback to old system
        _background_generate_questions_legacy(exam_type, count)

def _background_generate_questions_legacy(exam_type, count=25):
    """Legacy background generation as fallback"""
    try:
        with app.app_context():
            from strategic_ai_engine import StrategicAIEngine
            from models import Question, CachedQuestion
            
            logging.info(f"Background generation started for {exam_type}")
            engine = StrategicAIEngine()
            
            # Check if we need more questions
            existing_count = CachedQuestion.query.filter_by(exam_type=exam_type).count()
            if existing_count >= 100:  # Already have enough
                logging.info(f"Skipping background generation - {exam_type} already has {existing_count} questions")
                return
            
            # Generate questions in batches to avoid timeouts
            batch_size = 5  # Small batches to prevent timeouts
            for batch in range(0, count, batch_size):
                try:
                    questions_data = engine.generate_questions(
                        exam_type=exam_type,
                        difficulty=3,  # Use int for difficulty
                        topic_area='general',
                        count=min(batch_size, count - batch)
                    )
                    
                    if questions_data:
                        saved_count = 0
                        for q_data in questions_data:
                            try:
                                # Create unique ID
                                unique_id = f"{exam_type}_{int(time.time())}_{saved_count}"
                                
                                # Save directly to CachedQuestion for immediate use
                                cached_question = CachedQuestion()
                                cached_question.question_id = unique_id
                                cached_question.exam_type = exam_type
                                cached_question.difficulty = 3
                                cached_question.question_text = q_data['question_text']
                                cached_question.option_a = q_data['options'][0] if len(q_data['options']) > 0 else 'A'
                                cached_question.option_b = q_data['options'][1] if len(q_data['options']) > 1 else 'B'
                                cached_question.option_c = q_data['options'][2] if len(q_data['options']) > 2 else 'C'
                                cached_question.option_d = q_data['options'][3] if len(q_data['options']) > 3 else 'D'
                                cached_question.correct_answer = str(q_data['correct_answer'])
                                cached_question.explanation = q_data.get('explanation', 'Generated explanation')
                                cached_question.topic_area = 'General'
                                cached_question.tags = '["legacy_generated"]'
                                db.session.add(cached_question)
                                saved_count += 1
                                

                                
                            except Exception as e:
                                logging.error(f"Failed to save background question for {exam_type}: {e}")
                                db.session.rollback()
                                continue
                        
                        if saved_count > 0:
                            db.session.commit()
                            logging.info(f"Background generation saved {saved_count} questions for {exam_type}")
                        
                        # Short delay between batches to prevent API rate limiting
                        time.sleep(3)
                        
                except Exception as e:
                    logging.error(f"Background generation batch failed for {exam_type}: {e}")
                    db.session.rollback()
                    continue
            
            total_after = CachedQuestion.query.filter_by(exam_type=exam_type).count()
            logging.info(f"Background generation completed for {exam_type} - total cached: {total_after}")
                    
    except Exception as e:
        logging.error(f"Background generation failed for {exam_type}: {e}")
        try:
            db.session.rollback()
        except:
            pass

# Encouraging messages for correct answers
CORRECT_MESSAGES = [
    "Great job! 🎉 You've got this!",
    "Excellent work! 💪 Keep it up!",
    "Perfect! 🌟 You're making fantastic progress!",
    "That's right! 🏆 You're on a roll!",
    "Spot on! 🎯 You're learning fast!",
    "Brilliant! 🧠 Your hard work is paying off!",
    "Correct! ✅ You're mastering this material!"
]

# Encouraging messages for incorrect answers
INCORRECT_MESSAGES = [
    "Almost there! 🔍 Let's learn from this one.",
    "Not quite, but you're making progress! 📈",
    "That's not it, but don't give up! 💪",
    "Keep trying! 🌱 Growth comes from challenges.",
    "Not correct, but that's how we learn! 📚",
    "Don't worry! 🌟 Mistakes are part of learning.",
    "Incorrect, but you'll get it next time! 🚀"
]

# Study tips based on performance
STUDY_TIPS = [
    "Try creating flashcards for concepts you're struggling with.",
    "Consider taking short breaks between study sessions to improve retention.",
    "Try explaining the concept to someone else to strengthen your understanding.",
    "Review your incorrect answers to identify knowledge gaps.",
    "Practice similar questions to reinforce your understanding.",
    "Consider changing your study environment to improve focus.",
    "Try studying at different times of day to find when you're most productive."
]

def format_math_content(text):
    """Format text with proper LaTeX delimiters for MathJax"""
    if '\\(' in text and '\\)' in text:
        # Already has LaTeX delimiters
        return text

    # Format simple numbers and percentages
    def replace_math(match):
        content = match.group(0)
        if '°' in content:
            content = content.replace('°', '^\\circ')
        if '%' in content:
            content = content.replace('%', '\\%')
        return f'\\({content}\\)'

    # Pattern for numbers with optional decimals, degrees, or percentages
    pattern = r'\b\d+(?:\.\d+)?(?:°|%)?'
    text = re.sub(pattern, replace_math, text)

    # Format basic equations (e.g., "2x+3=7")
    equation_pattern = r'\b\d*[a-zA-Z]\s*[+\-*/=]\s*\d+'
    text = re.sub(equation_pattern, lambda m: f'\\({m.group(0)}\\)', text)

    return text

class PracticeForm(FlaskForm):
    answer = RadioField('Answer', choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], validators=[DataRequired()])
    question_id = HiddenField('Question ID', validators=[DataRequired()])

def get_trial_questions(exam_type, used_questions):
    """Get exactly 20 questions for trial users with HIGH-SPEED caching"""
    
    # PERFORMANCE BOOST: Try pre-loaded cache first
    if exam_type in CACHED_QUESTIONS_PER_EXAM and CACHED_QUESTIONS_PER_EXAM[exam_type]:
        cached_questions = CACHED_QUESTIONS_PER_EXAM[exam_type]
        if len(cached_questions) >= 20:
            selected = sample(cached_questions, 20)
            logging.info(f'⚡ ULTRA-FAST: Served 20 {exam_type} trial questions from memory cache')
            return selected
    
    # Fast database query with optimized indexing
    cached_questions = CachedQuestion.query.filter_by(exam_type=exam_type).limit(20).all()
    
    if cached_questions:
        logging.info(f'⚡ FAST: Selected {len(cached_questions)} cached questions for trial user')
        return cached_questions

    # Fallback to main questions table
    questions = Question.query.filter(
        Question.exam_type == exam_type,
        ~Question.id.in_(used_questions)
    ).limit(20).all()

    if questions:
        selected = sample(questions, min(20, len(questions)))
        logging.info(f'Selected {len(selected)} questions for trial user from main table')
        return selected

    # Check if we have ANY cached questions from previous generations
    any_cached = CachedQuestion.query.filter_by(exam_type=exam_type).limit(20).all()
    if any_cached:
        # Use what we have and start background generation for more
        logging.info(f"Found {len(any_cached)} cached questions for {exam_type}")
        threading.Thread(target=background_generate_questions, args=(exam_type,), daemon=True).start()
        return any_cached
    
    # As last resort, start immediate generation with timeout
    try:
        from strategic_ai_engine import StrategicAIEngine
        engine = StrategicAIEngine()
        
        logging.info(f"No cached questions available - starting emergency generation for {exam_type}")
        # Generate minimal questions to prevent timeouts and start background task
        generated_questions = engine.generate_questions(
            exam_type=exam_type,
            difficulty=3,  # Use integer for difficulty
            topic_area='general',
            count=3  # Minimal count to get started quickly
        )
        
        if not generated_questions:
            logging.warning(f"Strategic AI Engine returned empty result for {exam_type}")
            return None
        
        if generated_questions:
            # Convert generated questions to CachedQuestion format for immediate use
            trial_questions = []
            for i, q in enumerate(generated_questions):
                cached_q = CachedQuestion()
                cached_q.question_id = f"generated_{exam_type}_{i}_{int(time.time())}"
                cached_q.exam_type = exam_type
                cached_q.difficulty = 3
                cached_q.question_text = q.get('question_text', '')
                cached_q.option_a = q.get('options', [''])[0] if q.get('options') else ''
                cached_q.option_b = q.get('options', ['', ''])[1] if len(q.get('options', [])) > 1 else ''
                cached_q.option_c = q.get('options', ['', '', ''])[2] if len(q.get('options', [])) > 2 else ''
                cached_q.option_d = q.get('options', ['', '', '', ''])[3] if len(q.get('options', [])) > 3 else ''
                cached_q.correct_answer = str(q.get('correct_answer', 0))
                cached_q.explanation = q.get('explanation', '')
                cached_q.topic_area = q.get('topic_area', 'General')
                cached_q.generation_request_id = None
                trial_questions.append(cached_q)
                
            # Save generated questions to database for future use
            try:
                for q in trial_questions:
                    db.session.add(q)
                db.session.commit()
                logging.info(f"Saved {len(trial_questions)} generated questions to cache")
            except Exception as e:
                logging.error(f"Failed to save generated questions: {e}")
                db.session.rollback()
            
            logging.info(f'Generated {len(trial_questions)} new questions for trial user')
            
            # Start background generation for more questions
            threading.Thread(target=background_generate_questions, args=(exam_type,), daemon=True).start()
            
            return trial_questions
            
    except Exception as e:
        logging.error(f"Failed to generate questions: {e}")

    return None

@db_retry(max_retries=3, backoff_factor=1.0)
def get_practice_questions(exam_type):
    """Get practice questions based on user's subscription status with enhanced reliability"""
    start_time = time.time()
    logging.info(f"Starting question retrieval for {exam_type}")

    # Clear existing session data when switching exam types
    if 'exam_type' in session and session['exam_type'] != exam_type:
        PracticeSessionManager.clear_session()
        logging.info(f"Switched exam type from {session.get('exam_type')} to {exam_type}")

    if 'used_questions' not in session:
        session['used_questions'] = []

    # Check if we already have a valid session
    if PracticeSessionManager.validate_session():
        log_session_state()
        return True

    # Handle trial users (non-premium)
    if not current_user.subscription or not current_user.subscription.active:
        # Check trial limit (exactly 20 questions)
        question_count = UserProgress.query.filter_by(
            user_id=current_user.id,
            exam_type=exam_type
        ).count()

        if question_count >= 20:
            logging.info(f"Trial limit reached for user {current_user.id}")
            flash('Trial limit reached! Upgrade to premium for unlimited questions.', 'warning')
            return redirect(url_for('pricing'))

        # Get remaining trial questions
        questions = get_trial_questions(exam_type, session['used_questions'])
        if not questions:
            logging.error(f"No questions available for {exam_type}")
            flash(f'Unable to load questions for {exam_type}. This may be due to API issues. Please try again in a moment or contact support.', 'error')
            return redirect(url_for('dashboard'))

        # Handle both regular Question objects and CachedQuestion objects  
        question_ids = []
        for q in questions:
            if hasattr(q, 'question_id'):  # CachedQuestion
                question_ids.append(q.question_id)
            else:  # Regular Question
                question_ids.append(q.id)
        logging.info(f"Selected {len(question_ids)} trial questions")
        
        # Initialize session with proper state management
        if not PracticeSessionManager.initialize_session(exam_type, question_ids):
            flash('Failed to initialize practice session. Please try again.', 'error')
            return redirect(url_for('dashboard'))

    else:  # Premium user
        logging.info(f"Premium user, getting questions for {exam_type}")
        
        # First, try to get questions from cache
        cached_questions = CachedQuestion.query.filter(
            CachedQuestion.exam_type == exam_type,
            ~CachedQuestion.question_id.in_(session['used_questions'])
        ).limit(100).all()
        
        if cached_questions and len(cached_questions) >= 20:
            # We have enough cached questions
            logging.info(f"Using {len(cached_questions)} cached questions for premium user")
            selected = sample(cached_questions, min(50, len(cached_questions)))
            question_ids = [q.question_id for q in selected]
        else:
            # Fall back to regular questions
            questions = Question.query.filter(
                Question.exam_type == exam_type,
                ~Question.id.in_(session['used_questions'])
            ).all()

            if questions and len(questions) >= 10:
                selected = sample(questions, min(50, len(questions)))
                question_ids = [q.id for q in selected]
                logging.info(f'Selected {len(question_ids)} premium questions from main database')
                
                # Start background caching for this exam type
                for difficulty in ['easy', 'medium', 'hard']:
                    threading.Thread(
                        target=cache_questions_for_user,
                        args=(exam_type, difficulty),
                        daemon=True
                    ).start()
                logging.info(f"Started background caching for {exam_type}")
            elif cached_questions:
                # Use whatever cached questions we have
                selected = cached_questions
                question_ids = [q.question_id for q in selected]
                logging.info(f'Using limited cache of {len(question_ids)} questions')
            else:
                # Reset used questions as a last resort to prevent running out
                logging.warning(f"Running low on questions for {exam_type}, resetting used questions")
                session['used_questions'] = []
                
                # Try one more time with reset used_questions
                questions = Question.query.filter_by(exam_type=exam_type).all()
                if questions:
                    selected = sample(questions, min(30, len(questions)))
                    question_ids = [q.id for q in selected]
                    logging.info(f'Selected {len(question_ids)} premium questions after reset')
                else:
                    # Final fallback: Generate questions using Strategic AI Engine for premium users
                    try:
                        from strategic_ai_engine import StrategicAIEngine
                        engine = StrategicAIEngine()
                        
                        logging.info(f"Generating unlimited questions for premium user - {exam_type}")
                        generated_questions = engine.generate_questions(
                            exam_type=exam_type,
                            difficulty='medium',
                            topic_area='general',
                            count=50  # More questions for premium users
                        )
                        
                        if generated_questions:
                            # Convert to cached questions and save
                            premium_questions = []
                            for i, q in enumerate(generated_questions):
                                cached_q = CachedQuestion(
                                    question_id=f"premium_{exam_type}_{i}_{int(time.time())}",
                                    exam_type=exam_type,
                                    difficulty=3,
                                    question_text=q.get('question_text', ''),
                                    option_a=q.get('options', [''])[0] if q.get('options') else '',
                                    option_b=q.get('options', ['', ''])[1] if len(q.get('options', [])) > 1 else '',
                                    option_c=q.get('options', ['', '', ''])[2] if len(q.get('options', [])) > 2 else '',
                                    option_d=q.get('options', ['', '', '', ''])[3] if len(q.get('options', [])) > 3 else '',
                                    correct_answer=str(q.get('correct_answer', 0)),
                                    explanation=q.get('explanation', ''),
                                    topic_area=q.get('topic_area', 'General'),
                                    generation_request_id=None
                                )
                                premium_questions.append(cached_q)
                                
                            # Save generated questions
                            try:
                                for q in premium_questions:
                                    db.session.add(q)
                                db.session.commit()
                                logging.info(f"Generated and saved {len(premium_questions)} questions for premium user")
                                question_ids = [q.question_id for q in premium_questions]
                            except Exception as e:
                                logging.error(f"Failed to save generated questions: {e}")
                                db.session.rollback()
                                return False
                        else:
                            logging.error(f"Failed to generate questions for {exam_type}")
                            flash(f'Unable to generate questions for {exam_type}. Please try again or contact support.', 'error')
                            return redirect(url_for('dashboard'))
                            
                    except Exception as e:
                        logging.error(f"Strategic AI Engine failed: {e}")
                        flash(f'System temporarily unavailable for {exam_type}. Please try again later.', 'error')
                        return redirect(url_for('dashboard'))

    # Initialize session with proper state management for all users
    if not PracticeSessionManager.initialize_session(exam_type, question_ids):
        flash('Failed to initialize practice session. Please try again.', 'error')
        return redirect(url_for('dashboard'))
    
    # Update used questions tracking
    session['used_questions'].extend(question_ids)

    logging.info(f"Question selection completed in {time.time() - start_time:.2f}s")
    return True

@practice.route('/practice')
@login_required
@require_valid_session
def show_question():
    """Display current practice question with enhanced session validation"""
    log_session_state()
    
    # Handle navigation via URL parameters (do not clear stored answers)
    goto_param = request.args.get('goto')
    if goto_param is not None:
        try:
            target_index = int(goto_param)
        except ValueError:
            target_index = None
        if target_index is not None:
            question_ids = session.get('question_ids', [])
            if question_ids:
                max_index = len(question_ids) - 1
                if target_index < 0:
                    target_index = 0
                if target_index > max_index:
                    target_index = max_index
                session['current_index'] = target_index
                logging.debug(f"Jumping to question {target_index + 1} via goto param")
    if request.args.get('next'):
        current_index = session.get('current_index', 0)
        question_ids = session.get('question_ids', [])
        if current_index < len(question_ids) - 1:
            session['current_index'] = current_index + 1
            logging.debug(f"Moving to question {session['current_index'] + 1} of {len(question_ids)}")
            
            # Save progress to database
            from session_persistence import SessionPersistenceManager
            SessionPersistenceManager.save_session_to_db()
            
    elif request.args.get('prev'):
        current_index = session.get('current_index', 0)
        if current_index > 0:
            session['current_index'] = current_index - 1
            logging.debug(f"Moving back to question {session['current_index'] + 1}")
    
    if not PracticeSessionManager.validate_session():
        logging.error("Invalid practice session")
        flash('Your practice session was interrupted. Please start a new session.', 'warning')
        return redirect(url_for('dashboard'))

    current_index = session.get('current_index', 0)
    question_ids = session.get('question_ids', [])
    exam_type = session.get('exam_type', '')

    # Validate array bounds
    if current_index >= len(question_ids):
        logging.error(f"Index {current_index} out of bounds for {len(question_ids)} questions")
        flash('Practice session completed or corrupted. Starting fresh.', 'info')
        return redirect(url_for('dashboard'))
    
    # Get question from database with retry mechanism
    question_id = question_ids[current_index]
    
    # First check if this is a cached question ID with database retry
    try:
        cached_question = CachedQuestion.query.filter_by(question_id=question_id).first()
    except Exception as e:
        logging.error(f"Database error retrieving cached question: {e}")
        if not refresh_connection():
            flash('Database connection issue. Please try again.', 'error')
            return redirect(url_for('dashboard'))
        cached_question = CachedQuestion.query.filter_by(question_id=question_id).first()
    if cached_question:
        # Convert cached question to proper choices format
        choices = [
            cached_question.option_a,
            cached_question.option_b,
            cached_question.option_c,
            cached_question.option_d
        ]
        
        # Create a question-like object for template
        class CachedQuestionWrapper:
            def __init__(self, cached_q):
                self.id = cached_q.question_id
                self.exam_type = cached_q.exam_type
                self.difficulty = str(cached_q.difficulty)
                self.question_text = cached_q.question_text
                self.choices = choices
                self.correct_answer = cached_q.correct_answer
                self.explanation = getattr(cached_q, 'explanation', '')
                
        question = CachedQuestionWrapper(cached_question)
        logging.debug(f"Using cached question {question_id}")
    else:
        # Try to get from main database
        question = Question.query.get(question_id)
        
    if not question:
        logging.error(f"Question {question_id} not found in either cache or main db")
        return redirect(url_for('dashboard'))

    # Initialize choices as empty list if None
    if not hasattr(question, 'choices') or question.choices is None:
        # If choices are missing, try to look up the original question data
        original_question = Question.query.get(question.id)
        if original_question and hasattr(original_question, 'choices') and original_question.choices:
            question.choices = original_question.choices
            logging.debug(f"Retrieved original choices for question {question.id}")
        else:
            # If we still can't find choices, log an error - we should never show generic placeholders
            logging.error(f"CRITICAL ERROR: Question {question.id} has no choices data available")
            # Return to dashboard with error message
            flash("This question is missing answer choices. Please try another question or contact support.", "error")
            return redirect(url_for('dashboard'))

    # Parse choices from JSON if it's a string
    if isinstance(question.choices, str):
        try:
            question.choices = json.loads(question.choices)
            logging.debug(f"Successfully parsed choices JSON for question {question.id}")
        except json.JSONDecodeError:
            logging.error(f"Failed to parse choices JSON for question {question.id}: {question.choices}")
            # This is a critical error - return to dashboard with message
            flash("There was a problem loading this question. Please try another question.", "error")
            return redirect(url_for('dashboard'))
            
    # Ensure we have at least some choices - if not, this is a critical error
    if not question.choices or len(question.choices) == 0:
        logging.error(f"CRITICAL ERROR: Question {question.id} has empty choices array")
        flash("This question has no answer choices. Please try another question or contact support.", "error")
        return redirect(url_for('dashboard'))

    # Format math content for specific exam types
    if question.choices and exam_type in ['GMAT', 'MCAT', 'GRE', 'SAT']:
        logging.debug(f"Formatting math content for {exam_type} question")
        question.question_text = format_math_content(question.question_text)
        question.choices = [format_math_content(choice) for choice in question.choices]

    # Restore per-question state if previously answered
    answers_by_question = session.get('answers_by_question', {})
    feedback_by_question = session.get('feedback_by_question', {})
    question_key = str(question_id)
    user_answer = answers_by_question.get(question_key)
    feedback = feedback_by_question.get(question_key)
    show_feedback = bool(feedback)

    # Create form and set choices
    form = PracticeForm()
    choices_list = [(chr(65+i), choice) for i, choice in enumerate(question.choices)]
    # Don't set form.answer.choices directly, let the template handle it
    # form.answer.choices = choices_list  # This causes LSP errors
    form.question_id.data = question.id

    # If this is the first question, show a welcome message
    if 'buddy_message' not in session:
        session['buddy_message'] = "Welcome to your practice session! I'm your study buddy, and I'll be here to encourage you. Let's get started!"
    
    # Get streak information
    if 'current_streak' not in session:
        streak = Streak.query.filter_by(user_id=current_user.id).first()
        if streak:
            session['current_streak'] = streak.current_streak
        else:
            session['current_streak'] = 0
    
    # Get any new badges
    new_badges = session.pop('new_badges', [])
    
    logging.debug(f"Rendering question with {len(question.choices)} choices")
    
    # Get AI explanations for this question if available
    if feedback:
        tech_explanation = feedback.get('tech_explanation')
        simple_explanation = feedback.get('simple_explanation')
        session['is_correct'] = feedback.get('is_correct')
    else:
        tech_explanation = None
        simple_explanation = None
        session.pop('is_correct', None)
    
    return render_template('practice.html',
                         question=question,
                         show_feedback=show_feedback,
                         user_answer=user_answer,
                         form=form,
                         choices=choices_list,
                         buddy_message=session.get('buddy_message'),
                         streak=session.get('current_streak', 0),
                         new_badges=new_badges,
                         tech_explanation=tech_explanation,
                         simple_explanation=simple_explanation,
                         mixpanel_token=None)

@practice.route('/submit-answer', methods=['POST'])
@login_required
@require_valid_session
def submit_answer():
    """Submit answer with enhanced session validation and database retry"""
    
    if not PracticeSessionManager.validate_session():
        logging.error("Invalid session in submit_answer")
        flash('Your practice session was interrupted. Please start a new session.', 'warning')
        return redirect(url_for('dashboard'))

    answer = request.form.get('answer')
    current_index = session.get('current_index', 0)
    question_ids = session.get('question_ids', [])

    # Get question and check answer with bounds validation
    if current_index >= len(question_ids):
        logging.error(f"Index {current_index} out of bounds for {len(question_ids)} questions in submit_answer")
        flash('Practice session error. Please restart.', 'error')
        return redirect(url_for('dashboard'))
        
    question_id = question_ids[current_index]
    
    # First check if this is a cached question
    cached_question = CachedQuestion.query.filter_by(question_id=question_id).first()
    
    if cached_question:
        # Use correct answer from cached question
        correct_answer = cached_question.correct_answer
        question_text = cached_question.question_text
        
        # Handle case when cached_question.choices is None or not accessible
        try:
            choices = cached_question.choices
            # Parse choices from JSON if needed
            if isinstance(choices, str):
                try:
                    choices = json.loads(choices)
                except json.JSONDecodeError:
                    logging.error(f"Failed to parse choices JSON for cached question {question_id}")
                    choices = ["Option A", "Option B", "Option C", "Option D"]  # Fallback
            
            if choices and len(choices) > 0 and answer:
                idx = ord(answer.upper()) - ord('A')
                if 0 <= idx < len(choices):
                    user_choice = choices[idx]
                else:
                    user_choice = f"Option {answer}"
            else:
                user_choice = f"Option {answer or 'Unknown'}"
        except Exception as e:
            logging.error(f"Error accessing choices for cached question {question_id}: {str(e)}")
            user_choice = f"Option {answer}"
        
        logging.debug(f"Using cached question {question_id} for answer check")
    else:
        # Try to get from main database
        question = Question.query.get(question_id)
        if not question:
            logging.error(f"Question {question_id} not found in either cache or main db")
            return redirect(url_for('dashboard'))
        correct_answer = question.correct_answer
        question_text = question.question_text
        
        # Parse choices from JSON if needed
        try:
            choices = question.choices
            if isinstance(choices, str):
                try:
                    choices = json.loads(choices)
                except json.JSONDecodeError:
                    logging.error(f"Failed to parse choices JSON for question {question.id}")
                    choices = ["Option A", "Option B", "Option C", "Option D"]  # Fallback
            
            # Get user's selected answer text
            if choices and len(choices) > 0 and answer:
                idx = ord(answer.upper()) - ord('A')
                if 0 <= idx < len(choices):
                    user_choice = choices[idx]
                else:
                    user_choice = f"Option {answer}"
            else:
                user_choice = f"Option {answer or 'Unknown'}"
        except Exception as e:
            logging.error(f"Error accessing choices for question {question_id}: {str(e)}")
            user_choice = f"Option {answer}"
    
    # Check if answer is correct
    is_correct = (answer and correct_answer and answer.upper() == correct_answer.upper())
    logging.info(f"Submitted answer: {answer} for question {current_index + 1}")
    logging.info(f"Answer is {'correct' if is_correct else 'incorrect'}")

    # Log progress with enhanced error handling for foreign key constraints
    try:
        # First, ensure the question exists in the main question table
        question_id = question_ids[current_index]
        existing_question = Question.query.filter_by(id=question_id).first()
        
        if not existing_question and cached_question:
            # Create the question in main table on-the-fly
            new_question = Question()
            new_question.id = question_id
            new_question.exam_type = cached_question.exam_type
            new_question.question_text = cached_question.question_text
            new_question.difficulty = str(cached_question.difficulty) if cached_question.difficulty else "3"
            
            # Build choices array from cached question
            choices = [
                cached_question.option_a,
                cached_question.option_b,
                cached_question.option_c,
                cached_question.option_d
            ]
            new_question.choices = choices
            new_question.correct_answer = cached_question.correct_answer
            new_question.explanation = cached_question.explanation or "Explanation not available"
            new_question.subject = cached_question.topic_area or "General"
            new_question.is_generated = True
            new_question.generation_source = "cached_migration"
            
            db.session.add(new_question)
            db.session.commit()
            logging.info(f"Created question {question_id} in main table for progress tracking")
        
        # Now log the progress
        progress = UserProgress()
        progress.user_id = current_user.id
        progress.exam_type = session['exam_type']
        progress.question_id = question_id
        progress.answered_correctly = is_correct
        db.session.add(progress)
        db.session.commit()
        logging.debug(f"Successfully logged progress for question {question_id}")
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to log progress for question {question_ids[current_index]}: {e}")
        # Continue without blocking the user - progress logging is not critical for functionality
    
    # Check if we already have AI explanations for this question and answer correctness
    existing_explanation = AIExplanation.query.filter_by(
        question_id=question_id,
        answered_correctly=is_correct
    ).first()
    
    if existing_explanation:
        # Use existing explanation
        logging.info(f"Using existing AI explanation for question {question_id}")
        tech_explanation = existing_explanation.technical_explanation
        simple_explanation = existing_explanation.simplified_explanation
    else:
        # Generate new AI explanations
        logging.info(f"Generating new AI explanations for question {question_id}")
        try:
            tech_explanation, simple_explanation = get_dual_explanations(
                question_text, user_choice, is_correct
            )
            
            # Save the explanations to database
            new_explanation = AIExplanation()
            new_explanation.question_id = question_id
            new_explanation.answered_correctly = is_correct
            new_explanation.technical_explanation = tech_explanation
            new_explanation.simplified_explanation = simple_explanation
            db.session.add(new_explanation)
            db.session.commit()
            logging.info(f"Saved new AI explanation for question {question_id}")
            
        except Exception as e:
            logging.error(f"Failed to generate AI explanations: {str(e)}")
            # Default explanations if API fails
            tech_explanation = "Our AI explanation system is currently unavailable. Please check back later."
            simple_explanation = "We're having trouble explaining this right now. Please try another question!"
    
    # Update streak and check for badges
    streak = update_user_streak(current_user.id)
    new_badges = check_and_award_badges(current_user.id)
    
    # Generate buddy message
    buddy_message = get_encouraging_message(is_correct)
    
    # Add study tip occasionally (30% chance)
    if random.random() < 0.3:
        buddy_message += f" Tip: {get_random_study_tip()}"
    
    # Store state in session (persist per-question)
    answers_by_question = session.get('answers_by_question', {})
    feedback_by_question = session.get('feedback_by_question', {})

    q_key = str(question_id)
    answers_by_question[q_key] = answer
    feedback_by_question[q_key] = {
        'is_correct': is_correct,
        'tech_explanation': tech_explanation,
        'simple_explanation': simple_explanation
    }
    session['answers_by_question'] = answers_by_question
    session['feedback_by_question'] = feedback_by_question

    # Maintain current, user-visible session bits
    session['user_answer'] = answer
    session['show_feedback'] = True
    session['is_correct'] = is_correct
    session['buddy_message'] = buddy_message
    session['current_streak'] = streak.current_streak if streak else 1
    
    # Store new badges if any
    if new_badges:
        session['new_badges'] = [
            {
                'name': badge.name,
                'description': badge.description,
                'icon': badge.icon
            } 
            for badge in new_badges
        ]

    return redirect(url_for('practice.show_question'))

@practice.route('/previous-question')
@login_required
def previous_question():
    if 'question_ids' not in session:
        logging.error("No questions found in session for previous_question")
        return redirect(url_for('dashboard'))

    current_index = session.get('current_index', 0)
    if current_index > 0:
        session['current_index'] = current_index - 1
        logging.debug(f"Moving back to question {session['current_index'] + 1}")

    return redirect(url_for('practice.show_question'))

@practice.route('/next-question')
@login_required
def next_question():
    from session_persistence import SessionPersistenceManager
    
    if 'question_ids' not in session:
        logging.error("No questions found in session for next_question")
        return redirect(url_for('dashboard'))

    current_index = session.get('current_index', 0)
    if current_index < len(session['question_ids']) - 1:
        session['current_index'] = current_index + 1
        logging.debug(f"Moving to question {session['current_index'] + 1} of {len(session['question_ids'])}")
        
        # Save progress to database
        SessionPersistenceManager.save_session_to_db()
    else:
        # End of questions - mark session as completed
        logging.debug("Reached end of question batch")
        SessionPersistenceManager.mark_session_completed()
        
        # Update trial usage for non-premium users
        exam_type = session.get('exam_type')
        if exam_type and (not current_user.subscription or not current_user.subscription.active):
            questions_answered = len(session.get('question_ids', []))
            SessionPersistenceManager.update_trial_usage(exam_type, questions_answered)
        
        flash('Practice session complete!', 'success')
        return redirect(url_for('dashboard'))

    return redirect(url_for('practice.show_question'))

@practice.route('/exit-practice')
@login_required
def exit_practice():
    """Handle practice session exit with session preservation"""
    from session_persistence import SessionPersistenceManager
    
    try:
        # Save current session progress before exiting
        session_id = SessionPersistenceManager.save_session_to_db()
        if session_id:
            logging.info(f"Saved practice session {session_id} before exit")
            flash('Your progress has been saved! You can resume anytime.', 'info')
        
        # Update trial usage if user made progress
        exam_type = session.get('exam_type')
        current_index = session.get('current_index', 0)
        
        if exam_type and current_index > 0 and (not current_user.subscription or not current_user.subscription.active):
            # User answered some questions before exiting
            SessionPersistenceManager.update_trial_usage(exam_type, current_index)
            logging.debug(f"Updated trial usage: {current_index} questions for {exam_type}")
        
        # Clear volatile session data but preserve saved session ID
        volatile_keys = ['show_feedback', 'user_answer', 'tech_explanation', 'simple_explanation']
        for key in volatile_keys:
            session.pop(key, None)
        
        logging.info(f"User {current_user.id} exited practice session for {exam_type}")
        
    except Exception as e:
        logging.error(f"Error saving session on exit: {e}")
        flash('Session ended. You can start a new practice anytime!', 'info')
    
    return redirect(url_for('dashboard'))

@practice.route('/submit-contest', methods=['POST'])
@login_required  
def submit_contest():
    """Handle answer contest submissions from users"""
    try:
        question_id = request.form.get('question_id')
        user_answer = request.form.get('user_answer')
        correct_answer = request.form.get('correct_answer')
        user_work = request.form.get('user_work', '').strip()
        reason = request.form.get('reason', '').strip()
        exam_type = session.get('exam_type', 'Unknown')
        
        # Validation
        if not all([question_id, user_answer, correct_answer, user_work]):
            flash('Please provide your work and explanation to contest this answer.', 'error')
            return redirect(url_for('practice.show_question'))
        
        if len(user_work) < 10:
            flash('Please provide more detailed work showing your solution process.', 'error')
            return redirect(url_for('practice.show_question'))
        
        # Check if user already contested this question
        from models import AnswerContest
        existing_contest = AnswerContest.query.filter_by(
            user_id=current_user.id,
            question_id=question_id
        ).first()
        
        if existing_contest:
            flash('You have already submitted a contest for this question. Check your profile for updates.', 'info')
            return redirect(url_for('practice.show_question'))
        
        # Create new contest submission
        contest = AnswerContest(
            user_id=current_user.id,
            question_id=question_id,
            exam_type=exam_type,
            user_answer=user_answer,
            correct_answer=correct_answer,
            user_work=user_work,
            reason=reason,
            status='pending'
        )
        
        db.session.add(contest)
        db.session.commit()
        
        logging.info(f"Contest submitted by user {current_user.id} for question {question_id}")
        flash('Contest submitted successfully! We will review your work and respond within 24-48 hours.', 'success')
        
        # Add contest submission to session for immediate feedback
        session['contest_submitted'] = True
        
    except Exception as e:
        logging.error(f"Error submitting contest: {e}")
        db.session.rollback()
        flash('Failed to submit contest. Please try again.', 'error')
    
    return redirect(url_for('practice.show_question'))

def update_user_streak(user_id):
    """Update the user's streak"""
    today = date.today()
    
    # Get or create user streak
    streak = Streak.query.filter_by(user_id=user_id).first()
    if not streak:
        streak = Streak()
        streak.user_id = user_id
        streak.current_streak = 1
        streak.longest_streak = 1
        streak.last_activity_date = today
        db.session.add(streak)
        db.session.commit()
        return streak
    
    # If last activity was yesterday, increment streak
    if streak.last_activity_date:
        delta = (today - streak.last_activity_date).days
        
        if delta == 1:  # Consecutive day
            streak.current_streak += 1
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
        elif delta > 1:  # Streak broken
            streak.current_streak = 1
        # If delta == 0, user already practiced today, no need to update streak
    
    streak.last_activity_date = today
    db.session.commit()
    
    return streak

def check_and_award_badges(user_id):
    """Check if user has earned any new badges"""
    new_badges = []
    
    # Check questions answered badges
    questions_answered = UserProgress.query.filter_by(user_id=user_id).count()
    question_badges = Badge.query.filter_by(criteria='questions_answered').all()
    
    for badge in question_badges:
        if questions_answered >= badge.threshold:
            # Check if user already has this badge
            existing = UserBadge.query.filter_by(user_id=user_id, badge_id=badge.id).first()
            if not existing:
                new_badge = UserBadge()
                new_badge.user_id = user_id
                new_badge.badge_id = badge.id
                db.session.add(new_badge)
                new_badges.append(badge)
    
    # Check streak badges
    streak = Streak.query.filter_by(user_id=user_id).first()
    if streak:
        streak_badges = Badge.query.filter_by(criteria='streak').all()
        for badge in streak_badges:
            if streak.current_streak >= badge.threshold:
                existing = UserBadge.query.filter_by(user_id=user_id, badge_id=badge.id).first()
                if not existing:
                    new_badge = UserBadge()
                    new_badge.user_id = user_id
                    new_badge.badge_id = badge.id
                    db.session.add(new_badge)
                    new_badges.append(badge)
    
    # Check accuracy badges
    total_answers = UserProgress.query.filter_by(user_id=user_id).count()
    if total_answers >= 10:  # Only check accuracy after at least 10 questions
        correct_answers = UserProgress.query.filter_by(user_id=user_id, answered_correctly=True).count()
        accuracy = (correct_answers / total_answers) * 100
        
        accuracy_badges = Badge.query.filter_by(criteria='accuracy').all()
        for badge in accuracy_badges:
            if accuracy >= badge.threshold:
                existing = UserBadge.query.filter_by(user_id=user_id, badge_id=badge.id).first()
                if not existing:
                    new_badge = UserBadge()
                    new_badge.user_id = user_id
                    new_badge.badge_id = badge.id
                    db.session.add(new_badge)
                    new_badges.append(badge)
    
    # Check perfect session badges (10+ questions with 100% accuracy in a row)
    # This would typically be checked after a practice session
    
    if new_badges:
        db.session.commit()
    
    return new_badges

def get_buddy_message(is_correct):
    """Get an encouraging message from the study buddy"""
    if is_correct:
        return random.choice(CORRECT_MESSAGES)
    else:
        return random.choice(INCORRECT_MESSAGES)

def cache_questions_for_user(exam_type, difficulty):
    """Background task to cache questions for premium users"""
    try:
        # Set a higher limit for scalability (support 1B users)
        MAX_CACHE_LIMIT = 1000000  # 1 million questions in cache
        QUESTIONS_PER_BATCH = 100  # Process in batches for better performance
        
        # Use a DB session specific to this thread to avoid conflicts
        with app.app_context():
            # Check if we've hit the cache limit
            total_cached = db.session.query(func.count(CachedQuestion.id)).scalar()
            if total_cached >= MAX_CACHE_LIMIT:
                logging.info(f'Cache limit reached ({MAX_CACHE_LIMIT:,} questions)')
                return

            logging.info(f'Starting background caching for {exam_type} ({difficulty})')

            # Get existing cached questions count for this type/difficulty
            existing = db.session.query(func.count(CachedQuestion.id)).filter_by(
                exam_type=exam_type,
                difficulty=difficulty
            ).scalar()

            # Set a target count based on exam popularity
            target_count = 100  # Default target cache size per exam type/difficulty

            if existing < target_count:
                # Get questions that aren't already cached
                subquery = db.session.query(CachedQuestion.question_id).filter_by(
                    exam_type=exam_type,
                    difficulty=difficulty
                ).subquery()
                
                questions = Question.query.filter_by(
                    exam_type=exam_type,
                    difficulty=difficulty
                ).filter(~Question.id.in_(subquery)).limit(QUESTIONS_PER_BATCH).all()

                if questions:
                    questions_to_cache = min(target_count - existing, len(questions))
                    
                    # If we have more questions than needed, select randomly
                    if len(questions) > questions_to_cache:
                        selected = sample(questions, questions_to_cache)
                    else:
                        selected = questions

                    # Process in smaller transactions for better performance
                    for i in range(0, len(selected), 20):
                        batch = selected[i:i+20]
                        
                        for question in batch:
                            # Check if we've hit the cache limit during processing
                            if db.session.query(func.count(CachedQuestion.id)).scalar() >= MAX_CACHE_LIMIT:
                                logging.info('Cache limit reached during caching')
                                db.session.commit()
                                return

                            # Ensure choices are properly loaded
                            choices = question.choices
                            if isinstance(choices, str):
                                try:
                                    choices = json.loads(choices)
                                except json.JSONDecodeError:
                                    logging.error(f"Failed to parse choices JSON for question {question.id}")
                                    continue

                            # Create cached question with proper error handling
                            try:
                                cached = CachedQuestion()
                                cached.question_id = question.id
                                cached.exam_type = question.exam_type
                                cached.difficulty = 3  # Use integer difficulty
                                cached.question_text = question.question_text
                                cached.choices = choices
                                cached.correct_answer = question.correct_answer
                                db.session.add(cached)
                            except Exception as e:
                                logging.error(f"Error caching question {question.id}: {str(e)}")
                                continue

                        # Commit each batch separately
                        db.session.commit()
                        logging.info(f'Cached {len(batch)} questions (batch)')
                    
                    logging.info(f'Completed caching {questions_to_cache} new questions for {exam_type} ({difficulty})')

    except Exception as e:
        logging.error(f'Error during background caching: {str(e)}')
        db.session.rollback()