from pydantic_ai import Agent
from typing import List
from .models import PersonaProfile, GiftRecommendation, RecommendationResponse

class GiftRecommendationAgent:
    """Intelligent gift recommendation agent that maintains context about the recipient"""
    
    def __init__(self):
        self.agent = Agent(
            "huggingface:openai/gpt-oss-120b",
            output_type=List[GiftRecommendation],
            retries=3,
            system_prompt="""You are an expert gift recommendation specialist with years of experience in personalized gifting.

Your task is to analyze a complete recipient profile (including personal details and question responses) and recommend the most suitable gifts.

KEY PRINCIPLES:
1. Consider ALL available information: age, gender, relationship, occasion, AND question answers
2. The question answers are CRUCIAL - they reveal specific interests and personality traits
3. Match gifts to the recipient's lifestyle and interests shown through their choices
4. Consider the relationship context (what's appropriate for friends vs family vs romantic partners)
6. Provide clear reasoning for each recommendation

RECOMMENDATION CRITERIA:
- Relevance: How well does the gift match their revealed interests?
- Appropriateness: Is it suitable for the relationship and occasion?
- Uniqueness: Is it thoughtful and personal rather than generic?

CRITICAL: You must respond with a JSON array of gift recommendations. Each recommendation must have exactly these fields:
- title: string (short gift name)
- description: string (detailed description)
- price_range: string (e.g., "$20-50", "$100-200")
- reasoning: string (why this fits the person)
- confidence_score: float (between 0.0 and 1.0)
- category: string (gift category like "books", "electronics", etc.)

Example format:
[
  {
    "title": "Premium Book Set",
    "description": "Curated collection of bestselling novels",
    "price_range": "$30-60",
    "reasoning": "Perfect for someone who loves reading books",
    "confidence_score": 0.9,
    "category": "books"
  }
]

Remember: The goal is to suggest gifts that show you truly understand the recipient based on all the information gathered."""
        )
    
    async def generate_recommendations(self, profile: PersonaProfile) -> List[GiftRecommendation]:
        """Generate personalized gift recommendations based on complete profile"""
        
        # Build comprehensive context from all available data
        context = self._build_context(profile)
        
        # Generate recommendations using the agent
        result = await self.agent.run(context)
        return result.output
    
    def _build_context(self, profile: PersonaProfile) -> str:
        """Build a comprehensive context string from the persona profile"""
        
        context = f"""
RECIPIENT PROFILE:
Age: {profile.age}
Gender: {profile.gender}
Occasion: {profile.occasion}
Your Relationship: {profile.relationship}
Budget: {profile.budget if profile.budget else "No specific budget mentioned"}

INSIGHTS FROM QUESTIONS & ANSWERS:
"""
        
        # Add insights from question answers
        for insight in profile.question_insights:
            context += f"""
Question: "{insight.question}"
Available Options: {insight.available_choices}
Their Choice: "{insight.selected_choice}"
Category: {insight.insight_category}
"""
        
        context += f"""

TASK: Generate exactly 5 gift recommendations as a JSON array.
Requirements:
- {profile.age}-year-old {profile.gender}
- For {profile.occasion} from a {profile.relationship}
- Budget consideration: {profile.budget if profile.budget else "flexible budget"}
- Based on their question responses above
- Each recommendation must include: title, description, price_range, reasoning, confidence_score (0.0-1.0), category
- IMPORTANT: Ensure all price_range values respect the budget constraint
"""
        
        return context

# Create a singleton instance
gift_recommendation_agent = GiftRecommendationAgent()