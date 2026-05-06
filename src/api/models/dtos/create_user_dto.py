from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from models.user import Preferences

class CreateUserDTO(BaseModel):
    """
    Payload para crear un nuevo usuario.
    """
    username: str
    email: str
    password: str
    preferences: Optional[Preferences] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "janedoe",  
                "email": "jane@example.com",
                "password": "supersecret123",
                "preferences": None
            }
        }
    )