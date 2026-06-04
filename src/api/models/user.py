from pydantic import BaseModel, Field, ConfigDict, BeforeValidator
from typing import Optional, Annotated
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]


class AcousticParamRange(BaseModel):
    min: float
    max: float

class AcousticParam(AcousticParamRange):
    target: float

class AcousticProfile(BaseModel):
    energy: AcousticParam
    danceability: AcousticParam
    valence: AcousticParam
    acousticness: AcousticParam
    instrumentalness: AcousticParam
    tempo_range: AcousticParamRange


class Preferences(BaseModel):
    favorite_genres: Optional[list[str]] = None
    language: Optional[str] = None
    acoustic_profile: AcousticProfile


class UserModel(BaseModel):
    """
    Representa un usuario autenticado vía Spotify en MongoDB.
    """
    id: Optional[PyObjectId] = Field(default=None, alias="_id")

    spotify_id: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    profile_image: Optional[str] = None

    spotify_refresh_token: str = Field(exclude=True)

    created_at: datetime
    last_login: Optional[datetime] = None 

    preferences: Optional[Preferences] = None
    is_active: bool = True

    model_config = ConfigDict(
        validate_assignment=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "spotify_id": "31xyzabc123",
                "display_name": "Jane Doe",
                "email": "jane@example.com",
                "profile_image": "https://i.scdn.co/image/abc123",
                "created_at": "2024-01-15T10:30:00Z",
                "last_login": "2024-06-01T08:00:00Z",
                "preferences": None
            }
        }
    )