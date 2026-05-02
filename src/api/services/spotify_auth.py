import base64
import httpx

from fastapi import HTTPException
from cryptography.fernet import Fernet


def _spotify_basic_header(client_id: str, client_secret: str) -> str:
    """Genera el header Basic Auth para Spotify (Confidential Client)."""
    raw = f"{client_id}:{client_secret}".encode()
    return base64.b64encode(raw).decode()


async def exchange_code_for_tokens(
    client: httpx.AsyncClient,
    code: str,
    verifier: str,
    redirect_uri: str,
    client_id: str,
    client_secret: str,
) -> dict:
    """Intercambia el código de autorización por access + refresh token."""
    try:
        res = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": verifier,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {_spotify_basic_header(client_id, client_secret)}",
            },
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail="Error de conexión con Spotify")

    if res.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Spotify Auth Error: {res.text}")

    return res.json()


async def fetch_spotify_profile(
    client: httpx.AsyncClient,
    access_token: str,
) -> dict:
    """Obtiene el perfil del usuario autenticado en Spotify."""
    res = await client.get(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if res.status_code != 200:
        raise HTTPException(status_code=502, detail="No se pudo obtener el perfil de Spotify")

    return res.json()


def encrypt_refresh_token(fernet: Fernet, refresh_token: str) -> str:
    """Cifra el refresh token antes de persistirlo."""
    try:
        return fernet.encrypt(refresh_token.encode()).decode()
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno de cifrado")

