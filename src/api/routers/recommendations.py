from fastapi import APIRouter, Depends

from services.track_service import TrackService
from services.user_service import UserService
from models.mood import Mood
from models.recommendations_collection import RecommendationCollection
from dependencies import get_current_user, get_recommendation_service, get_track_service, get_user_service
from services.recommendation_service import RecommendationService

router = APIRouter()

@router.get(
        "",
        response_description="List all recommendations",
        response_model=RecommendationCollection,
        response_model_by_alias=True,
        )
async def get_recommendations(service: RecommendationService = Depends(get_recommendation_service)):
    return await service.list_recommendations()

@router.post(
        "",
        response_description="Get recommendations based on mood",
        response_model_by_alias=True,
        response_model=RecommendationCollection
        )
async def recommend(mood: Mood, spotify_user_id: str = Depends(get_current_user), 
                    service: RecommendationService = Depends(get_recommendation_service), 
                    user_service: UserService = Depends(get_user_service), 
                    track_service: TrackService = Depends(get_track_service)):
    return await service.recommend(mood=mood, spotify_user_id=spotify_user_id, user_service=user_service, track_service=track_service)

