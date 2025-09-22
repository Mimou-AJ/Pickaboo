from ..database.core import DbSession
from ..build_persona.entity import Persona, Relationship, AgeRange
from .entity import Question, Answer
from .models import QuestionResponse, AnswerRequest, AnswerResponse
from ..recommendations.service import QuestionRecommender, get_question_recommender
from fastapi import Depends
import uuid

class QuestionService:
    def __init__(self, session: DbSession, recommender: QuestionRecommender = Depends(get_question_recommender)):
        self.session = session
        self.recommender = recommender

    def get_next_question(self, persona_id: uuid.UUID) -> QuestionResponse:
        persona = self.session.query(Persona).filter(Persona.id == persona_id).one()
        
        asked_questions_query = self.session.query(Question).filter(Question.persona_id == persona_id)
        asked_question_ids = [q.id for q in asked_questions_query.all()]
        
        answers = self.session.query(Answer).filter(Answer.question_id.in_(asked_question_ids)).all()

        recommended_question_data = self.recommender.recommend_question(persona, asked_question_ids, answers)

        if not recommended_question_data:
            # Handle case where no more questions are available
            return None

        # Create and save the question to the database to get a real UUID
        question = Question(
            persona_id=persona_id, 
            question_text=recommended_question_data['question_text']
        )
        self.session.add(question)
        self.session.commit()
        self.session.refresh(question)

        # Now return the response from the persisted DB object
        return QuestionResponse.from_orm(question)

    def submit_answer(self, question_id: uuid.UUID, answer_request: AnswerRequest) -> AnswerResponse:
        answer = Answer(question_id=question_id, answer_choice=answer_request.answer_choice)
        self.session.add(answer)
        self.session.commit()
        self.session.refresh(answer)
        return AnswerResponse.from_orm(answer)

def get_question_service(session: DbSession, recommender: QuestionRecommender = Depends(get_question_recommender)) -> QuestionService:
    return QuestionService(session, recommender)
