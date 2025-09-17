from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    is_admin = db.Column(db.Boolean, default=False)
    subscription_plan = db.Column(db.String(20), default='free')  # 'free' or 'pro'
    trial_start_date = db.Column(db.DateTime, nullable=True)
    trial_end_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    subscription = db.relationship('Subscription', backref='user', uselist=False)
    study_plans = db.relationship('StudyPlan', backref='user', lazy=True)
    user_relationships_following = db.relationship('UserRelationship', foreign_keys='UserRelationship.follower_id', backref='follower', lazy='dynamic')
    user_relationships_followers = db.relationship('UserRelationship', foreign_keys='UserRelationship.following_id', backref='following', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_premium(self):
        """Check if user has active premium subscription or active trial"""
        return (self.subscription and self.subscription.active) or self.has_active_trial()
    
    def has_active_trial(self):
        """Check if user has an active trial"""
        if not self.trial_start_date or not self.trial_end_date:
            return False
        now = datetime.utcnow()
        return self.trial_start_date <= now <= self.trial_end_date
    
    def start_trial(self, duration_days=7):
        """Start a 7-day trial for the user"""
        now = datetime.utcnow()
        self.trial_start_date = now
        self.trial_end_date = now + timedelta(days=duration_days)
        logging.info(f"Started {duration_days}-day trial for user {self.id}: {self.trial_start_date} to {self.trial_end_date}")
        
    def get_trial_days_remaining(self):
        """Get number of days remaining in trial"""
        if not self.has_active_trial():
            return 0
        now = datetime.utcnow()
        days_remaining = (self.trial_end_date - now).days + 1
        return max(0, days_remaining)
    
    @property
    def questions_answered(self):
        """Get total questions answered by user"""
        return UserProgress.query.filter_by(user_id=self.id).count()

    def __repr__(self):
        return f'<User {self.email}>'

class Question(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    exam_type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100))
    difficulty = db.Column(db.String(20), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    choices = db.Column(db.JSON, nullable=False)
    correct_answer = db.Column(db.String(50), nullable=False)
    explanation = db.Column(db.Text)
    topics = db.Column(db.JSON)
    cognitive_level = db.Column(db.String(50))
    estimated_time = db.Column(db.Integer, default=120)
    question_weight = db.Column(db.Float, default=1.0)
    question_metadata = db.Column(db.JSON)
    is_generated = db.Column(db.Boolean, default=False)
    generation_source = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Question {self.id} ({self.exam_type})>'

class CachedQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.String(50), nullable=True)
    exam_type = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.Integer, default=3)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(50), nullable=False)
    explanation = db.Column(db.Text, default='')
    topic_area = db.Column(db.String(100), default='General')
    tags = db.Column(db.Text, default='[]')  # JSON string
    cached_at = db.Column(db.DateTime, default=datetime.utcnow)
    generation_request_id = db.Column(db.Integer, nullable=True)
    choices = db.Column(db.JSON, nullable=True)  # Legacy field for compatibility
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<CachedQuestion {self.id}>'

# Strategic Framework Database Models

class ExamConfig(db.Model):
    """Layer 1: Content Framework & Standards"""
    id = db.Column(db.Integer, primary_key=True)
    exam_type = db.Column(db.String(50), unique=True, nullable=False)
    enabled = db.Column(db.Boolean, default=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    difficulty_levels = db.Column(db.Text, default='[1,2,3,4,5]')  # JSON string
    topic_areas = db.Column(db.Text, default='[]')  # JSON string
    question_formats = db.Column(db.Text, default='["multiple_choice"]')  # JSON string
    time_limits = db.Column(db.Integer, default=120)
    passing_score = db.Column(db.Integer, default=70)
    content_weight = db.Column(db.Text, default='{}')  # JSON string
    estimated_duration = db.Column(db.Integer, default=120)
    total_questions = db.Column(db.Integer, default=0)
    difficulty_distribution = db.Column(db.JSON)
    content_framework = db.Column(db.JSON)
    generation_enabled = db.Column(db.Boolean, default=True)
    quality_threshold = db.Column(db.Float, default=0.85)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class QuestionMetrics(db.Model):
    """Layer 3: Quality Validation & Performance Tracking"""
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.String(50), db.ForeignKey('question.id'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    difficulty_level = db.Column(db.Integer, default=3)
    topic_area = db.Column(db.String(100), default='General')
    total_attempts = db.Column(db.Integer, default=0)
    correct_attempts = db.Column(db.Integer, default=0)
    average_time = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    difficulty_rating = db.Column(db.Float, default=0.0)
    discrimination_index = db.Column(db.Float, default=0.0)
    times_answered = db.Column(db.Integer, default=0)
    correct_percentage = db.Column(db.Float, default=0.0)
    quality_score = db.Column(db.Float, default=0.0)
    engagement_score = db.Column(db.Float, default=0.0)
    learning_effectiveness = db.Column(db.Float, default=0.0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    question = db.relationship('Question', backref='metrics')

class UserAbilityProfile(db.Model):
    """Layer 4: Adaptive Personalization Engine"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    current_difficulty = db.Column(db.Float, default=3.0)
    strength_areas = db.Column(db.Text, default='[]')  # JSON string
    weak_areas = db.Column(db.Text, default='[]')  # JSON string
    learning_velocity = db.Column(db.Float, default=1.0)
    question_count = db.Column(db.Integer, default=0)
    accuracy_rate = db.Column(db.Float, default=0.0)
    overall_ability = db.Column(db.Float, default=0.0)
    topic_abilities = db.Column(db.JSON, default=dict)
    confidence_calibration = db.Column(db.Float, default=0.0)
    preferred_difficulty = db.Column(db.String(20), default='medium')
    target_accuracy = db.Column(db.Float, default=0.75)
    learning_style = db.Column(db.JSON, default=dict)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='ability_profiles')

class GenerationRequest(db.Model):
    """Layer 2: AI Generation Engine Tracking"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    questions_requested = db.Column(db.Integer, default=1)
    questions_generated = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='pending')
    request_time = db.Column(db.DateTime, default=datetime.utcnow)
    completion_time = db.Column(db.DateTime, nullable=True)
    topic = db.Column(db.String(100), default='General')
    difficulty = db.Column(db.String(20), default='medium')
    request_type = db.Column(db.String(50), default='adaptive')
    generation_parameters = db.Column(db.JSON)
    generated_question_id = db.Column(db.String(50), nullable=True)
    quality_score = db.Column(db.Float, nullable=True)
    generation_time = db.Column(db.Float, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

class LearningSession(db.Model):
    """Learning session tracking for Strategic AI Engine"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    session_start = db.Column(db.DateTime, default=datetime.utcnow)
    session_end = db.Column(db.DateTime, nullable=True)
    questions_answered = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    total_time = db.Column(db.Integer, default=0)
    session_type = db.Column(db.String(50), default='practice')
    performance_data = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='learning_sessions')

class ContentOptimization(db.Model):
    """Layer 5: Continuous Learning & Improvement"""
    id = db.Column(db.Integer, primary_key=True)
    optimization_type = db.Column(db.String(50), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    performance_data = db.Column(db.JSON)
    optimization_parameters = db.Column(db.JSON)
    improvement_metrics = db.Column(db.JSON)
    implementation_status = db.Column(db.String(20), default='pending')
    effectiveness_score = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    implemented_at = db.Column(db.DateTime, nullable=True)

class QuestionGenerationTemplate(db.Model):
    """Strategic Framework: Generation Templates"""
    id = db.Column(db.Integer, primary_key=True)
    exam_type = db.Column(db.String(50), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    template_content = db.Column(db.Text, nullable=False)
    system_prompt = db.Column(db.Text, nullable=False)
    quality_criteria = db.Column(db.JSON)
    success_rate = db.Column(db.Float, default=0.0)
    usage_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime, nullable=True)

class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    question_id = db.Column(db.String(50), db.ForeignKey('question.id'), nullable=False)
    answered_correctly = db.Column(db.Boolean, nullable=False)
    response_time = db.Column(db.Integer, default=0)
    attempt_count = db.Column(db.Integer, default=1)
    confidence_level = db.Column(db.Integer, default=3)
    hints_used = db.Column(db.Integer, default=0)
    session_id = db.Column(db.String(100), nullable=True)
    review_needed = db.Column(db.Boolean, default=False)
    difficulty_rating = db.Column(db.Float, default=0.0)
    cognitive_load = db.Column(db.Float, default=0.0)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserProgress {self.user_id} - {self.question_id} ({self.answered_correctly})>'

class UserPerformance(db.Model):
    """Track user performance by exam type and topic for adaptive question generation"""
    __tablename__ = 'user_performance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)  # Percentage score (0-100)
    attempts = db.Column(db.Integer, default=1)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to ensure one record per user-exam-topic combination
    __table_args__ = (db.UniqueConstraint('user_id', 'exam_type', 'topic', name='_user_exam_topic_uc'),)
    
    @property
    def difficulty_level(self):
        """Determine difficulty level based on score"""
        if self.score < 40:
            return 'easy'
        elif self.score <= 70:
            return 'medium'
        else:
            return 'hard'
    
    def __repr__(self):
        return f'<UserPerformance {self.user_id} - {self.exam_type} - {self.topic}: {self.score}%>'

class UserActivity(db.Model):
    """Track user activity for rate limiting and analytics"""
    __tablename__ = 'user_activity'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # 'question_generated', 'answer_submitted', etc.
    count = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='activity_records')
    
    def __repr__(self):
        return f'<UserActivity {self.user_id} {self.activity_type} {self.count}>'

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    stripe_customer_id = db.Column(db.String(100), unique=True)
    active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Subscription {self.user_id} ({self.active})>'

class PracticeSession(db.Model):
    """Persistent practice session storage for seamless continuity"""
    id = db.Column(db.String(100), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    question_ids = db.Column(db.JSON, nullable=False)
    current_index = db.Column(db.Integer, default=0)
    session_stats = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)
    trial_limited = db.Column(db.Boolean, default=False)  # Session hit trial limit
    questions_in_session = db.Column(db.Integer, default=0)  # Track per-session count
    
    def __repr__(self):
        return f'<PracticeSession {self.id} - {self.user_id} ({self.exam_type})>'

class TrialUsage(db.Model):
    """Track trial usage per exam type for intelligent limit management"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    questions_used = db.Column(db.Integer, default=0)
    sessions_completed = db.Column(db.Integer, default=0)
    first_session_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_session_date = db.Column(db.DateTime, default=datetime.utcnow)
    trial_completed = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<TrialUsage {self.user_id} - {self.exam_type} ({self.questions_used}/20)>'

class AnswerContest(db.Model):
    """User-submitted contests for incorrect answers with their work"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.String(50), db.ForeignKey('question.id'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    user_answer = db.Column(db.String(10), nullable=False)  # A, B, C, D, E
    correct_answer = db.Column(db.String(10), nullable=False)  # System's answer
    user_work = db.Column(db.Text, nullable=False)  # User's written work/explanation
    reason = db.Column(db.Text, nullable=True)  # Why they believe their answer is correct
    status = db.Column(db.String(20), default='pending')  # pending, reviewed, resolved
    admin_response = db.Column(db.Text, nullable=True)  # Admin's response
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='answer_contests')
    question = db.relationship('Question', backref='contests')
    
    def __repr__(self):
        return f'<AnswerContest {self.user_id} - Q:{self.question_id} ({self.status})>'

# Models are now defined above in the Strategic Framework section

class StudyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    target_date = db.Column(db.Date, nullable=False)
    target_score = db.Column(db.Integer)
    current_score_estimate = db.Column(db.Integer)
    daily_study_time = db.Column(db.Integer, default=60)
    plan_data = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<StudyPlan {self.user_id} - {self.exam_type}>'

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    study_plan_id = db.Column(db.Integer, db.ForeignKey('study_plan.id'), nullable=False)
    planned_date = db.Column(db.Date, nullable=False)
    completed_date = db.Column(db.Date, nullable=True)
    planned_topics = db.Column(db.JSON)
    completed_topics = db.Column(db.JSON)
    planned_duration = db.Column(db.Integer, default=60)
    actual_duration = db.Column(db.Integer, nullable=True)
    performance_score = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<StudySession {self.study_plan_id} - {self.planned_date}>'

class StudyGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exam_type = db.Column(db.String(50), nullable=False)
    goal_type = db.Column(db.String(50), nullable=False)
    target_value = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float, default=0.0)
    deadline = db.Column(db.Date, nullable=True)
    is_achieved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StudyGoal {self.user_id} - {self.goal_type}>'

class UserRelationship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    relationship_type = db.Column(db.String(20), default='friend')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserRelationship {self.follower_id} -> {self.following_id}>'

class StudyGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    exam_type = db.Column(db.String(50), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    max_members = db.Column(db.Integer, default=50)
    invite_code = db.Column(db.String(20), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StudyGroup {self.name}>'

class StudyGroupMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role = db.Column(db.String(20), default='member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<StudyGroupMember {self.user_id} in {self.group_id}>'

class Leaderboard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    exam_type = db.Column(db.String(50), nullable=False)
    period_type = db.Column(db.String(20), nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    rankings = db.Column(db.JSON)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Leaderboard {self.exam_type} - {self.period_type}>'

class QuestionDiscussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.String(50), db.ForeignKey('question.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_text = db.Column(db.Text, nullable=False)
    is_helpful = db.Column(db.Boolean, default=False)
    helpful_votes = db.Column(db.Integer, default=0)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('question_discussion.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<QuestionDiscussion {self.question_id} by {self.user_id}>'


class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(50))  # FontAwesome icon class
    criteria = db.Column(db.String(50))  # Type of achievement: 'questions_answered', 'streak', 'accuracy', etc.
    threshold = db.Column(db.Integer)  # Number required to achieve badge
    color = db.Column(db.String(20), default='primary')  # CSS color class
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Badge {self.name} ({self.criteria}:{self.threshold})>'


class UserBadge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    badge_id = db.Column(db.Integer, db.ForeignKey('badge.id'), nullable=False)
    achieved_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='badges')
    badge = db.relationship('Badge')

    def __repr__(self):
        return f'<UserBadge {self.user_id}:{self.badge_id}>'


class Streak(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Streak {self.user_id} ({self.current_streak} days)>'


class AIExplanation(db.Model):
    """Store AI-generated explanations for questions and answers"""
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.String(50), db.ForeignKey('question.id'), nullable=False)
    answered_correctly = db.Column(db.Boolean, nullable=False)
    technical_explanation = db.Column(db.Text, nullable=False)
    simplified_explanation = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to Question
    question = db.relationship('Question', backref='ai_explanations')

    def __repr__(self):
        return f'<AIExplanation for Q:{self.question_id} (Correct: {self.answered_correctly})>'


