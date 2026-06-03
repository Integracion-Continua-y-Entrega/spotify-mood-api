import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
import logging

from models.track import Track
from dependencies import get_track_service, get_httpx_client, get_user_spotify_token  
from models.tracks_collection import TrackCollection
from services.track_service import TrackService

router = APIRouter()
logger = logging.getLogger(__name__)

MAX_BULK = 100 

class BulkRequest(BaseModel):
    ids: list[str]
    model_config = {"json_schema_extra": {"example": {"ids": ["664f...", "664f..."]}}}


@router.get(
    "/{track_id}",
    response_description="Find a track by its ID",
    response_model=Track,
    response_model_by_alias=True
)
async def get_track_by_id(
    track_id: str,
    service: TrackService = Depends(get_track_service),
):
    track = await service.find_by_id(track_id)
    if not track:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track '{track_id}' not found",
        )
    return track


@router.post(
    "/bulk",
    response_description="Find multiple tracks by their IDs",
    response_model=TrackCollection,
    response_model_by_alias=True,
)
async def get_tracks_bulk(
    body: BulkRequest,
    service: TrackService = Depends(get_track_service),
    http_client: httpx.AsyncClient = Depends(get_httpx_client),
    spotify_token: str = Depends(get_user_spotify_token)  
):
    if len(body.ids) > MAX_BULK:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Maximum {MAX_BULK} IDs per request",
        )
        
    try:
        # 1. Consultar a MongoDB los metadatos estáticos
        track_collection = await service.find_by_ids(body.ids)
        
        # 2. Extraer los spotify_ids de las canciones encontradas en lote
        spotify_ids = [
            track.external_ids.spotify_id 
            for track in track_collection.tracks 
            if track.external_ids and track.external_ids.spotify_id
        ]
        
        if not spotify_ids:
            return track_collection

        # 3. Consultar los previews a la API externa
        ids_param = ",".join(spotify_ids[:50])
        url = f"https://api.spotify.com/v1/tracks?ids={ids_param}"
        
        res = await http_client.get(
            url,
            headers={"Authorization": f"Bearer {spotify_token}"},  
            timeout=6.0
        )
        
        # 4. ⚡ SISTEMA DEFENSIVO ANTI-BLOQUEO
        if res.status_code == 200:
            tracks_data = res.json().get("tracks", [])
            previews_map = {t["id"]: t.get("preview_url") for t in tracks_data if t}
        else:
            # Si el servidor simulado da 403 Forbidden o falla, inyectamos una muestra de audio libre
            # para que el frontend cobre vida y puedas probar tus componentes sin limitaciones.
            logger.warning(f"Simulador de Spotify retornó {res.status_code}. Aplicando audio de respaldo.")
            previews_map = {
                sid: "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
                for sid in spotify_ids
            }
            
        # 5. Hidratar las propiedades en caliente antes de enviar la respuesta
        for track in track_collection.tracks:
            if track.external_ids and track.external_ids.spotify_id:
                track.preview_url = previews_map.get(track.external_ids.spotify_id)
                    
        return track_collection
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el servidor al hidratar los previews de audio: {str(e)}"
        )


@router.get(
    "",
    response_description="List all tracks with pagination",
    response_model=TrackCollection,
    response_model_by_alias=True,
)
async def get_tracks(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    service: TrackService = Depends(get_track_service),
):
    return await service.list_tracks(page=page, limit=limit)