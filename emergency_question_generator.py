"""
Emergency Question Generator - Offline Fallback System
Ensures questions are ALWAYS available even when OpenAI quota is exceeded
"""

import json
import random
from datetime import datetime
from models import CachedQuestion, db
import logging

logger = logging.getLogger(__name__)

class EmergencyQuestionGenerator:
    """Generate basic questions when all else fails - NEVER leave users without questions"""
    
    def __init__(self):
        self.fallback_templates = {
            'GMAT': {
                'math': [
                    {
                        'template': 'If a = {a} and b = {b}, what is a + b?',
                        'generator': lambda: {'a': random.randint(10, 50), 'b': random.randint(10, 50)},
                        'answer_calc': lambda vars: vars['a'] + vars['b']
                    },
                    {
                        'template': 'What is {percent}% of {number}?',
                        'generator': lambda: {'percent': random.choice([25, 50, 75]), 'number': random.randint(100, 1000)},
                        'answer_calc': lambda vars: vars['percent'] * vars['number'] / 100
                    }
                ],
                'verbal': [
                    {
                        'template': 'Which word best completes the sentence: "The {adj} decision was {verb} by the board."',
                        'choices': ['A. controversial, approved', 'B. simple, rejected', 'C. complex, delayed', 'D. obvious, ignored'],
                        'correct': 'A'
                    }
                ]
            },
            'GRE': {
                'math': [
                    {
                        'template': 'If x = {x}, what is 2x + 5?',
                        'generator': lambda: {'x': random.randint(5, 20)},
                        'answer_calc': lambda vars: 2 * vars['x'] + 5
                    }
                ],
                'verbal': [
                    {
                        'template': 'The word "{word}" most nearly means:',
                        'word_pairs': [('abundant', 'plentiful'), ('scarce', 'rare'), ('vital', 'essential')]
                    }
                ]
            },
            'MCAT': {
                'biology': [
                    {
                        'template': 'Which organelle is responsible for protein synthesis?',
                        'choices': ['A. Nucleus', 'B. Ribosome', 'C. Mitochondria', 'D. Golgi apparatus'],
                        'correct': 'B',
                        'explanation': 'Ribosomes are the cellular structures responsible for protein synthesis.'
                    }
                ],
                'chemistry': [
                    {
                        'template': 'What is the pH of a neutral solution at 25°C?',
                        'choices': ['A. 0', 'B. 7', 'C. 14', 'D. 1'],
                        'correct': 'B',
                        'explanation': 'A neutral solution has a pH of 7 at 25°C.'
                    }
                ]
            },
            'NCLEX': [
                {
                    'template': 'Which action should the nurse take first when a patient shows signs of {condition}?',
                    'conditions': ['shortness of breath', 'chest pain', 'altered mental status'],
                    'choices': ['A. Call the doctor', 'B. Assess vital signs', 'C. Administer oxygen', 'D. Document findings'],
                    'correct': 'B'
                }
            ],
            'LSAT': [
                {
                    'template': 'If all A are B, and some B are C, which of the following must be true?',
                    'choices': ['A. All A are C', 'B. Some A are C', 'C. No A are C', 'D. Cannot be determined'],
                    'correct': 'D'
                }
            ]
        }
    
    def generate_emergency_questions(self, exam_type, count=20):
        """Generate emergency fallback questions when all other systems fail"""
        questions = []
        
        try:
            if exam_type in self.fallback_templates:
                templates = self.fallback_templates[exam_type]
                
                for i in range(count):
                    question = self._create_question_from_template(exam_type, templates, i)
                    if question:
                        questions.append(question)
            
            # Store in database for immediate access
            self._store_emergency_questions(questions, exam_type)
            
            logger.info(f"Generated {len(questions)} emergency questions for {exam_type}")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating emergency questions: {e}")
            return []
    
    def _create_question_from_template(self, exam_type, templates, index):
        """Create a single question from templates"""
        try:
            # Select template based on exam type structure
            if isinstance(templates, dict):
                # Choose random subject
                subject = random.choice(list(templates.keys()))
                template_list = templates[subject]
            else:
                template_list = templates
                subject = 'general'
            
            template = random.choice(template_list)
            
            # Generate question text
            if 'generator' in template:
                vars = template['generator']()
                question_text = template['template'].format(**vars)
                
                # Generate multiple choice answers
                correct_answer = template['answer_calc'](vars)
                wrong_answers = [
                    correct_answer + random.randint(-10, 10),
                    correct_answer * 0.5,
                    correct_answer * 1.5
                ]
                
                choices = [str(int(correct_answer))] + [str(int(ans)) for ans in wrong_answers]
                random.shuffle(choices)
                correct_index = choices.index(str(int(correct_answer)))
                
            else:
                question_text = template['template']
                choices = template['choices']
                correct_index = ord(template['correct']) - ord('A')
            
            return {
                'id': f'emergency_{exam_type.lower()}_{index}_{random.randint(1000, 9999)}',
                'exam_type': exam_type,
                'subject': subject,
                'difficulty': 'medium',
                'question_text': question_text,
                'choices': choices,
                'correct_answer': correct_index,
                'explanation': template.get('explanation', 'This is an emergency fallback question.'),
                'is_emergency': True,
                'created_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating question from template: {e}")
            return None
    
    def _store_emergency_questions(self, questions, exam_type):
        """Store emergency questions in database"""
        try:
            for question in questions:
                cached_q = CachedQuestion(
                    question_id=question['id'],
                    exam_type=exam_type,
                    difficulty=3,
                    question_text=question['question_text'],
                    option_a=question['choices'][0] if len(question['choices']) > 0 else '',
                    option_b=question['choices'][1] if len(question['choices']) > 1 else '',
                    option_c=question['choices'][2] if len(question['choices']) > 2 else '',
                    option_d=question['choices'][3] if len(question['choices']) > 3 else '',
                    correct_answer=chr(ord('A') + question['correct_answer']),
                    explanation=question['explanation'],
                    topic_area=question['subject'],
                    tags=json.dumps(['emergency', 'fallback'])
                )
                
                db.session.add(cached_q)
            
            db.session.commit()
            logger.info(f"Stored {len(questions)} emergency questions in database")
            
        except Exception as e:
            logger.error(f"Error storing emergency questions: {e}")
            db.session.rollback()

# Global instance for easy access
emergency_generator = EmergencyQuestionGenerator()