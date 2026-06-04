from fastapi import APIRouter, Depends, HTTPException, Query, status

from exceptions.exceptions import InvalidIdError, NotFoundError, InternalError
from models.recommendation import Recommendation, USER_FEEDBACK
from models.mood import Mood
from models.recommendations_collection import RecommendationCollection
from dependencies import (
    get_current_user, 
    get_recommendation_service, 
    get_track_service, 
    get_user_service
)
from services.recommendation_service import RecommendationService
from services.track_service import TrackService
from services.user_service import UserService

router = APIRouter()


def handle_domain_exceptions(e: Exception) -> None:
    """Traduce excepciones de dominio a HTTPException."""
    if isinstance(e, InvalidIdError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)
    if isinstance(e, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    if isinstance(e, InternalError):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e.detail)
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error inesperado")


@router.get(
    "/recommendations",
    response_description="List all recommendations",
    response_model=RecommendationCollection,
    response_model_by_alias=True,
)
async def get_recommendations(
    service: RecommendationService = Depends(get_recommendation_service),
):
    try:
        return await service.list_recommendations()
    except Exception as e:
        handle_domain_exceptions(e)


@router.post(
    "/users/me/recommendations",
    response_description="Get recommendations based on mood",
    response_model=RecommendationCollection,
    response_model_by_alias=True,
)
async def recommend(
    mood: Mood,
    spotify_user_id: str = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
    user_service: UserService = Depends(get_user_service),
    track_service: TrackService = Depends(get_track_service),
):
    try:
        return await service.recommend(
            mood=mood,
            spotify_user_id=spotify_user_id,
            user_service=user_service,
            track_service=track_service,
        )
    except Exception as e:
        handle_domain_exceptions(e)


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
    try:
        return await service.find_by_user_id(spotify_user_id)
    except Exception as e:
        handle_domain_exceptions(e)


@router.get(
    "/recommendations/{recommendation_id}",
    response_description="Find a recommendation by its ID",
    response_model=Recommendation,
    response_model_by_alias=True,
)
async def get_recommendation_by_id(
    recommendation_id: str,
    tracks_page: int = Query(1, ge=1, description="Página de tracks recomendados"),
    tracks_limit: int = Query(10, ge=1, description="Límite de tracks por página"),
    service: RecommendationService = Depends(get_recommendation_service),
):
    try:
        return await service.find_by_id(
            recommendation_id,
            recommended_tracks_page=tracks_page,
            recommended_tracks_limit=tracks_limit,
        )
    except Exception as e:
        handle_domain_exceptions(e)


@router.patch(
    "/recommendations/{recommendation_id}/tracks/{track_id}",
    response_description="Update feedback for a recommended track",
)
async def update_recommended_track_feedback(
    recommendation_id: str,
    track_id: str,
    feedback: USER_FEEDBACK,
    service: RecommendationService = Depends(get_recommendation_service),
):
    try:
        await service.update_recommended_track_feedback(
            recommendation_id=recommendation_id,
            recommended_track_id=track_id,
            feedback=feedback,
        )
        return {"message": "Feedback actualizado correctamente"}
    except Exception as e:
        handle_domain_exceptions(e)