# models/playlist.py
from pydantic import BaseModel, Field, BeforeValidator
from typing import Annotated, Optional
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]

class PlaylistTrack(BaseModel):
    track_id: PyObjectId
    added_at: datetime
    position: int = Field(ge=1)

class Playlist(BaseModel):
    id:                Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id:           PyObjectId
    name:              str   = Field(min_length=1, max_length=100)
    description:       Optional[str] = Field(default=None, max_length=500)
    is_generated:      bool  = False
    recommendation_id: Optional[PyObjectId] = None
    tracks:            list[PlaylistTrack] = Field(default_factory=list)
    created_at:        datetime
    updated_at:        datetime
    is_public:         bool  = False