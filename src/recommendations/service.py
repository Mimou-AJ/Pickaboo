from ..database.core import DbSession
from ..build_persona.entity import Persona
from ..questions.entity import Question, Answer
from ..questions.answer_choice import AnswerChoice
from .models import (
    PersonaProfile, 
    QuestionInsight, 
    RecommendationRequest, 
    RecommendationResponse,
    GiftRecommendation
)
from .agent import gift_recommendation_agent
from typing import List, Dict
from uuid import UUID
import asyncio

class RecommendationService:
    """Service to generate personalized gift recommendations"""
    
    def __init__(self, session: DbSession):
        self.session = session
    
    async def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Generate gift recommendations for a persona based on all collected data"""
        
        # 1. Build complete profile from persona + question answers
        profile = self._build_persona_profile(request.persona_id)
        
        # 2. Generate recommendations using the AI agent
        recommendations = await gift_recommendation_agent.generate_recommendations(profile)
        
        # 3. Limit to requested number and calculate confidence
        limited_recommendations = recommendations[:request.max_recommendations]
        confidence_level = self._calculate_confidence_level(limited_recommendations, len(profile.question_insights))
        
        # 4. Build recipient summary
        recipient_summary = self._build_recipient_summary(profile)
        
        return RecommendationResponse(
            persona_id=request.persona_id,
            recipient_summary=recipient_summary,
            recommendations=limited_recommendations,
            total_recommendations=len(limited_recommendations),
            confidence_level=confidence_level
        )
    
    def _build_persona_profile(self, persona_id: UUID) -> PersonaProfile:
        """Build complete persona profile including question insights"""
        
        # Get persona details
        persona = self.session.query(Persona).filter(Persona.id == persona_id).first()
        if not persona:
            raise ValueError(f"Persona not found: {persona_id}")
        
        # Get all questions and answers for this persona
        questions_with_answers = self.session.query(Question, Answer).join(
            Answer, Question.id == Answer.question_id
        ).filter(Question.persona_id == persona_id).all()
        
        # Build question insights
        question_insights = []
        for question, answer in questions_with_answers:
            insight = QuestionInsight(
                question=question.question_text,
                selected_choice=answer.selected_choice_text,
                available_choices=question.choices if question.choices else [],
                insight_category=self._categorize_question(question.question_text)
            )
            question_insights.append(insight)
        
        return PersonaProfile(
            persona_id=persona_id,
            age=persona.age,
            gender=persona.gender.value if persona.gender else "unknown",
            occasion=persona.occasion.value,
            relationship=persona.relationship.value,
            budget=self._format_budget(persona.budget),
            question_insights=question_insights
        )
    
    def _format_budget(self, budget_enum) -> str:
        """Convert budget enum to user-friendly string"""
        if not budget_enum:
            return None
        
        budget_map = {
            "under_25": "Less than €25",
            "25-50": "€25-€50",
            "50-100": "€50-€100",
            "over_100": "More than €100"
        }
        
        return budget_map.get(budget_enum.value, budget_enum.value)
    
    def _categorize_question(self, question_text: str) -> str:
        """Categorize a question to help with analysis"""
        question_lower = question_text.lower()
        
        if any(word in question_lower for word in ["hobby", "free time", "weekend", "activity", "sport"]):
            return "interests"
        elif any(word in question_lower for word in ["style", "fashion", "look", "wear", "outfit"]):
            return "style"
        elif any(word in question_lower for word in ["food", "eat", "drink", "cuisine", "restaurant"]):
            return "lifestyle"
        elif any(word in question_lower for word in ["music", "movie", "book", "entertainment"]):
            return "entertainment"
        elif any(word in question_lower for word in ["travel", "vacation", "trip", "place"]):
            return "travel"
        else:
            return "preferences"
    
    def _calculate_confidence_level(self, recommendations: List[GiftRecommendation], insights_count: int) -> str:
        """Calculate overall confidence level based on recommendations and data quality"""
        
        if not recommendations:
            return "low"
        
        avg_confidence = sum(rec.confidence_score for rec in recommendations) / len(recommendations)
        
        # Factor in the amount of data we have
        data_factor = min(insights_count / 5, 1.0)  # Optimal with 5+ insights
        
        final_confidence = avg_confidence * data_factor
        
        if final_confidence >= 0.8:
            return "high"
        elif final_confidence >= 0.6:
            return "medium"
        else:
            return "low"
    
    def _build_recipient_summary(self, profile: PersonaProfile) -> str:
        """Build a natural language summary of the recipient"""
        
        insights_summary = []
        for insight in profile.question_insights:
            insights_summary.append(f"chose '{insight.selected_choice}' when asked about {insight.question.lower()}")
        
        base_summary = f"The recipient is a {profile.age}-year-old {profile.gender}."
        
        if insights_summary:
            insights_text = "Based on their responses, they " + ", and they ".join(insights_summary[:3])
            if len(insights_summary) > 3:
                insights_text += f", among other preferences."
            return f"{base_summary} {insights_text}"
        
        return base_summary

def get_recommendation_service(session: DbSession) -> RecommendationService:
    return RecommendationService(session)