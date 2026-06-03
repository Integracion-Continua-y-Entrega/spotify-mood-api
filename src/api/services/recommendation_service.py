import datetime
import logging
from typing import Literal

import numpy as np

from analytics.recommend import get_tracks_recommendations
from analytics.time_of_day import get_time_of_day
from models.mood import Mood
from models.recommendation import AcousticRangeFilter, QueryParams, Recommendation, RecommendedTrack, SessionContext, TempoRangeFilter, USER_FEEDBACK
from models.recommendations_collection import RecommendationCollection
from services.track_service import TrackService
from services.user_service import UserService
from exceptions.exceptions import InvalidIdError, NotFoundError, InternalError
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorCollection

logger = logging.getLogger(__name__)

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
        """
        Genera una recomendación personalizada basada en el mood del usuario
        y su perfil acústico, y la persiste en la base de datos.

        Args:
            mood: Representa el estado de ánimo del usuario al generar las recomendaciones.
            spotify_user_id: ID del usuario en Spotify.
            user_service: Servicio requerido para obtener el perfil acústico del usuario.
            track_service: Servicio requerido para recuperar el catálogo de tracks

        Returns:
            RecommendationCollection con las canciones recomendadas.

        Raises:
            InternalError: Si ocurre algún fallo durante el proceso. 
        """
        try:
            # Carga el catálogo completo (850k)
            raw_tracks = await track_service.list_tracks_raw(limit=850000)

            acoustic_profile = (
                await user_service.find_by_spotify_id(spotify_user_id)
            ).model_dump()["preferences"]["acoustic_profile"]
            
            recommendation_dict = get_tracks_recommendations(
                raw_tracks, 
                acoustic_profile, 
                mood,
                recent_track_ids=await self.get_recent_tracks_ids(
                    spotify_user_id=spotify_user_id,
                    mood=mood,
                    limit=3
                ),
                feedback_map=await self.get_track_feedback_map(
                    spotify_user_id=spotify_user_id
                )
            )

            results = recommendation_dict["tracks"]
            query_params_dict = recommendation_dict["query_params"]

            # Si todos los scores son igual a cero, se iguala a 1 para evitar error de división por cero
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
                query_params=QueryParams(
                    energy=AcousticRangeFilter(
                        min=query_params_dict["energy"]["min"],
                        max=query_params_dict["energy"]["max"],
                    ),
                    danceability=AcousticRangeFilter(
                        min=query_params_dict["danceability"]["min"],
                        max=query_params_dict["danceability"]["max"],
                    ),
                    valence=AcousticRangeFilter(
                        min=query_params_dict["valence"]["min"],
                        max=query_params_dict["valence"]["max"],
                    ),
                    tempo=TempoRangeFilter(
                        min=query_params_dict["tempo"]["min"],
                        max=query_params_dict["tempo"]["max"],
                    ),
                ),
                tracks=recommended_tracks,
                total_results=len(recommended_tracks),
                session_context=SessionContext(
                    mood=mood.value,
                    time_of_day=get_time_of_day().value
                ),
            )

            await self._log_recommendation_intersection(
                spotify_user_id=spotify_user_id,
                current_tracks=recommended_tracks
            )

            recommendation_id = await self.create(recommendation)
            recommendation.id = recommendation_id

            return RecommendationCollection(recommendations=[recommendation])

        except Exception as e:
            logger.error(f"Error al generar recomendaciones: {e}")
            raise InternalError("Error interno al generar recomendaciones")

    async def create(self, recommendation: Recommendation) -> str:
        # El modelo de guardado en la base de datos se mantiene puro y ligero
        doc = recommendation.model_dump(by_alias=True, exclude={"id"})
        result = await self.recommendations.insert_one(doc)
        return str(result.inserted_id)

    async def update_recommended_track_feedback(
        self,
        recommendation_id: str,
        recommended_track_id: str,
        feedback: USER_FEEDBACK,
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
        
    async def _log_recommendation_intersection(
        self,
        spotify_user_id: str,
        current_tracks: list[RecommendedTrack]
    ) -> None:
        """
        Recupera la recomendación más reciente del usuario y calcula
        la intersección de tracks con la recomendación actual.

        Se registra como log informativo para monitorear diversidad.
        """
        previous_recommendation = await self.recommendations.find_one(
            {"user_id": spotify_user_id},
            sort=[("generated_at", -1)],
            projection={"tracks.track_id": 1},
        )

        if not previous_recommendation:
            logger.info(
                f"[Recommendation Diversity] "
                f"user={spotify_user_id} previous_recommendation=None"
            )
            return

        previous_track_ids = {
            track["track_id"]
            for track in previous_recommendation.get("tracks", [])
        }

        current_track_ids = {
            track.track_id
            for track in current_tracks
        }

        intersection = previous_track_ids.intersection(
            current_track_ids
        )

        overlap_percentage = (
            len(intersection) / len(current_track_ids)
            if current_track_ids
            else 0
        )

        logger.info(
            "[Recommendation Diversity] "
            f"user={spotify_user_id} "
            f"intersection={len(intersection)}/{len(current_track_ids)} "
            f"overlap={overlap_percentage:.2%} "
            f"repeated_tracks={list(intersection)[:10]}"
        )

    async def get_recent_recommendations(
        self,
        spotify_user_id: str,
        limit: int = 10,
        mood: Mood | None = None
    ) -> RecommendationCollection:
        """
        Recupera las últimas 'n' recomendaciones de un usuario, 
        filtradas opcionalmente por un estado de ánimo (mood).
        """
        try:
            query_filter = {"user_id": spotify_user_id}

            if mood is not None:
                query_filter["session_context.mood"] = mood.value

            sort_field = "generated_at" 

            cursor = self.recommendations.find(
                query_filter,
                sort=[(sort_field, -1)]
            ).limit(limit)

            docs = await cursor.to_list(length=limit)
            
            return RecommendationCollection(
                recommendations=[Recommendation.model_validate(doc) for doc in docs]
            )

        except Exception as e:
            logger.error(f"Error al obtener recomendaciones recientes para {spotify_user_id}: {e}")
            raise InternalError("Error al recuperar el historial de recomendaciones")
        
    async def get_recent_tracks_ids(
        self, 
        spotify_user_id: str, 
        mood: Mood | None = None,
        limit : int = 10
    ) -> list[str]:
        """
        Recupera directamente de la BD los track_ids de las últimas 3 
        recomendaciones sin procesar modelos intermedios.
        """
        try:
            query = {"user_id": spotify_user_id}
            if mood is not None:
                query["session_context.mood"] = mood.value

            pipeline = [
                {"$match": query},
                {"$sort": {"generated_at": -1}}, 
                {"$limit": limit},
                {"$project": {"tracks_ids": "$tracks.track_id", "_id": 0}},
                {"$unwind": "$tracks_ids"},
                {"$group": {
                    "_id": None,
                    "all_ids": {"$addToSet": "$tracks_ids"} 
                }}
            ]

            cursor = self.recommendations.aggregate(pipeline)
            result = await cursor.to_list(length=1)

            if not result:
                return []

            return result[0]["all_ids"]

        except Exception as e:
            logger.error(f"Error al agregar track_ids para {spotify_user_id}: {e}")
            raise InternalError("Error al procesar el historial de tracks")
        
    async def get_track_feedback_map(
        self, 
        spotify_user_id: str, 
        limit_recommendations: int = 50
    ) -> dict[str, str]:
        """
        Construye un mapa de {track_id: user_feedback} basado en las últimas 
        'n' recomendaciones del usuario que contienen interacciones reales.
        """
        try:
            pipeline = [
                {"$match": {"user_id": spotify_user_id}},
                
                {"$sort": {"generated_at": -1}},
                
                {"$limit": limit_recommendations},
                
                {"$unwind": "$tracks"},
                
                {
                    "$match": {
                        "tracks.user_feedback": {"$ne": None}
                    }
                },
                
                {
                    "$sort": {
                        "tracks.feedback_at": 1,
                        "generated_at": 1
                    }
                },
                
                {
                    "$group": {
                        "_id": "$tracks.track_id",
                        "feedback": {"$last": "$tracks.user_feedback"}
                    }
                }
            ]

            cursor = self.recommendations.aggregate(pipeline)
            results = await cursor.to_list(length=None)

            feedback_map = {doc["_id"]: doc["feedback"] for doc in results}

            return feedback_map

        except Exception as e:
            logger.error(f"Error al generar el mapa de feedback para {spotify_user_id}: {e}")
            raise InternalError("Error interno al recopilar el feedback del usuario")