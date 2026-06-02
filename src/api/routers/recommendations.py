from fastapi import APIRouter, Depends, HTTPException, status
import httpx  # 👈 CORREGIDO: Importación necesaria para el tipado

from models.recommendation import Recommendation
from services.track_service import TrackService
from services.user_service import UserService
from models.mood import Mood
from models.recommendations_collection import RecommendationCollection
from dependencies import (
    get_current_user, 
    get_recommendation_service, 
    get_track_service, 
    get_user_service,
    get_httpx_client,
    get_user_spotify_token
)
from services.recommendation_service import RecommendationService

router = APIRouter()

@router.get(
        "/recommendations",
        response_description="List all recommendations",
        response_model=RecommendationCollection,
        response_model_by_alias=True,
        )
async def get_recommendations(service: RecommendationService = Depends(get_recommendation_service)):
    return await service.list_recommendations()

# 👈 CORREGIDO: Se eliminó el método redundante e incompleto que estaba aquí

@router.post(
        "/users/me/recommendations",
        response_description="Get recommendations based on mood",
        response_model_by_alias=True,
        response_model=RecommendationCollection
        )
async def recommend(
                    mood: Mood, 
                    spotify_user_id: str = Depends(get_current_user), 
                    service: RecommendationService = Depends(get_recommendation_service), 
                    user_service: UserService = Depends(get_user_service), 
                    track_service: TrackService = Depends(get_track_service),
                    http_client: httpx.AsyncClient = Depends(get_httpx_client), 
                    spotify_token: str = Depends(get_user_spotify_token)        
):
    return await service.recommend(
        mood=mood, 
        spotify_user_id=spotify_user_id, 
        user_service=user_service, 
        track_service=track_service,
        http_client=http_client,
        access_token=spotify_token
    )

@router.get(
    "/users/me/recommendations",
    response_description="Recommendations for the current authenticated user",
    response_model=RecommendationCollection,
    response_model_by_alias=True,
)
async def get_my_recommendations(
    spotify_user_id: str = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    return await service.find_by_user_id(spotify_user_id)


@router.get(
    "/recommendations/{id}",
    response_description="Find a recommendation by its ID",
    response_model=Recommendation,
    response_model_by_alias=True,
)
async def get_recommendation_by_id(
    recommendation_id: str,
    service: RecommendationService = Depends(get_recommendation_service),
):
    recommendation = await service.find_by_id(recommendation_id)
    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found",
        )
    return recommendation