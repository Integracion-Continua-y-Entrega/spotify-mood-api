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
        
        
    async def create_playlist(self, user_id: str, playlist_data: dict):
        """
        Crea una nueva playlist en Spotify (Implementación pendiente).
        """
        # Por ahora solo devolvemos un diccionario simulado para que el test y el router funcionen
        return {
            "id": "new_playlist_999",
            "name": playlist_data.get("name", "Nueva Playlist"),
            "url": "https://open.spotify.com/playlist/new_playlist_999"
        }
