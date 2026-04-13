from fastapi import FastAPI
from models.users_collection import UserCollection
from models.tracks_collection import TrackCollection
from models.recommendations_collection import RecommendationCollection
from models.playlists_collection import PlaylistCollection
from db.connection import get_database, get_collections

app = FastAPI()
db = get_database()

@app.get("/api/v1/health")
async def get_api_health():
    return {"status": "ok"}

@app.get(
        "/api/v1/users",
        response_description="List all users",
        response_model=UserCollection,
        response_model_by_alias=False
        )
async def get_users():
    try:
        users = db.get_collection("users")

        return UserCollection(
            users=await users.find().to_list(1000))
    except Exception as e:
        raise Exception(e)
    
@app.get(
        "/api/v1/tracks",
        response_description="List all tracks",
        response_model=TrackCollection,
        response_model_by_alias=False)
async def get_tracks():
    try:
        tracks = db.get_collection("tracks")

        return TrackCollection(
            tracks=await tracks.find().to_list(1000))
    except Exception as e:
        raise Exception(e)
    
@app.get(
        "/api/v1/recommendations",
        response_description="List all recommendations",
        response_model=RecommendationCollection,
        response_model_by_alias=False
        )
async def get_recommendations():
    try:
        recommendations = db.get_collection("recommendations")

        return RecommendationCollection(
            recommendations=await recommendations.find().to_list(1000))
    except Exception as e:
        raise Exception(e)

@app.get(
        "/api/v1/playlists",
        response_description="List all playlists",
        response_model=PlaylistCollection,
        response_model_by_alias=False)
async def get_playlists():
    try:
        playlists = db.get_collection("playlists")

        return PlaylistCollection(
            playlists=await playlists.find().to_list(1000))
    except Exception as e:
        raise Exception(e)

