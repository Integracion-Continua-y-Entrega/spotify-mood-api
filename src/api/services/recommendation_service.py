from analytics.recommend import get_tracks_recommendations
from models.recommendation import QueryParams, Recommendation, RecommendedTrack, SessionContext
from services.track_service import TrackService
from services.user_service import UserService
from models.mood import Mood
from models.recommendations_collection import RecommendationCollection
from bson import ObjectId
from bson.errors import InvalidId

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
            sort=[("created_at", -1)],
        )
        return RecommendationCollection(recommendations=await cursor.to_list(100))

    async def recommend(
        self, 
        mood: Mood, 
        spotify_user_id: str, 
        user_service: UserService, 
        track_service: TrackService
    ):  # 🧠 CORREGIDO: Firma limpia y desacoplada de llamadas HTTP externas
        try:
            # 1. Obtener todas las canciones locales
            tracks_collection = await track_service.list_tracks(limit=10000)
            tracks_list = tracks_collection.tracks

            acoustic_profile = (await user_service.find_by_spotify_id(spotify_user_id)).model_dump()["preferences"]["acoustic_profile"]

            # 2. Calcular proximidad del algoritmo matemático
            result_df = get_tracks_recommendations([t.model_dump() for t in tracks_list], acoustic_profile, mood)
            max_dist = result_df['distance'].max() or 1
            top_results = result_df.head(30)
            
            recommended_tracks = [
                RecommendedTrack(
                    track_id=row['id'],
                    score=round(1 - (row['distance'] / max_dist), 4),
                    rank=rank
                )
                for rank, (_, row) in enumerate(top_results.iterrows(), start=1)
            ]

            recommendation = Recommendation(
                user_id=spotify_user_id,
                query_params=QueryParams(),
                tracks=recommended_tracks,
                total_results=len(recommended_tracks),
                session_context=SessionContext(mood=mood.value)
            )

            recommendation_id = await self.create(recommendation)
            recommendation.id = recommendation_id

            return RecommendationCollection(recommendations=[recommendation])

        except Exception as e:
            logger.error(f"Error en el algoritmo de recomendación: {e}")
            print(e)

    async def create(self, recommendation: Recommendation) -> str:
        # El modelo de guardado en la base de datos se mantiene puro y ligero
        doc = recommendation.model_dump(by_alias=True, exclude={"id"})
        result = await self.recommendations.insert_one(doc)
        return str(result.inserted_id)