from fastapi import HTTPException

from analytics.recommend import get_tracks_recommendations
from models.recommendation import QueryParams, Recommendation, RecommendedTrack, SessionContext
from services.track_service import TrackService
from services.user_service import UserService
from models.mood import Mood
from models.recommendations_collection import RecommendationCollection
from bson import ObjectId
from bson.errors import InvalidId
import time

import logging

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(self, collection):
        self.recommendations = collection

    async def list_recommendations(self):
        try:
            return RecommendationCollection(
                recommendations=await self.recommendations.find().to_list(1000))
        except Exception as e:
            raise Exception(e)
        
    async def find_by_id(self, recommendation_id: str) -> Recommendation | None:
        try:
            oid = ObjectId(recommendation_id)
        except InvalidId:
            return None
        doc = await self.recommendations.find_one({"_id": oid})
        return Recommendation.model_validate(doc) if doc else None

    async def find_by_user_id(self, spotify_user_id: str) -> RecommendationCollection:
        cursor = self.recommendations.find(
            {"user_id": spotify_user_id},
            sort=[("created_at", -1)],  # más recientes primero
        )
        return RecommendationCollection(recommendations=await cursor.to_list(100))

    
    async def recommend(self, mood: Mood, spotify_user_id: str, user_service: UserService, track_service: TrackService) :
        try:
            
            start = time.perf_counter()

            # Traer los tracks en bruto como lista de dicts
            raw_tracks = await track_service.list_tracks_raw(limit=500000)

            end = time.perf_counter()

            
            logger.info("Fetch tracks took %.2fms", (end - start) * 1000)            
            
            # Traer el perfil acústico del usuario
            acoustic_profile = (await user_service.find_by_spotify_id(spotify_user_id)).model_dump()["preferences"]["acoustic_profile"] 

            
            # Obtener las canciones recomendadas 
            # Obtener canciones recomendadas


            start = time.perf_counter()


            results = get_tracks_recommendations(
                raw_tracks,
                acoustic_profile,
                mood
            )

            

            end = time.perf_counter()

            
            logger.info("Recommendation engine took %.2fms", (end - start) * 1000)            
                
            
            start = time.perf_counter()


            # Distancia máxima para normalización
            max_dist = max(r["distance"] for r in results) or 1.0


            recommended_tracks = [
                RecommendedTrack(
                    track_id=result["id"],
                    score=round(
                        1 - (result["distance"] / max_dist),
                        4
                    ),
                    rank=rank
                )
                for rank, result in enumerate(results, start=1)
            ]


            recommendation = Recommendation(
                user_id=spotify_user_id,
                query_params=QueryParams(),
                tracks=recommended_tracks,
                total_results=len(recommended_tracks),
                session_context=SessionContext(
                    mood=mood.value
                )
            )

            recommendation_id = await self.create(recommendation)

            recommendation.id = recommendation_id


            end = time.perf_counter()

            
            logger.info("Process reccomendations took %.2fms", (end - start) * 1000)            
    
            return RecommendationCollection(
                recommendations=[recommendation]
            )

        except Exception as e:
            logging.error(f"Error en recomendación: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Error interno al generar recomendaciones"
            )

    async def create(self, recommendation: Recommendation) -> str:
        doc = recommendation.model_dump(by_alias=True, exclude={"id"})
        result = await self.recommendations.insert_one(doc)
        return str(result.inserted_id)