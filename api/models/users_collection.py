from models.user import UserModel
from pydantic import BaseModel
from typing import List

class UserCollection(BaseModel):
    """
    A container holding a list of `UserModel` instances"""

    users: List[UserModel]