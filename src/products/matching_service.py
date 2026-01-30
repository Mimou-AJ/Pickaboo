"""RAG pipeline for matching products to recipient profiles."""
from typing import List, Optional, Tuple
from pydantic_ai import Agent
from sqlalchemy.orm import Session
import logging

from ..recommendations.models import PersonaProfile
from .models import MatchedProductResponse
from .repository import ProductRepository

logger = logging.getLogger(__name__)


class ProductMatchingService:
    """RAG pipeline for personalized product matching."""
    
    def __init__(self, session: Session):
        """
        Initialize matching service.
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.repository = ProductRepository(session)
        
        # Initialize LLM re-ranking agent
        self.reranker = Agent(
            "huggingface:deepseek-ai/DeepSeek-V3",
            output_type=List[MatchedProductResponse],
            system_prompt="""You are a gift matching expert who helps find the perfect products for recipients.

Given a recipient profile and candidate products, your task is to:
1. Select the top 5 products that best match the recipient's preferences, demographics, and occasion
2. Provide clear reasoning explaining WHY each product is a good match
3. Assign confidence scores (0.0-1.0) based on how well the product fits

Consider:
- Age appropriateness
- Gender preferences  
- Occasion suitability
- Budget constraints
- Personal preferences from questionnaire answers
- Product attributes (type, tags, colors, style)

Be specific in your reasoning - reference the recipient's answers and product features.
Confidence should reflect match quality: 0.9+ = excellent match, 0.7-0.9 = good match, 0.5-0.7 = decent match."""
        )
    
    async def find_gifts(
        self,
        profile: PersonaProfile,
        budget_range: Optional[Tuple[float, float]] = None,
        top_k: int = 5
    ) -> List[MatchedProductResponse]:
        """
        Complete RAG pipeline: retrieval → augmentation → generation.
        
        Args:
            profile: Complete recipient profile
            budget_range: (min_price, max_price) tuple
            top_k: Number of recommendations to return
            
        Returns:
            List of matched products with reasoning and confidence
        """
        logger.info(f"Finding gifts for persona {profile.persona_id}")
        
        # Stage 1: Build query from profile
        query = self._build_query_from_profile(profile)
        logger.info(f"Built search query: {query}")
        
        # Stage 2: Retrieval (vector search)
        min_price = budget_range[0] if budget_range else None
        max_price = budget_range[1] if budget_range else None
        
        # Retrieve more candidates than needed for re-ranking
        candidates_count = top_k * 3
        
        # Apply gender filter if specified
        gender_filter = None
        if profile.gender and profile.gender.lower() in ["male", "female"]:
            gender_filter = "men" if profile.gender.lower() == "male" else "women"
        
        candidates = self.repository.semantic_search(
            query=query,
            top_k=candidates_count,
            min_price=min_price,
            max_price=max_price,
            gender_filter=gender_filter
        )
        
        if not candidates:
            logger.warning("No candidate products found")
            return []
        
        logger.info(f"Retrieved {len(candidates)} candidate products")
        
        # Stage 3: Augmentation (build LLM prompt)
        prompt = self._build_reranking_prompt(profile, candidates)
        
        # Stage 4: Generation (LLM re-ranking)
        try:
            result = await self.reranker.run(prompt)
            matched_products = result.data
            
            # Limit to requested number
            matched_products = matched_products[:top_k]
            
            logger.info(f"Re-ranked and selected {len(matched_products)} products")
            return matched_products
            
        except Exception as e:
            logger.error(f"Error in LLM re-ranking: {e}")
            # Fallback: return top candidates without LLM reasoning
            return self._fallback_matching(candidates, top_k)
    
    def _build_query_from_profile(self, profile: PersonaProfile) -> str:
        """
        Build natural language search query from recipient profile.
        
        Args:
            profile: Recipient profile
            
        Returns:
            Search query string
        """
        parts = []
        
        # Basic demographics
        parts.append(f"Gift for {profile.age} year old {profile.gender}")
        
        # Occasion and relationship
        parts.append(profile.occasion)
        parts.append(profile.relationship)
        
        # Extract key preferences from question insights
        preferences = []
        for insight in profile.question_insights:
            choice = insight.selected_choice.lower()
            # Filter out "none of the above" type responses
            if "none" not in choice and "don't" not in choice and "not" not in choice:
                preferences.append(choice)
        
        if preferences:
            parts.extend(preferences[:5])  # Top 5 preferences
        
        query = " | ".join(parts)
        return query
    
    def _build_reranking_prompt(
        self,
        profile: PersonaProfile,
        candidates: List[Tuple]
    ) -> str:
        """
        Build prompt for LLM re-ranking.
        
        Args:
            profile: Recipient profile
            candidates: List of (Product, similarity_score) tuples
            
        Returns:
            Prompt string
        """
        prompt_parts = []
        
        # Recipient profile
        prompt_parts.append("# Recipient Profile")
        prompt_parts.append(f"Age: {profile.age}")
        prompt_parts.append(f"Gender: {profile.gender}")
        prompt_parts.append(f"Occasion: {profile.occasion}")
        prompt_parts.append(f"Relationship: {profile.relationship}")
        prompt_parts.append(f"Budget: {profile.budget}")
        prompt_parts.append("")
        
        # Question insights
        prompt_parts.append("# Recipient Preferences")
        for insight in profile.question_insights:
            prompt_parts.append(f"Q: {insight.question}")
            prompt_parts.append(f"A: {insight.selected_choice}")
        prompt_parts.append("")
        
        # Candidate products
        prompt_parts.append("# Candidate Products")
        for i, (product, similarity) in enumerate(candidates, 1):
            prompt_parts.append(f"\n## Product {i}")
            prompt_parts.append(f"ID: {product.id}")
            prompt_parts.append(f"Name: {product.name}")
            prompt_parts.append(f"Vendor: {product.vendor}")
            prompt_parts.append(f"Type: {product.product_type}")
            prompt_parts.append(f"Price: €{product.price_eur}")
            if product.colors:
                prompt_parts.append(f"Colors: {', '.join(product.colors)}")
            if product.sizes:
                prompt_parts.append(f"Sizes: {', '.join(product.sizes)}")
            prompt_parts.append(f"Gender: {product.gender_target}")
            if product.tags:
                prompt_parts.append(f"Tags: {', '.join(product.tags)}")
            prompt_parts.append(f"Similarity Score: {similarity:.3f}")
        
        prompt_parts.append("\n# Task")
        prompt_parts.append("Select the top 5 products that best match this recipient.")
        prompt_parts.append("For each product, provide match_reasoning and confidence score.")
        
        return "\n".join(prompt_parts)
    
    def _fallback_matching(
        self,
        candidates: List[Tuple],
        top_k: int
    ) -> List[MatchedProductResponse]:
        """
        Fallback matching without LLM (uses similarity scores only).
        
        Args:
            candidates: List of (Product, similarity_score) tuples
            top_k: Number of results
            
        Returns:
            List of matched products
        """
        results = []
        for product, similarity in candidates[:top_k]:
            matched = MatchedProductResponse(
                id=product.id,
                name=product.name,
                vendor=product.vendor,
                product_type=product.product_type,
                price_eur=product.price_eur,
                price_min=product.price_min,
                price_max=product.price_max,
                available=product.available,
                colors=product.colors,
                sizes=product.sizes,
                gender_target=product.gender_target,
                tags=product.tags,
                product_url=product.product_url,
                image_url=product.image_url,
                similarity_score=similarity,
                match_reasoning="Based on semantic similarity to recipient profile",
                confidence=similarity
            )
            results.append(matched)
        
        return results
