from ..database.core import DbSession
from ..build_persona.entity import Persona
from .entity import Question, Answer
from .models import QuestionResponse, AnswerRequest, AnswerResponse
from fastapi import Depends
import uuid
import asyncio

from ..questions_agent.detective import gift_detective
from ..questions_agent.models import GiftDependencies


class QuestionService:
    def __init__(self, session: DbSession):
        self.session = session

    def get_next_question(self, persona_id: uuid.UUID) -> list[str]:
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

        # Save each question to DB
        questions = []
        for q_text in result.output.questions:
            question = Question(
                persona_id=persona_id,
                question_text=q_text,
            )
            self.session.add(question)
            self.session.commit()
            self.session.refresh(question)
            questions.append(question.question_text)

        # Return all questions as a list
        return questions
    
def get_question_service(session: DbSession ) -> QuestionService:
    return QuestionService(session)    
