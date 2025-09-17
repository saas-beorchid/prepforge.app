import os
import sys
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app, session
from flask_login import current_user
from sqlalchemy import func, desc, and_, extract, text, case
from models import db, User, Question, UserProgress, Subscription, Streak, Badge, UserBadge, AIExplanation, CachedQuestion
import json
import calendar

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
admin = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin password for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if admin is already authenticated in the session
        if session.get('admin_authenticated'):
            return f(*args, **kwargs)
        else:
            # If not authenticated, redirect to the admin login page
            return redirect(url_for('admin.admin_login', next=request.url))
    return decorated_function

@admin.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page with password protection"""
    if request.method == 'POST':
        password = request.form.get('password')
        # Check against the hardcoded password
        if password == "Aragorn@27":
            # Set admin as authenticated in session
            session['admin_authenticated'] = True
            next_url = request.args.get('next') or url_for('admin.admin_dashboard')
            return redirect(next_url)
        else:
            flash('Invalid admin password.', 'danger')
    
    return render_template('admin/login.html')

@admin.route('/')
@admin_required
def admin_dashboard():
    """Admin dashboard with key metrics and navigation"""
    # Store redirect information in session to ensure proper post-login redirection
    session['next_url'] = url_for('admin.admin_dashboard')
    # Get basic user stats
    total_users = User.query.count()
    premium_users = User.query.join(Subscription).filter(Subscription.active == True).count()
    trial_users = total_users - premium_users
    
    # Get questions stats
    total_questions = Question.query.count()
    total_answers = UserProgress.query.count()
    
    # Get recent user registrations (last 7 days)
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    new_users_count = User.query.filter(User.created_at >= one_week_ago).count()
    
    # Get conversion rate (% of users who upgrade to premium)
    conversion_rate = (premium_users / total_users * 100) if total_users > 0 else 0
    
    # Get average user accuracy
    accuracy_query = db.session.query(
        func.avg(case((UserProgress.answered_correctly == True, 100), else_=0))
    ).scalar()
    avg_accuracy = accuracy_query or 0
    
    # Get top exam types
    top_exams = db.session.query(
        UserProgress.exam_type,
        func.count(UserProgress.id).label('count')
    ).group_by(UserProgress.exam_type).order_by(desc('count')).limit(5).all()
    
    # Get daily activity for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_activity = db.session.query(
        func.date(UserProgress.timestamp).label('date'),
        func.count(UserProgress.id).label('answers'),
        func.count(func.distinct(UserProgress.user_id)).label('users')
    ).filter(UserProgress.timestamp >= thirty_days_ago).group_by('date').order_by('date').all()
    
    # Format data for charts
    daily_labels = [d.date.strftime('%m/%d') for d in daily_activity]
    daily_answers = [d.answers for d in daily_activity]
    daily_users = [d.users for d in daily_activity]
    
    exam_labels = [e.exam_type for e in top_exams]
    exam_counts = [e.count for e in top_exams]
    
    return render_template(
        'admin/dashboard.html',
        total_users=total_users,
        premium_users=premium_users,
        trial_users=trial_users,
        total_questions=total_questions,
        total_answers=total_answers,
        new_users_count=new_users_count,
        conversion_rate=round(conversion_rate, 1),
        avg_accuracy=round(avg_accuracy, 1),
        daily_labels=json.dumps(daily_labels),
        daily_answers=json.dumps(daily_answers),
        daily_users=json.dumps(daily_users),
        exam_labels=json.dumps(exam_labels),
        exam_counts=json.dumps(exam_counts),
        top_exams=top_exams
    )

@admin.route('/users')
@admin_required
def user_management():
    """View and manage users"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    filter_type = request.args.get('filter', 'all')
    
    query = User.query
    
    # Apply search filter
    if search:
        query = query.filter(
            (User.name.ilike(f'%{search}%')) | 
            (User.email.ilike(f'%{search}%'))
        )
    
    # Apply user type filter
    if filter_type == 'premium':
        query = query.join(Subscription).filter(Subscription.active == True)
    elif filter_type == 'trial':
        query = query.outerjoin(Subscription).filter(
            (Subscription.active.is_(None)) | (Subscription.active == False)
        )
    elif filter_type == 'new':
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        query = query.filter(User.created_at >= one_week_ago)
    
    # Get paginated users
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Get general user stats
    total_users = User.query.count()
    premium_count = User.query.join(Subscription).filter(Subscription.active == True).count()
    trial_count = total_users - premium_count
    
    # Get signups by day of week
    day_of_week_stats = db.session.query(
        extract('dow', User.created_at).label('day_of_week'),
        func.count(User.id).label('count')
    ).group_by('day_of_week').order_by('day_of_week').all()
    
    # Format day of week data
    days_of_week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    day_counts = [0] * 7
    for stat in day_of_week_stats:
        day_counts[int(stat.day_of_week)] = stat.count
    
    return render_template(
        'admin/users.html',
        users=users,
        search=search,
        filter_type=filter_type,
        total_users=total_users,
        premium_count=premium_count,
        trial_count=trial_count,
        days_of_week=json.dumps(days_of_week),
        day_counts=json.dumps(day_counts)
    )

@admin.route('/user/<int:user_id>')
@admin_required
def user_detail(user_id):
    """Detailed view of a specific user"""
    user = User.query.get_or_404(user_id)
    
    # Check if user has a subscription
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    
    # Get user progress
    progress_items = UserProgress.query.filter_by(user_id=user.id).order_by(UserProgress.timestamp.desc()).limit(100).all()
    
    # Get user badges
    user_badges = UserBadge.query.filter_by(user_id=user.id).join(Badge).order_by(UserBadge.achieved_at.desc()).all()
    
    # Get user streak
    streak = Streak.query.filter_by(user_id=user.id).first()
    
    # Calculate user statistics
    total_questions_answered = UserProgress.query.filter_by(user_id=user.id).count()
    correct_answers = UserProgress.query.filter_by(user_id=user.id, answered_correctly=True).count()
    accuracy = (correct_answers / total_questions_answered * 100) if total_questions_answered > 0 else 0
    
    # Get answers by exam type
    exam_breakdown = db.session.query(
        UserProgress.exam_type,
        func.count(UserProgress.id).label('count'),
        func.avg(case([(UserProgress.answered_correctly == True, 100)], else_=0)).label('accuracy')
    ).filter(UserProgress.user_id == user.id).group_by(UserProgress.exam_type).order_by(desc('count')).all()
    
    # Get progress over time
    progress_by_day = db.session.query(
        func.date(UserProgress.timestamp).label('date'),
        func.count(UserProgress.id).label('count'),
        func.avg(case([(UserProgress.answered_correctly == True, 100)], else_=0)).label('accuracy')
    ).filter(UserProgress.user_id == user.id).group_by('date').order_by('date').all()
    
    # Format data for charts
    dates = [p.date.strftime('%Y-%m-%d') for p in progress_by_day]
    daily_counts = [p.count for p in progress_by_day]
    daily_accuracy = [round(p.accuracy or 0, 1) for p in progress_by_day]
    
    return render_template(
        'admin/user_detail.html',
        user=user,
        subscription=subscription,
        progress_items=progress_items,
        user_badges=user_badges,
        streak=streak,
        total_questions_answered=total_questions_answered,
        correct_answers=correct_answers,
        accuracy=round(accuracy, 1),
        exam_breakdown=exam_breakdown,
        dates=json.dumps(dates),
        daily_counts=json.dumps(daily_counts),
        daily_accuracy=json.dumps(daily_accuracy)
    )

@admin.route('/subscriptions')
@admin_required
def subscription_management():
    """View and manage subscriptions"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status = request.args.get('status', 'active')
    
    query = Subscription.query.join(User)
    
    if status == 'active':
        query = query.filter(Subscription.active == True)
    elif status == 'inactive':
        query = query.filter(Subscription.active == False)
    
    # Get subscriptions with pagination
    subscriptions = query.order_by(Subscription.updated_at.desc()).paginate(page=page, per_page=per_page)
    
    # Get subscription stats
    total_subscriptions = Subscription.query.count()
    active_subscriptions = Subscription.query.filter_by(active=True).count()
    inactive_subscriptions = total_subscriptions - active_subscriptions
    conversion_rate = (total_subscriptions / User.query.count() * 100) if User.query.count() > 0 else 0
    
    # Calculate monthly recurring revenue (MRR) - assuming $15/month per subscriber
    monthly_revenue = active_subscriptions * 15
    
    # Get subscriptions over time
    subscriptions_by_month = db.session.query(
        func.date_trunc('month', Subscription.created_at).label('month'),
        func.count(Subscription.id).label('count')
    ).group_by('month').order_by('month').all()
    
    # Format data for charts
    months = [m.month.strftime('%Y-%m') for m in subscriptions_by_month]
    monthly_counts = [m.count for m in subscriptions_by_month]
    
    # Add current year for template
    current_year = datetime.utcnow().year
    
    return render_template(
        'admin/subscriptions.html',
        subscriptions=subscriptions,
        status=status,
        total_subscriptions=total_subscriptions,
        active_subscriptions=active_subscriptions,
        inactive_subscriptions=inactive_subscriptions,
        conversion_rate=round(conversion_rate, 1),
        monthly_revenue=monthly_revenue,
        months=json.dumps(months),
        monthly_counts=json.dumps(monthly_counts),
        current_year=current_year
    )

@admin.route('/analytics')
@admin_required
def analytics():
    """Detailed analytics dashboard"""
    # Get time range from request params (default: last 30 days)
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get daily user engagement
    daily_engagement = db.session.query(
        func.date(UserProgress.timestamp).label('date'),
        func.count(UserProgress.id).label('answers'),
        func.count(func.distinct(UserProgress.user_id)).label('users'),
        func.avg(case((UserProgress.answered_correctly == True, 100), else_=0)).label('accuracy')
    ).filter(UserProgress.timestamp >= start_date).group_by('date').order_by('date').all()
    
    # Get exam type popularity
    exam_popularity = db.session.query(
        UserProgress.exam_type,
        func.count(UserProgress.id).label('count'),
        func.avg(case((UserProgress.answered_correctly == True, 100), else_=0)).label('accuracy')
    ).filter(UserProgress.timestamp >= start_date).group_by(UserProgress.exam_type).order_by(desc('count')).all()
    
    # Get user type comparison (premium vs trial)
    premium_stats = db.session.query(
        func.count(UserProgress.id).label('answers'),
        func.count(func.distinct(UserProgress.user_id)).label('users'),
        func.avg(case((UserProgress.answered_correctly == True, 100), else_=0)).label('accuracy')
    ).join(User).join(Subscription).filter(
        and_(
            UserProgress.timestamp >= start_date,
            Subscription.active == True
        )
    ).first()
    
    trial_stats = db.session.query(
        func.count(UserProgress.id).label('answers'),
        func.count(func.distinct(UserProgress.user_id)).label('users'),
        func.avg(case((UserProgress.answered_correctly == True, 100), else_=0)).label('accuracy')
    ).join(User).outerjoin(Subscription).filter(
        and_(
            UserProgress.timestamp >= start_date,
            (Subscription.active.is_(None)) | (Subscription.active == False)
        )
    ).first()
    
    # Get user retention stats (users who return multiple days)
    retention_data = db.session.query(
        func.count(func.distinct(UserProgress.user_id)).label('users'),
        func.count(func.distinct(func.date(UserProgress.timestamp))).label('days')
    ).filter(UserProgress.timestamp >= start_date).group_by(UserProgress.user_id).all()
    
    retention_counts = {1: 0, 2: 0, 3: 0, '4+': 0, '7+': 0, '14+': 0}
    
    for item in retention_data:
        if item.days >= 14:
            retention_counts['14+'] += 1
        elif item.days >= 7:
            retention_counts['7+'] += 1
        elif item.days >= 4:
            retention_counts['4+'] += 1
        else:
            retention_counts[item.days] += 1
    
    # Format data for charts
    dates = [d.date.strftime('%m/%d') for d in daily_engagement]
    daily_answers = [d.answers for d in daily_engagement]
    daily_users = [d.users for d in daily_engagement]
    # Convert Decimal objects to float for JSON serialization
    daily_accuracy = [float(round(d.accuracy or 0, 1)) for d in daily_engagement]
    
    exam_names = [e.exam_type for e in exam_popularity]
    exam_counts = [e.count for e in exam_popularity]
    # Convert Decimal objects to float for JSON serialization
    exam_accuracy = [float(round(e.accuracy or 0, 1)) for e in exam_popularity]
    
    return render_template(
        'admin/analytics.html',
        days=days,
        dates=json.dumps(dates),
        daily_answers=json.dumps(daily_answers),
        daily_users=json.dumps(daily_users),
        daily_accuracy=json.dumps(daily_accuracy),
        exam_names=json.dumps(exam_names),
        exam_counts=json.dumps(exam_counts),
        exam_accuracy=json.dumps(exam_accuracy),
        premium_stats=premium_stats,
        trial_stats=trial_stats,
        retention_counts=retention_counts
    )

@admin.route('/questions')
@admin_required
def question_management():
    """View and manage questions"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    exam_type = request.args.get('exam_type', '')
    difficulty = request.args.get('difficulty', '')
    
    query = Question.query
    
    if exam_type:
        query = query.filter(Question.exam_type == exam_type)
    
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    
    # Get question list with pagination
    questions = query.order_by(Question.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Get all available exam types and difficulties for filters
    available_exams = db.session.query(Question.exam_type).distinct().order_by(Question.exam_type).all()
    available_difficulties = db.session.query(Question.difficulty).distinct().order_by(Question.difficulty).all()
    
    # Get question stats
    total_questions = Question.query.count()
    cached_questions = CachedQuestion.query.count()
    cache_ratio = (cached_questions / total_questions * 100) if total_questions > 0 else 0
    
    # Get questions by exam type
    exam_distribution = db.session.query(
        Question.exam_type,
        func.count(Question.id).label('count')
    ).group_by(Question.exam_type).order_by(desc('count')).all()
    
    # Get questions by difficulty
    difficulty_distribution = db.session.query(
        Question.difficulty,
        func.count(Question.id).label('count')
    ).group_by(Question.difficulty).order_by(Question.difficulty).all()
    
    return render_template(
        'admin/questions.html',
        questions=questions,
        exam_type=exam_type,
        difficulty=difficulty,
        available_exams=[e.exam_type for e in available_exams],
        available_difficulties=[d.difficulty for d in available_difficulties],
        total_questions=total_questions,
        cached_questions=cached_questions,
        cache_ratio=round(cache_ratio, 1),
        exam_distribution=exam_distribution,
        difficulty_distribution=difficulty_distribution
    )

@admin.route('/question/<string:question_id>')
@admin_required
def question_detail(question_id):
    """Detailed view of a specific question"""
    question = Question.query.get_or_404(question_id)
    
    # Get question stats
    answers_count = UserProgress.query.filter_by(question_id=question.id).count()
    correct_count = UserProgress.query.filter_by(question_id=question.id, answered_correctly=True).count()
    accuracy = (correct_count / answers_count * 100) if answers_count > 0 else 0
    
    # Check if question is cached
    is_cached = CachedQuestion.query.filter_by(question_id=question.id).first() is not None
    
    # Get AI explanations for this question
    explanations = AIExplanation.query.filter_by(question_id=question.id).all()
    
    # Get similar questions (same exam type and difficulty)
    similar_questions = Question.query.filter(
        Question.exam_type == question.exam_type,
        Question.difficulty == question.difficulty,
        Question.id != question.id
    ).limit(5).all()
    
    return render_template(
        'admin/question_detail.html',
        question=question,
        answers_count=answers_count,
        correct_count=correct_count,
        accuracy=round(accuracy, 1),
        is_cached=is_cached,
        explanations=explanations,
        similar_questions=similar_questions
    )

@admin.route('/system')
@admin_required
def system_status():
    """System status and performance monitoring"""
    # Get cache stats
    cache_size = CachedQuestion.query.count()
    total_questions = Question.query.count()
    cache_ratio = (cache_size / total_questions * 100) if total_questions > 0 else 0
    
    # Get cache by exam type
    cache_by_exam = db.session.query(
        CachedQuestion.exam_type,
        func.count(CachedQuestion.id).label('count')
    ).group_by(CachedQuestion.exam_type).order_by(desc('count')).all()
    
    # Get API usage stats
    api_calls = AIExplanation.query.count()
    api_call_rate = db.session.query(
        func.date(AIExplanation.created_at).label('date'),
        func.count(AIExplanation.id).label('count')
    ).group_by('date').order_by(desc('date')).limit(30).all()
    
    # Get recent errors from logs (simplified example)
    recent_errors = []
    try:
        # This is a placeholder for actual log retrieval logic
        # In a real implementation, you might parse log files or query an error tracking service
        pass
    except Exception as e:
        logger.error(f"Failed to retrieve error logs: {str(e)}")
    
    # Get server info
    import flask
    server_info = {
        'platform': os.name,
        'python_version': sys.version,
        'flask_version': flask.__version__,
        'database_size': 'Unknown',  # Would need a custom query for the specific DB
        'uptime': 'Unknown',  # Would need to track start time
    }
    
    # Format data for charts
    api_dates = [d.date.strftime('%m/%d') for d in api_call_rate]
    api_counts = [d.count for d in api_call_rate]
    
    exam_types = [e.exam_type for e in cache_by_exam]
    exam_counts = [e.count for e in cache_by_exam]
    
    return render_template(
        'admin/system.html',
        cache_size=cache_size,
        total_questions=total_questions,
        cache_ratio=round(cache_ratio, 1),
        api_calls=api_calls,
        server_info=server_info,
        recent_errors=recent_errors,
        api_dates=json.dumps(api_dates),
        api_counts=json.dumps(api_counts),
        exam_types=json.dumps(exam_types),
        exam_counts=json.dumps(exam_counts),
        cache_by_exam=cache_by_exam
    )

# API endpoints for admin data
@admin.route('/api/daily-stats', methods=['GET'])
@admin_required
def api_daily_stats():
    """Get daily stats for the last 30 days"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    daily_stats = db.session.query(
        func.date(UserProgress.timestamp).label('date'),
        func.count(UserProgress.id).label('answers'),
        func.count(func.distinct(UserProgress.user_id)).label('users'),
        func.avg(case((UserProgress.answered_correctly == True, 100), else_=0)).label('accuracy')
    ).filter(UserProgress.timestamp >= start_date).group_by('date').order_by('date').all()
    
    result = [{
        'date': d.date.strftime('%Y-%m-%d'),
        'answers': d.answers,
        'users': d.users,
        'accuracy': float(round(d.accuracy or 0, 1))
    } for d in daily_stats]
    
    return jsonify(result)

@admin.route('/api/user-growth', methods=['GET'])
@admin_required
def api_user_growth():
    """Get user growth over time"""
    # Get monthly user signups
    monthly_users = db.session.query(
        func.date_trunc('month', User.created_at).label('month'),
        func.count(User.id).label('count')
    ).group_by('month').order_by('month').all()
    
    result = [{
        'month': m.month.strftime('%Y-%m'),
        'count': m.count
    } for m in monthly_users]
    
    return jsonify(result)

@admin.route('/api/exam-popularity', methods=['GET'])
@admin_required
def api_exam_popularity():
    """Get exam type popularity"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    exam_stats = db.session.query(
        UserProgress.exam_type,
        func.count(UserProgress.id).label('count'),
        func.avg(case((UserProgress.answered_correctly == True, 100), else_=0)).label('accuracy')
    ).filter(UserProgress.timestamp >= start_date).group_by(UserProgress.exam_type).order_by(desc('count')).all()
    
    result = [{
        'exam_type': e.exam_type,
        'count': e.count,
        'accuracy': float(round(e.accuracy or 0, 1))
    } for e in exam_stats]
    
    return jsonify(result)

# Model update functions (to add admin flag to User model)
def add_admin_field_to_user():
    """Check if admin field exists in User model, add it if not"""
    with current_app.app_context():
        # Check if column exists
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        if 'is_admin' not in columns:
            # Add the column
            db.engine.execute('ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT false')
            logger.info("Added is_admin column to User model")