from pymongo import MongoClient
import os

client = MongoClient(
    host="mongodb")

db = client["myNewDatabase"]

db.users.insert_many(
    [{
        "name": "José Fernando Enríquez Maldonado"
    }]
)

client.close()