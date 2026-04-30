from models.user import UserModel
from pydantic import BaseModel

class UserCollection(BaseModel):
    """
    A container holding a list of `User` instances"""

    users: list[UserModel]