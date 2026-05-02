from fastapi import *
from models.dtos.create_user_dto import CreateUserDTO
from models.user import UserModel
from services.user_service import UserService
from models.users_collection import UserCollection
from dependencies import get_user_service

router = APIRouter()

@router.get(
        "/users",
        response_description="List all users",
        response_model=UserCollection,
        response_model_by_alias=False
        )
async def get_users(service: UserService = Depends(get_user_service)):
    return await service.list_users()

@router.post("/users", 
             response_description="Create a user",
             response_model=UserModel,
             response_model_by_alias=False)
async def create_user(dto: CreateUserDTO, service: UserService = Depends(get_user_service)):
    return await service.create_user(dto)
