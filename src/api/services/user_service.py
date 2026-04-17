from models.dtos.create_user_dto import CreateUserDTO
from models.user import UserModel
from models.users_collection import UserCollection

class UserService:
    def __init__(self, collection):
        self.users = collection

    async def list_users(self):
        try:
            return UserCollection(
                users=await self.users.find().to_list(1000))
        except Exception as e:
            raise Exception(e)
        
    async def create_user(self, dto: CreateUserDTO) -> UserModel:
        try:
            user = UserModel(
                username=dto.username,
                email=dto.email,
                password_hash=dto.password,
            )

            result = await self.users.insert_one(user.model_dump(by_alias=True, exclude_none=True))
            user.id = result.inserted_id

            return user
        except Exception as e:
            raise Exception(e)

