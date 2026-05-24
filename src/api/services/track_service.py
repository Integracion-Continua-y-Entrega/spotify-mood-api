from bson import ObjectId
from bson.errors import InvalidId

from models.track import Track
from models.tracks_collection import TrackCollection
from motor.motor_asyncio import AsyncIOMotorCollection

class TrackService:
    def __init__(self, collection: AsyncIOMotorCollection):
        self.tracks = collection

    # Obtener tracks con paginación
    async def list_tracks(self, page: int = 1, limit: int = 50) -> TrackCollection:
        skip = (page - 1) * limit
        cursor = self.tracks.find().skip(skip).limit(limit)
        return TrackCollection(tracks=await cursor.to_list(limit))
    
    async def list_tracks_raw(self, page: int = 1, limit: int = 50) -> list[dict]:
        skip = (page - 1) * limit

        cursor = self.tracks.find(
            {}, 
            {
                "_id": 1, 
                "acoustic_features": 1, 
                "external_ids.spotify_id": 1
            }
        ).skip(skip).limit(limit)
        
        return await cursor.to_list(limit)

    # Obtener total de tracks
    async def count(self) -> int:
        return await self.tracks.count_documents({})
        
    # Buscar un track por su identificador de Spotify
    async def find_by_spotify_id(self, spotify_id: str) -> Track | None:
        doc = await self.tracks.find_one({"external_ids.spotify_id": spotify_id})
        return Track.model_validate(doc) if doc else None
    
    async def find_by_genre(self, genre: str, limit: int = 50) -> TrackCollection:
        cursor = self.tracks.find({"genre": genre}).limit(limit)
        return TrackCollection(tracks=await cursor.to_list(limit))

    async def find_by_year(self, year: int, limit: int = 50) -> TrackCollection:
        cursor = self.tracks.find({"release_year": year}).limit(limit)
        return TrackCollection(tracks=await cursor.to_list(limit))
    
    async def create(self, track: Track) -> Track:
        result = await self.tracks.insert_one(track.model_dump(by_alias=True, exclude={"id"}))
        track.id = str(result.inserted_id)
        return track
    
    async def find_by_id(self, track_id: str) -> Track | None:
        try:
            oid = ObjectId(track_id)
        except InvalidId:
            return None
        doc = await self.tracks.find_one({"_id": oid})
        return Track.model_validate(doc) if doc else None

    async def find_by_ids(self, track_ids: list[str]) -> TrackCollection:
        oids = []
        for tid in track_ids:
            try:
                oids.append(ObjectId(tid))
            except InvalidId:
                pass 
        if not oids:
            return TrackCollection(tracks=[])
        cursor = self.tracks.find({"_id": {"$in": oids}})
        return TrackCollection(tracks=await cursor.to_list(len(oids)))

