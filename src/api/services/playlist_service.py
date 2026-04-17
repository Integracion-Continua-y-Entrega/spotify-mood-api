from models.playlists_collection import PlaylistCollection

class PlaylistService:
    def __init__(self, collection):
        self.playlists = collection

    async def list_playlists(self):
        try:
            return PlaylistCollection(
                playlists=await self.playlists.find().to_list(1000))
        except Exception as e:
            raise Exception(e)
