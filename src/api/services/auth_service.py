from datetime import datetime, timedelta, timezone
import logging
import os
import logging
import time
from dotenv import load_dotenv
from fastapi import HTTPException
import httpx
from jose import jwt
from cryptography.fernet import Fernet

from services.track_service import TrackService
from models.login_payload import LoginPayload
from services.spotify_service import encrypt_refresh_token, exchange_code_for_tokens, fetch_spotify_profile, fetch_user_top_tracks
from services.user_service import UserService

ACCESS_TOKEN_EXPIRE_HOURS = 8
logger = logging.getLogger(__name__)

load_dotenv()

def _require_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"Variable de entorno requerida no encontrada: {key}")
    return value

SECRET_KEY            = _require_env("JWT_SECRET_KEY")
SPOTIFY_CLIENT_ID     = _require_env("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = _require_env("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI  = _require_env("SPOTIFY_REDIRECT_URI")
ENCRYPTION_KEY        = _require_env("TOKEN_ENCRYPTION_KEY")

fernet = Fernet(ENCRYPTION_KEY)

logger = logging.getLogger(__name__)

class AuthService():
    
    # 💡 CORREGIDO: Las variables de clase van directas, sin decoradores.
    with_ui_metadata = True  # Flag de control visual interno

    @staticmethod
    async def create_session_jwt(spotify_id: str, secret_key: str) -> tuple[str, int]:
        """
        Genera el JWT de sesión de la aplicación.
        Retorna (token, expires_in_seconds).
        """
        expires_in = ACCESS_TOKEN_EXPIRE_HOURS * 3600
        now = datetime.now(timezone.utc)

        token = jwt.encode(
            {
                "sub": spotify_id,
                "iat": now,
                "exp": now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
            },
            secret_key,
            algorithm="HS256",
        )
        return token, expires_in
    
    async def spotify_login(self, payload: LoginPayload, user_service: UserService, track_service: TrackService):
        async with httpx.AsyncClient() as client:
            tokens = await exchange_code_for_tokens(
                client, payload.code, payload.verifier,
                SPOTIFY_REDIRECT_URI, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET,
            )
            logger.info("Spotify granted scopes: %s", tokens.get("scope", ""))

            spotify_user = await fetch_spotify_profile(client, tokens["access_token"])
            spotify_user_top_tracks = await fetch_user_top_tracks(client, tokens["access_token"])

        encrypted_refresh = encrypt_refresh_token(fernet, tokens["refresh_token"])
        session_token, expires_in = await self.create_session_jwt(spotify_user["id"], SECRET_KEY)

        # 1. Setup y persistencia base del usuario
        await user_service.upsert_user(spotify_user, encrypted_refresh)
        await user_service.update_user_preferences(spotify_user["id"], spotify_user_top_tracks, track_service) 

        # 2. ⚡ MEJORA CRÍTICA: Persistir el token de acceso vivo de Spotify en MongoDB
        # Esto alimenta a la dependencia get_user_spotify_token usada en /tracks/bulk
        await user_service.update_spotify_access_token(spotify_user["id"], tokens["access_token"])

        return {
            "access_token": session_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "spotify_access_token": tokens["access_token"],
            "user": {
                "name": spotify_user.get("display_name"),
                "id": spotify_user["id"],
            },
        }
    
    async def refresh_session(self, spotify_id: str, user_service: UserService):
        user = await user_service.find_by_spotify_id(spotify_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")

        refresh_token = fernet.decrypt(user.spotify_refresh_token.encode()).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://accounts.spotify.com/api/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": SPOTIFY_CLIENT_ID,
                    "client_secret": SPOTIFY_CLIENT_SECRET,
                },
            )
        
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")

        token_data = response.json()

        # Si Spotify mandó una rotación de refresh token, la actualizamos cifrada
        if "refresh_token" in token_data:
            nuevo_encrypted = encrypt_refresh_token(fernet, token_data["refresh_token"])
            await user_service.update_refresh_token(spotify_id, nuevo_encrypted)

        if "access_token" in token_data:
            await user_service.update_spotify_access_token(spotify_id, token_data["access_token"])

        session_token, expires_in = await self.create_session_jwt(spotify_id, SECRET_KEY)

        return {
            "access_token": session_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "spotify_access_token": token_data["access_token"],
        }