from models.track import Track
from pydantic import BaseModel

class TrackCollection(BaseModel):
    """
    A container holding a list of `Track` instances"""

    tracks: list[Track]