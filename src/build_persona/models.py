from pydantic import BaseModel, Field
from typing import Optional
import uuid
from .entity import Occasion, Gender, Relationship, BudgetRange


class PersonaRequest(BaseModel):
    occasion: Occasion
    age: int
    gender: Optional[Gender] = None
    relationship: Relationship
    budget: Optional[BudgetRange] = None


class PersonaResponse(BaseModel):
    id: uuid.UUID
    occasion: Occasion
    age: int
    gender: Optional[Gender]
    relationship: Relationship
    budget: Optional[BudgetRange] = None

    class Config:
        from_attributes = True
