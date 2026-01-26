from ..database.core import DbSession
from ..build_persona.entity import Persona
from ..questions.entity import Question, Answer
from .models import (
    PersonaProfile, 
    QuestionInsight, 
    RecommendationRequest, 
    RecommendationResponse,
    GiftRecommendation
)
from .agent import gift_recommendation_agent
from typing import List, Dict, Optional, Tuple
from uuid import UUID
import asyncio
from ..messages.repository import MessageRepository
from ..products.matching_service import ProductMatchingService
from ..products.repository import ProductRepository

class RecommendationService:
    """Service to generate personalized gift recommendations"""
    
    def __init__(self, session: DbSession):
        self.session = session
        self.message_repo = MessageRepository(session)
        self.product_matcher = ProductMatchingService(session)
    
    async def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Generate gift recommendations for a persona based on all collected data"""
        
        # 1. Build complete profile from persona + question answers
        profile = self._build_persona_profile(request.persona_id)
        
        # 2. Check if we have products in database (RAG pipeline)
        product_repo = ProductRepository(self.session)
        product_count = product_repo.count_products()
        
        if product_count > 0:
            # Use RAG pipeline with real products
            budget_range = self._get_budget_range(profile.budget)
            
            try:
                matched_products = await self.product_matcher.find_gifts(
                    profile=profile,
                    budget_range=budget_range,
                    top_k=request.max_recommendations
                )
                
                if matched_products:
                    # Convert matched products to GiftRecommendation format
                    recommendations = self._convert_matched_products_to_recommendations(matched_products)
                    confidence_level = self._calculate_confidence_level_from_products(matched_products)
                    recipient_summary = self._build_recipient_summary(profile)
                    
                    return RecommendationResponse(
                        persona_id=request.persona_id,
                        recipient_summary=recipient_summary,
                        recommendations=recommendations,
                        total_recommendations=len(recommendations),
                        confidence_level=confidence_level
                    )
            except Exception as e:
                # Log error but fallback to LLM-only approach
                import logging
                logging.warning(f"RAG pipeline failed, falling back to LLM-only: {e}")
        
        # Fallback: Use original LLM-only approach when no products or RAG fails
        message_history = await self.message_repo.load_all_messages(request.persona_id)
        recommendations = await gift_recommendation_agent.generate_recommendations(profile, message_history)
        
        limited_recommendations = recommendations[:request.max_recommendations]
        confidence_level = self._calculate_confidence_level(limited_recommendations, len(profile.question_insights))
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

    def _get_budget_range(self, budget: Optional[str]) -> Tuple[float, float]:
        """
        Convert budget string to price range tuple.
        
        Args:
            budget: Budget string (e.g., "€25-€50")
            
        Returns:
            Tuple of (min_price, max_price)
        """
        if not budget:
            return (0, 10000)
        
        budget_map = {
            "Less than €25": (0, 25),
            "€25-€50": (25, 50),
            "€50-€100": (50, 100),
            "More than €100": (100, 10000)
        }
        
        return budget_map.get(budget, (0, 10000))
    
    def _convert_matched_products_to_recommendations(
        self, 
        matched_products: List
    ) -> List[GiftRecommendation]:
        """
        Convert MatchedProductResponse to GiftRecommendation format.
        
        Args:
            matched_products: List of MatchedProductResponse
            
        Returns:
            List of GiftRecommendation
        """
        recommendations = []
        
        for product in matched_products:
            # Format price range
            if product.price_eur:
                price_range = f"€{product.price_eur:.2f}"
            else:
                price_range = "Price not available"
            
            # Build purchase links
            purchase_links = []
            if product.product_url:
                purchase_links.append(product.product_url)
            
            # Determine category from product_type or tags
            category = product.product_type if product.product_type else "Gift"
            
            recommendation = GiftRecommendation(
                title=product.name,
                description=f"{product.vendor or 'Quality product'} - {category}",
                price_range=price_range,
                reasoning=product.match_reasoning,
                confidence_score=product.confidence,
                category=category,
                purchase_links=purchase_links if purchase_links else None
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_confidence_level_from_products(self, matched_products: List) -> str:
        """
        Calculate confidence level from matched products.
        
        Args:
            matched_products: List of MatchedProductResponse
            
        Returns:
            Confidence level string
        """
        if not matched_products:
            return "low"
        
        avg_confidence = sum(p.confidence for p in matched_products) / len(matched_products)
        
        if avg_confidence >= 0.8:
            return "high"
        elif avg_confidence >= 0.6:
            return "medium"
        else:
            return "low"

def get_recommendation_service(session: DbSession) -> RecommendationService:
    return RecommendationService(session)