"""
xAI (Grok) Question Generation Engine
Replaces OpenAI with xAI for generating exam questions with identical JSON format
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class XAIQuestionGenerator:
    """xAI-powered question generator using Grok models"""
    
    def __init__(self):
        """Initialize xAI client with custom endpoint"""
        try:
            self.client = OpenAI(
                base_url="https://api.x.ai/v1",
                api_key=os.environ.get("XAI_API_KEY")
            )
            logger.info("✅ xAI client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize xAI client: {e}")
            raise
    
    def generate_questions(self, exam_type: str, topic: str = None, count: int = 5) -> List[Dict]:
        """
        Generate exam questions using xAI Grok model
        
        Args:
            exam_type: Type of exam (GMAT, GRE, MCAT, etc.)
            topic: Specific topic (optional)
            count: Number of questions to generate (max 10)
            
        Returns:
            List of question dictionaries with OpenAI-compatible format
        """
        try:
            # Limit count to prevent API overuse
            count = min(count, 10)
            
            # Generate system prompt optimized for Grok's reasoning
            system_prompt = self._create_system_prompt(exam_type, topic)
            user_prompt = self._create_user_prompt(exam_type, topic, count)
            
            logger.info(f"🤖 Generating {count} {exam_type} questions{f' on {topic}' if topic else ''}")
            
            # Call xAI API with retry logic
            response = self._call_xai_with_retry(system_prompt, user_prompt)
            
            # Parse and validate response
            questions = self._parse_response(response, exam_type)
            
            logger.info(f"✅ Generated {len(questions)} questions successfully")
            return questions
            
        except Exception as e:
            logger.error(f"❌ Question generation failed: {e}")
            raise
    
    def generate_adaptive_questions(self, exam_type: str, topic: str, difficulty: str, user_score: float, count: int = 1) -> List[Dict]:
        """
        Generate adaptive questions based on user performance
        
        Args:
            exam_type: Type of exam (GMAT, GRE, MCAT, etc.)
            topic: Specific topic to focus on
            difficulty: Difficulty level (easy, medium, hard)
            user_score: User's current score percentage
            count: Number of questions to generate
            
        Returns:
            List of adaptive question dictionaries
        """
        try:
            count = min(count, 5)  # Limit for adaptive generation
            
            # Create adaptive system prompt with user context
            system_prompt = self._create_adaptive_system_prompt(exam_type, topic, difficulty, user_score)
            user_prompt = self._create_adaptive_user_prompt(exam_type, topic, difficulty, count)
            
            logger.info(f"🎯 Generating {count} adaptive {difficulty} {exam_type} questions on {topic} (user score: {user_score:.1f}%)")
            
            # Call xAI API with retry logic
            response = self._call_xai_with_retry(system_prompt, user_prompt)
            
            # Parse and validate response
            questions = self._parse_response(response, exam_type)
            
            # Add difficulty metadata
            for question in questions:
                question['difficulty'] = difficulty
                question['adaptive'] = True
                question['user_context'] = {
                    'score': user_score,
                    'topic': topic,
                    'target_difficulty': difficulty
                }
            
            logger.info(f"✅ Generated {len(questions)} adaptive {difficulty} questions")
            return questions
            
        except Exception as e:
            logger.error(f"❌ Adaptive question generation failed: {e}")
            raise
    
    def _create_system_prompt(self, exam_type: str, topic: str = None) -> str:
        """Create system prompt optimized for Grok's reasoning capabilities"""
        
        base_prompt = f"""You are an expert {exam_type} question generator with deep understanding of exam patterns and difficulty levels.

CRITICAL REQUIREMENTS:
1. Generate unique, original multiple-choice questions that have never been used before
2. Each question must have exactly 4 options (A, B, C, D)
3. Ensure one correct answer and three plausible distractors
4. Match authentic {exam_type} difficulty and style exactly
5. Provide detailed explanations for correct answers

OUTPUT FORMAT (JSON only):
{{
  "questions": [
    {{
      "question": "Question text here",
      "options": {{
        "A": "First option",
        "B": "Second option", 
        "C": "Third option",
        "D": "Fourth option"
      }},
      "answer": "A",
      "explanation": "Detailed explanation why A is correct and others are wrong"
    }}
  ]
}}

Use your reasoning capabilities to ensure questions are:
- Pedagogically sound and test real understanding
- Free from ambiguity or trick elements
- Appropriate for the target exam level
- Varied in approach and content areas"""

        if topic:
            base_prompt += f"\n\nSPECIFIC FOCUS: All questions must cover {topic} within {exam_type}."
            
        return base_prompt
    
    def _create_adaptive_system_prompt(self, exam_type: str, topic: str, difficulty: str, user_score: float) -> str:
        """Create adaptive system prompt with user context"""
        
        difficulty_guidance = {
            'easy': "Focus on fundamental concepts. Use straightforward language and basic applications. Avoid complex multi-step problems.",
            'medium': "Include moderate complexity with some multi-step reasoning. Test understanding of core concepts with practical applications.",
            'hard': "Challenge the user with complex scenarios, advanced applications, and sophisticated reasoning. Include edge cases and nuanced concepts."
        }
        
        score_context = ""
        if user_score < 40:
            score_context = "The user is struggling with this topic. Provide questions that build confidence and reinforce basic understanding."
        elif user_score <= 70:
            score_context = "The user has moderate understanding. Provide questions that challenge them to apply concepts in new ways."
        else:
            score_context = "The user has strong understanding. Provide challenging questions that test advanced applications and edge cases."
        
        adaptive_prompt = f"""You are an expert {exam_type} adaptive question generator with deep understanding of learner progression.

USER CONTEXT:
- Current score in {topic}: {user_score:.1f}%
- Target difficulty: {difficulty}
- Learning guidance: {score_context}

DIFFICULTY REQUIREMENTS FOR {difficulty.upper()}:
{difficulty_guidance[difficulty]}

ADAPTIVE PRINCIPLES:
1. Questions must match the user's current ability level in {topic}
2. Provide appropriate scaffolding for the difficulty level
3. Ensure questions are neither too easy nor too hard for their current score
4. Focus specifically on {topic} within {exam_type}

CRITICAL REQUIREMENTS:
1. Generate unique, original multiple-choice questions that have never been used before
2. Each question must have exactly 4 options (A, B, C, D)
3. Ensure one correct answer and three plausible distractors
4. Match authentic {exam_type} difficulty and style exactly
5. Provide detailed explanations for correct answers

OUTPUT FORMAT (JSON only):
{{
  "questions": [
    {{
      "question": "Question text here",
      "options": {{
        "A": "First option",
        "B": "Second option", 
        "C": "Third option",
        "D": "Fourth option"
      }},
      "answer": "A",
      "explanation": "Detailed explanation why A is correct and others are wrong"
    }}
  ]
}}

TOPIC FOCUS: All questions must specifically test {topic} concepts within {exam_type} at {difficulty} level."""
        
        return adaptive_prompt
    
    def _create_user_prompt(self, exam_type: str, topic: str = None, count: int = 5) -> str:
        """Create user prompt for specific question generation"""
        
        topic_text = f" focusing on {topic}" if topic else ""
        
        return f"""Generate exactly {count} unique {exam_type} multiple-choice questions{topic_text}.

Requirements:
- Each question must be completely original and never used before
- Follow authentic {exam_type} format and difficulty
- Provide comprehensive explanations for correct answers
- Ensure variety in question types and complexity levels
- Return ONLY valid JSON in the specified format

Generate the questions now:"""
    
    def _call_xai_with_retry(self, system_prompt: str, user_prompt: str, max_retries: int = 3) -> str:
        """Call xAI API with exponential backoff retry logic"""
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="grok-2-1212",  # Use latest Grok model
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=4000,
                    temperature=0.8  # Balanced creativity for question variety
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                wait_time = (2 ** attempt) * 1  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"⚠️  xAI API attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    logger.info(f"⏳ Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ All {max_retries} xAI API attempts failed")
                    raise
    
    def _parse_response(self, response: str, exam_type: str) -> List[Dict]:
        """Parse and validate xAI response to ensure format compatibility"""
        
        try:
            # Parse JSON response
            data = json.loads(response)
            
            if "questions" not in data or not isinstance(data["questions"], list):
                raise ValueError("Invalid response format: missing 'questions' array")
            
            validated_questions = []
            
            for i, q in enumerate(data["questions"]):
                # Validate required fields
                required_fields = ["question", "options", "answer", "explanation"]
                for field in required_fields:
                    if field not in q:
                        raise ValueError(f"Question {i+1} missing required field: {field}")
                
                # Validate options format
                if not isinstance(q["options"], dict):
                    raise ValueError(f"Question {i+1} options must be a dictionary")
                
                expected_options = ["A", "B", "C", "D"]
                for opt in expected_options:
                    if opt not in q["options"]:
                        raise ValueError(f"Question {i+1} missing option: {opt}")
                
                # Validate answer is valid option
                if q["answer"] not in expected_options:
                    raise ValueError(f"Question {i+1} invalid answer: {q['answer']}")
                
                # Clean and format question
                clean_question = {
                    "question": str(q["question"]).strip(),
                    "options": {
                        "A": str(q["options"]["A"]).strip(),
                        "B": str(q["options"]["B"]).strip(), 
                        "C": str(q["options"]["C"]).strip(),
                        "D": str(q["options"]["D"]).strip()
                    },
                    "answer": str(q["answer"]).strip(),
                    "explanation": str(q["explanation"]).strip(),
                    "exam_type": exam_type,
                    "generated_by": "xai_grok"
                }
                
                validated_questions.append(clean_question)
            
            logger.info(f"✅ Validated {len(validated_questions)} questions")
            return validated_questions
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {e}")
            logger.error(f"Raw response: {response[:500]}...")
            raise ValueError(f"Invalid JSON response from xAI: {e}")
        
        except Exception as e:
            logger.error(f"❌ Response validation failed: {e}")
            raise
    
    def test_integration(self) -> bool:
        """Test xAI integration with a simple question generation"""
        
        try:
            logger.info("🧪 Testing xAI integration...")
            
            # Test with GRE quant algebra as requested
            questions = self.generate_questions("GRE", "algebra", 1)
            
            if not questions:
                logger.error("❌ No questions generated in test")
                return False
            
            question = questions[0]
            required_fields = ["question", "options", "answer", "explanation"]
            
            for field in required_fields:
                if field not in question:
                    logger.error(f"❌ Missing field in test question: {field}")
                    return False
            
            logger.info("✅ xAI integration test passed")
            logger.info(f"Test question: {question['question'][:100]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ xAI integration test failed: {e}")
            return False
    
    def _create_adaptive_user_prompt(self, exam_type: str, topic: str, difficulty: str, count: int) -> str:
        """Create adaptive user prompt"""
        return f"""Generate {count} {difficulty}-level {exam_type} multiple-choice question{'s' if count != 1 else ''} specifically focused on {topic}.

Requirements:
- Target difficulty: {difficulty}
- Topic focus: {topic}
- Question count: {count}
- Format: Multiple choice with 4 options (A, B, C, D)
- Include detailed explanations

Respond with valid JSON only."""

# Initialize global instance
try:
    xai_generator = XAIQuestionGenerator()
    logger.info("🚀 Global xAI question generator initialized")
except Exception as e:
    logger.error(f"❌ Failed to initialize global xAI generator: {e}")
    xai_generator = None