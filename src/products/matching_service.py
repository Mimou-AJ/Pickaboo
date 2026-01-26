"""RAG pipeline for product matching and personalized recommendations."""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from pydantic_ai import Agent
from .repository import ProductRepository
from .models import MatchedProductResponse
from ..recommendations.models import PersonaProfile
import logging

logger = logging.getLogger(__name__)


class ProductMatchingService:
    """Service implementing RAG pipeline for product recommendations."""
    
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
            "huggingface:deepseek-ai/DeepSeek-V3.1",
            output_type=List[MatchedProductResponse],
            system_prompt="""You are a gift matching expert specializing in personalized product recommendations.

Your task is to analyze a recipient's profile and a list of candidate products, then select and rank the best matches.

For each selected product, you must:
1. Explain WHY this product is a great match for THIS specific recipient
2. Reference specific details from their profile (age, interests, preferences, occasion)
3. Assign a confidence score (0.0-1.0) based on match quality

Be thoughtful, specific, and personalized in your reasoning. Avoid generic explanations."""
        )
    
    async def find_gifts(
        self,
        profile: PersonaProfile,
        budget_range: Optional[Tuple[float, float]] = None,
        top_k: int = 5
    ) -> List[MatchedProductResponse]:
        """
        Execute RAG pipeline to find matching products.
        
        Pipeline stages:
        1. Build query from recipient profile
        2. Retrieval: Vector search for candidates
        3. Augmentation: Build LLM prompt with profile + products
        4. Generation: LLM re-ranks and explains matches
        5. Return top_k matched products
        
        Args:
            profile: Complete recipient profile with Q&A insights
            budget_range: Optional (min_price, max_price) tuple
            top_k: Number of final recommendations to return
            
        Returns:
            List of MatchedProductResponse with reasoning
        """
        logger.info(f"Finding gifts for persona {profile.persona_id}")
        
        # Stage 1: Build query from profile
        query = self._build_query_from_profile(profile)
        logger.debug(f"Generated query: {query[:100]}...")
        
        # Stage 2: Retrieval (get more candidates than needed for re-ranking)
        retrieval_k = top_k * 3  # Retrieve 3x to allow LLM to select best
        
        min_price = budget_range[0] if budget_range else None
        max_price = budget_range[1] if budget_range else None
        
        # Apply gender filter if specified
        gender_filter = profile.gender.lower() if profile.gender and profile.gender != "unknown" else None
        
        candidates = self.repository.semantic_search(
            query=query,
            top_k=retrieval_k,
            min_price=min_price,
            max_price=max_price,
            gender_filter=gender_filter
        )
        
        logger.info(f"Retrieved {len(candidates)} candidate products")
        
        if not candidates:
            logger.warning("No candidate products found")
            return []
        
        # Stage 3 & 4: Augmentation + Generation (LLM re-ranking)
        matched_products = await self._rerank_with_llm(profile, candidates, top_k)
        
        logger.info(f"Returned {len(matched_products)} matched products")
        return matched_products
    
    def _build_query_from_profile(self, profile: PersonaProfile) -> str:
        """
        Build semantic search query from recipient profile.
        
        Args:
            profile: Recipient profile
            
        Returns:
            Query string for vector search
        """
        parts = []
        
        # Basic demographics
        parts.append(f"Gift for {profile.age} year old {profile.gender}")
        
        # Occasion and relationship
        parts.append(profile.occasion)
        parts.append(profile.relationship)
        
        # Extract insights from Q&A, filtering out "None of the above"
        for insight in profile.question_insights:
            choice = insight.selected_choice
            if choice and "none of the above" not in choice.lower():
                parts.append(choice)
        
        query = " | ".join(parts)
        return query
    
    async def _rerank_with_llm(
        self,
        profile: PersonaProfile,
        candidates: List[Tuple],  # List of (Product, similarity_score)
        top_k: int
    ) -> List[MatchedProductResponse]:
        """
        Use LLM to re-rank candidates and provide reasoning.
        
        Args:
            profile: Recipient profile
            candidates: List of (Product, similarity_score) tuples
            top_k: Number to return
            
        Returns:
            List of MatchedProductResponse with reasoning
        """
        # Build prompt for LLM
        prompt = self._build_reranking_prompt(profile, candidates, top_k)
        
        try:
            # Call LLM agent
            result = await self.reranker.run(prompt)
            matched_products = result.data
            
            # Limit to top_k
            return matched_products[:top_k]
            
        except Exception as e:
            logger.error(f"Error in LLM re-ranking: {e}")
            # Fallback: return top candidates by similarity without LLM reasoning
            return self._fallback_matches(candidates, top_k)
    
    def _build_reranking_prompt(
        self,
        profile: PersonaProfile,
        candidates: List[Tuple],
        top_k: int
    ) -> str:
        """
        Build prompt for LLM re-ranking.
        
        Args:
            profile: Recipient profile
            candidates: Product candidates with scores
            top_k: Number to select
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = []
        
        # Profile section
        prompt_parts.append("=== RECIPIENT PROFILE ===")
        prompt_parts.append(f"Age: {profile.age}")
        prompt_parts.append(f"Gender: {profile.gender}")
        prompt_parts.append(f"Occasion: {profile.occasion}")
        prompt_parts.append(f"Relationship: {profile.relationship}")
        if profile.budget:
            prompt_parts.append(f"Budget: {profile.budget}")
        
        # Q&A insights
        if profile.question_insights:
            prompt_parts.append("\n=== PREFERENCES & INTERESTS ===")
            for insight in profile.question_insights:
                prompt_parts.append(f"- {insight.question}")
                prompt_parts.append(f"  Answer: {insight.selected_choice}")
        
        # Candidate products
        prompt_parts.append(f"\n=== CANDIDATE PRODUCTS (select best {top_k}) ===")
        for idx, (product, similarity) in enumerate(candidates, 1):
            prompt_parts.append(f"\nProduct {idx}:")
            prompt_parts.append(f"  ID: {product.id}")
            prompt_parts.append(f"  Name: {product.name}")
            if product.vendor:
                prompt_parts.append(f"  Brand: {product.vendor}")
            if product.product_type:
                prompt_parts.append(f"  Type: {product.product_type}")
            if product.price_eur:
                prompt_parts.append(f"  Price: €{product.price_eur:.2f}")
            if product.colors:
                prompt_parts.append(f"  Colors: {', '.join(product.colors[:5])}")
            if product.tags:
                prompt_parts.append(f"  Tags: {', '.join(product.tags[:8])}")
            prompt_parts.append(f"  Similarity Score: {similarity:.3f}")
        
        # Instructions
        prompt_parts.append(f"\n=== TASK ===")
        prompt_parts.append(f"Select the top {top_k} products that best match this recipient.")
        prompt_parts.append("For each product, provide:")
        prompt_parts.append("1. match_reasoning: Detailed explanation of why this product suits THIS recipient")
        prompt_parts.append("2. confidence: Score from 0.0 to 1.0 indicating match quality")
        prompt_parts.append("\nBe specific and reference details from the recipient's profile.")
        
        return "\n".join(prompt_parts)
    
    def _fallback_matches(
        self,
        candidates: List[Tuple],
        top_k: int
    ) -> List[MatchedProductResponse]:
        """
        Fallback when LLM fails: return top candidates by similarity.
        
        Args:
            candidates: Product candidates with scores
            top_k: Number to return
            
        Returns:
            List of MatchedProductResponse with generic reasoning
        """
        matches = []
        for product, similarity in candidates[:top_k]:
            match = MatchedProductResponse(
                id=product.id,
                name=product.name,
                vendor=product.vendor,
                product_type=product.product_type,
                price_eur=product.price_eur,
                product_url=product.product_url,
                image_url=product.image_url,
                colors=product.colors,
                sizes=product.sizes,
                tags=product.tags,
                similarity_score=similarity,
                match_reasoning="This product matches based on semantic similarity to the recipient's profile.",
                confidence=similarity
            )
            matches.append(match)
        return matches
