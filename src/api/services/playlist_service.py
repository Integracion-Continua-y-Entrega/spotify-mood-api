import os
from datetime import datetime, timezone
from fastapi import HTTPException
from models.playlist import Playlist
from models.playlists_collection import PlaylistCollection
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from bson.errors import InvalidId
from cryptography.fernet import Fernet
import httpx
import logging

from services.spotify_service import _spotify_basic_header, encrypt_refresh_token

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    key = os.getenv("TOKEN_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY no definida en .env")
    return Fernet(key)


async def _get_spotify_access_token_data(spotify_id: str, users_collection) -> dict:
    """Obtiene un access token fresco de Spotify usando el refresh token en MongoDB."""
    doc = await users_collection.find_one({"spotify_id": spotify_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    fernet = _get_fernet()
    try:
        refresh_token = fernet.decrypt(doc["spotify_refresh_token"].encode()).decode()
    except Exception:
        raise HTTPException(status_code=500, detail="Error al descifrar el refresh token")

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Credenciales de Spotify no configuradas")

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                "https://accounts.spotify.com/api/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {_spotify_basic_header(client_id, client_secret)}",
                },
                timeout=10.0,
            )
            res.raise_for_status()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            detail = f"Error al refrescar token de Spotify: {e.response.text}"

            try:
                spotify_error = e.response.json()
            except ValueError:
                spotify_error = {}

            if spotify_error.get("error") == "invalid_grant":
                status_code = 401
                detail = (
                    "El refresh token de Spotify fue revocado o expiró. "
                    "Inicia sesión nuevamente con Spotify para generar un token válido."
                )

            raise HTTPException(status_code=status_code, detail=detail)
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Error de conexión con Spotify")

    token_data = res.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=502, detail="Spotify no devolvió access_token")

    if token_data.get("refresh_token"):
        encrypted_refresh = encrypt_refresh_token(fernet, token_data["refresh_token"])
        await users_collection.update_one(
            {"spotify_id": spotify_id},
            {"$set": {"spotify_refresh_token": encrypted_refresh}},
        )

    return {
        "access_token": access_token,
        "scope": token_data.get("scope", ""),
    }


async def _get_spotify_access_token(spotify_id: str, users_collection) -> str:
    token_data = await _get_spotify_access_token_data(spotify_id, users_collection)
    return token_data["access_token"]


async def _get_spotify_ids_from_track_ids(
    track_ids: list[str],
    tracks_collection,
) -> list[str]:
    """Convierte una lista de track_ids de MongoDB a spotify_ids."""
    oids = []
    for tid in track_ids:
        try:
            oids.append(ObjectId(tid))
        except InvalidId:
            pass

    if not oids:
        return []

    cursor = tracks_collection.find(
        {"_id": {"$in": oids}},
        {"external_ids.spotify_id": 1},
    )
    docs = await cursor.to_list(len(oids))
    spotify_ids_by_track_id = {
        str(d["_id"]): d["external_ids"]["spotify_id"]
        for d in docs
        if d.get("external_ids", {}).get("spotify_id")
    }

    return [
        spotify_ids_by_track_id[tid]
        for tid in track_ids
        if tid in spotify_ids_by_track_id
    ]


class PlaylistService:
    def __init__(
        self,
        collection: AsyncIOMotorCollection,
        users_collection: AsyncIOMotorCollection = None,
        tracks_collection: AsyncIOMotorCollection = None,
    ):
        self.playlists = collection
        self.users = users_collection
        self.tracks = tracks_collection

    async def list_playlists(self) -> PlaylistCollection:
        try:
            return PlaylistCollection(
                playlists=await self.playlists.find().to_list(1000)
            )
        except Exception as e:
            raise Exception(e)

    async def list_user_playlists(self, spotify_id: str) -> PlaylistCollection:
        """Recupera todas las playlists creadas por el usuario autenticado."""
        try:
            docs = await self.playlists.find({"user_id": spotify_id}).to_list(1000)
            return PlaylistCollection(playlists=docs)
        except Exception as e:
            logger.error(f"Error al obtener playlists del usuario {spotify_id}: {e}")
            raise HTTPException(status_code=500, detail="Error al obtener playlists")

    async def create_spotify_playlist(
        self,
        spotify_id: str,
        name: str,
        track_ids: list[str],
        description: str = "",
        public: bool = False,
    ) -> Playlist:
        """
        Flujo completo:
        1. Obtiene access token de Spotify automaticamente
        2. Convierte track_ids de MongoDB a spotify_ids
        3. Crea la playlist en Spotify
        4. Agrega las canciones a la playlist
        5. Persiste la playlist en MongoDB
        """
        token_data = await _get_spotify_access_token_data(spotify_id, self.users)
        access_token = token_data["access_token"]
        granted_scope = token_data.get("scope", "")

        spotify_track_ids = await _get_spotify_ids_from_track_ids(track_ids, self.tracks)
        if len(spotify_track_ids) != len(track_ids):
            raise HTTPException(
                status_code=400,
                detail="Todas las canciones recomendadas deben existir y tener spotify_id",
            )

        async with httpx.AsyncClient() as client:
            try:
                me_res = await client.get(
                    "https://api.spotify.com/v1/me",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
                me_res.raise_for_status()
                current_spotify_user = me_res.json()
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Error de Spotify al validar usuario: {e.response.text}",
                )

            current_spotify_id = current_spotify_user.get("id")
            if current_spotify_id != spotify_id:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": "El token de Spotify pertenece a otro usuario",
                        "jwt_spotify_id": spotify_id,
                        "spotify_me_id": current_spotify_id,
                    },
                )

            try:
                res = await client.post(
                    "https://api.spotify.com/v1/me/playlists",
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
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail={
                        "message": "Error de Spotify al crear playlist",
                        "spotify_response": e.response.text,
                        "jwt_spotify_id": spotify_id,
                        "spotify_me_id": current_spotify_id,
                        "granted_scope": granted_scope,
                        "required_scope": (
                            "playlist-modify-public"
                            if public
                            else "playlist-modify-private"
                        ),
                    },
                )

            spotify_playlist = res.json()
            playlist_id = spotify_playlist["id"]

            uris = [f"spotify:track:{sid}" for sid in spotify_track_ids]
            try:
                add_res = await client.post(
                    f"https://api.spotify.com/v1/playlists/{playlist_id}/items",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json",
                    },
                    json={"uris": uris},
                    timeout=10.0,
                )
                add_res.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Error de Spotify al agregar canciones: {e.response.text}",
                )

        now = datetime.now(timezone.utc)
        playlist_doc = {
            "user_id": spotify_id,
            "name": spotify_playlist.get("name", name),
            "description": spotify_playlist.get("description", description),
            "is_generated": True,
            "recommendation_id": None,
            "tracks": [
                {"track_id": tid, "added_at": now, "position": i + 1}
                for i, tid in enumerate(track_ids)
            ],
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
