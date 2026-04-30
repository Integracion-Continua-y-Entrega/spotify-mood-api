import os
import httpx
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from fastapi.middleware.cors import CORSMiddleware

from db.connection import get_database, MongoDB
from services.spotify_auth import (
    exchange_code_for_tokens,
    fetch_spotify_profile,
    encrypt_refresh_token,
    upsert_user,
    create_session_jwt,
)

from routers import playlists, recommendations, tracks, users

load_dotenv()

def _require_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"❌ Variable de entorno requerida no encontrada: {key}")
    return value

SECRET_KEY            = _require_env("JWT_SECRET_KEY")
SPOTIFY_CLIENT_ID     = _require_env("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = _require_env("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI  = _require_env("SPOTIFY_REDIRECT_URI")
ENCRYPTION_KEY        = _require_env("TOKEN_ENCRYPTION_KEY")

fernet = Fernet(ENCRYPTION_KEY)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_database()
    app.state.users_collection = db.get_collection("users")
    yield
    await MongoDB.close_connection()

app = FastAPI(lifespan=lifespan)
app.include_router(playlists.router)
app.include_router(recommendations.router)
app.include_router(users.router)
app.include_router(tracks.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginPayload(BaseModel):
    code: str
    verifier: str


@app.post("/api/v1/auth/login")
async def spotify_login(request: Request, payload: LoginPayload):
    async with httpx.AsyncClient() as client:
        tokens = await exchange_code_for_tokens(
            client, payload.code, payload.verifier,
            SPOTIFY_REDIRECT_URI, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET,
        )
        spotify_user = await fetch_spotify_profile(client, tokens["access_token"])

    encrypted_refresh = encrypt_refresh_token(fernet, tokens["refresh_token"])
    await upsert_user(request.app.state.users_collection, spotify_user, encrypted_refresh)
    session_token, expires_in = create_session_jwt(spotify_user["id"], SECRET_KEY)

    return {
        "access_token": session_token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {
            "name": spotify_user.get("display_name"),
            "id": spotify_user["id"],
        },
    }