from pydantic import *
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
    """
    Container for user preferences.
    """
    favorite_generes: list[str]
    language: str
    acoustic_profile: AcousticProfile

class UserModel(BaseModel):
    """
    Container for a single user record.
    """

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    username: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    preferences: Optional[Preferences] = None
    is_active: bool = True

    model_config = ConfigDict(
        validate_assignment=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": "Jane Doe"
            }
        } 
    )
