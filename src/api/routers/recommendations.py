from fastapi import APIRouter, Depends

from models.recommendations_collection import RecommendationCollection
from dependencies import get_recommendation_service
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

@router.post(
        "/recommendations",
        response_description="Get recommendations based on mood",
        response_model=RecommendationCollection,
        response_model_by_alias=True,
        )
async def recommend(service: RecommendationService = Depends(get_recommendation_service)):
    return await service.recommend()

