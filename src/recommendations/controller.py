from fastapi import APIRouter, Depends, HTTPException
from ..database.core import get_db
from ..auth.service import get_current_user
from ..auth.models import TokenData
from .service import get_recommendation_service, RecommendationService
from .models import RecommendationRequest, RecommendationResponse
from uuid import UUID
import asyncio

router = APIRouter()

@router.post("/personas/{persona_id}/recommendations", response_model=RecommendationResponse)
async def get_gift_recommendations(
    persona_id: UUID,
    max_recommendations: int = 5,
    include_reasoning: bool = True,
    current_user: TokenData = Depends(get_current_user),
    session = Depends(get_db)
):
    """
    Generate personalized gift recommendations based on persona and question answers.
    
    This endpoint analyzes:
    - Persona details (age, gender, occasion, budget, relationship)
    - All question-answer pairs to understand recipient's personality and interests
    - Provides intelligent, contextual gift suggestions with reasoning
    """
    try:
        service = get_recommendation_service(session)
        request = RecommendationRequest(
            persona_id=persona_id,
            max_recommendations=max_recommendations,
            include_reasoning=include_reasoning
        )
        
        # Generate recommendations (this maintains full context)
        recommendations = await service.get_recommendations(request)
        
        return recommendations
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(e)}")

@router.get("/personas/{persona_id}/profile", response_model=dict)
async def get_persona_profile_summary(
    persona_id: UUID,
    current_user: TokenData = Depends(get_current_user),
    session = Depends(get_db)
):
    """
    Get a complete summary of the persona profile including all collected insights.
    
    This is useful for debugging or showing users what information has been collected.
    """
    try:
        service = get_recommendation_service(session)
        # Build the profile (same as used for recommendations)
        profile = service._build_persona_profile(persona_id)
        
        return {
            "persona_details": {
                "age": profile.age,
                "gender": profile.gender,
                "occasion": profile.occasion,
                "relationship": profile.relationship
            },
            "question_insights": [
                {
                    "question": insight.question,
                    "selected_choice": insight.selected_choice,
                    "available_choices": insight.available_choices,
                    "category": insight.insight_category
                }
                for insight in profile.question_insights
            ],
            "insights_count": len(profile.question_insights),
            "ready_for_recommendations": len(profile.question_insights) > 0
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")