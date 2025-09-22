from pydantic import BaseModel, Field
from typing import Optional
import uuid
from .entity import Occasion, Budget, AgeRange, Gender, Relationship

class PersonaRequest(BaseModel):
    occasion: Occasion
    budget: Budget
    age_range: AgeRange
    gender: Optional[Gender] = None
    relationship: Relationship

class PersonaResponse(BaseModel):
    id: uuid.UUID
    occasion: Occasion
    budget: Budget
    age_range: AgeRange
    gender: Optional[Gender]
    relationship: Relationship

    class Config:
        from_attributes = True
