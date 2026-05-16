from fastapi import APIRouter, Depends, Body
from models.dtos.create_user_dto import CreateUserDTO
from models.user import UserModel
from models.users_collection import UserCollection
from models.playlists_collection import PlaylistCollection
from models.playlist import Playlist
from services.user_service import UserService
from services.playlist_service import PlaylistService
from dependencies import get_current_user, get_user_service, get_playlist_service

router = APIRouter()

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
    response_description="Create a new playlist in the user's Spotify account",
    response_model=Playlist,
    status_code=201,
)
async def create_my_playlist(
    name: str = Body(..., embed=True),
    description: str = Body("", embed=True),
    public: bool = Body(False, embed=True),
    access_token: str = Body(..., embed=True, description="Spotify access token del usuario"),
    playlist_service: PlaylistService = Depends(get_playlist_service),
    user_id: str = Depends(get_current_user),
):
    return await playlist_service.create_spotify_playlist(
        spotify_id=user_id,
        access_token=access_token,
        name=name,
        description=description,
        public=public,
    )