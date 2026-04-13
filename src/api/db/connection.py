import os
from pymongo import AsyncMongoClient
from pymongo.errors import ConnectionFailure

# TODO: 1. Reemplazar MongoClient por AsyncMongoClient
def get_database():
    """
    Retorna la instancia de la base de datos.
    Lee las credenciales exclusivamente desde variables de entorno.
    """
    mongo_uri = os.getenv("MONGO_URI")
    db_name   = os.getenv("MONGO_DB", "music_recommendations")

    if not mongo_uri:
        raise EnvironmentError("MONGO_URI no está definida en las variables de entorno.")

    client = AsyncMongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

    try:
        client.admin.command("ping")
        print("Conexión a MongoDB exitosa.")
    except ConnectionFailure as e:
        raise ConnectionFailure(f"No se pudo conectar a MongoDB: {e}")

    return client[db_name]


# Colecciones disponibles
def get_collections(db):
    return {
        "users":           db["users"],
        "tracks":          db["tracks"],
        "recommendations": db["recommendations"],
        "playlists":       db["playlists"],
    }