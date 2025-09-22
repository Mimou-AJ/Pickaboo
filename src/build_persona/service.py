from .models import PersonaRequest, PersonaResponse
from .entity import Persona
from ..database.core import DbSession
from ..auth.service import get_current_user
from ..auth.models import TokenData
from fastapi import Depends

class PersonaService:
    def __init__(self, session: DbSession):
        self.session = session

    def create_persona_request(self, request: PersonaRequest, user: TokenData) -> PersonaResponse:
        persona = Persona(
            user_id=user.user_id,
            occasion=request.occasion,
            budget=request.budget,
            age_range=request.age_range,
            gender=request.gender,
            relationship=request.relationship
        )
        self.session.add(persona)
        self.session.commit()
        self.session.refresh(persona)
        return PersonaResponse.from_orm(persona)

def get_persona_service(session: DbSession) -> PersonaService:
    return PersonaService(session)
