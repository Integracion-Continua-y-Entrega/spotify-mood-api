from datetime import datetime, timezone
from fastapi import HTTPException

from analytics.preferences import calculate_user_preferences
from services.track_service import TrackService
from models.user import UserModel
from models.users_collection import UserCollection
from motor.motor_asyncio import AsyncIOMotorCollection

import logging

# Configuración del logger del módulo
logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.users = collection

    async def list_users(self):
        try:
            return UserCollection(
                users=await self.users.find().to_list(1000))
        except Exception as e:
            logger.error(f"Error al listar usuarios: {e}")
            raise Exception(e)
                
    async def count(self) -> int:
        return await self.users.count_documents({"is_active": True})

    async def find_by_id(self, user_id: str) -> UserModel | None:
        doc = await self.users.find_one({"_id": user_id})
        return UserModel.model_validate(doc) if doc else None

    async def find_by_spotify_id(self, spotify_id: str) -> UserModel | None:
        doc = await self.users.find_one({"spotify_id": spotify_id})
        return UserModel.model_validate(doc) if doc else None

    async def find_by_email(self, email: str) -> UserModel | None:
        doc = await self.users.find_one({"email": email})
        return UserModel.model_validate(doc) if doc else None
    
    async def clear_preferences(self, spotify_id: str) -> None:
        result = await self.users.update_one(
            {"spotify_id": spotify_id},
            {"$unset": {"preferences": ""}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Usuario {spotify_id} no encontrado")
    
    async def deactivate(self, spotify_id: str) -> None:
        """Soft delete: marca el usuario como inactivo sin eliminarlo."""
        result = await self.users.update_one(
            {"spotify_id": spotify_id},
            {"$set": {"is_active": False}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Usuario {spotify_id} no encontrado")

    async def reactivate(self, spotify_id: str) -> None:
        result = await self.users.update_one(
            {"spotify_id": spotify_id},
            {"$set": {"is_active": True}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Usuario {spotify_id} no encontrado")
    
    async def upsert_user(
        self,
        spotify_user: dict,
        encrypted_refresh: str,
    ) -> None:
        """Crea o actualiza el usuario en MongoDB."""
        now = datetime.now(timezone.utc)
        try:
            await self.users.update_one(
                {"spotify_id": spotify_user["id"]},
                {
                    "$set": {
                        "display_name": spotify_user.get("display_name"),
                        "email": spotify_user.get("email"),
                        "profile_image": (
                            spotify_user["images"][0]["url"]
                            if spotify_user.get("images")
                            else None
                        ),
                        "spotify_refresh_token": encrypted_refresh,
                        "last_login": now,
                    },
                    "$setOnInsert": {
                        "spotify_id": spotify_user["id"],
                        "created_at": now,
                        "is_active": True,  # ⚡ MEJORA: Asegura que nazca activo para el método count()
                    },
                },
                upsert=True,
            )
        except Exception as e:
            logger.error(f"Error en upsert_user de MongoDB: {e}")
            raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
        
    async def update_user_preferences(self, spotify_id: str, top_raw_tracks: list[dict], track_service: TrackService) -> None:
        """Actualiza las preferencias musicales del usuario calculadas por el módulo de analíticas."""        
        try:
            tracks = [await track_service.find_by_spotify_id(t["id"]) for t in top_raw_tracks]

            for i in range(len(tracks)):
                logger.info(f"Procesando preferencia {i}: {tracks[i]}")

            valid_tracks = [t.model_dump() for t in tracks if t is not None]
            
            if not valid_tracks:
                raise ValueError(f"No se encontraron tracks válidos en la BD para el usuario {spotify_id}")

            preferences = calculate_user_preferences(valid_tracks)

            result = await self.users.update_one(
                {"spotify_id": spotify_id}, 
                {"$set": {"preferences": preferences.model_dump()}}
            )

            if result.matched_count == 0:
                raise LookupError(f"Usuario con id {spotify_id} no encontrado")

        except (ValueError, LookupError) as e:
            logger.error(f"Error de validación en preferencias: {e}")  # ⚡ MEJORA: Uso correcto de loggers
            raise 
        except Exception as e:
            logger.error(f"Error crítico en update_user_preferences: {e}")
            raise RuntimeError(f"Error inesperado al actualizar preferencias: {e}") from e
    
    async def update_refresh_token(self, spotify_id: str, encrypted_refresh: str) -> None:
        """Actualiza el refresh token encriptado del usuario."""
        result = await self.users.update_one(
            {"spotify_id": spotify_id},
            {"$set": {"spotify_refresh_token": encrypted_refresh}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail=f"Usuario {spotify_id} no encontrado")

    # =====================================================================
    # ⚡ NUEVO MÉTODO: REQUERIDO PARA REPRODUCCIÓN EN TIEMPO REAL
    # =====================================================================

    async def update_spotify_access_token(self, spotify_id: str, access_token: str) -> None:
        """
        Guarda o actualiza el access_token vivo de Spotify del usuario en MongoDB.
        Alimentará de forma segura al inyector masivo de vistas de preescucha.
        """
        result = await self.users.update_one(
            {"spotify_id": spotify_id},
            {"$set": {"spotify_access_token": access_token}}
        )
        if result.matched_count == 0:
            logger.warning(f"No se pudo guardar el token. Usuario {spotify_id} no encontrado.")
            raise HTTPException(status_code=404, detail=f"Usuario {spotify_id} no encontrado")