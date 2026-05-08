from pydantic import BaseModel, Field, BeforeValidator
from typing import Annotated, Optional, Literal
from datetime import datetime

PyObjectId = Annotated[str, BeforeValidator(str)]

class AcousticRangeFilter(BaseModel):
    """Rango min/max para un parámetro acústico."""
    min: float = Field(ge=0.0, le=1.0)
    max: float = Field(ge=0.0, le=1.0)

class TempoRangeFilter(BaseModel):
    min: float = Field(ge=0.0)
    max: float = Field(ge=0.0)

class QueryParams(BaseModel):
    energy:       Optional[AcousticRangeFilter] = None
    danceability: Optional[AcousticRangeFilter] = None
    valence:      Optional[AcousticRangeFilter] = None
    tempo:        Optional[TempoRangeFilter] = None
    genre:        Optional[list[str]] = None

class RecommendedTrack(BaseModel):
    track_id:      PyObjectId
    score:         float = Field(ge=0.0, le=1.0)
    rank:          int   = Field(ge=1)
    user_feedback: Optional[Literal["like", "dislike", "skip"]] = None
    feedback_at:   Optional[datetime] = None

class SessionContext(BaseModel):
    mood:        Optional[str] = None
    activity:    Optional[str] = None
    time_of_day: Optional[str] = None

class Recommendation(BaseModel):
    id:              Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id:         PyObjectId
    generated_at:    datetime = Field(default_factory=datetime.now)
    query_params:    QueryParams
    tracks:          list[RecommendedTrack] = Field(default_factory=list)
    total_results:   int = Field(ge=0)
    session_context: Optional[SessionContext] = None