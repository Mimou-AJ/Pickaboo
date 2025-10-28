from pydantic_ai import Agent
from typing import List
from .models import PersonaProfile, GiftRecommendation, RecommendationResponse
from pydantic_ai.messages import ModelMessage

class GiftRecommendationAgent:
    """Intelligent gift recommendation agent that maintains context about the recipient"""
    
    def __init__(self):
        self.agent = Agent(
            "huggingface:deepseek-ai/DeepSeek-V3.1",
            output_type=List[GiftRecommendation],
            retries=2,
            system_prompt="""You are an expert gift recommendation specialist with years of experience in personalized gifting.

You have been asking the user questions about the gift recipient to understand their preferences. 
Now, based on ALL the conversation history (the questions you asked and the answers you received), 
recommend the most suitable gifts.

KEY PRINCIPLES:
1. Review the ENTIRE conversation history - every question and answer matters
2. The answers reveal specific interests, personality traits, and preferences
3. When you see "None of the above" answers, pay attention - these tell you what the recipient is NOT interested in
4. Match gifts to the recipient's lifestyle shown through their choices
5. Consider the relationship context and occasion
6. Respect the budget

RECOMMENDATION CRITERIA:
- Relevance: How well does the gift match their revealed interests?
- Appropriateness: Is it suitable for the relationship and occasion?
- Thoughtfulness: Does it show you understand them based on the conversation?
- Avoidance: Don't recommend things related to topics where they answered "None of the above"

CRITICAL: You must respond with a JSON array of gift recommendations. Each recommendation must have exactly these fields:
- title: string (short gift name)
- description: string (detailed description)
- price_range: string (e.g., "$20-50", "$100-200")
- reasoning: string (why this fits based on what you learned from the conversation)
- confidence_score: float (between 0.0 and 1.0)
- category: string (gift category like "books", "electronics", etc.)

Example format:
[
  {
    "title": "Premium Book Set",
    "description": "Curated collection of bestselling novels",
    "price_range": "$30-60",
    "reasoning": "Based on our conversation, they love reading and prefer fiction",
    "confidence_score": 0.9,
    "category": "books"
  }
]

Remember: Use the conversation history to make truly personalized recommendations."""
        )
    
    async def generate_recommendations(
        self, 
        profile: PersonaProfile, 
        message_history: List[ModelMessage]
    ) -> List[GiftRecommendation]:
        """Generate personalized gift recommendations using conversation history"""
        
        # Build the request prompt
        prompt = self._build_recommendation_prompt(profile)
        
        # Use the message history from the question generation process
        result = await self.agent.run(prompt, message_history=message_history)
        return result.output
    
    def _build_recommendation_prompt(self, profile: PersonaProfile) -> str:
        """Build a prompt that references the conversation history"""
        
        prompt = f"""Based on our conversation above about the gift recipient, generate exactly 5 gift recommendations as a JSON array.

RECIPIENT SUMMARY:
- Age: {profile.age}
- Gender: {profile.gender}
- Occasion: {profile.occasion}
- Your Relationship: {profile.relationship}
- Budget: {profile.budget if profile.budget else "flexible budget"}

TASK: Generate 5 gift recommendations based on what you learned from asking questions.
- Each recommendation must include: title, description, price_range, reasoning, confidence_score (0.0-1.0), category
- IMPORTANT: Ensure all price_range values respect the budget constraint
- Reference specific answers from our conversation in your reasoning
"""
        
        return prompt

# Create a singleton instance
gift_recommendation_agent = GiftRecommendationAgent()