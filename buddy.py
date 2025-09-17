import random
import logging
from datetime import datetime, date
from flask import Blueprint, flash, redirect, url_for, request, jsonify, session, render_template
from flask_login import current_user, login_required
from sqlalchemy import func, desc

from app import db
from models import Badge, UserBadge, Streak, UserProgress, Question

buddy = Blueprint('buddy', __name__)

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

DEFAULT_BADGES = [
    # Questions answered badges
    {"name": "First Step", "description": "Answer your first question", "icon": "fa-solid fa-shoe-prints", "criteria": "questions_answered", "threshold": 1, "color": "info"},
    {"name": "Getting Started", "description": "Answer 10 questions", "icon": "fa-solid fa-play", "criteria": "questions_answered", "threshold": 10, "color": "info"},
    {"name": "On a Roll", "description": "Answer 50 questions", "icon": "fa-solid fa-person-running", "criteria": "questions_answered", "threshold": 50, "color": "primary"},
    {"name": "Question Master", "description": "Answer 100 questions", "icon": "fa-solid fa-graduation-cap", "criteria": "questions_answered", "threshold": 100, "color": "primary"},
    {"name": "Expert", "description": "Answer 500 questions", "icon": "fa-solid fa-crown", "criteria": "questions_answered", "threshold": 500, "color": "warning"},
    {"name": "Ultimate Scholar", "description": "Answer 1000 questions", "icon": "fa-solid fa-trophy", "criteria": "questions_answered", "threshold": 1000, "color": "danger"},
    
    # Streak badges
    {"name": "Consistent", "description": "Maintain a 3-day streak", "icon": "fa-solid fa-calendar-check", "criteria": "streak", "threshold": 3, "color": "info"},
    {"name": "Dedicated", "description": "Maintain a 7-day streak", "icon": "fa-solid fa-calendar-week", "criteria": "streak", "threshold": 7, "color": "primary"},
    {"name": "Committed", "description": "Maintain a 14-day streak", "icon": "fa-solid fa-calendar-star", "criteria": "streak", "threshold": 14, "color": "warning"},
    {"name": "Unstoppable", "description": "Maintain a 30-day streak", "icon": "fa-solid fa-fire", "criteria": "streak", "threshold": 30, "color": "danger"},
    
    # Accuracy badges
    {"name": "Sharp Eye", "description": "Achieve 70% accuracy", "icon": "fa-solid fa-bullseye", "criteria": "accuracy", "threshold": 70, "color": "info"},
    {"name": "Precision", "description": "Achieve 80% accuracy", "icon": "fa-solid fa-crosshairs", "criteria": "accuracy", "threshold": 80, "color": "primary"},
    {"name": "Excellence", "description": "Achieve 90% accuracy", "icon": "fa-solid fa-award", "criteria": "accuracy", "threshold": 90, "color": "warning"},
    {"name": "Perfect Score", "description": "Achieve 100% accuracy in a session", "icon": "fa-solid fa-star", "criteria": "perfect_session", "threshold": 10, "color": "danger"},
]


def initialize_badges():
    """Create default badges if they don't exist"""
    logging.info("Initializing badges...")
    
    existing_count = Badge.query.count()
    if existing_count == 0:
        for badge_data in DEFAULT_BADGES:
            badge = Badge(**badge_data)
            db.session.add(badge)
        
        db.session.commit()
        logging.info(f"Created {len(DEFAULT_BADGES)} default badges")
    else:
        logging.info(f"Badges already exist ({existing_count})")


def get_encouraging_message(is_correct):
    """Get a random encouraging message based on whether the answer was correct"""
    if is_correct:
        return random.choice(CORRECT_MESSAGES)
    else:
        return random.choice(INCORRECT_MESSAGES)


def get_random_study_tip():
    """Get a random study tip"""
    return random.choice(STUDY_TIPS)


def update_user_streak(user_id):
    """Update the user's streak"""
    today = date.today()
    
    # Get or create user streak
    streak = Streak.query.filter_by(user_id=user_id).first()
    if not streak:
        streak = Streak(user_id=user_id, current_streak=1, longest_streak=1, last_activity_date=today)
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
                new_badge = UserBadge(user_id=user_id, badge_id=badge.id)
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
                    new_badge = UserBadge(user_id=user_id, badge_id=badge.id)
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
                    new_badge = UserBadge(user_id=user_id, badge_id=badge.id)
                    db.session.add(new_badge)
                    new_badges.append(badge)
    
    # Check perfect session badges (10+ questions with 100% accuracy in a row)
    # This would typically be checked after a practice session
    
    if new_badges:
        db.session.commit()
    
    return new_badges


def get_user_stats(user_id):
    """Get user statistics for the dashboard"""
    stats = {}
    
    # Total questions answered
    stats['total_questions'] = UserProgress.query.filter_by(user_id=user_id).count()
    
    # Correct answers
    stats['correct_answers'] = UserProgress.query.filter_by(
        user_id=user_id, answered_correctly=True).count()
    
    # Calculate accuracy
    if stats['total_questions'] > 0:
        stats['accuracy'] = round((stats['correct_answers'] / stats['total_questions']) * 100, 1)
    else:
        stats['accuracy'] = 0
    
    # Get streak information
    streak = Streak.query.filter_by(user_id=user_id).first()
    if streak:
        stats['current_streak'] = streak.current_streak
        stats['longest_streak'] = streak.longest_streak
    else:
        stats['current_streak'] = 0
        stats['longest_streak'] = 0
    
    # Get badges earned
    user_badges = UserBadge.query.filter_by(user_id=user_id).all()
    stats['badges_count'] = len(user_badges)
    
    # Get most recent badges (limit to 3)
    recent_badges = UserBadge.query.filter_by(user_id=user_id).order_by(
        UserBadge.achieved_at.desc()).limit(3).all()
    
    stats['recent_badges'] = []
    for ub in recent_badges:
        badge = Badge.query.get(ub.badge_id)
        if badge:
            stats['recent_badges'].append({
                'name': badge.name,
                'description': badge.description,
                'icon': badge.icon,
                'color': badge.color,
                'achieved_at': ub.achieved_at.strftime('%b %d, %Y')
            })
    
    # Calculate progress to next badge
    next_question_badge = Badge.query.filter(
        Badge.criteria == 'questions_answered',
        Badge.threshold > stats['total_questions']
    ).order_by(Badge.threshold).first()
    
    if next_question_badge:
        stats['next_badge'] = {
            'name': next_question_badge.name,
            'threshold': next_question_badge.threshold,
            'current': stats['total_questions'],
            'percentage': min(100, round((stats['total_questions'] / next_question_badge.threshold) * 100))
        }
    
    return stats


@buddy.route('/api/buddy-message', methods=['POST'])
@login_required
def get_buddy_message():
    """Get a contextual buddy message based on the user's answer"""
    data = request.get_json()
    is_correct = data.get('is_correct', False)
    
    message = get_encouraging_message(is_correct)
    
    # Update streak if this is the first activity today
    streak = update_user_streak(current_user.id)
    
    # Check for new badges
    new_badges = check_and_award_badges(current_user.id)
    
    response = {
        'message': message,
        'streak': streak.current_streak if streak else 1
    }
    
    if new_badges:
        response['new_badges'] = [{
            'name': badge.name,
            'description': badge.description,
            'icon': badge.icon
        } for badge in new_badges]
    
    # Sometimes include a study tip
    if random.random() < 0.3:  # 30% chance
        response['study_tip'] = get_random_study_tip()
        
    return jsonify(response)


@buddy.route('/badges')
@login_required
def view_badges():
    """View all badges and user progress"""
    # Get all badges grouped by category
    badges = {
        'questions': Badge.query.filter_by(criteria='questions_answered').order_by(Badge.threshold).all(),
        'streak': Badge.query.filter_by(criteria='streak').order_by(Badge.threshold).all(),
        'accuracy': Badge.query.filter_by(criteria='accuracy').order_by(Badge.threshold).all(),
        'special': Badge.query.filter_by(criteria='perfect_session').all()
    }
    
    # Get user's earned badges
    user_badges = UserBadge.query.filter_by(user_id=current_user.id).all()
    earned_badge_ids = [ub.badge_id for ub in user_badges]
    
    # Get user stats
    stats = get_user_stats(current_user.id)
    
    return render_template(
        'badges.html',
        badges=badges,
        earned_badge_ids=earned_badge_ids,
        stats=stats
    )