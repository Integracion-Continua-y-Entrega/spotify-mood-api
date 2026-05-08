from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from models.track import Track
from dependencies import get_track_service
from models.tracks_collection import TrackCollection
from services.track_service import TrackService

router = APIRouter()

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
):
    if len(body.ids) > MAX_BULK:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Maximum {MAX_BULK} IDs per request",
        )
    return await service.find_by_ids(body.ids)


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
