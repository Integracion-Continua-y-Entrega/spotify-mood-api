from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.connection import get_database, MongoDB
from routers import recommendations, tracks, users, auth
import logging
from asyncio import create_task
from dependencies import get_track_service

description = """
🎶 **Spotify Mood API** ayuda a gestionar tus listas y descubrir música.

## Recursos
* **Users**: Gestión de perfiles y sincronización.
* **Playlists & Tracks**: Manipulación de contenido musical.
* **Recommendations**: Algoritmos basados en tus gustos.
* **Auth**: Flujo seguro con Spotify OAuth2 + JWT.
"""

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_database()
    app.state.users_collection = db.get_collection("users")

    create_task(_warm_cache())
    
    yield
    await MongoDB.close_connection()

# Configuración de FastAPI
app = FastAPI(
    title="Spotify Mood API",
    description=description,
    version="1.0.0",
    lifespan=lifespan,
    # 3. Agrupación por etiquetas
    openapi_tags=[
        {"name": "auth", "description": "Operaciones de login y tokens"},
        {"name": "users", "description": "Información de usuarios"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://0.0.0.0:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de routers con etiquetas
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(tracks.router, prefix="/api/v1/tracks", tags=["tracks"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["recommendations"])

async def _warm_cache():
    try:
        track_service = get_track_service()
        await track_service.list_tracks_raw()
    except Exception as e:
        logging.warning("Warm-up de caché falló: %s", e)

# app.include_router(playlists.router, prefix="/api/v1/playlists", tags=["playlists"])
