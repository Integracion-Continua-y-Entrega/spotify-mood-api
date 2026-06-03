from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from models.dtos.create_user_dto import CreateUserDTO
from models.user import UserModel
from models.users_collection import UserCollection
from models.playlists_collection import PlaylistCollection
from models.playlist import Playlist
from services.user_service import UserService
from services.playlist_service import PlaylistService
from dependencies import get_current_user, get_user_service, get_playlist_service

router = APIRouter()


class CreatePlaylistRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    track_ids: list[str] = Field(
        ...,
        min_length=10,
        max_length=10,
        description="IDs de MongoDB de las canciones recomendadas",
    )
    description: str = Field(default="", max_length=500)
    public: bool = False

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Happy Mood",
                "description": "Playlist generada desde recomendaciones Happy",
                "public": False,
                "track_ids": [
                    "69f89955736605d266657297",
                    "69f8994f736605d266655a24",
                    "69f8994f736605d26665607e",
                    "69f89955736605d266657c95",
                    "69f89955736605d2666573fc",
                    "69f8994f736605d266655f34",
                    "69f89955736605d26665745c",
                    "69f89955736605d266657328",
                    "69f89955736605d266657510",
                    "69f8994f736605d266656c7d",
                ],
            }
        }
    }

@router.get(
    "",
    response_description="List all users",
    response_model=UserCollection,
    response_model_by_alias=False,
)
async def get_users(
    service: UserService = Depends(get_user_service),
    user_id: str = Depends(get_current_user)
):
    return await service.list_users()


@router.get(
    "/me",
    response_model=UserModel,
    response_model_by_alias=True
)
async def get_me(
    user_service: UserService = Depends(get_user_service),
    user_id: str = Depends(get_current_user)
):
    return await user_service.find_by_spotify_id(user_id)


@router.get(
    "/me/playlists",
    response_description="List playlists of the authenticated user",
    response_model=PlaylistCollection,
)
async def get_my_playlists(
    playlist_service: PlaylistService = Depends(get_playlist_service),
    user_id: str = Depends(get_current_user),
):
    """Recupera todas las playlists del usuario autenticado."""
    return await playlist_service.list_user_playlists(user_id)


@router.post(
    "/me/playlists",
    response_description="Create a new playlist with recommended tracks",
    response_model=Playlist,
    status_code=201,
)
async def create_my_playlist(
    body: CreatePlaylistRequest,
    playlist_service: PlaylistService = Depends(get_playlist_service),
    user_id: str = Depends(get_current_user),
):
    """Crea una playlist en Spotify con las canciones recomendadas y la persiste en MongoDB."""
    return await playlist_service.create_spotify_playlist(
        spotify_id=user_id,
        name=body.name,
        track_ids=body.track_ids,
        description=body.description,
        public=body.public,
    )
