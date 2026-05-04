from models.track import Track
from models.tracks_collection import TrackCollection
from motor.motor_asyncio import AsyncIOMotorCollection

class TrackService:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.tracks = collection

    async def list_tracks(self):
        try:
            return TrackCollection(
                tracks=await self.tracks.find().to_list(50))
        except Exception as e:
            raise Exception(e)
        
    async def find_by_spotify_id(self, spotify_id: str) -> Track | None:
        doc = await self.tracks.find_one({"external_ids.spotify_id": spotify_id})
        if doc is None:
            return None
        return Track.model_validate(doc)

