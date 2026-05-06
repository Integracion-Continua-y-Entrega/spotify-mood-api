from datetime import datetime, timezone
from venv import logger

from fastapi import Depends, HTTPException

from analytics.preferences import calculate_user_preferences
from services.track_service import TrackService
from models.dtos.create_user_dto import CreateUserDTO
from models.user import UserModel
from models.users_collection import UserCollection
from motor.motor_asyncio import AsyncIOMotorCollection


class UserService:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.users = collection

    async def list_users(self):
        try:
            return UserCollection(
                users=await self.users.find().to_list(1000))
        except Exception as e:
            raise Exception(e)
        
    async def create_user(self, dto: CreateUserDTO) -> UserModel:
        try:
            user = UserModel(
                username=dto.username,
                email=dto.email,
                password_hash=dto.password,
            )

            result = await self.users.insert_one(user.model_dump(by_alias=True, exclude_none=True))
            user.id = result.inserted_id

            return user
        except Exception as e:
            raise Exception(e)
        
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
                    },
                },
                upsert=True,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
        
    async def update_user_preferences(self, spotify_id: str, top_raw_tracks: list[dict], track_service: TrackService) -> None:
        """Actualizar las preferencias musicales del usuario"""        
        try:
            tracks = [await track_service.find_by_spotify_id(t["id"]) for t in top_raw_tracks]

            for i in range(len(tracks)):
                logger.info(f"{i}. {tracks[i]}")

            valid_tracks = [t.model_dump() for t in tracks if t is not None]
            
            if not valid_tracks:
                raise ValueError(f"No se encontraron tracks válidos para el usuario {spotify_id}")

            preferences = calculate_user_preferences(valid_tracks)

            result = await self.users.update_one(
                {"spotify_id": spotify_id}, 
                {"$set": {"preferences": preferences.model_dump()}}
            )

            if result.matched_count == 0:
                raise LookupError(f"Usuario con id {spotify_id} no encontrado")

        except (ValueError, LookupError) as e:
            print(f"Error de validación: {e}")
            raise 
        except Exception as e:
            raise RuntimeError(f"Error inesperado al actualizar preferencias: {e}") from e