from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class PersonaProfile(BaseModel):
    """Complete profile including persona details and question answers"""
    persona_id: UUID
    age: int
    gender: str
    occasion: str
    relationship: str
    budget: Optional[str] = None
    
    # Aggregated question answers
    question_insights: List["QuestionInsight"]

class QuestionInsight(BaseModel):
    """Insight from a question-answer pair"""
    question: str
    selected_choice: str
    available_choices: List[str]
    insight_category: str  # e.g., "interests", "preferences", "lifestyle"

class GiftRecommendation(BaseModel):
    """A single gift recommendation"""
    title: str
    description: str
    price_range: str
    reasoning: str
    confidence_score: float  # 0.0 to 1.0
    category: str
    purchase_links: Optional[List[str]] = None

class RecommendationRequest(BaseModel):
    """Request for gift recommendations"""
    persona_id: UUID
    max_recommendations: int = 5
    include_reasoning: bool = True

class RecommendationResponse(BaseModel):
    """Response containing gift recommendations"""
    persona_id: UUID
    recipient_summary: str
    recommendations: List[GiftRecommendation]
    total_recommendations: int
    confidence_level: str  # "high", "medium", "low"

# Update forward references
PersonaProfile.model_rebuild()