import base64
import httpx

from fastapi import HTTPException
from cryptography.fernet import Fernet

SPOTIFY_ME_URL = "https://api.spotify.com/v1/me"

import logging

logger = logging.getLogger(__name__)

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
    logger.info("Fetching Spotify user profile...")

    try:
        res = await client.get(
            SPOTIFY_ME_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )

        res.raise_for_status()

    except httpx.HTTPStatusError as e:
        status = e.response.status_code

        try:
            res_json = e.response.json()
        except ValueError:
            res_json = {"raw": e.response.text}

        message = None
        if isinstance(res_json, dict):
            message = res_json.get("error", {}).get("message")

        logger.warning(f"Spotify Profile Error | status={status} | message={message or e.response.text}")

        if status == 401:
            raise HTTPException(status_code=401, detail=message or "Token inválido o expirado")
        elif status == 429:
            raise HTTPException(status_code=429, detail=message or "Rate limit excedido")
        elif 500 <= status < 600:
            raise HTTPException(status_code=502, detail=message or "Error en Spotify")
        else:
            raise HTTPException(
                status_code=400,
                detail=message or f"Error inesperado ({status})"
            )

    logger.info(f"Spotify profile fetched successfully | status={res.status_code}")
    return res.json()

async def fetch_user_top_tracks(client: httpx.AsyncClient, access_token: str) -> list[dict]:
    time_ranges = ["short_term", "medium_term", "long_term"]
    seen_ids = set()
    all_tracks = []

    for time_range in time_ranges:
        url = f"https://api.spotify.com/v1/me/top/tracks?limit=50&time_range={time_range}"
        logger.info(f"Fetching top tracks [{time_range}]...")

        try:
            res = await client.get(url, headers={"Authorization": f"Bearer {access_token}"})
        except httpx.RequestError as e:
            logger.error(f"Connection error with Spotify: {e}")
            raise HTTPException(status_code=500, detail="Error de conexión con Spotify")

        if res.status_code != 200:
            logger.warning(f"Spotify Error | status={res.status_code} | body={res.text}")
            raise HTTPException(status_code=400, detail=f"Spotify Error: {res.text}")

        tracks = res.json().get("items", [])

        # Deduplicar por spotify id
        for track in tracks:
            if track["id"] not in seen_ids:
                seen_ids.add(track["id"])
                all_tracks.append(track)

    logger.info(f"Total top tracks únicos: {len(all_tracks)}")
    return all_tracks


def encrypt_refresh_token(fernet: Fernet, refresh_token: str) -> str:
    """Cifra el refresh token antes de persistirlo."""
    try:
        return fernet.encrypt(refresh_token.encode()).decode()
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno de cifrado")

async def fetch_preview_urls_map(
    client: httpx.AsyncClient,
    spotify_ids: list[str],
    access_token: str
) -> dict[str, str | None]:
    """
    Consulta la API de Spotify para obtener los preview_url de una lista de hasta 50 IDs.
    Devuelve un diccionario mapeado: {spotify_id: preview_url}
    """
    if not spotify_ids:
        return {}

    # Spotify permite un máximo de 50 IDs por petición
    ids_param = ",".join(spotify_ids[:50])
    
    # NOTA: Si tu entorno de pruebas requiere URLs especiales de googleusercontent, 
    # cambia esta URL por: f"https://api.spotify.com/v1/tracks?ids={ids_param}"
    url = f"https://api.spotify.com/v1/tracks?ids={ids_param}"

    try:
        res = await client.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5.0,
        )
        
        if res.status_code == 200:
            tracks_data = res.json().get("tracks", [])
            # Creamos el mapa filtrando que el track no venga nulo
            return {t["id"]: t.get("preview_url") for t in tracks_data if t}
        else:
            logger.warning(f"No se pudieron enriquecer los previews. Spotify status: {res.status_code}")
            
    except Exception as e:
        logger.error(f"Error de conexión al obtener previews de Spotify: {e}")

    return {}
