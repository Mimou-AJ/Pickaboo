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
            system_prompt="""You are Jinny, a world-class gift recommendation specialist.

You have been profiling a gift recipient by asking targeted questions across 5 dimensions:
lifestyle, hobbies, style, personality, and unmet wants.

Your job is to recommend gifts that:
1. MATCH positive signals — things the recipient actively chose or expressed interest in
2. AVOID negative signals — when they answered "None of the above", they rejected ALL those options. Never recommend anything in those rejected categories.
3. FIT the occasion and relationship (e.g., a Valentine's gift from a partner is different from a birthday gift from a colleague)
4. RESPECT the budget strictly
5. SURPRISE & DELIGHT — go beyond the obvious; combine multiple signals into creative gift ideas

For each recommendation, your reasoning MUST reference specific answers from the conversation.
Bad reasoning: "This is a great gift for anyone."
Good reasoning: "Since she chose 'yoga & meditation' for hobbies and 'minimalist' for style, this handcrafted meditation cushion fits perfectly."

CRITICAL: You must respond with a JSON array. Each item must have exactly these fields:
- title: string (concise gift name)
- description: string (what it is and why it's special)
- price_range: string (e.g., "€20-50") — MUST respect the budget
- reasoning: string (2-3 sentences connecting the gift to specific Q&A answers)
- confidence_score: float (0.0 to 1.0, based on how many profile signals this gift matches)
- category: string (gift category)
"""
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
        
        # Separate positive and negative signals
        positive = []
        negative = []
        for insight in profile.question_insights:
            if "none of the above" in insight.selected_choice.lower():
                rejected = [c for c in insight.available_choices if "none of the above" not in c.lower()]
                negative.append(f"  - Rejected: {', '.join(rejected)} (Q: {insight.question})")
            else:
                positive.append(f"  - {insight.selected_choice} (Q: {insight.question})")

        prompt = f"""Based on our conversation, generate exactly 5 gift recommendations as a JSON array.

=== RECIPIENT ===
Age: {profile.age}  |  Gender: {profile.gender}  |  Occasion: {profile.occasion}
Relationship: {profile.relationship}  |  Budget: {profile.budget if profile.budget else 'flexible'}
"""
        if positive:
            prompt += "\n=== POSITIVE SIGNALS (things they like) ===\n" + "\n".join(positive) + "\n"
        if negative:
            prompt += "\n=== NEGATIVE SIGNALS (AVOID these categories) ===\n" + "\n".join(negative) + "\n"

        prompt += f"""
=== INSTRUCTIONS ===
- Generate 5 recommendations. Each must have: title, description, price_range, reasoning, confidence_score (0.0-1.0), category
- price_range MUST respect the budget: {profile.budget if profile.budget else 'flexible'}
- reasoning MUST cite specific positive signals above
- Do NOT recommend anything related to negative signals
- Aim for variety: cover different categories so the buyer has real choices
"""
        
        return prompt

# Create a singleton instance
gift_recommendation_agent = GiftRecommendationAgent()