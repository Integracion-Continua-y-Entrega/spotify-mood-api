from models.tracks_collection import TrackCollection

class TrackService:
    def __init__(self, collection):
        self.tracks = collection

    async def list_tracks(self):
        try:
            return TrackCollection(
                tracks=await self.tracks.find().to_list(1000))
        except Exception as e:
            raise Exception(e)
