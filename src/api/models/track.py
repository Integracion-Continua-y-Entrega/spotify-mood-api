from pydantic import BaseModel, Field, BeforeValidator
from typing import Annotated, Optional
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]

class ExternalIds(BaseModel):
    spotify_id: str
    isrc: Optional[str] = None

class AcousticFeatures(BaseModel):
    energy: float = Field(ge=0.0, le=1.0)
    danceability: float = Field(ge=0.0, le=1.0)
    valence: float = Field(ge=0.0, le=1.0)
    acousticness: float = Field(ge=0.0, le=1.0)
    instrumentalness: float = Field(ge=0.0, le=1.0)
    liveness: float = Field(ge=0.0, le=1.0)
    speechiness: float = Field(ge=0.0, le=1.0)
    loudness: float
    tempo: float
    key: int = Field(ge=0, le=11)
    mode: int = Field(ge=0, le=1)
    time_signature: Optional[int] = None

class Track(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    title: str
    artist: str
    album: str
    release_year: Optional[int] = None
    duration_ms: int
    genre: Optional[list[str]] = None
    language: Optional[str] = None
    external_ids: ExternalIds
    acoustic_features: AcousticFeatures
    preview_url: Optional[str] = None
    added_at: Optional[datetime] = None

    model_config = {"populate_by_name": True}