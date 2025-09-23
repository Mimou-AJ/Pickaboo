from pydantic import BaseModel, Field
from typing import Optional, List


class GiftDependencies(BaseModel):
    age: int
    gender: str
    occasion: str
    relationship: str


class GiftQuestions(BaseModel):
    questions: List[str] = Field(description="Smart questions to ask to better understand the gift recipient")
    detective_comment: str = Field(description="Detective-style summary or reasoning behind the questions")