import json
from typing import List, Dict, Any
from ..build_persona.entity import Persona
from ..questions.entity import Answer

class QuestionRecommender:
    def __init__(self, questions_dataset_path: str = "full_dataset.json"):
        with open(questions_dataset_path, 'r') as f:
            self.questions = json.load(f)

    def recommend_question(self, persona: Persona, asked_questions: List[str], answers: List[Answer]) -> Dict[str, Any]:
        eligible_questions = [q for q in self.questions if q['id'] not in asked_questions]
        
        # This is a simplified placeholder for the full rule engine.
        # A complete implementation would parse and apply all visibility,
        # scoring, and follow-up rules.
        
        scored_questions = []
        for question in eligible_questions:
            score = question.get('weight', 5)
            scored_questions.append((score, question))
        
        if not scored_questions:
            return None

        scored_questions.sort(key=lambda x: x[0], reverse=True)
        return scored_questions[0][1]

def get_question_recommender() -> QuestionRecommender:
    return QuestionRecommender()
