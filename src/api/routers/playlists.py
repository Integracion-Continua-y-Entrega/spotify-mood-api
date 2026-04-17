from fastapi import APIRouter, Depends

from models.playlists_collection import PlaylistCollection
from dependencies import get_playlist_service
from services.playlist_service import PlaylistService

router = APIRouter(prefix="/api/v1")

@router.get(
        "/playlists",
        response_description="List all playlists",
        response_model=PlaylistCollection,
        response_model_by_alias=True
        )
async def get_recommendations(service: PlaylistService = Depends(get_playlist_service)):
    return await service.list_playlists()
