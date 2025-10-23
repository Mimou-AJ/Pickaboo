from fastapi import APIRouter, Depends, status
from .models import PersonaRequest, PersonaResponse
from .service import PersonaService, get_persona_service

router = APIRouter(
    prefix="/build-persona",
    tags=["Build Persona"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PersonaResponse)
def create_persona(
    request: PersonaRequest,
    service: PersonaService = Depends(get_persona_service),
):
    return service.create_persona_request(request)
