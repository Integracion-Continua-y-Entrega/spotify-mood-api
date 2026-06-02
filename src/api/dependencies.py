import os
import jwt

from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from services.auth_service import AuthService
from db.connection import get_database, MongoDB
from services.playlist_service import PlaylistService
from services.recommendation_service import RecommendationService
from services.track_service import TrackService
from services.user_service import UserService 

db = get_database()
collections = MongoDB.get_collections()

bearer_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> str:
    """Valida el JWT y devuelve el spotify_id del usuario."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        spotify_id: str = payload.get("sub")
        if not spotify_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        return spotify_id
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado o inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_service() -> UserService:
    return UserService(collection=collections["users"])

def get_track_service() -> TrackService:
    return TrackService(collection=collections["tracks"])

def get_recommendation_service() -> RecommendationService:
    return RecommendationService(collection=collections["recommendations"])

def get_playlist_service() -> PlaylistService:
    return PlaylistService(
        collection=collections["playlists"],
        users_collection=collections["users"],
        tracks_collection=collections["tracks"],
    )

def get_auth_service() -> AuthService:
    return AuthService()