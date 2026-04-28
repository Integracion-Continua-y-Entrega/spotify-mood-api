from db.connection import MongoDB, get_database
from services.playlist_service import PlaylistService
from services.recommendation_service import RecommendationService
from services.track_service import TrackService
from services.user_service import UserService 

db = get_database()
collections = MongoDB.get_collections(db=db)

def get_user_service() -> UserService:
    return UserService(collection=collections["users"])

def get_track_service() -> TrackService:
    return TrackService(collection=collections["tracks"])

def get_recommendation_service() -> RecommendationService:
    return RecommendationService(collection=collections["recommendations"])

def get_playlist_service() -> PlaylistService:
    return PlaylistService(collection=collections["playlists"])