from datetime import datetime, timezone
from fastapi import HTTPException
from models.playlist import Playlist, PlaylistTrack
from models.playlists_collection import PlaylistCollection
from motor.motor_asyncio import AsyncIOMotorCollection
import httpx
import logging

logger = logging.getLogger(__name__)

class PlaylistService:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.playlists = collection

    async def list_playlists(self):
        try:
            return PlaylistCollection(
                playlists=await self.playlists.find().to_list(1000))
        except Exception as e:
            raise Exception(e)

    async def list_user_playlists(self, spotify_id: str) -> PlaylistCollection:
        try:
            docs = await self.playlists.find(
                {"user_id": spotify_id}
            ).to_list(1000)
            return PlaylistCollection(playlists=docs)
        except Exception as e:
            logger.error(f"Error al obtener playlists del usuario {spotify_id}: {e}")
            raise HTTPException(status_code=500, detail="Error al obtener playlists")

    async def create_spotify_playlist(
        self,
        spotify_id: str,
        access_token: str,
        name: str,
        description: str = "",
        public: bool = False,
    ) -> Playlist:
        """
        Crea una playlist en Spotify y la persiste en MongoDB.
        """
        # 1. Crear la playlist en Spotify
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(
                    f"https://api.spotify.com/v1/users/{spotify_id}/playlists",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "name": name,
                        "description": description,
                        "public": public,
                    },
                    timeout=10.0,
                )
                res.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Error al crear playlist en Spotify: {e.response.text}")
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Error de Spotify: {e.response.text}"
                )
            except httpx.RequestError as e:
                raise HTTPException(status_code=500, detail="Error de conexión con Spotify")

        spotify_playlist = res.json()

        # 2. Persistir en MongoDB
        now = datetime.now(timezone.utc)
        playlist_doc = {
            "user_id": spotify_id,
            "name": spotify_playlist.get("name", name),
            "description": spotify_playlist.get("description", description),
            "is_generated": False,
            "recommendation_id": None,
            "tracks": [],
            "created_at": now,
            "updated_at": now,
            "is_public": public,
        }

        try:
            result = await self.playlists.insert_one(playlist_doc)
            playlist_doc["_id"] = str(result.inserted_id)
            return Playlist(**playlist_doc)
        except Exception as e:
            logger.error(f"Error al persistir playlist en MongoDB: {e}")
            raise HTTPException(status_code=500, detail="Error al guardar la playlist")
