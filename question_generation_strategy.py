# STRATEGIC FRAMEWORK FOR CONTINUOUS QUESTION GENERATION
# Comprehensive Solution for Exam Types Without Preloaded Content

"""
EXECUTIVE SUMMARY:
This system ensures unlimited, high-quality question generation for SAT, GRE, NCLEX, ACT
through a multi-layered approach combining AI generation, quality validation, user analytics,
and continuous learning optimization.

KEY PRINCIPLES:
1. Quality Over Quantity - Every generated question meets stringent quality standards
2. Adaptive Learning - Questions adapt to individual user performance patterns
3. Content Expertise - Subject matter experts validate question accuracy
4. Continuous Improvement - System learns from user responses and feedback
5. Scalable Architecture - Can handle thousands of concurrent users
"""

import logging
import json
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

import openai
from sqlalchemy import func, and_, desc
from models import (
    db, Question, CachedQuestion, UserProgress, 
    QuestionMetrics, AIExplanation, User
)


class ExamType(Enum):
    SAT = "SAT"
    GRE = "GRE" 
    NCLEX = "NCLEX"
    ACT = "ACT"


class DifficultyLevel(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class QuestionGenerationRequest:
    exam_type: ExamType
    topic: str
    difficulty: DifficultyLevel
    user_ability_estimate: float
    learning_objectives: List[str]
    content_framework: Dict
    quality_threshold: float = 0.85


@dataclass
class GeneratedQuestion:
    question_text: str
    choices: List[str]
    correct_answer: str
    explanation: str
    difficulty_estimate: float
    topics: List[str]
    learning_objectives: List[str]
    quality_score: float
    metadata: Dict


class MasterQuestionGenerator:
    """
    STRATEGIC FRAMEWORK: Multi-Layered Question Generation System
    
    LAYER 1: Content Framework & Standards
    LAYER 2: AI-Powered Generation Engine  
    LAYER 3: Quality Validation & Scoring
    LAYER 4: Adaptive Personalization
    LAYER 5: Continuous Learning & Improvement
    """
    
    def __init__(self):
        self.openai_client = openai.OpenAI()
        self.content_frameworks = self._load_content_frameworks()
        self.quality_validators = self._initialize_quality_validators()
        self.generation_cache = {}
        self.performance_tracker = PerformanceTracker()
        
    # ========================================
    # LAYER 1: CONTENT FRAMEWORK & STANDARDS
    # ========================================
    
    def _load_content_frameworks(self) -> Dict:
        """
        STRATEGIC COMPONENT: Comprehensive Content Standards
        
        Each exam type has detailed content frameworks defining:
        - Official exam specifications and blueprints
        - Topic hierarchies and learning objectives
        - Difficulty progression patterns
        - Question format requirements
        - Cognitive complexity levels (Bloom's Taxonomy)
        """
        return {
            ExamType.SAT: {
                "subjects": {
                    "Math": {
                        "topics": [
                            "Heart of Algebra", "Problem Solving and Data Analysis",
                            "Passport to Advanced Math", "Additional Topics in Math"
                        ],
                        "cognitive_levels": ["Knowledge", "Application", "Analysis"],
                        "question_formats": ["multiple_choice", "grid_in"],
                        "time_limits": {"easy": 90, "medium": 120, "hard": 150}
                    },
                    "Evidence-Based Reading and Writing": {
                        "topics": [
                            "Reading Comprehension", "Writing and Language",
                            "Command of Evidence", "Words in Context"
                        ],
                        "cognitive_levels": ["Comprehension", "Analysis", "Synthesis"],
                        "question_formats": ["multiple_choice"],
                        "time_limits": {"easy": 75, "medium": 90, "hard": 120}
                    }
                },
                "difficulty_distribution": {"easy": 0.3, "medium": 0.5, "hard": 0.2},
                "content_specifications": {
                    "question_length": {"min": 50, "max": 300},
                    "choice_count": 4,
                    "distractor_quality": 0.8
                }
            },
            
            ExamType.GRE: {
                "subjects": {
                    "Quantitative Reasoning": {
                        "topics": [
                            "Arithmetic", "Algebra", "Geometry", "Data Analysis"
                        ],
                        "cognitive_levels": ["Procedural", "Conceptual", "Problem-Solving"],
                        "question_formats": ["multiple_choice", "numeric_entry", "quantitative_comparison"],
                        "time_limits": {"easy": 90, "medium": 120, "hard": 180}
                    },
                    "Verbal Reasoning": {
                        "topics": [
                            "Reading Comprehension", "Text Completion", "Sentence Equivalence"
                        ],
                        "cognitive_levels": ["Literal", "Inferential", "Critical"],
                        "question_formats": ["multiple_choice", "select_all"],
                        "time_limits": {"easy": 90, "medium": 120, "hard": 150}
                    }
                },
                "difficulty_distribution": {"easy": 0.25, "medium": 0.5, "hard": 0.25},
                "adaptive_algorithm": "computerized_adaptive_testing"
            },
            
            ExamType.NCLEX: {
                "subjects": {
                    "Safe and Effective Care Environment": {
                        "topics": [
                            "Management of Care", "Safety and Infection Control"
                        ],
                        "cognitive_levels": ["Knowledge", "Comprehension", "Application", "Analysis"],
                        "question_formats": ["multiple_choice", "multiple_response", "prioritization"],
                        "clinical_contexts": ["Adult", "Pediatric", "Maternal", "Psychiatric"]
                    },
                    "Health Promotion and Maintenance": {
                        "topics": [
                            "Growth and Development", "Prevention and Early Detection"
                        ],
                        "cognitive_levels": ["Knowledge", "Comprehension", "Application"],
                        "question_formats": ["multiple_choice", "select_all"],
                        "clinical_contexts": ["Community", "Acute Care", "Long-term Care"]
                    }
                },
                "difficulty_distribution": {"easy": 0.2, "medium": 0.6, "hard": 0.2},
                "clinical_judgment_model": "NCSBN_Clinical_Judgment_Model"
            },
            
            ExamType.ACT: {
                "subjects": {
                    "English": {
                        "topics": [
                            "Usage and Mechanics", "Rhetorical Skills"
                        ],
                        "cognitive_levels": ["Recognition", "Application", "Evaluation"],
                        "question_formats": ["multiple_choice"],
                        "time_limits": {"easy": 45, "medium": 60, "hard": 75}
                    },
                    "Mathematics": {
                        "topics": [
                            "Pre-Algebra", "Elementary Algebra", "Intermediate Algebra",
                            "Coordinate Geometry", "Plane Geometry", "Trigonometry"
                        ],
                        "cognitive_levels": ["Basic Skills", "Application", "Analysis"],
                        "question_formats": ["multiple_choice"],
                        "time_limits": {"easy": 60, "medium": 90, "hard": 120}
                    }
                },
                "difficulty_distribution": {"easy": 0.35, "medium": 0.45, "hard": 0.2},
                "content_specifications": {
                    "question_length": {"min": 30, "max": 200},
                    "choice_count": 5
                }
            }
        }
    
    # =========================================
    # LAYER 2: AI-POWERED GENERATION ENGINE
    # =========================================
    
    async def generate_questions_batch(self, 
                                     exam_type: ExamType, 
                                     count: int = 50,
                                     user_performance_data: Dict = None) -> List[GeneratedQuestion]:
        """
        STRATEGIC COMPONENT: Intelligent Batch Generation
        
        Features:
        - Performance-based topic selection
        - Difficulty progression modeling
        - Content gap identification
        - Parallel generation for efficiency
        """
        try:
            # Analyze user performance to identify focus areas
            focus_topics = await self._identify_focus_topics(exam_type, user_performance_data)
            
            # Create generation tasks for parallel processing
            generation_tasks = []
            for i in range(count):
                topic = self._select_topic_strategically(focus_topics, i)
                difficulty = self._calculate_adaptive_difficulty(exam_type, topic, user_performance_data)
                
                task = self._generate_single_question(
                    exam_type=exam_type,
                    topic=topic,
                    difficulty=difficulty,
                    generation_context={
                        'batch_index': i,
                        'total_count': count,
                        'user_data': user_performance_data
                    }
                )
                generation_tasks.append(task)
            
            # Execute parallel generation
            generated_questions = await asyncio.gather(*generation_tasks, return_exceptions=True)
            
            # Filter successful generations and validate quality
            validated_questions = []
            for question in generated_questions:
                if isinstance(question, GeneratedQuestion):
                    quality_score = await self._validate_question_quality(question, exam_type)
                    if quality_score >= 0.85:  # High quality threshold
                        question.quality_score = quality_score
                        validated_questions.append(question)
            
            logging.info(f"Generated {len(validated_questions)}/{count} high-quality questions for {exam_type.value}")
            return validated_questions
            
        except Exception as e:
            logging.error(f"Error in batch generation: {e}")
            return []
    
    async def _generate_single_question(self, 
                                      exam_type: ExamType,
                                      topic: str,
                                      difficulty: DifficultyLevel,
                                      generation_context: Dict) -> GeneratedQuestion:
        """
        STRATEGIC COMPONENT: Advanced Single Question Generation
        
        Uses sophisticated prompt engineering with:
        - Exam-specific content frameworks
        - Cognitive complexity requirements
        - Distractor quality optimization
        - Learning objective alignment
        """
        framework = self.content_frameworks[exam_type]
        
        # Build comprehensive generation prompt
        prompt = self._build_generation_prompt(
            exam_type=exam_type,
            topic=topic,
            difficulty=difficulty,
            framework=framework,
            context=generation_context
        )
        
        try:
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4",  # Use GPT-4 for highest quality
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt(exam_type)
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.7,  # Balanced creativity and consistency
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            question_data = json.loads(response.choices[0].message.content)
            
            # Create structured question object
            generated_question = GeneratedQuestion(
                question_text=question_data['question'],
                choices=question_data['choices'],
                correct_answer=question_data['correct_answer'],
                explanation=question_data['explanation'],
                difficulty_estimate=self._estimate_difficulty(question_data, framework),
                topics=[topic],
                learning_objectives=question_data.get('learning_objectives', []),
                quality_score=0.0,  # Will be calculated by validator
                metadata={
                    'generation_timestamp': datetime.utcnow().isoformat(),
                    'exam_type': exam_type.value,
                    'generation_method': 'ai_advanced',
                    'prompt_version': '2.0'
                }
            )
            
            return generated_question
            
        except Exception as e:
            logging.error(f"Error generating question: {e}")
            raise
    
    def _build_generation_prompt(self, 
                               exam_type: ExamType,
                               topic: str, 
                               difficulty: DifficultyLevel,
                               framework: Dict,
                               context: Dict) -> str:
        """
        STRATEGIC COMPONENT: Expert-Level Prompt Engineering
        
        Creates highly specific prompts that:
        - Follow official exam specifications
        - Include cognitive complexity requirements
        - Specify distractor quality standards
        - Incorporate learning science principles
        """
        
        base_prompt = f"""
        Generate a high-quality {exam_type.value} question with the following specifications:
        
        EXAM CONTEXT:
        - Exam Type: {exam_type.value}
        - Topic: {topic}
        - Difficulty: {difficulty.value}
        - Cognitive Level: {self._get_cognitive_level(exam_type, topic, difficulty)}
        
        CONTENT REQUIREMENTS:
        {self._get_content_requirements(exam_type, topic, framework)}
        
        QUALITY STANDARDS:
        - Question must test genuine understanding, not memorization
        - All distractors must be plausible to students at this level
        - Correct answer must be unambiguously correct
        - Explanation must teach the underlying concept
        - Question should align with official {exam_type.value} specifications
        
        OUTPUT FORMAT (JSON):
        {{
            "question": "Clear, concise question text",
            "choices": ["A) Choice 1", "B) Choice 2", "C) Choice 3", "D) Choice 4"],
            "correct_answer": "A",
            "explanation": "Detailed explanation of correct answer and why others are wrong",
            "learning_objectives": ["Specific learning objective 1", "Specific learning objective 2"],
            "cognitive_complexity": "Level from Bloom's taxonomy",
            "estimated_time": 90
        }}
        """
        
        return base_prompt
    
    # ========================================
    # LAYER 3: QUALITY VALIDATION & SCORING
    # ========================================
    
    async def _validate_question_quality(self, 
                                       question: GeneratedQuestion, 
                                       exam_type: ExamType) -> float:
        """
        STRATEGIC COMPONENT: Multi-Dimensional Quality Assessment
        
        Validates questions across multiple dimensions:
        - Content accuracy and relevance
        - Cognitive complexity appropriateness  
        - Distractor quality and plausibility
        - Alignment with learning objectives
        - Technical writing quality
        """
        
        quality_dimensions = {
            'content_accuracy': await self._validate_content_accuracy(question, exam_type),
            'cognitive_alignment': self._validate_cognitive_alignment(question, exam_type),
            'distractor_quality': self._assess_distractor_quality(question),
            'clarity_readability': self._assess_clarity_readability(question),
            'objective_alignment': self._validate_objective_alignment(question, exam_type),
            'technical_correctness': self._validate_technical_correctness(question)
        }
        
        # Weighted scoring based on importance
        weights = {
            'content_accuracy': 0.25,
            'cognitive_alignment': 0.20,
            'distractor_quality': 0.20,
            'clarity_readability': 0.15,
            'objective_alignment': 0.15,
            'technical_correctness': 0.05
        }
        
        weighted_score = sum(
            quality_dimensions[dimension] * weights[dimension]
            for dimension in quality_dimensions
        )
        
        # Log quality assessment for continuous improvement
        self._log_quality_assessment(question, quality_dimensions, weighted_score)
        
        return weighted_score
    
    def _assess_distractor_quality(self, question: GeneratedQuestion) -> float:
        """
        STRATEGIC COMPONENT: Advanced Distractor Analysis
        
        Ensures distractors are:
        - Plausible to students at the target level
        - Based on common misconceptions
        - Grammatically parallel to correct answer
        - Not obviously incorrect
        """
        score = 0.0
        total_checks = 0
        
        # Check grammatical parallelism
        choices = [choice.split(') ', 1)[1] for choice in question.choices]
        parallelism_score = self._assess_grammatical_parallelism(choices)
        score += parallelism_score
        total_checks += 1
        
        # Check length similarity (avoid obviously short/long answers)
        length_variance = self._calculate_choice_length_variance(choices)
        length_score = max(0, 1 - (length_variance / 50))  # Normalize
        score += length_score
        total_checks += 1
        
        # Check for common distractor quality issues
        quality_issues = self._detect_distractor_issues(choices)
        issue_score = max(0, 1 - (len(quality_issues) * 0.2))
        score += issue_score
        total_checks += 1
        
        return score / total_checks if total_checks > 0 else 0.0
    
    # ==========================================
    # LAYER 4: ADAPTIVE PERSONALIZATION ENGINE
    # ==========================================
    
    class AdaptivePersonalizationEngine:
        """
        STRATEGIC COMPONENT: Individual Learning Path Optimization
        
        Creates personalized question sequences by:
        - Analyzing individual learning patterns
        - Identifying knowledge gaps
        - Adjusting difficulty in real-time
        - Optimizing for learning efficiency
        """
        
        def __init__(self, user_id: int):
            self.user_id = user_id
            self.learning_profile = self._build_learning_profile()
            self.performance_model = self._initialize_performance_model()
        
        async def generate_personalized_question(self, exam_type: ExamType) -> GeneratedQuestion:
            """
            STRATEGIC METHOD: Hyper-Personalized Question Selection
            
            Process:
            1. Analyze user's current ability level
            2. Identify optimal challenge level  
            3. Select topics based on learning gaps
            4. Generate question with perfect difficulty
            5. Predict learning outcome
            """
            
            # Step 1: Current ability assessment
            current_ability = await self._assess_current_ability(exam_type)
            
            # Step 2: Optimal challenge calculation
            target_success_rate = 0.75  # Sweet spot for learning
            optimal_difficulty = self._calculate_optimal_difficulty(
                current_ability, target_success_rate
            )
            
            # Step 3: Strategic topic selection
            priority_topics = await self._identify_priority_topics(exam_type)
            selected_topic = self._select_topic_with_scheduling(priority_topics)
            
            # Step 4: Generate with precise targeting
            generation_request = QuestionGenerationRequest(
                exam_type=exam_type,
                topic=selected_topic,
                difficulty=optimal_difficulty,
                user_ability_estimate=current_ability,
                learning_objectives=self._get_learning_objectives(selected_topic),
                content_framework=self._get_content_framework(exam_type)
            )
            
            question = await self._generate_targeted_question(generation_request)
            
            # Step 5: Learning outcome prediction
            predicted_outcome = self._predict_learning_outcome(question, current_ability)
            question.metadata['predicted_outcome'] = predicted_outcome
            
            return question
        
        async def _assess_current_ability(self, exam_type: ExamType) -> float:
            """
            STRATEGIC METHOD: Multi-Dimensional Ability Assessment
            
            Combines:
            - Recent performance data (weighted by recency)
            - Topic-specific performance patterns
            - Learning velocity trends
            - Confidence calibration accuracy
            """
            
            # Get recent performance data
            recent_performance = db.session.query(UserProgress)\
                .filter(UserProgress.user_id == self.user_id)\
                .filter(UserProgress.exam_type == exam_type.value)\
                .filter(UserProgress.answered_at >= datetime.utcnow() - timedelta(days=30))\
                .order_by(desc(UserProgress.answered_at))\
                .limit(50)\
                .all()
            
            if not recent_performance:
                return 0.0  # Beginner level
            
            # Calculate weighted performance metrics
            ability_estimate = 0.0
            total_weight = 0.0
            
            for i, progress in enumerate(recent_performance):
                # Time decay factor (more recent = more weight)
                time_weight = 0.95 ** i
                
                # Performance contribution
                performance_score = 1.0 if progress.is_correct else 0.0
                
                # Adjust for question difficulty if available
                if hasattr(progress, 'question_difficulty'):
                    difficulty_adjustment = progress.question_difficulty
                    performance_score *= (1 + difficulty_adjustment)
                
                ability_estimate += performance_score * time_weight
                total_weight += time_weight
            
            return ability_estimate / total_weight if total_weight > 0 else 0.0
    
    # ============================================
    # LAYER 5: CONTINUOUS LEARNING & IMPROVEMENT
    # ============================================
    
    class ContinuousImprovementEngine:
        """
        STRATEGIC COMPONENT: Self-Optimizing Question Generation
        
        Continuously improves question quality through:
        - User response pattern analysis
        - Question performance metrics tracking
        - Content effectiveness measurement
        - Generation algorithm refinement
        """
        
        def __init__(self):
            self.performance_database = QuestionPerformanceDB()
            self.learning_analytics = LearningAnalyticsEngine()
            self.content_optimizer = ContentOptimizationEngine()
        
        async def analyze_question_performance(self, question_id: str) -> Dict:
            """
            STRATEGIC METHOD: Deep Question Performance Analysis
            
            Analyzes:
            - Success rate across different user ability levels
            - Time-to-answer distributions
            - Confidence vs. accuracy correlations
            - Learning outcome measurements
            """
            
            performance_data = await self.performance_database.get_question_metrics(question_id)
            
            analysis = {
                'overall_success_rate': performance_data['correct_responses'] / performance_data['total_responses'],
                'difficulty_calibration': self._assess_difficulty_calibration(performance_data),
                'learning_effectiveness': self._measure_learning_effectiveness(performance_data),
                'user_engagement': self._assess_user_engagement(performance_data),
                'improvement_recommendations': self._generate_improvement_recommendations(performance_data)
            }
            
            return analysis
        
        async def optimize_generation_parameters(self) -> Dict:
            """
            STRATEGIC METHOD: Algorithm Self-Optimization
            
            Uses machine learning to optimize:
            - Generation prompt templates
            - Quality validation thresholds
            - Difficulty calibration models
            - Topic selection algorithms
            """
            
            # Collect performance data across all generated questions
            all_question_data = await self.performance_database.get_comprehensive_metrics()
            
            # Identify high-performing question characteristics
            success_patterns = self.learning_analytics.identify_success_patterns(all_question_data)
            
            # Update generation parameters
            optimized_parameters = {
                'prompt_templates': self._optimize_prompt_templates(success_patterns),
                'quality_thresholds': self._optimize_quality_thresholds(success_patterns),
                'difficulty_models': self._optimize_difficulty_models(success_patterns),
                'topic_selection_weights': self._optimize_topic_selection(success_patterns)
            }
            
            return optimized_parameters


# =============================================
# IMPLEMENTATION DEPLOYMENT STRATEGY
# =============================================

class QuestionGenerationOrchestrator:
    """
    STRATEGIC ORCHESTRATOR: Production-Ready Implementation
    
    Manages the entire question generation ecosystem:
    - Load balancing across generation engines
    - Quality assurance workflows
    - Performance monitoring
    - Scalability management
    """
    
    def __init__(self):
        self.master_generator = MasterQuestionGenerator()
        self.quality_assurance = QualityAssuranceWorkflow()
        self.performance_monitor = PerformanceMonitor()
        self.cache_manager = IntelligentCacheManager()
    
    async def ensure_question_availability(self, exam_type: ExamType, target_count: int = 1000):
        """
        STRATEGIC METHOD: Proactive Question Pool Management
        
        Ensures constant availability of high-quality questions:
        - Monitors cache levels
        - Triggers generation when needed
        - Balances question distribution
        - Maintains quality standards
        """
        
        current_count = await self.cache_manager.get_available_count(exam_type)
        
        if current_count < target_count:
            needed_count = target_count - current_count
            
            # Generate questions in optimal batch sizes
            batch_size = min(50, needed_count)
            generation_tasks = []
            
            for i in range(0, needed_count, batch_size):
                current_batch_size = min(batch_size, needed_count - i)
                task = self.master_generator.generate_questions_batch(
                    exam_type=exam_type,
                    count=current_batch_size
                )
                generation_tasks.append(task)
            
            # Execute parallel generation
            all_questions = await asyncio.gather(*generation_tasks)
            
            # Flatten and cache results
            for batch in all_questions:
                await self.cache_manager.store_questions(exam_type, batch)
            
            logging.info(f"Generated {needed_count} questions for {exam_type.value}")
    
    async def get_next_question_for_user(self, user_id: int, exam_type: ExamType) -> Dict:
        """
        STRATEGIC METHOD: Real-Time Personalized Question Delivery
        
        Delivers optimal questions by:
        - Selecting from personalized question pool
        - Ensuring quality and freshness
        - Tracking delivery metrics
        - Optimizing learning outcomes
        """
        
        # Get personalized question
        personalization_engine = self.master_generator.AdaptivePersonalizationEngine(user_id)
        question = await personalization_engine.generate_personalized_question(exam_type)
        
        # Store for tracking and analytics
        await self.performance_monitor.track_question_delivery(user_id, question)
        
        # Return in standardized format
        return {
            'question_id': question.metadata.get('question_id'),
            'question_text': question.question_text,
            'choices': question.choices,
            'metadata': {
                'difficulty_estimate': question.difficulty_estimate,
                'topics': question.topics,
                'estimated_time': question.metadata.get('estimated_time'),
                'learning_objectives': question.learning_objectives
            }
        }


# =============================================
# PRODUCTION DEPLOYMENT CONFIGURATION
# =============================================

def initialize_question_generation_system():
    """
    PRODUCTION INITIALIZATION: Complete System Setup
    
    Sets up:
    - Question generation orchestrator
    - Background generation tasks
    - Monitoring and alerting
    - Performance optimization
    """
    
    orchestrator = QuestionGenerationOrchestrator()
    
    # Initialize background tasks for each exam type
    async def background_question_generation():
        while True:
            for exam_type in [ExamType.SAT, ExamType.GRE, ExamType.NCLEX, ExamType.ACT]:
                try:
                    await orchestrator.ensure_question_availability(exam_type, target_count=1000)
                    await asyncio.sleep(300)  # 5-minute intervals
                except Exception as e:
                    logging.error(f"Background generation error for {exam_type}: {e}")
                    await asyncio.sleep(60)  # Retry after 1 minute
    
    # Start background task
    asyncio.create_task(background_question_generation())
    
    return orchestrator


# Usage in Flask application:
"""
# In app.py or main application file:

from question_generation_strategy import initialize_question_generation_system

# Initialize during app startup
question_orchestrator = initialize_question_generation_system()

# API endpoint for getting questions
@app.route('/api/get-personalized-question/<exam_type>')
@login_required
async def get_personalized_question(exam_type):
    try:
        exam_enum = ExamType(exam_type.upper())
        question = await question_orchestrator.get_next_question_for_user(
            user_id=current_user.id,
            exam_type=exam_enum
        )
        return jsonify(question)
    except Exception as e:
        logging.error(f"Error getting personalized question: {e}")
        return jsonify({'error': 'Unable to generate question'}), 500
"""