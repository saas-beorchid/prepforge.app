import json
import os
import logging
from app import app, db
from models import Question

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def load_questions():
    """Load questions from JSON files in questions_data directory"""
    json_dir = "questions_data"

    if not os.path.exists(json_dir):
        logging.error(f"Questions directory {json_dir} not found!")
        return

    logging.info(f"Starting to load questions from {json_dir}")

    with app.app_context():
        db.create_all()

        # Process each JSON file
        for filename in os.listdir(json_dir):
            if not filename.endswith('.json'):
                continue

            exam_type = filename.replace('_Questions.json', '').upper()
            if exam_type.startswith('USMLE_STEP'):
                exam_type = f"USMLE_STEP_{exam_type[-1]}"

            file_path = os.path.join(json_dir, filename)
            logging.info(f"Processing {filename} for {exam_type}")

            try:
                # Check existing questions
                existing_count = Question.query.filter_by(exam_type=exam_type).count()
                if existing_count >= 100:
                    logging.info(f"Skipping {exam_type} - already has {existing_count} questions")
                    continue

                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Handle both single question and array formats
                questions = data if isinstance(data, list) else [data]

                # Load up to 100 questions per exam type
                for i, q in enumerate(questions[:100]):
                    question = Question(
                        id=q.get('id') or f"{exam_type.lower()}_{i+1:03d}",
                        exam_type=exam_type,
                        difficulty=q.get('difficulty', 'medium'),
                        question_text=q['question'],
                        choices=q.get('choices', q.get('options', [])),
                        correct_answer=q['correct_answer'],
                        explanation=q.get('explanation', ''),
                        subject=q.get('subject', 'General')
                    )
                    db.session.add(question)

                db.session.commit()
                loaded_count = min(len(questions), 100)
                logging.info(f"Successfully loaded {loaded_count} questions for {exam_type}")

            except Exception as e:
                logging.error(f"Error processing {filename}: {str(e)}")
                db.session.rollback()
                continue

        # Log final counts
        exam_types = db.session.query(Question.exam_type).distinct().all()
        for (exam_type,) in exam_types:
            count = Question.query.filter_by(exam_type=exam_type).count()
            logging.info(f"Total questions for {exam_type}: {count}")

if __name__ == "__main__":
    load_questions()