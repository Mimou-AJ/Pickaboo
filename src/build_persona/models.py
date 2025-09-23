from pydantic import BaseModel, Field
from typing import Optional
import uuid
from .entity import Occasion, Gender, Relationship  # removed Budget, AgeRange


class PersonaRequest(BaseModel):
    occasion: Occasion
    age: int
    gender: Optional[Gender] = None
    relationship: Relationship


class PersonaResponse(BaseModel):
    id: uuid.UUID
    occasion: Occasion
    age: int
    gender: Optional[Gender]
    relationship: Relationship

    class Config:
        from_attributes = True
