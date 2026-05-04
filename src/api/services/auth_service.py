from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import httpx
from jose import jwt
from cryptography.fernet import Fernet

from services.track_service import TrackService
from models.login_payload import LoginPayload
from services.spotify_service import encrypt_refresh_token, exchange_code_for_tokens, fetch_spotify_profile, fetch_user_top_tracks
from services.user_service import UserService

ACCESS_TOKEN_EXPIRE_HOURS = 8

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

class AuthService():
    
    @staticmethod
    async def create_session_jwt(spotify_id: str, secret_key: str) -> tuple[str, int]:
        """
        Genera el JWT de sesión.
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

            spotify_user = await fetch_spotify_profile(client, tokens["access_token"])

            spotify_user_top_tracks = await fetch_user_top_tracks(client, tokens["access_token"])

        encrypted_refresh = encrypt_refresh_token(fernet, tokens["refresh_token"])
        session_token, expires_in = await self.create_session_jwt(spotify_user["id"], SECRET_KEY)

        # Setup del usuario
        await user_service.upsert_user(spotify_user, encrypted_refresh)
        await user_service.update_user_preferences(spotify_user["id"], spotify_user_top_tracks["items"], track_service)

        return {
            "access_token": session_token,
            "token_type": "bearer",
            "expires_in": expires_in,
            "user": {
                "name": spotify_user.get("display_name"),
                "id": spotify_user["id"],
            },
        }