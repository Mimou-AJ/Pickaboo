from pydantic import BaseModel
from uuid import UUID
from .answer_choice import AnswerChoice

class QuestionResponse(BaseModel):
    id: UUID
    question_text: str

    class Config:
        from_attributes = True

class AnswerRequest(BaseModel):
    answer_choice: AnswerChoice

class AnswerResponse(BaseModel):
    id: UUID
    answer_choice: AnswerChoice

    class Config:
        from_attributes = True
