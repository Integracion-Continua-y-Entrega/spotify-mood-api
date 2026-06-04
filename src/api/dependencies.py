import os
from jose import jwt  # 🧠 CORREGIDO: Usar python-jose de forma consistente con auth_service
from jose.exceptions import JWTError 
import httpx 

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
    """Valida el JWT de la sesión y devuelve el spotify_id del usuario."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=["HS256"])
        spotify_id: str = payload.get("sub")
        if not spotify_id:
            raise HTTPException(status_code=401, detail="Token inválido")
        return spotify_id
    except JWTError:  # 🧠 CORREGIDO: Captura la excepción correspondiente de python-jose
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado o inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =====================================================================
# 📂 INYECTORES DE SERVICIOS
# =====================================================================

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


# =====================================================================
# ⚡ DEPENDENCIAS PARA HIDRATACIÓN DE PREVIEWS EN TIEMPO REAL
# =====================================================================

async def get_httpx_client():
    """Provee una instancia única y asíncrona de httpx para llamadas externas."""
    async with httpx.AsyncClient() as client:
        yield client

async def get_user_spotify_token(
    spotify_user_id: str = Depends(get_current_user)
) -> str:
    """
    Recupera el access_token real de Spotify directamente desde el documento raw de MongoDB.
    Bypassea filtros de Pydantic evitando errores de campos no mapeados.
    """
    user_doc = await collections["users"].find_one({"spotify_id": spotify_user_id})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuario no encontrado en el sistema"
        )
        
    # Busca dinámicamente bajo cualquier variante de nombre de propiedad guardada
    access_token = user_doc.get("spotify_access_token") or user_doc.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="El usuario no cuenta con un token activo de Spotify"
        )
        
    return access_token