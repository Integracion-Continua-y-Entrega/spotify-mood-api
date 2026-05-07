from fastapi import *
from models.dtos.create_user_dto import CreateUserDTO
from models.user import UserModel
from services.user_service import UserService
from models.users_collection import UserCollection
from dependencies import get_current_user, get_user_service
from dependencies import get_track_service


router = APIRouter()

@router.get(
        "",
        response_description="List all users",
        response_model=UserCollection,
        response_model_by_alias=False,
        )
async def get_users(service: UserService = Depends(get_user_service), user_id: str = Depends(get_current_user)
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
