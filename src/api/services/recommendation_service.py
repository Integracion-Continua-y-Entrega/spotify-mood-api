import datetime
import logging
from typing import Literal

from analytics.recommend import get_tracks_recommendations
from models.mood import Mood
from models.recommendation import QueryParams, Recommendation, RecommendedTrack, SessionContext
from models.recommendations_collection import RecommendationCollection
from services.track_service import TrackService
from services.user_service import UserService
from exceptions.exceptions import InvalidIdError, NotFoundError, InternalError
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

logger = logging.getLogger(__name__)

user_feedback = Literal['like', 'dislike', 'skip']


class RecommendationService:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.recommendations = collection

    async def list_recommendations(self) -> RecommendationCollection:
        try:
            return RecommendationCollection(
                recommendations=await self.recommendations.find().to_list(1000)
            )
        except Exception as e:
            logger.error(f"Error al listar recomendaciones: {e}")
            raise InternalError("Error al obtener las recomendaciones")

    async def find_by_id(
        self,
        recommendation_id: str,
        recommended_tracks_page: int = 1,
        recommended_tracks_limit: int = 10,
    ) -> Recommendation:
        try:
            oid = ObjectId(recommendation_id)
        except InvalidId:
            raise InvalidIdError("ID de recomendación inválido")

        skip = (recommended_tracks_page - 1) * recommended_tracks_limit

        doc = await self.recommendations.find_one(
            {"_id": oid},
            {"tracks": {"$slice": [skip, recommended_tracks_limit]}}
        )

        if not doc:
            raise NotFoundError(f"Recomendación '{recommendation_id}' no encontrada")

        return Recommendation.model_validate(doc)

    async def find_by_user_id(self, spotify_user_id: str) -> RecommendationCollection:
        try:
            cursor = self.recommendations.find(
                {"user_id": spotify_user_id},
                sort=[("created_at", -1)],
            )
            return RecommendationCollection(recommendations=await cursor.to_list(100))
        except Exception as e:
            logger.error(f"Error al buscar recomendaciones del usuario {spotify_user_id}: {e}")
            raise InternalError("Error al obtener las recomendaciones del usuario")

    async def recommend(
        self,
        mood: Mood,
        spotify_user_id: str,
        user_service: UserService,
        track_service: TrackService,
    ) -> RecommendationCollection:
        try:
            raw_tracks = await track_service.list_tracks_raw(limit=850000)

            acoustic_profile = (
                await user_service.find_by_spotify_id(spotify_user_id)
            ).model_dump()["preferences"]["acoustic_profile"]

            results = get_tracks_recommendations(raw_tracks, acoustic_profile, mood)

            max_dist = max(r["distance"] for r in results) or 1.0

            recommended_tracks = [
                RecommendedTrack(
                    track_id=result["id"],
                    score=round(1 - (result["distance"] / max_dist), 4),
                    rank=rank,
                )
                for rank, result in enumerate(results, start=1)
            ]

            recommendation = Recommendation(
                user_id=spotify_user_id,
                query_params=QueryParams(),
                tracks=recommended_tracks,
                total_results=len(recommended_tracks),
                session_context=SessionContext(mood=mood.value),
            )

            recommendation_id = await self.create(recommendation)
            recommendation.id = recommendation_id

            return RecommendationCollection(recommendations=[recommendation])

        except Exception as e:
            logger.error(f"Error al generar recomendaciones: {e}")
            raise InternalError("Error interno al generar recomendaciones")

    async def create(self, recommendation: Recommendation) -> str:
        doc = recommendation.model_dump(by_alias=True, exclude={"id"})
        result = await self.recommendations.insert_one(doc)
        return str(result.inserted_id)

    async def update_recommended_track_feedback(
        self,
        recommendation_id: str,
        recommended_track_id: str,
        feedback: user_feedback,
    ) -> None:
        try:
            oid = ObjectId(recommendation_id)
        except InvalidId:
            raise InvalidIdError("ID de recomendación inválido")

        result = await self.recommendations.update_one(
            {"_id": oid, "tracks.track_id": recommended_track_id},
            {"$set": {
                "tracks.$.user_feedback": feedback,
                "tracks.$.feedback_at": datetime.datetime.now(datetime.timezone.utc),
            }}
        )

        if result.matched_count == 0:
            raise NotFoundError(
                f"Recomendación '{recommendation_id}' o Track '{recommended_track_id}' no encontrado"
            )