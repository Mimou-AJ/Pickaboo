from pydantic import BaseModel, field_validator
from uuid import UUID
from .answer_choice import AnswerChoice

class QuestionResponse(BaseModel):
    id: UUID
    question_text: str

    class Config:
        from_attributes = True

class AnswerRequest(BaseModel):
    answer_choice: AnswerChoice

class QuestionAnswerItem(BaseModel):
    question_id: UUID
    answer_choice: str  # Accept the actual choice text selected by user

class BulkAnswerRequest(BaseModel):
    answers: list[QuestionAnswerItem]

class AnswerResponse(BaseModel):
    id: UUID
    selected_choice: str  # Return the actual choice text selected by user

    class Config:
        from_attributes = True

class BulkAnswerResponse(BaseModel):
    submitted_count: int
    answers: list[AnswerResponse]

class SuggestedQuestion(BaseModel):
    id: UUID
    question: str
    choices: list[str]
