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
from typing import List, Dict
from uuid import UUID
import asyncio
from ..messages.repository import MessageRepository
from ..products.matching_service import ProductMatchingService
from ..products.models import MatchedProductResponse

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
        
        # 2. Load message history from repository
        message_history = await self.message_repo.load_all_messages(request.persona_id)
        
        # 3. Try RAG pipeline with real products first
        persona = self.session.query(Persona).filter(Persona.id == request.persona_id).first()
        if persona and persona.budget:
            budget_range = self._get_budget_range(persona.budget.value)
            
            try:
                # Get matched products from RAG pipeline
                matched_products = await self.product_matcher.find_gifts(
                    profile=profile,
                    budget_range=budget_range,
                    top_k=request.max_recommendations
                )
                
                # If we got real products, use them
                if matched_products:
                    recommendations = self._convert_products_to_recommendations(matched_products)
                    confidence_level = self._calculate_confidence_level(recommendations, len(profile.question_insights))
                    recipient_summary = self._build_recipient_summary(profile)
                    
                    return RecommendationResponse(
                        persona_id=request.persona_id,
                        recipient_summary=recipient_summary,
                        recommendations=recommendations,
                        total_recommendations=len(recommendations),
                        confidence_level=confidence_level
                    )
            except Exception as e:
                # Log error but continue to fallback
                import logging
                logging.warning(f"RAG pipeline failed, falling back to LLM-only: {e}")
        
        # 4. Fallback: Generate recommendations using the AI agent (LLM-only)
        recommendations = await gift_recommendation_agent.generate_recommendations(profile, message_history)
        
        # 5. Limit to requested number and calculate confidence
        limited_recommendations = recommendations[:request.max_recommendations]
        confidence_level = self._calculate_confidence_level(limited_recommendations, len(profile.question_insights))
        
        # 6. Build recipient summary
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
    
    def _get_budget_range(self, budget: str) -> tuple:
        """
        Convert budget enum to price range tuple.
        
        Args:
            budget: Budget enum value (e.g., "under_25")
            
        Returns:
            Tuple of (min_price, max_price)
        """
        budget_map = {
            "under_25": (0, 25),
            "25-50": (25, 50),
            "50-100": (50, 100),
            "over_100": (100, 10000)
        }
        return budget_map.get(budget, (0, 10000))
    
    def _convert_products_to_recommendations(
        self, 
        matched_products: List[MatchedProductResponse]
    ) -> List[GiftRecommendation]:
        """
        Convert matched products to gift recommendations.
        
        Args:
            matched_products: List of matched products from RAG pipeline
            
        Returns:
            List of gift recommendations
        """
        recommendations = []
        
        for product in matched_products:
            # Format price range
            if product.price_min and product.price_max:
                price_range = f"€{product.price_min:.2f} - €{product.price_max:.2f}"
            elif product.price_eur:
                price_range = f"€{product.price_eur:.2f}"
            else:
                price_range = "Price not available"
            
            # Build description
            description_parts = []
            if product.vendor:
                description_parts.append(f"by {product.vendor}")
            if product.product_type:
                description_parts.append(product.product_type)
            if product.colors:
                description_parts.append(f"Available in {', '.join(product.colors[:3])}")
            
            description = ". ".join(description_parts) if description_parts else "No description available"
            
            # Determine category from tags or product type
            category = product.product_type if product.product_type else "General Gift"
            
            # Build purchase links
            purchase_links = []
            if product.product_url:
                purchase_links.append(product.product_url)
            
            recommendation = GiftRecommendation(
                title=product.name,
                description=description,
                price_range=price_range,
                reasoning=product.match_reasoning,
                confidence_score=product.confidence,
                category=category,
                purchase_links=purchase_links if purchase_links else None
            )
            recommendations.append(recommendation)
        
        return recommendations

def get_recommendation_service(session: DbSession) -> RecommendationService:
    return RecommendationService(session)