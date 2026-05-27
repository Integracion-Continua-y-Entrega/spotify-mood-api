from fastapi import APIRouter, Depends

from models.playlists_collection import PlaylistCollection
from dependencies import get_playlist_service
from services.playlist_service import PlaylistService

router = APIRouter()

@router.get(
        "",
        response_description="List all playlists",
        response_model=PlaylistCollection,
        response_model_by_alias=True
        )
async def get_recommendations(service: PlaylistService = Depends(get_playlist_service)):
    return await service.list_playlists()


from fastapi import APIRouter, Depends, Body

# ... (tu código GET existente) ...

@router.post(
    "",
    response_description="Create a new playlist"
)
async def create_new_playlist(
    # Recibimos el body como un dict genérico por ahora
    playlist_data: dict = Body(...), 
    service: PlaylistService = Depends(get_playlist_service)
):
    # En producción aquí extraeríamos el ID del usuario real desde el token
    user_id_mock = "qa_user_123" 
    return await service.create_playlist(user_id_mock, playlist_data)

