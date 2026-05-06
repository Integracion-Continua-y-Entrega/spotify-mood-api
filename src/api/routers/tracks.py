from fastapi import APIRouter, Depends

from dependencies import get_track_service
from models.tracks_collection import TrackCollection
from services.track_service import TrackService

router = APIRouter()

@router.get(
        "",
        response_description="List all tracks",
        response_model=TrackCollection,
        response_model_by_alias=True,
        )
async def get_tracks(service: TrackService = Depends(get_track_service)):
    return await service.list_tracks()

