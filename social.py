# Social Learning Features Blueprint

import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc, func, and_, or_
from models import (
    db, User, UserProgress, Streak, StudyGroup, StudyGroupMember, 
    UserRelationship, Leaderboard, QuestionDiscussion
)

social = Blueprint('social', __name__, url_prefix='/social')

@social.route('/leaderboard')
@social.route('/leaderboard/<exam_type>')
@social.route('/leaderboard/<exam_type>/<period>')
@login_required
def leaderboard(exam_type='GMAT', period='weekly'):
    """Display leaderboard for specified exam and period"""
    try:
        # Validate exam type and period
        valid_exams = ['GMAT', 'MCAT', 'GRE', 'LSAT', 'SAT', 'ACT', 'USMLE', 'NCLEX', 'IELTS', 'TOEFL', 'PMP', 'CFA']
        valid_periods = ['daily', 'weekly', 'monthly', 'all-time']
        
        if exam_type not in valid_exams:
            exam_type = 'GMAT'
        if period not in valid_periods:
            period = 'weekly'
        
        # Calculate date range for period
        end_date = datetime.utcnow().date()
        if period == 'daily':
            start_date = end_date
        elif period == 'weekly':
            start_date = end_date - timedelta(days=7)
        elif period == 'monthly':
            start_date = end_date - timedelta(days=30)
        else:  # all-time
            start_date = datetime(2020, 1, 1).date()
        
        # Query user performance for leaderboard
        leaderboard_query = db.session.query(
            User.id,
            User.username,
            func.count(UserProgress.id).label('questions_answered'),
            func.avg(
                func.case(
                    (UserProgress.is_correct == True, 100),
                    else_=0
                )
            ).label('accuracy'),
            func.max(Streak.current_streak).label('max_streak')
        ).select_from(User)\
         .join(UserProgress, User.id == UserProgress.user_id)\
         .outerjoin(Streak, User.id == Streak.user_id)\
         .filter(UserProgress.exam_type == exam_type)\
         .filter(UserProgress.answered_at >= start_date)\
         .filter(UserProgress.answered_at <= end_date)\
         .group_by(User.id, User.username)\
         .having(func.count(UserProgress.id) >= 5)  # Minimum 5 questions
        
        # Apply privacy filters (only show users who opted in)
        leaderboard_query = leaderboard_query.filter(
            or_(
                User.privacy_settings == None,
                User.privacy_settings['show_in_leaderboard'] == True
            )
        )
        
        # Calculate composite score and order
        rankings = []
        for user_data in leaderboard_query.all():
            # Composite score: accuracy * log(questions) + streak_bonus
            score = (user_data.accuracy or 0) * (1 + 0.1 * (user_data.questions_answered or 0)) / 100
            streak_bonus = min((user_data.max_streak or 0) * 2, 50)
            final_score = score + streak_bonus
            
            rankings.append({
                'user_id': user_data.id,
                'username': user_data.username,
                'questions_answered': user_data.questions_answered or 0,
                'accuracy': round(user_data.accuracy or 0, 1),
                'max_streak': user_data.max_streak or 0,
                'score': round(final_score, 1),
                'is_current_user': user_data.id == current_user.id
            })
        
        # Sort by score descending
        rankings.sort(key=lambda x: x['score'], reverse=True)
        
        # Add rank numbers
        for i, ranking in enumerate(rankings):
            ranking['rank'] = i + 1
        
        # Get current user's position
        user_position = next((r for r in rankings if r['is_current_user']), None)
        
        return render_template('social/leaderboard.html',
                             rankings=rankings[:50],  # Top 50
                             exam_type=exam_type,
                             period=period,
                             user_position=user_position,
                             valid_exams=valid_exams,
                             valid_periods=valid_periods)
    
    except Exception as e:
        logging.error(f"Error loading leaderboard: {e}")
        flash('Error loading leaderboard data', 'error')
        return redirect(url_for('main.dashboard'))

@social.route('/study-groups')
@login_required
def study_groups():
    """Display study groups interface"""
    try:
        # Get user's current groups
        user_groups = db.session.query(StudyGroup)\
            .join(StudyGroupMember, StudyGroup.id == StudyGroupMember.group_id)\
            .filter(StudyGroupMember.user_id == current_user.id)\
            .filter(StudyGroupMember.is_active == True)\
            .all()
        
        # Get available public groups (not already joined)
        joined_group_ids = [group.id for group in user_groups]
        available_groups = db.session.query(StudyGroup)\
            .filter(StudyGroup.is_public == True)\
            .filter(~StudyGroup.id.in_(joined_group_ids))\
            .filter(
                db.session.query(func.count(StudyGroupMember.id))\
                .filter(StudyGroupMember.group_id == StudyGroup.id)\
                .filter(StudyGroupMember.is_active == True)\
                .as_scalar() < StudyGroup.max_members
            )\
            .order_by(desc(StudyGroup.created_at))\
            .limit(20)\
            .all()
        
        # Add member counts to groups
        for group in user_groups + available_groups:
            group.member_count = db.session.query(func.count(StudyGroupMember.id))\
                .filter(StudyGroupMember.group_id == group.id)\
                .filter(StudyGroupMember.is_active == True)\
                .scalar()
        
        return render_template('social/study_groups.html',
                             user_groups=user_groups,
                             available_groups=available_groups)
    
    except Exception as e:
        logging.error(f"Error loading study groups: {e}")
        flash('Error loading study groups', 'error')
        return redirect(url_for('main.dashboard'))

@social.route('/join-group/<int:group_id>', methods=['POST'])
@login_required
def join_study_group(group_id):
    """Join a study group"""
    try:
        # Validate group exists and is joinable
        group = StudyGroup.query.get_or_404(group_id)
        
        # Check if already a member
        existing_member = StudyGroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if existing_member:
            return jsonify({'success': False, 'message': 'Already a member of this group'})
        
        # Check group capacity
        current_members = db.session.query(func.count(StudyGroupMember.id))\
            .filter(StudyGroupMember.group_id == group_id)\
            .filter(StudyGroupMember.is_active == True)\
            .scalar()
        
        if current_members >= group.max_members:
            return jsonify({'success': False, 'message': 'Group is full'})
        
        # Create membership
        membership = StudyGroupMember(
            group_id=group_id,
            user_id=current_user.id,
            role='member'
        )
        db.session.add(membership)
        db.session.commit()
        
        # Log activity
        logging.info(f"User {current_user.id} joined study group {group_id}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully joined {group.name}!',
            'redirect': url_for('social.group_discussion', group_id=group_id)
        })
    
    except Exception as e:
        logging.error(f"Error joining study group: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to join group'})

@social.route('/group/<int:group_id>')
@login_required
def group_discussion(group_id):
    """Study group discussion page"""
    try:
        # Verify user is a member
        membership = StudyGroupMember.query.filter_by(
            group_id=group_id,
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not membership:
            flash('You are not a member of this study group', 'error')
            return redirect(url_for('social.study_groups'))
        
        group = StudyGroup.query.get_or_404(group_id)
        
        # Get group members
        members = db.session.query(User, StudyGroupMember)\
            .join(StudyGroupMember, User.id == StudyGroupMember.user_id)\
            .filter(StudyGroupMember.group_id == group_id)\
            .filter(StudyGroupMember.is_active == True)\
            .order_by(StudyGroupMember.joined_at)\
            .all()
        
        return render_template('social/group_discussion.html',
                             group=group,
                             members=members,
                             user_role=membership.role)
    
    except Exception as e:
        logging.error(f"Error loading group discussion: {e}")
        flash('Error loading group discussion', 'error')
        return redirect(url_for('social.study_groups'))

@social.route('/question-discussion/<question_id>')
@login_required
def question_discussion(question_id):
    """Question discussion interface"""
    try:
        # Get existing discussions for question
        discussions = db.session.query(QuestionDiscussion, User)\
            .join(User, QuestionDiscussion.user_id == User.id)\
            .filter(QuestionDiscussion.question_id == question_id)\
            .filter(QuestionDiscussion.parent_comment_id == None)\
            .order_by(desc(QuestionDiscussion.helpful_votes))\
            .all()
        
        # Get replies for each comment
        for discussion, user in discussions:
            discussion.replies = db.session.query(QuestionDiscussion, User)\
                .join(User, QuestionDiscussion.user_id == User.id)\
                .filter(QuestionDiscussion.parent_comment_id == discussion.id)\
                .order_by(QuestionDiscussion.created_at)\
                .all()
        
        return render_template('social/question_discussion.html',
                             question_id=question_id,
                             discussions=discussions)
    
    except Exception as e:
        logging.error(f"Error loading question discussion: {e}")
        flash('Error loading discussion', 'error')
        return redirect(url_for('main.dashboard'))

@social.route('/submit-comment', methods=['POST'])
@login_required
def submit_comment():
    """Submit a comment on a question"""
    try:
        data = request.get_json()
        question_id = data.get('question_id')
        comment_text = data.get('comment_text', '').strip()
        parent_comment_id = data.get('parent_comment_id')
        
        # Validate input
        if not question_id or not comment_text:
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        if len(comment_text) < 10:
            return jsonify({'success': False, 'message': 'Comment too short (minimum 10 characters)'})
        
        if len(comment_text) > 1000:
            return jsonify({'success': False, 'message': 'Comment too long (maximum 1000 characters)'})
        
        # Create comment
        comment = QuestionDiscussion(
            question_id=question_id,
            user_id=current_user.id,
            comment_text=comment_text,
            parent_comment_id=parent_comment_id
        )
        db.session.add(comment)
        db.session.commit()
        
        # Return comment data for immediate display
        return jsonify({
            'success': True,
            'comment': {
                'id': comment.id,
                'text': comment.comment_text,
                'username': current_user.username,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                'helpful_votes': 0,
                'is_helpful': False
            }
        })
    
    except Exception as e:
        logging.error(f"Error submitting comment: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to submit comment'})

@social.route('/vote-comment/<int:comment_id>', methods=['POST'])
@login_required
def vote_comment(comment_id):
    """Vote on comment helpfulness"""
    try:
        comment = QuestionDiscussion.query.get_or_404(comment_id)
        
        # Toggle helpful vote
        comment.helpful_votes += 1
        comment.is_helpful = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'new_vote_count': comment.helpful_votes
        })
    
    except Exception as e:
        logging.error(f"Error voting on comment: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to vote'})

@social.route('/api/social-notifications')
@login_required
def get_social_notifications():
    """Get social activity notifications for user"""
    try:
        notifications = []
        
        # Get recent group activities
        recent_memberships = db.session.query(StudyGroupMember, StudyGroup, User)\
            .join(StudyGroup, StudyGroupMember.group_id == StudyGroup.id)\
            .join(User, StudyGroupMember.user_id == User.id)\
            .filter(StudyGroupMember.group_id.in_(
                db.session.query(StudyGroupMember.group_id)\
                .filter(StudyGroupMember.user_id == current_user.id)\
                .filter(StudyGroupMember.is_active == True)
            ))\
            .filter(StudyGroupMember.user_id != current_user.id)\
            .filter(StudyGroupMember.joined_at >= datetime.utcnow() - timedelta(days=7))\
            .order_by(desc(StudyGroupMember.joined_at))\
            .limit(10)\
            .all()
        
        for membership, group, user in recent_memberships:
            notifications.append({
                'type': 'group_join',
                'message': f'{user.username} joined {group.name}',
                'time': membership.joined_at.strftime('%Y-%m-%d %H:%M'),
                'group_id': group.id
            })
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'count': len(notifications)
        })
    
    except Exception as e:
        logging.error(f"Error getting social notifications: {e}")
        return jsonify({'success': False, 'notifications': [], 'count': 0})

@social.route('/create-group', methods=['GET', 'POST'])
@login_required
def create_study_group():
    """Create a new study group"""
    if request.method == 'GET':
        return render_template('social/create_group.html')
    
    try:
        data = request.get_json() if request.is_json else request.form
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        exam_type = data.get('exam_type', 'GMAT')
        is_public = data.get('is_public', True)
        max_members = min(int(data.get('max_members', 20)), 100)
        
        # Validate input
        if not name or len(name) < 3:
            return jsonify({'success': False, 'message': 'Group name must be at least 3 characters'})
        
        # Generate unique invite code
        import string
        import random
        invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        
        # Create group
        group = StudyGroup(
            name=name,
            description=description,
            exam_type=exam_type,
            creator_id=current_user.id,
            is_public=is_public,
            max_members=max_members,
            invite_code=invite_code
        )
        db.session.add(group)
        db.session.flush()  # Get the group ID
        
        # Add creator as admin
        membership = StudyGroupMember(
            group_id=group.id,
            user_id=current_user.id,
            role='admin'
        )
        db.session.add(membership)
        db.session.commit()
        
        logging.info(f"User {current_user.id} created study group {group.id}")
        
        return jsonify({
            'success': True,
            'message': 'Study group created successfully!',
            'group_id': group.id,
            'invite_code': invite_code
        })
    
    except Exception as e:
        logging.error(f"Error creating study group: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to create group'})

# Error handlers for the social blueprint
@social.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@social.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500