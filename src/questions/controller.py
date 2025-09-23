from fastapi import APIRouter, Depends, status
from .models import QuestionResponse, AnswerRequest, AnswerResponse
from .service import QuestionService, get_question_service
from ..auth.service import get_current_user
from ..entities.user import User
import uuid
from typing import List

router = APIRouter(
    tags=["Questions"],
    responses={404: {"description": "Not found"}},
)

@router.get("/personas/{persona_id}/questions/next", response_model=List[str])
def get_next_question(
    persona_id: uuid.UUID,
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user),
):
    return service.get_next_question(persona_id)

@router.post("/questions/{question_id}/answer", status_code=status.HTTP_201_CREATED, response_model=AnswerResponse)
def submit_answer(
    question_id: uuid.UUID,
    request: AnswerRequest,
    service: QuestionService = Depends(get_question_service),
    current_user: User = Depends(get_current_user),
):
    return service.submit_answer(question_id, request)