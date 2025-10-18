from ..database.core import DbSession
from ..build_persona.entity import Persona
from .entity import Question, Answer
from .answer_choice import AnswerChoice
from .models import QuestionResponse, AnswerResponse, BulkAnswerRequest, BulkAnswerResponse
import uuid
from typing import List, Dict
import asyncio

from ..questions_agent.detective import gift_detective
from ..questions_agent.models import GiftDependencies


class QuestionService:
    def __init__(self, session):
        self.session = session

    def get_next_question(self, persona_id: uuid.UUID) -> List[Dict]:
        persona = self.session.query(Persona).filter(Persona.id == persona_id).one()

        deps = GiftDependencies(
            age=persona.age,
            gender=persona.gender.value if persona.gender else "unknown",
            occasion=persona.occasion.value,
            relationship=persona.relationship.value,
        )

        result = asyncio.run(
            gift_detective.run("Help me figure out the best questions to ask. max 5 questions.", deps=deps)
        )

        # Save each question to DB and return structured items with choices
        items: List[Dict] = []
        for q in result.output.questions:
            # q.question is the text, q.choices is List[str]
            question = Question(
                persona_id=persona_id,
                question_text=q.question,
                choices=q.choices,  # Save the choices as JSON
            )
            self.session.add(question)
            self.session.commit()
            self.session.refresh(question)

            items.append({
                "id": question.id,
                "question": question.question_text,
                "choices": q.choices,
            })

        return items

    def submit_bulk_answers(self, request: BulkAnswerRequest) -> BulkAnswerResponse:
        """Submit multiple answers for different questions in one operation"""
        submitted_answers = []
        
        for answer_item in request.answers:
            # Verify the question exists
            question = self.session.query(Question).filter(Question.id == answer_item.question_id).first()
            if not question:
                continue  # Skip invalid question IDs
            
            # Get the selected choice text and map to position-based enum
            selected_text = answer_item.answer_choice
            choice_index = 0
            if question.choices and selected_text in question.choices:
                choice_index = question.choices.index(selected_text)
            
            # Map choice index to enum (0->yes, 1->probably, 2->probably_not, 3->no, default->yes)
            choice_mapping = [AnswerChoice.yes, AnswerChoice.probably, AnswerChoice.probably_not, AnswerChoice.no]
            enum_choice = choice_mapping[choice_index] if choice_index < len(choice_mapping) else AnswerChoice.yes
            
            # Create and save the answer
            answer = Answer(
                question_id=answer_item.question_id,
                answer_choice=enum_choice,
                selected_choice_text=selected_text
            )
            self.session.add(answer)
            self.session.commit()
            self.session.refresh(answer)
            
            submitted_answers.append(AnswerResponse(
                id=answer.id,
                selected_choice=answer.selected_choice_text
            ))
        
        return BulkAnswerResponse(
            submitted_count=len(submitted_answers),
            answers=submitted_answers
        )
    
def get_question_service(session: DbSession) -> QuestionService:
    return QuestionService(session)
