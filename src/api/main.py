import os
import base64
import httpx
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from jose import jwt
from cryptography.fernet import Fernet
from fastapi.middleware.cors import CORSMiddleware
from db.connection import get_database, MongoDB

# 1. Cargar variables de entorno
load_dotenv()


def _require_env(key: str) -> str:
    """Valida que las variables de entorno existan al arrancar."""
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"❌ Error Crítico: Variable de entorno requerida no encontrada: {key}")
    return value

# Configuración validada (Fail-fast)
SECRET_KEY            = _require_env("JWT_SECRET_KEY")
SPOTIFY_CLIENT_ID     = _require_env("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = _require_env("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI  = _require_env("SPOTIFY_REDIRECT_URI")
ENCRYPTION_KEY        = _require_env("TOKEN_ENCRYPTION_KEY")

fernet = Fernet(ENCRYPTION_KEY)

# 2. Manejo del ciclo de vida (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Iniciando servidor y conectando a MongoDB...")
    db = get_database()
    app.state.users_collection = db.get_collection("users")
    yield
    # ✅ Cerramos la conexión al apagar el servidor
    await MongoDB.close_connection()

app = FastAPI(lifespan=lifespan)

origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Modelos y Utilidades
class LoginPayload(BaseModel):
    code: str
    verifier: str

def _get_spotify_auth_header() -> str:
    """Genera el header de Basic Auth para Confidential Client."""
    raw = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}".encode()
    return base64.b64encode(raw).decode()

# 4. Endpoints
@app.post("/api/v1/auth/login")
async def spotify_login(request: Request, payload: LoginPayload):
    print(f"--- 🟢 Iniciando Login para el código: {payload.code[:10]}... ---")
    
    async with httpx.AsyncClient() as client:
        # A. Intercambio de código
        print("DEBUG: Enviando código a Spotify...")
        try:
            token_res = await client.post(
                "https://accounts.spotify.com/api/token", # <-- OJO: Verifica esta URL, en tu código decía googleusercontent
                data={
                    "grant_type": "authorization_code",
                    "code": payload.code,
                    "redirect_uri": SPOTIFY_REDIRECT_URI,
                    "code_verifier": payload.verifier,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {_get_spotify_auth_header()}",
                },
            )
            print(f"DEBUG: Status Spotify Token: {token_res.status_code}")
        except Exception as e:
            print(f"❌ Error en la petición HTTP a Spotify: {e}")
            raise HTTPException(status_code=500, detail="Error de conexión con Spotify")

        if token_res.status_code != 200:
            print(f"❌ Error de Spotify (Token): {token_res.text}")
            raise HTTPException(
                status_code=400, 
                detail=f"Spotify Auth Error: {token_res.text}"
            )

        tokens = token_res.json()
        print("✅ Tokens obtenidos con éxito")

        # B. Obtener perfil
        print("DEBUG: Obteniendo perfil de usuario...")
        user_res = await client.get(
            "https://api.spotify.com/v1/me", # <-- OJO: Verifica esta URL
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        
        if user_res.status_code != 200:
            print(f"❌ Error de Spotify (User Profile): {user_res.text}")
            raise HTTPException(status_code=502, detail="No se pudo obtener el perfil de Spotify")

        spotify_user = user_res.json()
        print(f"✅ Usuario identificado: {spotify_user.get('id')}")

        # C. Cifrado
        try:
            encrypted_refresh = fernet.encrypt(
                tokens["refresh_token"].encode()
            ).decode()
            print("✅ Refresh Token cifrado")
        except Exception as e:
            print(f"❌ Error al cifrar token: {e}")
            raise HTTPException(status_code=500, detail="Error interno de cifrado")

        # D. Upsert consistente usando app.state
        print("DEBUG: Intentando Upsert en MongoDB...")
        try:
            now = datetime.now(timezone.utc)
            
            await request.app.state.users_collection.update_one(
                {"spotify_id": spotify_user["id"]},
                {
                    # Campos que se actualizan SIEMPRE en cada login
                    "$set": {
                        "display_name": spotify_user.get("display_name"),
                        "email": spotify_user.get("email"),
                        "profile_image": spotify_user["images"][0]["url"] if spotify_user.get("images") else None,
                        "spotify_refresh_token": encrypted_refresh,
                        "last_login": now
                    },
                    # Campos que SOLO se guardan la primera vez (cuando se crea el doc)
                    "$setOnInsert": {
                        "spotify_id": spotify_user["id"], # También es buena práctica ponerlo aquí
                        "created_at": now
                    }
                },
                upsert=True,
            )
            print("✅ Base de Datos actualizada (con created_at)")
        except Exception as e:
            print(f"❌ Error en MongoDB: {e}")
            raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")

        # E. JWT
        print("DEBUG: Generando JWT final...")

        ACCESS_TOKEN_EXPIRE_HOURS = 8  # 👈 AÑADE esta constante arriba del return

        session_token = jwt.encode(
            {
                "sub": spotify_user["id"],
                "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),  # 👈 usa la constante
                "iat": datetime.now(timezone.utc)
            },
            SECRET_KEY,
            algorithm="HS256",
        )

        print("--- 🏁 Login completado con éxito ---")
        return {
            "access_token": session_token, 
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_HOURS * 3600,  # 👈 AÑADE ESTA LÍNEA (= 28800 segundos)
            "user": {
                "name": spotify_user.get("display_name"),
                "id": spotify_user["id"]
            }
        }