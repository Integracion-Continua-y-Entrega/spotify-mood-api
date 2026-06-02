from analytics.recommend import get_tracks_recommendations
from models.recommendation import QueryParams, Recommendation, RecommendedTrack, SessionContext
from services.track_service import TrackService
from services.user_service import UserService
from models.mood import Mood
from models.recommendations_collection import RecommendationCollection
# 👈 IMPORTANTE: Importa la función que creamos en tu spotify_service
from services.spotify_service import fetch_preview_urls_map 
import httpx
from bson import ObjectId
from bson.errors import InvalidId

import logging

logger = logging.Logger(__name__, level=logging.INFO)

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

    async def recommend(
        self, 
        mood: Mood, 
        spotify_user_id: str, 
        user_service: UserService, 
        track_service: TrackService,
        http_client: httpx.AsyncClient,  # 👈 AGREGADO
        access_token: str                # 👈 AGREGADO
    ):
        try:
            # 1. Obtener todas las canciones del sistema
            tracks_collection = await track_service.list_tracks(limit=10000)
            tracks_list = tracks_collection.tracks
            
            # Crear un mapa rápido de {str(track._id): objeto_track} para buscar eficientemente después
            tracks_map = {str(t.id): t for t in tracks_list}

            acoustic_profile = (await user_service.find_by_spotify_id(spotify_user_id)).model_dump()["preferences"]["acoustic_profile"]

            # 2. Ejecutar el algoritmo de Machine Learning / Analíticas
            result_df = get_tracks_recommendations([t.model_dump() for t in tracks_list], acoustic_profile, mood)
            max_dist = result_df['distance'].max() or 1
            
            # Limitemos el top de recomendaciones a las mejores 20 o 30 para no saturar a Spotify
            top_results = result_df.head(30)

            # 3. Recopilar los spotify_ids únicos de las canciones recomendadas para ir a buscar sus previews
            spotify_ids_to_enrich = []
            for _, row in top_results.iterrows():
                track_obj = tracks_map.get(str(row['id']))
                if track_obj and track_obj.external_ids.spotify_id:
                    spotify_ids_to_enrich.append(track_obj.external_ids.spotify_id)

            # 4. Consultar a la API de Spotify los previews en caliente
            previews_map = await fetch_preview_urls_map(http_client, spotify_ids_to_enrich, access_token)

            # 5. Construir los objetos recomendados acoplando los detalles completos hidratados
            recommended_tracks = []
            for rank, (_, row) in enumerate(top_results.iterrows(), start=1):
                track_id_str = str(row['id'])
                track_details = tracks_map.get(track_id_str)

                if track_details:
                    # Inyectamos el preview url en caliente obtenido del mapa de Spotify
                    track_details.preview_url = previews_map.get(track_details.external_ids.spotify_id)

                recommended_tracks.append(
                    RecommendedTrack(
                        track_id=track_id_str,
                        score=round(1 - (row['distance'] / max_dist), 4),
                        rank=rank,
                        track_details=track_details # 👈 AQUÍ SE HIDRATA: Pasamos el objeto Track completo modificado
                    )
                )

            recommendation = Recommendation(
                user_id=spotify_user_id,
                query_params=QueryParams(),
                tracks=recommended_tracks,
                total_results=len(recommended_tracks),
                session_context=SessionContext(mood=mood.value)
            )

            # Guardamos la recomendación en Mongo (excluyendo los track_details si quieres mantener tu DB ligera)
            recommendation_id = await self.create(recommendation)
            recommendation.id = recommendation_id

            return RecommendationCollection(recommendations=[recommendation])

        except Exception as e:
            logger.error(f"Error en el proceso de recomendación: {e}")
            print(e)

    async def create(self, recommendation: Recommendation) -> str:
        # Al guardar en Mongo, excluimos track_details de la persistencia para no duplicar datos pesados
        doc = recommendation.model_dump(by_alias=True, exclude={"id", "tracks": {"__all__": {"track_details"}}})
        result = await self.recommendations.insert_one(doc)
        return str(result.inserted_id)