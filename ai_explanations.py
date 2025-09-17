import os
import logging
import json
import random
from openai import OpenAI
import time
from models import Question, QuestionMetrics, CachedQuestion, db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize xAI (Grok) client conditionally
try:
    api_key = os.environ.get("XAI_API_KEY")
    if api_key:
        client = OpenAI(
            base_url="https://api.x.ai/v1",
            api_key=api_key
        )
        logger.info("xAI (Grok) client initialized successfully")
    else:
        client = None
        logger.warning("XAI_API_KEY not found - AI explanations will be disabled")
except Exception as e:
    client = None
    logger.error(f"Failed to initialize xAI client: {e}")

def get_dual_explanations(question, answer_choice, is_correct):
    """
    Generate both technical and simplified explanations using OpenAI.
    
    Args:
        question (str): The question text
        answer_choice (str): The selected answer choice
        is_correct (bool): Whether the answer was correct
        
    Returns:
        tuple: (technical_explanation, simplified_explanation)
    """
    # Check if xAI client is available
    if client is None:
        logger.warning("xAI client not available - using fallback explanations")
        return get_fallback_explanations(question, answer_choice, is_correct)
    

    
    try:
        # Build enhanced prompts for xAI Grok
        if is_correct:
            prompt = f"""
            You are an expert tutor providing detailed explanations for test preparation. The user correctly answered this question:
            
            Question: {question}
            Correct Answer: {answer_choice}
            
            Provide comprehensive explanations in exactly this format:
            
            TECHNICAL: Write a detailed academic explanation (150-200 words) covering:
            - The specific concept being tested
            - Why this answer is correct with step-by-step reasoning
            - Key terminology and principles involved
            - Common patterns or rules that apply
            
            SIMPLIFIED: Write a clear, conversational explanation (100-150 words) that:
            - Explains the concept in simple terms
            - Uses analogies or examples when helpful
            - Highlights the main takeaway
            - Encourages the student's understanding
            
            Make both explanations educational, engaging, and tailored to help the student master similar questions.
            """
        else:
            prompt = f"""
            You are an expert tutor providing detailed explanations for test preparation. The user incorrectly answered this question:
            
            Question: {question}
            User's Incorrect Answer: {answer_choice}
            
            Provide comprehensive explanations in exactly this format:
            
            TECHNICAL: Write a detailed academic explanation (200-250 words) covering:
            - The specific concept being tested
            - Why the chosen answer is incorrect (specific reasoning)
            - What the correct answer should be and why
            - The underlying principles or rules violated
            - How to avoid this mistake in future questions
            
            SIMPLIFIED: Write a clear, supportive explanation (150-200 words) that:
            - Explains what went wrong in simple terms
            - Shows the correct approach step-by-step
            - Provides a memory tip or strategy
            - Encourages continued learning
            
            Make both explanations constructive, educational, and designed to prevent similar mistakes.
            """
        
        # Make the API call
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                response = client.chat.completions.create(
                    model="grok-2-1212",  # Use xAI's Grok model
                    messages=[
                        {"role": "system", "content": "You are an expert educational tutor who provides detailed, comprehensive explanations for test preparation. Always format your response with clear TECHNICAL: and SIMPLIFIED: sections."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=800  # Increased for more detailed explanations
                )
                
                # Extract content from response
                content = response.choices[0].message.content
                
                # Parse the response to extract the technical and simplified explanations
                technical_explanation = ""
                simplified_explanation = ""
                
                if "TECHNICAL:" in content and "SIMPLIFIED:" in content:
                    # Split the content by the markers
                    parts = content.split("SIMPLIFIED:")
                    if len(parts) >= 2:
                        technical_part = parts[0]
                        simplified_part = parts[1]
                        
                        # Clean up the technical part
                        if "TECHNICAL:" in technical_part:
                            technical_explanation = technical_part.split("TECHNICAL:")[1].strip()
                        else:
                            technical_explanation = technical_part.strip()
                            
                        # The simplified part is already clean
                        simplified_explanation = simplified_part.strip()
                else:
                    # Fallback if format is not as expected
                    technical_explanation = "Sorry, we couldn't generate a specific explanation for this answer."
                    simplified_explanation = "We're having trouble explaining this one. Please try another question!"
                
                return technical_explanation, simplified_explanation
                
            except Exception as e:
                error_str = str(e).lower()
                retry_count += 1
                logger.error(f"Error calling xAI API (attempt {retry_count}/{max_retries}): {str(e)}")
                
                # Check for quota/rate limit errors - don't retry these
                if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
                    logger.warning(f"xAI quota exhausted, using fallback explanations")
                    return get_fallback_explanations(question, answer_choice, is_correct)
                
                if retry_count < max_retries:
                    # Exponential backoff
                    time.sleep(2 ** retry_count)
                else:
                    raise
        
    except Exception as e:
        error_str = str(e).lower()
        logger.error(f"Failed to generate AI explanations: {str(e)}")
        
        # Check for quota/rate limit errors
        if "429" in error_str or "quota" in error_str or "rate limit" in error_str:
            logger.warning("OpenAI API quota exhausted, using fallback explanations")
            return get_fallback_explanations(question, answer_choice, is_correct)
        
        return get_fallback_explanations(question, answer_choice, is_correct)

class QuestionGenerator:
    """AI-powered question generation system"""
    
    def __init__(self, exam_type):
        self.exam_type = exam_type
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.client = OpenAI(api_key=api_key)
            else:
                self.client = None
                logger.warning("OPENAI_API_KEY not found - question generation will be disabled")
        except Exception as e:
            self.client = None
            logger.error(f"Failed to initialize OpenAI client: {e}")
        self.generation_templates = self._load_generation_templates()
    
    def _load_generation_templates(self):
        """Load exam-specific generation templates"""
        templates = {
            'GMAT': {
                'subjects': ['quantitative', 'verbal', 'integrated_reasoning'],
                'topics': {
                    'quantitative': ['arithmetic', 'algebra', 'geometry', 'data_sufficiency'],
                    'verbal': ['critical_reasoning', 'reading_comprehension', 'sentence_correction'],
                    'integrated_reasoning': ['multi_source_reasoning', 'table_analysis', 'graphics_interpretation']
                },
                'difficulty_levels': ['medium', 'hard', 'expert']
            },
            'MCAT': {
                'subjects': ['biology', 'chemistry', 'physics', 'psychology'],
                'topics': {
                    'biology': ['cell_biology', 'genetics', 'evolution', 'ecology'],
                    'chemistry': ['organic', 'general', 'biochemistry'],
                    'physics': ['mechanics', 'thermodynamics', 'electromagnetism'],
                    'psychology': ['cognitive', 'behavioral', 'social']
                },
                'difficulty_levels': ['medium', 'hard']
            },
            'GRE': {
                'subjects': ['quantitative', 'verbal'],
                'topics': {
                    'quantitative': ['arithmetic', 'algebra', 'geometry', 'data_analysis'],
                    'verbal': ['reading_comprehension', 'text_completion', 'sentence_equivalence']
                },
                'difficulty_levels': ['medium', 'hard']
            }
        }
        
        return templates.get(self.exam_type, {
            'subjects': ['general'],
            'topics': {'general': ['critical_thinking', 'problem_solving']},
            'difficulty_levels': ['medium', 'hard']
        })
    
    def generate_question(self, topic, difficulty, subject=None):
        """Generate a single question for specified topic and difficulty"""
        if not self.client:
            logger.warning("OpenAI client not available for question generation")
            return None
        
        try:
            # Build context-specific prompt
            prompt = self._build_generation_prompt(topic, difficulty, subject)
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are an expert {self.exam_type} question writer with deep knowledge of standardized test formats."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.8
            )
            
            generated_content = response.choices[0].message.content
            question_data = self._parse_generated_question(generated_content, topic, difficulty, subject)
            
            if self.validate_generated_question(question_data):
                return question_data
            else:
                logger.warning(f"Generated question failed validation for {topic}/{difficulty}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating question: {e}")
            return None
    
    def _build_generation_prompt(self, topic, difficulty, subject):
        """Build exam-specific generation prompt"""
        base_prompt = f"""
        Generate a high-quality {self.exam_type} practice question with the following specifications:
        
        Topic: {topic}
        Subject: {subject or 'general'}
        Difficulty: {difficulty}
        
        Requirements:
        1. Question must be realistic and representative of actual {self.exam_type} questions
        2. Include exactly 4 answer choices (A, B, C, D)
        3. Only one correct answer
        4. Include detailed explanation for the correct answer
        5. Question should test {topic} concepts at {difficulty} level
        
        Format your response exactly as follows:
        QUESTION: [Your question text here]
        CHOICES:
        A) [Choice A]
        B) [Choice B] 
        C) [Choice C]
        D) [Choice D]
        CORRECT: [Letter of correct answer]
        EXPLANATION: [Detailed explanation of why the correct answer is right and others are wrong]
        """
        
        # Add exam-specific guidance
        if self.exam_type == 'GMAT':
            base_prompt += "\nEnsure quantitative questions include numerical reasoning and verbal questions test logical analysis."
        elif self.exam_type == 'MCAT':
            base_prompt += "\nInclude scientific reasoning and evidence-based analysis appropriate for medical school preparation."
        elif self.exam_type == 'GRE':
            base_prompt += "\nFocus on graduate-level reasoning and vocabulary appropriate for academic success."
        
        return base_prompt
    
    def _parse_generated_question(self, content, topic, difficulty, subject):
        """Parse AI-generated content into structured question data"""
        try:
            lines = content.strip().split('\n')
            question_data = {
                'exam_type': self.exam_type,
                'subject': subject or 'general',
                'difficulty': difficulty,
                'topics': [topic],
                'is_generated': True,
                'generation_source': 'openai_gpt4'
            }
            
            current_section = None
            choices = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('QUESTION:'):
                    question_data['question_text'] = line[9:].strip()
                elif line.startswith('CHOICES:'):
                    current_section = 'choices'
                elif line.startswith('CORRECT:'):
                    question_data['correct_answer'] = line[8:].strip()
                elif line.startswith('EXPLANATION:'):
                    question_data['explanation'] = line[12:].strip()
                elif current_section == 'choices' and line:
                    if line.startswith(('A)', 'B)', 'C)', 'D)')):
                        choice_letter = line[0]
                        choice_text = line[2:].strip()
                        choices[choice_letter] = choice_text
            
            question_data['choices'] = [choices.get(letter, '') for letter in ['A', 'B', 'C', 'D']]
            question_data['id'] = f"gen_{self.exam_type.lower()}_{random.randint(100000, 999999)}"
            
            return question_data
            
        except Exception as e:
            logger.error(f"Error parsing generated question: {e}")
            return None
    
    def validate_generated_question(self, question_data):
        """Validate generated question meets quality standards"""
        if not question_data:
            return False
        
        required_fields = ['id', 'exam_type', 'question_text', 'choices', 'correct_answer', 'explanation']
        for field in required_fields:
            if field not in question_data or not question_data[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate choices
        if len(question_data['choices']) != 4:
            logger.warning("Question must have exactly 4 choices")
            return False
        
        # Check correct answer format
        if question_data['correct_answer'] not in ['A', 'B', 'C', 'D']:
            logger.warning(f"Invalid correct answer format: {question_data['correct_answer']}")
            return False
        
        # Check question length (reasonable bounds)
        question_length = len(question_data['question_text'])
        if question_length < 20 or question_length > 1000:
            logger.warning(f"Question length ({question_length}) outside acceptable range")
            return False
        
        # Check explanation quality
        explanation_length = len(question_data['explanation'])
        if explanation_length < 50:
            logger.warning("Explanation too short")
            return False
        
        return True

def get_fallback_explanations(question, answer_choice, is_correct):
    """Provide fallback explanations when OpenAI is not available"""
    if is_correct:
        technical = "Your answer is correct. This demonstrates good understanding of the key concepts."
        simplified = "Great job! You got this one right."
    else:
        technical = "This answer is incorrect. Please review the relevant concepts and try similar questions for practice."
        simplified = "Not quite right. Don't worry - keep practicing and you'll improve!"
    
    return technical, simplified
    
    def batch_generate_questions(self, count=50, topics=None, difficulties=None):
        """Generate multiple questions in batch"""
        if not topics:
            topics = []
            for subject_topics in self.generation_templates.get('topics', {}).values():
                topics.extend(subject_topics)
        
        if not difficulties:
            difficulties = self.generation_templates.get('difficulty_levels', ['medium', 'hard'])
        
        generated_questions = []
        generation_summary = {
            'total_attempted': count,
            'successful': 0,
            'failed': 0,
            'validation_failures': 0
        }
        
        for i in range(count):
            # Randomly select topic and difficulty
            topic = random.choice(topics)
            difficulty = random.choice(difficulties)
            
            # Generate question
            question_data = self.generate_question(topic, difficulty)
            
            if question_data:
                # Store in database
                try:
                    # Add to Question table
                    question = Question()
                    question.id = question_data['id']
                    question.exam_type = question_data['exam_type']
                    question.subject = question_data.get('subject')
                    question.difficulty = question_data['difficulty']
                    question.question_text = question_data['question_text']
                    question.choices = question_data['choices']
                    question.correct_answer = question_data['correct_answer']
                    question.explanation = question_data['explanation']
                    question.topics = question_data.get('topics')
                    question.is_generated = True
                    question.generation_source = question_data.get('generation_source')
                    
                    # Add to cache
                    cached_question = CachedQuestion()
                    cached_question.question_id = question_data['id']
                    cached_question.exam_type = question_data['exam_type']
                    cached_question.difficulty = question_data['difficulty']
                    cached_question.question = question_data['question_text']
                    cached_question.choices = question_data['choices']
                    cached_question.correct_answer = question_data['correct_answer']
                    cached_question.explanation = question_data['explanation']
                    
                    db.session.add(question)
                    db.session.add(cached_question)
                    
                    generated_questions.append(question_data)
                    generation_summary['successful'] += 1
                    
                except Exception as e:
                    logger.error(f"Error storing generated question: {e}")
                    generation_summary['failed'] += 1
            else:
                generation_summary['failed'] += 1
            
            # Add delay to respect rate limits
            time.sleep(1)
        
        try:
            db.session.commit()
            logger.info(f"Successfully generated and stored {generation_summary['successful']} questions")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error committing generated questions: {e}")
        
        return generation_summary