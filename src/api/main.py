from fastapi import FastAPI
from pymongo import AsyncMongoClient
from models.users_collection import UserCollection
import os 

app = FastAPI()
client = AsyncMongoClient(host="mongodb")

@app.get("/api/v1/health")
async def get_api_health():
    return {"status": "ok"}

@app.get(
        "/api/v1/users",
        response_description="List all users",
        response_model=UserCollection,
        response_model_by_alias=False)
async def get_users():
    try:
        database = client.get_database("myNewDatabase")
        users = database.get_collection("users")

        return UserCollection(
            users=await users.find().to_list(1000))
    except Exception as e:
        raise Exception(e)