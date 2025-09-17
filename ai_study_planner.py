# AI-Powered Study Plan Generation System

import logging
import json
import os
import openai
from datetime import datetime, date, timedelta
from sqlalchemy import func, and_, desc
from models import (
    db, User, UserProgress, StudyPlan, StudySession, 
    StudyGoal, Question, QuestionMetrics, AIExplanation
)

class StudyPlanGenerator:
    """AI-powered study plan generation with personalized recommendations"""
    
    def __init__(self, user_id, exam_type, target_date=None):
        self.user_id = user_id
        self.exam_type = exam_type
        self.target_date = target_date or (date.today() + timedelta(days=60))
        self.user = User.query.get(user_id)
        
        # Configure OpenAI client
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
            else:
                self.openai_client = None
                logging.warning("OPENAI_API_KEY not found - AI recommendations will be disabled")
        except Exception as e:
            logging.warning(f"OpenAI client not available: {e}")
            self.openai_client = None

    def create_comprehensive_study_plan(self, daily_study_time=60, target_score=None):
        """Create a complete AI-powered study plan"""
        try:
            # Step 1: Analyze current performance
            performance_analysis = self.analyze_performance_gaps()
            
            # Step 2: Generate personalized schedule
            study_schedule = self.generate_study_schedule(
                daily_study_time, 
                performance_analysis
            )
            
            # Step 3: Create AI-enhanced recommendations
            ai_recommendations = self.generate_ai_recommendations(
                performance_analysis, 
                study_schedule
            )
            
            # Step 4: Create database records
            study_plan = self.create_study_plan_record(
                daily_study_time, 
                target_score, 
                study_schedule, 
                ai_recommendations
            )
            
            # Step 5: Generate study sessions
            self.create_study_sessions(study_plan, study_schedule)
            
            # Step 6: Set personalized goals
            self.create_study_goals(study_plan, performance_analysis)
            
            logging.info(f"Created comprehensive study plan {study_plan.id} for user {self.user_id}")
            return study_plan
            
        except Exception as e:
            logging.error(f"Error creating study plan: {e}")
            raise

    def analyze_performance_gaps(self):
        """Analyze user's current performance to identify weak areas"""
        try:
            # Get user's recent performance data
            recent_progress = db.session.query(UserProgress)\
                .filter(UserProgress.user_id == self.user_id)\
                .filter(UserProgress.exam_type == self.exam_type)\
                .filter(UserProgress.answered_at >= datetime.utcnow() - timedelta(days=30))\
                .all()
            
            if not recent_progress:
                # No recent data, provide general recommendations
                return self.get_default_performance_analysis()
            
            # Analyze performance by topic
            topic_performance = {}
            for progress in recent_progress:
                if hasattr(progress, 'question') and progress.question and progress.question.topics:
                    topics = progress.question.topics if isinstance(progress.question.topics, list) else []
                    for topic in topics:
                        if topic not in topic_performance:
                            topic_performance[topic] = {'correct': 0, 'total': 0, 'avg_time': 0}
                        
                        topic_performance[topic]['total'] += 1
                        if progress.is_correct:
                            topic_performance[topic]['correct'] += 1
                        if hasattr(progress, 'response_time') and progress.response_time:
                            topic_performance[topic]['avg_time'] += progress.response_time
            
            # Calculate accuracy and identify weak areas
            weak_areas = []
            strong_areas = []
            
            for topic, stats in topic_performance.items():
                accuracy = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
                avg_time = stats['avg_time'] / stats['total'] if stats['total'] > 0 else 0
                
                topic_analysis = {
                    'topic': topic,
                    'accuracy': accuracy,
                    'questions_attempted': stats['total'],
                    'average_time': avg_time,
                    'priority': self.calculate_topic_priority(accuracy, stats['total'], avg_time)
                }
                
                if accuracy < 70 or stats['total'] < 5:  # Weak areas
                    weak_areas.append(topic_analysis)
                else:  # Strong areas
                    strong_areas.append(topic_analysis)
            
            # Sort by priority
            weak_areas.sort(key=lambda x: x['priority'], reverse=True)
            strong_areas.sort(key=lambda x: x['accuracy'], reverse=True)
            
            # Overall statistics
            total_questions = len(recent_progress)
            total_correct = sum(1 for p in recent_progress if p.is_correct)
            overall_accuracy = (total_correct / total_questions) * 100 if total_questions > 0 else 0
            
            return {
                'overall_accuracy': overall_accuracy,
                'total_questions': total_questions,
                'weak_areas': weak_areas,
                'strong_areas': strong_areas,
                'recommended_focus_time': self.calculate_focus_distribution(weak_areas, strong_areas),
                'study_intensity': self.determine_study_intensity(overall_accuracy, total_questions)
            }
            
        except Exception as e:
            logging.error(f"Error analyzing performance: {e}")
            return self.get_default_performance_analysis()

    def calculate_topic_priority(self, accuracy, questions_attempted, avg_time):
        """Calculate priority score for topic based on performance metrics"""
        # Lower accuracy = higher priority
        accuracy_factor = max(0, 100 - accuracy) / 100
        
        # Fewer questions attempted = higher priority (need more practice)
        practice_factor = max(0, 20 - questions_attempted) / 20
        
        # Longer time = higher priority (struggling with topic)
        time_factor = min(avg_time / 300, 1) if avg_time > 0 else 0  # Normalize to 5 minutes
        
        return (accuracy_factor * 0.5) + (practice_factor * 0.3) + (time_factor * 0.2)

    def calculate_focus_distribution(self, weak_areas, strong_areas):
        """Calculate how much time to spend on each area"""
        total_weak = len(weak_areas)
        total_strong = len(strong_areas)
        
        if total_weak == 0:
            return {'weak_areas': 0, 'strong_areas': 80, 'new_material': 20}
        elif total_strong == 0:
            return {'weak_areas': 70, 'strong_areas': 0, 'new_material': 30}
        else:
            return {'weak_areas': 60, 'strong_areas': 25, 'new_material': 15}

    def determine_study_intensity(self, accuracy, total_questions):
        """Determine study intensity based on current performance"""
        if accuracy < 60 or total_questions < 20:
            return 'intensive'  # Need more focus
        elif accuracy < 80:
            return 'moderate'   # Steady improvement
        else:
            return 'maintenance' # Keep up good work

    def generate_study_schedule(self, daily_study_time, performance_analysis):
        """Generate personalized study schedule"""
        try:
            days_until_exam = (self.target_date - date.today()).days
            total_study_hours = (days_until_exam * daily_study_time) / 60
            
            # Distribute time based on performance analysis
            focus_distribution = performance_analysis['recommended_focus_time']
            weak_areas = performance_analysis['weak_areas']
            strong_areas = performance_analysis['strong_areas']
            
            schedule = []
            current_date = date.today()
            
            # Create weekly patterns
            weekly_pattern = self.create_weekly_pattern(daily_study_time, focus_distribution)
            
            for week in range(min(days_until_exam // 7, 12)):  # Max 12 weeks
                week_start = current_date + timedelta(weeks=week)
                week_schedule = self.generate_week_schedule(
                    week_start, 
                    weekly_pattern, 
                    weak_areas, 
                    strong_areas,
                    week + 1
                )
                schedule.extend(week_schedule)
            
            return {
                'total_days': days_until_exam,
                'total_hours': total_study_hours,
                'daily_minutes': daily_study_time,
                'weekly_pattern': weekly_pattern,
                'detailed_schedule': schedule[:42]  # Limit to 6 weeks for UI
            }
            
        except Exception as e:
            logging.error(f"Error generating schedule: {e}")
            return self.get_default_schedule(daily_study_time)

    def create_weekly_pattern(self, daily_study_time, focus_distribution):
        """Create a weekly study pattern"""
        return {
            'monday': {'duration': daily_study_time, 'focus': 'weak_areas', 'intensity': 'high'},
            'tuesday': {'duration': daily_study_time, 'focus': 'new_material', 'intensity': 'medium'},
            'wednesday': {'duration': daily_study_time, 'focus': 'weak_areas', 'intensity': 'high'},
            'thursday': {'duration': daily_study_time * 0.8, 'focus': 'strong_areas', 'intensity': 'medium'},
            'friday': {'duration': daily_study_time, 'focus': 'weak_areas', 'intensity': 'high'},
            'saturday': {'duration': daily_study_time * 1.2, 'focus': 'mixed_review', 'intensity': 'medium'},
            'sunday': {'duration': daily_study_time * 0.5, 'focus': 'light_review', 'intensity': 'low'}
        }

    def generate_week_schedule(self, week_start, weekly_pattern, weak_areas, strong_areas, week_number):
        """Generate detailed schedule for one week"""
        week_schedule = []
        
        for day_offset in range(7):
            study_date = week_start + timedelta(days=day_offset)
            day_name = study_date.strftime('%A').lower()
            
            if day_name in weekly_pattern:
                day_config = weekly_pattern[day_name]
                
                session = {
                    'date': study_date,
                    'duration': int(day_config['duration']),
                    'focus_area': day_config['focus'],
                    'intensity': day_config['intensity'],
                    'topics': self.select_topics_for_day(
                        day_config['focus'], 
                        weak_areas, 
                        strong_areas, 
                        week_number
                    ),
                    'goals': self.set_daily_goals(day_config, week_number),
                    'recommended_questions': self.calculate_question_count(day_config['duration'])
                }
                
                week_schedule.append(session)
        
        return week_schedule

    def select_topics_for_day(self, focus_type, weak_areas, strong_areas, week_number):
        """Select topics to study for a specific day"""
        if focus_type == 'weak_areas':
            # Rotate through weak areas
            if weak_areas:
                index = (week_number - 1) % len(weak_areas)
                return [weak_areas[index]['topic']]
            return ['General Practice']
        
        elif focus_type == 'strong_areas':
            # Maintain strong areas
            if strong_areas:
                index = (week_number - 1) % len(strong_areas)
                return [strong_areas[index]['topic']]
            return ['Review']
        
        elif focus_type == 'new_material':
            # Introduce new topics progressively
            all_topics = self.get_exam_topics()
            covered_topics = [area['topic'] for area in weak_areas + strong_areas]
            new_topics = [t for t in all_topics if t not in covered_topics]
            return new_topics[:2] if new_topics else ['Advanced Practice']
        
        elif focus_type == 'mixed_review':
            # Mix of weak and strong areas
            topics = []
            if weak_areas:
                topics.append(weak_areas[0]['topic'])
            if strong_areas:
                topics.append(strong_areas[0]['topic'])
            return topics or ['Comprehensive Review']
        
        else:  # light_review
            return ['Quick Review']

    def set_daily_goals(self, day_config, week_number):
        """Set specific goals for each study day"""
        base_accuracy = 70 + (week_number * 2)  # Progressive improvement
        
        if day_config['intensity'] == 'high':
            return {
                'target_accuracy': min(base_accuracy + 5, 90),
                'min_questions': 15,
                'focus': 'Intensive practice on weak areas'
            }
        elif day_config['intensity'] == 'medium':
            return {
                'target_accuracy': base_accuracy,
                'min_questions': 10,
                'focus': 'Balanced practice and learning'
            }
        else:  # low intensity
            return {
                'target_accuracy': base_accuracy - 5,
                'min_questions': 5,
                'focus': 'Light review and consolidation'
            }

    def calculate_question_count(self, duration_minutes):
        """Calculate recommended number of questions based on study duration"""
        # Assume 3-4 minutes per question including review
        return max(duration_minutes // 4, 5)

    def generate_ai_recommendations(self, performance_analysis, study_schedule):
        """Generate AI-powered study recommendations"""
        if not self.openai_client:
            return self.get_default_recommendations(performance_analysis)
        
        try:
            # Prepare context for AI
            context = {
                'exam_type': self.exam_type,
                'overall_accuracy': performance_analysis['overall_accuracy'],
                'weak_areas': [area['topic'] for area in performance_analysis['weak_areas'][:3]],
                'strong_areas': [area['topic'] for area in performance_analysis['strong_areas'][:3]],
                'days_until_exam': study_schedule['total_days'],
                'daily_study_time': study_schedule['daily_minutes']
            }
            
            prompt = f"""
            Create personalized study recommendations for a {self.exam_type} student with the following profile:
            
            Current Performance:
            - Overall accuracy: {context['overall_accuracy']:.1f}%
            - Weak areas: {', '.join(context['weak_areas']) if context['weak_areas'] else 'None identified'}
            - Strong areas: {', '.join(context['strong_areas']) if context['strong_areas'] else 'None identified'}
            - Study time available: {context['daily_study_time']} minutes/day for {context['days_until_exam']} days
            
            Provide specific, actionable recommendations in these categories:
            1. Study strategies for weak areas
            2. Maintenance strategies for strong areas  
            3. Time management tips
            4. Motivation and mindset advice
            5. Exam day preparation
            
            Format as JSON with categories as keys and arrays of recommendations as values.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert test prep tutor creating personalized study plans."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            recommendations = json.loads(response.choices[0].message.content)
            return recommendations
            
        except Exception as e:
            logging.error(f"Error generating AI recommendations: {e}")
            return self.get_default_recommendations(performance_analysis)

    def get_default_recommendations(self, performance_analysis):
        """Fallback recommendations when AI is not available"""
        weak_areas = performance_analysis['weak_areas']
        accuracy = performance_analysis['overall_accuracy']
        
        recommendations = {
            'study_strategies': [
                f"Focus 60% of study time on weak areas: {', '.join([a['topic'] for a in weak_areas[:3]])}",
                "Use spaced repetition for challenging concepts",
                "Practice questions daily with immediate review",
                "Create summary notes for each topic"
            ],
            'time_management': [
                "Study in focused 25-minute blocks with 5-minute breaks",
                "Reserve weekends for comprehensive review",
                "Track progress weekly to adjust plan as needed",
                "Maintain consistent daily study schedule"
            ],
            'motivation': [
                f"Current accuracy of {accuracy:.1f}% shows good foundation",
                "Celebrate small wins and progress milestones",
                "Join study groups for peer support",
                "Visualize exam success daily"
            ]
        }
        
        return recommendations

    def create_study_plan_record(self, daily_study_time, target_score, study_schedule, ai_recommendations):
        """Create StudyPlan database record"""
        try:
            # Estimate current score based on accuracy
            current_performance = self.analyze_performance_gaps()
            estimated_current_score = self.convert_accuracy_to_score(
                current_performance['overall_accuracy']
            )
            
            # Create comprehensive plan data
            plan_data = {
                'schedule': study_schedule,
                'recommendations': ai_recommendations,
                'performance_analysis': current_performance,
                'created_by': 'ai_planner_v1.0',
                'last_updated': datetime.utcnow().isoformat()
            }
            
            study_plan = StudyPlan(
                user_id=self.user_id,
                exam_type=self.exam_type,
                target_date=self.target_date,
                target_score=target_score or self.get_default_target_score(),
                current_score_estimate=estimated_current_score,
                daily_study_time=daily_study_time,
                plan_data=plan_data,
                is_active=True
            )
            
            db.session.add(study_plan)
            db.session.commit()
            
            return study_plan
            
        except Exception as e:
            logging.error(f"Error creating study plan record: {e}")
            db.session.rollback()
            raise

    def create_study_sessions(self, study_plan, study_schedule):
        """Create StudySession records for the plan"""
        try:
            sessions_created = 0
            
            for session_data in study_schedule['detailed_schedule']:
                study_session = StudySession(
                    study_plan_id=study_plan.id,
                    planned_date=session_data['date'],
                    planned_topics=json.dumps(session_data['topics']),
                    planned_duration=session_data['duration'],
                    notes=f"Focus: {session_data['focus_area']}, Intensity: {session_data['intensity']}"
                )
                
                db.session.add(study_session)
                sessions_created += 1
                
                # Commit in batches to avoid memory issues
                if sessions_created % 20 == 0:
                    db.session.commit()
            
            db.session.commit()
            logging.info(f"Created {sessions_created} study sessions for plan {study_plan.id}")
            
        except Exception as e:
            logging.error(f"Error creating study sessions: {e}")
            db.session.rollback()
            raise

    def create_study_goals(self, study_plan, performance_analysis):
        """Create StudyGoal records based on performance analysis"""
        try:
            goals_created = 0
            current_accuracy = performance_analysis['overall_accuracy']
            
            # Accuracy improvement goal
            target_accuracy = min(current_accuracy + 15, 90)
            accuracy_goal = StudyGoal(
                user_id=self.user_id,
                exam_type=self.exam_type,
                goal_type='accuracy',
                target_value=target_accuracy,
                current_value=current_accuracy,
                deadline=self.target_date
            )
            db.session.add(accuracy_goal)
            goals_created += 1
            
            # Weekly practice goal
            practice_goal = StudyGoal(
                user_id=self.user_id,
                exam_type=self.exam_type,
                goal_type='weekly_questions',
                target_value=70,  # 70 questions per week
                current_value=0,
                deadline=date.today() + timedelta(weeks=1)
            )
            db.session.add(practice_goal)
            goals_created += 1
            
            # Streak maintenance goal
            streak_goal = StudyGoal(
                user_id=self.user_id,
                exam_type=self.exam_type,
                goal_type='streak',
                target_value=14,  # 2-week streak
                current_value=0,
                deadline=date.today() + timedelta(days=14)
            )
            db.session.add(streak_goal)
            goals_created += 1
            
            db.session.commit()
            logging.info(f"Created {goals_created} study goals for plan {study_plan.id}")
            
        except Exception as e:
            logging.error(f"Error creating study goals: {e}")
            db.session.rollback()
            raise

    # Helper methods
    def get_exam_topics(self):
        """Get all topics for the exam type"""
        topics_by_exam = {
            'GMAT': ['Quantitative Reasoning', 'Verbal Reasoning', 'Integrated Reasoning', 'Analytical Writing'],
            'GRE': ['Quantitative Reasoning', 'Verbal Reasoning', 'Analytical Writing'],
            'MCAT': ['Chemical and Physical Foundations', 'Critical Analysis and Reasoning', 'Biological and Biochemical Foundations', 'Psychological, Social, and Biological Foundations'],
            'LSAT': ['Logical Reasoning', 'Reading Comprehension', 'Analytical Reasoning', 'Writing Sample'],
            'SAT': ['Evidence-Based Reading and Writing', 'Math'],
            'ACT': ['English', 'Mathematics', 'Reading', 'Science', 'Writing']
        }
        return topics_by_exam.get(self.exam_type, ['General'])

    def convert_accuracy_to_score(self, accuracy):
        """Convert accuracy percentage to exam score"""
        # Simplified conversion - would need exam-specific scaling
        score_mappings = {
            'GMAT': int(200 + (accuracy / 100) * 600),  # 200-800 scale
            'GRE': int(130 + (accuracy / 100) * 40),    # 130-170 scale
            'MCAT': int(472 + (accuracy / 100) * 56),   # 472-528 scale
            'SAT': int(400 + (accuracy / 100) * 1200),  # 400-1600 scale
            'ACT': int(1 + (accuracy / 100) * 35)       # 1-36 scale
        }
        return score_mappings.get(self.exam_type, int(accuracy))

    def get_default_target_score(self):
        """Get default target score for exam type"""
        defaults = {
            'GMAT': 650,
            'GRE': 155,
            'MCAT': 500,
            'SAT': 1200,
            'ACT': 24
        }
        return defaults.get(self.exam_type, 80)

    def get_default_performance_analysis(self):
        """Default analysis when no data available"""
        return {
            'overall_accuracy': 50,
            'total_questions': 0,
            'weak_areas': [{'topic': topic, 'accuracy': 50, 'questions_attempted': 0, 'priority': 0.8} 
                          for topic in self.get_exam_topics()],
            'strong_areas': [],
            'recommended_focus_time': {'weak_areas': 70, 'strong_areas': 0, 'new_material': 30},
            'study_intensity': 'intensive'
        }

    def get_default_schedule(self, daily_study_time):
        """Default schedule when generation fails"""
        return {
            'total_days': 60,
            'total_hours': 60,
            'daily_minutes': daily_study_time,
            'weekly_pattern': self.create_weekly_pattern(daily_study_time, {'weak_areas': 70, 'strong_areas': 20, 'new_material': 10}),
            'detailed_schedule': []
        }

# Utility functions for external use
def create_user_study_plan(user_id, exam_type, target_date=None, daily_study_time=60, target_score=None):
    """Main function to create a comprehensive study plan for a user"""
    try:
        generator = StudyPlanGenerator(user_id, exam_type, target_date)
        study_plan = generator.create_comprehensive_study_plan(daily_study_time, target_score)
        return study_plan
    except Exception as e:
        logging.error(f"Error creating user study plan: {e}")
        raise

def update_study_plan_progress(plan_id, session_data):
    """Update study plan progress based on completed session"""
    try:
        # Update the specific session
        session = StudySession.query.get(session_data.get('session_id'))
        if session:
            session.completed_date = date.today()
            session.actual_duration = session_data.get('duration')
            session.performance_score = session_data.get('accuracy')
            session.notes = session_data.get('notes', '')
            
            # Update completed topics
            if session_data.get('topics_completed'):
                session.completed_topics = json.dumps(session_data['topics_completed'])
            
        # Update overall plan progress
        study_plan = StudyPlan.query.get(plan_id)
        if study_plan and study_plan.plan_data:
            plan_data = study_plan.plan_data
            plan_data['last_updated'] = datetime.utcnow().isoformat()
            plan_data['progress_updated'] = True
            study_plan.plan_data = plan_data
        
        db.session.commit()
        logging.info(f"Updated study plan progress for plan {plan_id}")
        
    except Exception as e:
        logging.error(f"Error updating study plan progress: {e}")
        db.session.rollback()
        raise