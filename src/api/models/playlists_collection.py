from models.playlist import Playlist
from pydantic import BaseModel

class PlaylistCollection(BaseModel):
    """
    A container holding a list of `Playlist` instances"""

    playlists: list[Playlist]