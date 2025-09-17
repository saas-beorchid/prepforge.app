import os
# Load environment variables from .env if present (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env")
except ImportError:
    print("⚠️  python-dotenv not installed; .env will not be loaded automatically.")
import json
from random import sample
from datetime import timedelta, datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from sqlalchemy.orm import DeclarativeBase
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired
import logging
import stripe
import threading

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

app = Flask(__name__)
# CRITICAL FIX: Force ASCII-only session secret to prevent Unicode encoding errors
# The SESSION_SECRET from Replit Secrets contains unicode characters that break Flask-Login
# Force use of ASCII-safe secret regardless of environment
session_secret = "56466b068d201ac13889faf784afe536bbeacb9159d91938794d1daba6f899d4"
app.secret_key = session_secret
app.config['SECRET_KEY'] = session_secret

# Log the fix
logging.info(f"🔧 FIXED: Using ASCII-safe SESSION_SECRET (length: {len(session_secret)}, ASCII: {session_secret.isascii()})")

# Temporarily disable CSRF for testing purposes
app.config['WTF_CSRF_ENABLED'] = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

# Enhanced connection pool settings for SSL stability and high performance
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": 15,  # Optimized pool size for stability
    "max_overflow": 25,  # Conservative overflow to prevent SSL drops
    "pool_recycle": 180,  # More frequent recycle to prevent SSL timeouts (3 minutes)
    "pool_pre_ping": True,  # Test connections before using them
    "pool_timeout": 20,  # Faster timeout to detect issues quickly
    "pool_reset_on_return": "commit",  # Reset connections to clean state
    "connect_args": {
        "sslmode": "require",
        "connect_timeout": 10,
        "application_name": "PrepForge_App"
    }
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Enhanced session configuration for better security and user experience
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True  # Use secure cookies in production

# Register chr and ord functions as Jinja2 filters
app.jinja_env.filters['chr'] = chr
app.jinja_env.filters['ord'] = ord

# Configure Stripe - Load from .env file
def load_env_var(key):
    """Load environment variable from .env file"""
    value = os.environ.get(key)
    if value:
        return value
    
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(f'{key}='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        logging.error(f"❌ Could not load {key} from .env: {e}")
    
    return None

stripe.api_key = load_env_var('STRIPE_SECRET_KEY')
if stripe.api_key:
    logging.info("✅ Stripe API key loaded successfully")
else:
    logging.error("❌ STRIPE_SECRET_KEY not found - Stripe integration will not work")

# Configure Mixpanel
MIXPANEL_TOKEN = os.environ.get('MIXPANEL_TOKEN')

@app.context_processor
def inject_mixpanel_token():
    """Make Mixpanel token available in all templates"""
    return dict(mixpanel_token=MIXPANEL_TOKEN)

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.signin'

@login_manager.user_loader
def load_user(id):
    from models import User
    return User.query.get(int(id))

@app.before_request
def make_session_permanent():
    """Enhanced session management with practice state preservation"""
    session.permanent = True
    
    # Ensure session has required keys for practice flow
    if current_user.is_authenticated:
        logging.debug(f"Session active for user_id {current_user.id}")
        
        # Initialize practice session keys if missing
        if 'used_questions' not in session:
            session['used_questions'] = []
        if 'session_stats' not in session:
            session['session_stats'] = {
                'questions_answered': 0,
                'correct_answers': 0,
                'session_start': None
            }

def preload_questions():
    """Preload 100 questions per exam type into the database"""
    from models import Question
    exam_types = [
        'USMLE_STEP_1', 'USMLE_STEP_2', 'NCLEX', 'GRE', 'GMAT',
        'MCAT', 'IELTS', 'TOEFL', 'SAT', 'ACT', 'PMP', 'CFA'
    ]

    with app.app_context():
        for exam_type in exam_types:
            questions = Question.query.filter_by(exam_type=exam_type).all()
            if questions:
                count = len(questions)
                logging.info(f"Preloaded {count} questions for {exam_type}")
            else:
                logging.warning(f"No questions found for {exam_type}")

class ExamForm(FlaskForm):
    exam_type = SelectField('Exam Type', choices=[
        ('', 'Select an exam type...'),
        ('GRE', 'GRE - Graduate Record Examination'),
        ('GMAT', 'GMAT - Graduate Management Admission Test'),
        ('MCAT', 'MCAT - Medical College Admission Test'),
        ('USMLE_STEP_1', 'USMLE Step 1 - Medical Licensing'),
        ('USMLE_STEP_2', 'USMLE Step 2 - Medical Licensing'),
        ('NCLEX', 'NCLEX - Nursing Licensure'),
        ('LSAT', 'LSAT - Law School Admission Test'),
        ('SAT', 'SAT - Scholastic Assessment Test'),
        ('ACT', 'ACT - American College Testing'),
        ('IELTS', 'IELTS - English Language Testing'),
        ('TOEFL', 'TOEFL - English as Foreign Language'),
        ('PMP', 'PMP - Project Management Professional'),
        ('CFA', 'CFA - Chartered Financial Analyst')
    ], validators=[DataRequired()])
    submit = SubmitField('Start Practice')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quiz')
@login_required
def quiz():
    """Interactive quiz page with API integration"""
    try:
        from subscription_gate import get_trial_remaining
        trial_remaining = get_trial_remaining(current_user.id) if hasattr(current_user, 'subscription_plan') and current_user.subscription_plan == 'free' else None
    except Exception as e:
        logging.warning(f"Could not get trial remaining: {e}")
        trial_remaining = 20  # Default for free users
    
    return render_template('quiz.html',
                         trial_remaining=trial_remaining,
                         mixpanel_token=os.environ.get('MIXPANEL_TOKEN'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get user stats from buddy module
    from buddy import get_user_stats
    from session_persistence import SessionPersistenceManager
    
    stats = get_user_stats(current_user.id)
    
    # Check for incomplete sessions to offer resumption
    incomplete_sessions = SessionPersistenceManager.get_incomplete_sessions()
    
    # Try to restore session if user just logged in
    if not session.get('session_initialized') and incomplete_sessions:
        session_restored = SessionPersistenceManager.restore_session_from_db()
        if session_restored:
            flash('Welcome back! Your previous session has been restored.', 'info')
    
    form = ExamForm()
    return render_template('dashboard.html', 
                         form=form, 
                         stats=stats,
                         incomplete_sessions=incomplete_sessions)

@app.route('/resume-session', methods=['POST'])
@login_required
def resume_session():
    """Resume a saved practice session"""
    from session_persistence import SessionPersistenceManager
    from models import PracticeSession
    
    session_id = request.form.get('session_id')
    if not session_id:
        flash('Invalid session ID.', 'error')
        return redirect(url_for('dashboard'))
    
    # Verify session belongs to current user
    practice_session = PracticeSession.query.filter_by(
        id=session_id,
        user_id=current_user.id,
        completed=False
    ).first()
    
    if not practice_session:
        flash('Session not found or already completed.', 'error')
        return redirect(url_for('dashboard'))
    
    # Restore session data
    session['persistent_session_id'] = practice_session.id
    session['exam_type'] = practice_session.exam_type
    session['question_ids'] = practice_session.question_ids
    session['current_index'] = practice_session.current_index
    session['session_stats'] = practice_session.session_stats or {}
    session['session_initialized'] = True
    session['show_feedback'] = False
    
    flash(f'Resumed your {practice_session.exam_type} session!', 'success')
    return redirect(url_for('practice.show_question'))

@app.route('/pricing')
@login_required
def pricing():
    return render_template('pricing.html')

@app.route('/start-trial', methods=['POST'])
@login_required
def start_trial():
    """Activate a 7-day free trial for the user"""
    try:
        from models import User, db
        
        # Check if user already has an active trial or subscription
        if current_user.has_active_trial():
            flash('You already have an active trial!', 'info')
            return redirect(url_for('dashboard'))
        
        if current_user.subscription and current_user.subscription.active:
            flash('You already have a Pro subscription!', 'info') 
            return redirect(url_for('dashboard'))
            
        # Start the 7-day trial
        current_user.start_trial(duration_days=7)
        db.session.commit()
        
        # Log the trial activation
        logging.info(f"✅ Started 7-day trial for user {current_user.id}")
        
        flash('🎉 Your 7-day free trial has started! You now have Pro access for 7 days.', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"❌ Error starting trial for user {current_user.id}: {e}")
        flash('Failed to start trial. Please try again.', 'error')
        return redirect(url_for('pricing'))

@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        # Ensure Stripe API key is loaded
        if not stripe.api_key:
            stripe.api_key = load_env_var('STRIPE_SECRET_KEY')
            if not stripe.api_key:
                logging.error("❌ STRIPE_SECRET_KEY not available at checkout time")
                flash('Payment system is temporarily unavailable. Please try again later.', 'error')
                return redirect(url_for('quiz'))
            else:
                logging.info("✅ Stripe API key reloaded for checkout session")
        
        logging.info(f"Creating checkout session for user {current_user.id}")
        
        # First check if we already have a product or need to create one
        products = stripe.Product.list(limit=100)
        product_id = None
        
        # Find existing product
        for product in products.data:
            if product.name == 'PrepForge Pro Subscription':
                product_id = product.id
                app.logger.info(f'Found existing product: {product_id}')
                break
                
        # Create product if not found
        if not product_id:
            product = stripe.Product.create(
                name='PrepForge Pro Subscription',
                description='Unlimited access to all practice questions'
            )
            product_id = product.id
            app.logger.info(f'Created new product: {product_id}')

        # Check for existing price
        prices = stripe.Price.list(product=product_id, limit=100)
        price_id = None
        
        # Find existing price
        for price in prices.data:
            if price.unit_amount == 1500 and price.currency == 'usd' and price.recurring.interval == 'month':
                price_id = price.id
                app.logger.info(f'Found existing price: {price_id}')
                break
                
        # Create price if not found
        if not price_id:
            price = stripe.Price.create(
                unit_amount=1500,  # $15.00
                currency='usd',
                recurring={"interval": "month"},
                product=product_id,
            )
            price_id = price.id
            app.logger.info(f'Created new price: {price_id}')

        # Look for existing customer
        from models import Subscription
        subscription = Subscription.query.filter_by(user_id=current_user.id).first()
        customer_id = None
        
        if subscription and subscription.stripe_customer_id:
            customer_id = subscription.stripe_customer_id
            app.logger.info(f'Using existing customer: {customer_id}')
            
        # Create Checkout Session for embedded checkout
        checkout_session = stripe.checkout.Session.create(
            ui_mode='embedded',  # Enable embedded checkout
            payment_method_types=['card'],
            customer=customer_id if customer_id else None,  # Pass existing customer ID if available
            customer_email=current_user.email if not customer_id else None,  # Only use if no customer exists
            client_reference_id=str(current_user.id),  # Add user ID reference
            metadata={
                'user_id': current_user.id,
                'user_email': current_user.email
            },
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            return_url=request.host_url + 'return?session_id={CHECKOUT_SESSION_ID}',
        )

        # Store session ID temporarily for verification
        session['checkout_session_id'] = checkout_session.id
        app.logger.info(f'Created checkout session {checkout_session.id} for user {current_user.id}')
        
        # Return client secret for embedded checkout
        return jsonify({
            'success': True,
            'client_secret': checkout_session.client_secret,
            'session_id': checkout_session.id
        })
    except Exception as e:
        app.logger.error(f'Error creating checkout session: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/return')
def return_page():
    session_id = request.args.get('session_id')
    
    if session_id:
        try:
            # Retrieve the session to check its status
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            
            if checkout_session.status == 'complete':
                return render_template('success.html', session=checkout_session)
            else:
                return render_template('cancel.html', session=checkout_session)
        except Exception as e:
            app.logger.error(f'Error retrieving session: {e}')
            return render_template('cancel.html', error='Session not found')
    
    return render_template('cancel.html', error='No session ID provided')


@app.route('/ai-dashboard')
@login_required
def ai_dashboard():
    """Strategic AI Engine Dashboard - Redirect to admin panel"""
    return redirect(url_for('admin.admin_dashboard'))

@app.route('/cancel-subscription')
@login_required
def cancel_subscription():
    """Cancel the user's subscription in Stripe"""
    from models import Subscription
    
    user_id = current_user.id
    subscription = Subscription.query.filter_by(user_id=user_id).first()
    
    if subscription and subscription.active and subscription.stripe_customer_id:
        try:
            # Get all the customer's subscriptions
            subscriptions = stripe.Subscription.list(
                customer=subscription.stripe_customer_id,
                status="active",
                limit=1
            )
            
            # Cancel each active subscription
            for stripe_sub in subscriptions.auto_paging_iter():
                stripe.Subscription.modify(stripe_sub.id, cancel_at_period_end=True)
            
            # Update the database
            subscription.active = False
            subscription.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash('Your subscription has been canceled successfully.', 'success')
        except Exception as e:
            print(f"Error canceling subscription: {str(e)}")
            flash('There was an error processing your request. Please try again.', 'error')
    else:
        flash('No active subscription found.', 'warning')
    
    return redirect(url_for('profile'))


@app.route('/payment-success')
@login_required
def payment_success():
    from models import Subscription
    
    # Get checkout session ID from session if available
    checkout_session_id = session.get('checkout_session_id')
    
    try:
        if checkout_session_id:
            # Retrieve session data from Stripe to confirm it's valid
            checkout_session = stripe.checkout.Session.retrieve(checkout_session_id)
            
            # Check if this session belongs to the current user
            if str(checkout_session.metadata.get('user_id')) == str(current_user.id):
                # Get the customer ID from the session
                customer_id = checkout_session.customer
                
                # Create or update subscription
                from models import Subscription
                subscription = Subscription.query.filter_by(user_id=current_user.id).first()
                if not subscription:
                    subscription = Subscription(
                        user_id=current_user.id, 
                        stripe_customer_id=customer_id,
                        active=True
                    )
                    db.session.add(subscription)
                    app.logger.info(f"Created new subscription for user {current_user.id} with customer ID {customer_id}")
                else:
                    subscription.active = True
                    # Only update the customer_id if it was previously empty
                    if not subscription.stripe_customer_id:
                        subscription.stripe_customer_id = customer_id
                    app.logger.info(f"Updated subscription for user {current_user.id}")
                
                db.session.commit()
                
                # Clear the checkout session from our flask session
                session.pop('checkout_session_id', None)
                
                flash('Your premium subscription has been activated!', 'success')
            else:
                app.logger.warning(f"User ID mismatch: {checkout_session.metadata.get('user_id')} vs {current_user.id}")
        else:
            # Fallback for direct access to payment-success (without session ID)
            app.logger.warning("No checkout session ID in session, performing basic subscription activation")
            from models import Subscription
            subscription = Subscription.query.filter_by(user_id=current_user.id).first()
            if not subscription:
                subscription = Subscription(user_id=current_user.id, active=True)
                db.session.add(subscription)
            else:
                subscription.active = True
            db.session.commit()
            
    except Exception as e:
        app.logger.error(f"Error processing payment success: {str(e)}")
        flash('There was an issue activating your subscription. Please contact support.', 'error')
    
    # After subscription activation, restore any preserved session
    from session_persistence import SessionPersistenceManager
    if session.get('preserve_session') == 'true':
        session_restored = SessionPersistenceManager.restore_session_from_db()
        if session_restored:
            flash('Welcome to PrepForge Pro! Your session has been restored.', 'success')
            return redirect(url_for('practice.show_question'))
    
    return redirect(url_for('dashboard'))

@app.route('/start-practice', methods=['POST'])
@login_required
def start_practice():
    from models import UserProgress
    from session_persistence import SessionPersistenceManager
    
    form = ExamForm()
    if form.validate_on_submit():
        exam_type = form.exam_type.data
        logging.debug(f"Selected exam type: {exam_type}")

        # Get comprehensive trial status using new system
        trial_status = SessionPersistenceManager.get_trial_status(exam_type)
        
        if not trial_status['can_start_session']:
            # Trial limit reached - show enhanced completion page
            from buddy import get_user_stats
            stats = get_user_stats(current_user.id)
            
            # Get exam-specific stats
            exam_progress = UserProgress.query.filter_by(
                user_id=current_user.id,
                exam_type=exam_type
            ).all()
            
            exam_stats = {
                'questions_completed': len(exam_progress),
                'correct_answers': len([p for p in exam_progress if p.answered_correctly]),
                'accuracy': round((len([p for p in exam_progress if p.answered_correctly]) / len(exam_progress) * 100), 1) if exam_progress else 0
            }
            
            # Check if there's a current session to preserve
            current_session = None
            incomplete_sessions = SessionPersistenceManager.get_incomplete_sessions()
            if incomplete_sessions:
                current_session = incomplete_sessions[0]  # Most recent
            
            # Save any current session before redirecting
            SessionPersistenceManager.save_session_to_db()
            
            return render_template('trial_completion.html',
                                 exam_type=exam_type,
                                 stats=stats,
                                 exam_stats=exam_stats,
                                 current_session=current_session,
                                 session_preserved=current_session is not None,
                                 achievements=['First Steps', 'Question Explorer', 'Knowledge Seeker'])

        from practice import get_practice_questions
        result = get_practice_questions(exam_type)

        # Handle different return types from get_practice_questions
        if result and result is not True:  # Check for redirect response
            return result  # Return the redirect to dashboard with error message
        elif result is True:  # Success case
            # Save session to database for persistence
            SessionPersistenceManager.save_session_to_db()
            logging.debug(f"Session keys: {list(session.keys())}")
            return redirect(url_for('practice.show_question'))
        else:
            logging.error("Failed to load practice questions")
            flash(f'Unable to load practice questions for {exam_type}. Our AI system may be generating new content - please try again in a moment.', 'error')
            return redirect(url_for('dashboard'))

    logging.error("Form validation failed")
    logging.debug(f"Form errors: {form.errors}")
    return redirect(url_for('dashboard'))

@app.route('/profile')
@login_required
def profile():
    # Get user progress statistics
    from models import UserProgress
    progress = UserProgress.query.filter_by(user_id=current_user.id).all()
    total_questions = len(progress)

    # Calculate stats per exam type
    stats = {}
    for exam_type in ['USMLE_STEP_1', 'USMLE_STEP_2', 'GRE', 'GMAT', 'MCAT']:
        exam_progress = [p for p in progress if p.exam_type == exam_type]
        if exam_progress:
            correct = len([p for p in exam_progress if p.answered_correctly])
            total = len(exam_progress)
            percentage = (correct / total) * 100
            stats[exam_type] = {
                'total': total,
                'correct': correct,
                'percentage': round(percentage, 1)
            }

    return render_template('profile.html', 
                         stats=stats, 
                         total_questions=total_questions,
                         subscription=current_user.subscription,
                         name=current_user.name)


@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if name and name != current_user.name:
            current_user.name = name
            logging.info(f"Saved name: {name} for user_id {current_user.id}")

        if email and email != current_user.email:
            # Check if email already exists
            from models import User
            if User.query.filter_by(email=email).first():
                flash('Email already exists', 'error')
                return redirect(url_for('profile'))
            current_user.email = email

        if new_password:
            if new_password != confirm_password:
                flash('Passwords do not match', 'error')
                return redirect(url_for('profile'))
            current_user.set_password(new_password)

        db.session.commit()
        flash('Profile updated successfully', 'success')
    return redirect(url_for('profile'))

@app.route('/update_name', methods=['POST'])
@login_required
def update_name():
    if request.method == 'POST':
        user_name = request.form.get('user_name')
        if user_name:
            session['user_name'] = user_name
            flash('Name updated successfully', 'success')
        return redirect(url_for('dashboard'))

# Add these new routes after the existing routes
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy-policy')
def privacy_policy():
    with open('attached_assets/Pasted-PRIVACY-POLICY-Effective-Date-February-24th-2025-Last-Updated-February-24th-2025-1-INTRODUCTION-1741243142018.txt', 'r') as f:
        content = f.read().replace('\n', '<br>')
    return render_template('privacy_policy.html', content=content)

@app.route('/terms')
def terms():
    with open('attached_assets/Pasted-TERMS-OF-SERVICE-AGREEMENT-Effective-Date-February-24th-2025-Last-Updated-February-24th-2025-1--1741243116812.txt', 'r') as f:
        content = f.read().replace('\n', '<br>')
    return render_template('terms.html', content=content)


@app.route('/profile/history')
@login_required
def question_history():
    from models import UserProgress, Question, CachedQuestion

    # Get user's question history with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20

    progress = UserProgress.query.filter_by(user_id=current_user.id)\
        .order_by(UserProgress.timestamp.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    history = []
    for p in progress.items:
        # Try to get question from cache first
        question = CachedQuestion.query.filter_by(question_id=p.question_id).first()
        if not question:
            # Fallback to main database
            question = Question.query.get(p.question_id)

        if question:
            history.append({
                'question_text': question.question_text,
                'options': question.choices if hasattr(question, 'choices') else question.options,
                'correct_answer': question.correct_answer,
                'user_answer': p.answered_correctly,
                'timestamp': p.timestamp,
                'exam_type': p.exam_type
            })

    return render_template('profile_history.html',
                         history=history,
                         pagination=progress)

# Stripe webhook endpoint for handling payment events
@app.route('/webhook', methods=['POST'])
def webhook():
    # Get the webhook signature header from Stripe
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    payload = request.data.decode('utf-8')
    sig_header = request.headers.get('Stripe-Signature')
    event = None

    try:
        if webhook_secret:
            # Verify webhook signature and extract the event
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        else:
            # When testing, webhook_secret may not be available
            # Don't use this in production
            app.logger.warning("Webhook secret not found, parsing data directly (unsafe for production)")
            data = json.loads(payload)
            event = stripe.Event.construct_from(data, stripe.api_key)
            
        app.logger.info(f"Webhook received: {event.type}")
    except ValueError as e:
        # Invalid payload
        app.logger.error(f"Webhook ValueError: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        app.logger.error(f"Webhook SignatureVerificationError: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        app.logger.error(f"Webhook general error: {str(e)}")
        return jsonify({'error': str(e)}), 400

    # Handle the event
    if event.type == 'checkout.session.completed':
        session = event.data.object  # contains a stripe.checkout.Session
        client_reference_id = session.get('client_reference_id')
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        
        if client_reference_id:
            try:
                from models import User, Subscription
                # Convert client_reference_id to int (user_id)
                user_id = int(client_reference_id)
                
                # Find the user
                user = User.query.get(user_id)
                if user:
                    # CRITICAL: Update user subscription_plan to 'pro'
                    user.subscription_plan = 'pro'
                    app.logger.info(f"✅ Updated user {user_id} subscription_plan to 'pro'")
                    
                    # Update or create subscription record
                    subscription = Subscription.query.filter_by(user_id=user_id).first()
                    if not subscription:
                        subscription = Subscription(
                            user_id=user_id,
                            stripe_customer_id=customer_id,
                            active=True
                        )
                        db.session.add(subscription)
                        app.logger.info(f"Created subscription for user {user_id} via webhook")
                    else:
                        subscription.active = True
                        if not subscription.stripe_customer_id and customer_id:
                            subscription.stripe_customer_id = customer_id
                        app.logger.info(f"Updated subscription for user {user_id} via webhook")
                        
                    db.session.commit()
                    app.logger.info(f"🎉 UPGRADE COMPLETE: User {user_id} is now Pro subscriber")
                else:
                    app.logger.error(f"User {user_id} not found for checkout.session.completed event")
            except Exception as e:
                app.logger.error(f"Error processing checkout.session.completed: {str(e)}")
                db.session.rollback()
        else:
            app.logger.warning("checkout.session.completed event missing client_reference_id")
    
    elif event.type == 'customer.subscription.updated':
        subscription = event.data.object
        customer_id = subscription.customer
        
        try:
            from models import Subscription
            # Find subscriptions matching this customer ID
            db_subscription = Subscription.query.filter_by(stripe_customer_id=customer_id).first()
            
            if db_subscription:
                # Check subscription status
                status = subscription.status
                if status in ['active', 'trialing']:
                    db_subscription.active = True
                else:
                    db_subscription.active = False
                
                db.session.commit()
                app.logger.info(f"Updated subscription status to {status} for customer {customer_id}")
            else:
                app.logger.warning(f"No subscription found for customer {customer_id}")
        except Exception as e:
            app.logger.error(f"Error processing customer.subscription.updated: {str(e)}")
            db.session.rollback()
            
    elif event.type == 'customer.subscription.deleted':
        subscription = event.data.object
        customer_id = subscription.customer
        
        try:
            from models import Subscription
            # Find subscriptions matching this customer ID
            db_subscription = Subscription.query.filter_by(stripe_customer_id=customer_id).first()
            
            if db_subscription:
                db_subscription.active = False
                db.session.commit()
                app.logger.info(f"Deactivated subscription for customer {customer_id}")
            else:
                app.logger.warning(f"No subscription found for customer {customer_id}")
        except Exception as e:
            app.logger.error(f"Error processing customer.subscription.deleted: {str(e)}")
            db.session.rollback()

    return render_template('webhook_success.html', message="Webhook received successfully"), 200

# Error Handlers with Humor
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error_pages/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error_pages/500.html'), 500

# Register blueprints
from auth import auth as auth_blueprint
from practice import practice as practice_blueprint
from buddy import buddy as buddy_blueprint, initialize_badges
from admin import admin as admin_blueprint
app.register_blueprint(auth_blueprint)
app.register_blueprint(practice_blueprint)
app.register_blueprint(buddy_blueprint)
app.register_blueprint(admin_blueprint)

# Register social learning blueprint
from social import social
app.register_blueprint(social)

# Register AI Question API blueprint (imported safely at runtime)
try:
    from ai_question_api import ai_question_bp
    app.register_blueprint(ai_question_bp)
    logging.info("✅ AI Question API blueprint registered successfully")
except Exception as e:
    logging.warning(f"⚠️ Failed to register AI Question API blueprint: {e}")

# Register Quiz API blueprint
try:
    from quiz_api import quiz_api
    app.register_blueprint(quiz_api)
    logging.info("✅ Quiz API blueprint registered successfully")
except Exception as e:
    logging.warning(f"⚠️ Failed to register Quiz API blueprint: {e}")

# Initialize subscription gate system with proper app context
try:
    from subscription_gate import init_subscription_gate
    init_subscription_gate(app)
    logging.info("✅ Subscription gate initialized successfully")
except Exception as e:
    logging.warning(f"⚠️ Failed to initialize subscription gate: {e}")

def initialize_cache():
    """Initialize the comprehensive question availability system"""
    logging.info("🚀 Starting comprehensive question availability system")
    
    # Import and initialize the new comprehensive system
    try:
        from comprehensive_question_availability_system import initialize_comprehensive_system
        initialize_comprehensive_system()
        logging.info("✅ Comprehensive question availability system initialized successfully")
    except Exception as e:
        logging.error(f"❌ Failed to initialize comprehensive system: {e}")
        
        # Fallback to old system
        logging.info("🔄 Falling back to legacy cache initialization")
        _legacy_cache_initialization()

def _legacy_cache_initialization():
    """Legacy cache initialization as fallback"""
    with app.app_context():
        from models import Question, CachedQuestion
        from random import sample
        logging.info("Starting legacy cache initialization")

        try:
            # Check current cache size
            cache_count = CachedQuestion.query.count()
            logging.info(f"Current cache size: {cache_count} questions")

            if cache_count < 200000:
                # Get all exam types
                exam_types = db.session.query(Question.exam_type).distinct().all()
                exam_types = [et[0] for et in exam_types]

                for exam_type in exam_types:
                    for difficulty in ['easy', 'medium', 'hard']:
                        questions = Question.query.filter_by(
                            exam_type=exam_type,
                            difficulty=difficulty
                        ).all()

                        if questions:
                            # Cache up to 100 questions per difficulty level
                            to_cache = min(100, len(questions))
                            for question in sample(questions, to_cache):
                                if CachedQuestion.query.count() >= 200000:
                                    logging.info("Cache limit (200,000) reached during initialization")
                                    return

                                # Check if question is already cached
                                if not CachedQuestion.query.filter_by(question_id=question.id).first():
                                    try:
                                        cached = CachedQuestion(
                                            question_id=question.id,
                                            exam_type=question.exam_type,
                                            difficulty=3,  # Default medium
                                            question_text=question.question_text,
                                            option_a=question.choices[0] if len(question.choices) > 0 else 'A',
                                            option_b=question.choices[1] if len(question.choices) > 1 else 'B',
                                            option_c=question.choices[2] if len(question.choices) > 2 else 'C',
                                            option_d=question.choices[3] if len(question.choices) > 3 else 'D',
                                            correct_answer=question.correct_answer,
                                            explanation=getattr(question, 'explanation', 'No explanation available'),
                                            topic_area='General',
                                            tags='["legacy"]'
                                        )
                                        db.session.add(cached)
                                    except Exception as e:
                                        logging.error(f"Failed to cache question {question.id}: {e}")
                                        continue

                            db.session.commit()
                            logging.info(f"Preloaded {to_cache} questions for {exam_type}")

            logging.info("Legacy cache initialization completed")
        except Exception as e:
            logging.error(f"Error during legacy cache initialization: {str(e)}")
            db.session.rollback()

with app.app_context():
    from models import User, Question, UserProgress, Subscription, CachedQuestion, Badge, UserBadge, Streak
    db.create_all()

    # Initialize badges
    initialize_badges()
    
    # Set up admin role
    from setup_admin import setup_admin_role
    setup_admin_role()
    
    # Start cache initialization in a background thread
    thread = threading.Thread(target=initialize_cache)
    thread.daemon = True  # Make thread daemon so it doesn't block app shutdown
    thread.start()
    logging.info("Started cache initialization thread")

    # Preload questions
    preload_questions()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)