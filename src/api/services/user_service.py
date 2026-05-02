from datetime import datetime, timezone

from fastapi import HTTPException

from models.dtos.create_user_dto import CreateUserDTO
from models.user import UserModel
from models.users_collection import UserCollection

class UserService:
    def __init__(self, collection):
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
            await self.update_one(
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
