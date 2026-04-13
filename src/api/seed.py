import datetime

from pymongo import MongoClient
import os

client = MongoClient(host="mongodb")

# Seleccionar la base de datos 
db = client["music_recommendations"]

# Crear usuario de aplicación
# Nota: Esto requiere permisos de 'userAdmin' en la conexión actual
# try:
#     db.command("createUser", "api_user",
#                pwd=os.getenv("MONGO_PASSWORD", "changeme"),
#                roles=[{"role": "readWrite", "db": "music_recommendations"}])
# except Exception as e:
#     print(f"Nota: El usuario ya existe o error de permisos: {e}")

# Definición de Esquemas de Validación ---

user_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["username", "email", "password_hash", "created_at"],
        "properties": {
            "username": {"bsonType": "string"},
            "email": {"bsonType": "string"},
            "password_hash": {"bsonType": "string"},
            "created_at": {"bsonType": "date"},
            "is_active": {"bsonType": "bool"}
        }
    }
}

track_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["title", "artist", "acoustic_features"],
        "properties": {
            "title": {"bsonType": "string"},
            "artist": {"bsonType": "string"},
            "acoustic_features": {
                "bsonType": "object",
                "required": ["energy", "danceability", "valence", "tempo"],
                "properties": {
                    "energy": {"bsonType": "double", "minimum": 0, "maximum": 1},
                    "danceability": {"bsonType": "double", "minimum": 0, "maximum": 1},
                    "valence": {"bsonType": "double", "minimum": 0, "maximum": 1},
                    "tempo": {"bsonType": "double", "minimum": 0}
                }
            }
        }
    }
}

collections = db.list_collection_names()

if "users" not in collections:
    db.create_collection("users", validator=user_validator)

if "tracks" not in collections:
    db.create_collection("tracks", validator=track_validator)

if "recommendations" not in collections:
    db.create_collection("recommendations")

if "playlists" not in collections:
    db.create_collection("playlists")

# Índices de Usuarios
db.users.create_index("email", unique=True)
db.users.create_index("username", unique=True)

# Índices de Tracks
db.tracks.create_index("acoustic_features.energy")
db.tracks.create_index("acoustic_features.danceability")
db.tracks.create_index("acoustic_features.valence")
db.tracks.create_index("acoustic_features.tempo")
db.tracks.create_index("genre")
db.tracks.create_index([("artist", 1), ("title", 1)])

# Índice compuesto para recomendaciones
db.tracks.create_index([
    ("acoustic_features.energy", 1),
    ("acoustic_features.valence", 1),
    ("acoustic_features.danceability", 1)
])

# Índices de Relación
db.recommendations.create_index([("user_id", 1), ("generated_at", -1)])
db.playlists.create_index([("user_id", 1), ("created_at", -1)])

# Inserción datos de prueba
db.users.insert_many([
    {
        "username": "jfer_enriquez",
        "email": "fernando@example.com",
        "password_hash": "hash_seguro_aqui",
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now(),
        "is_active": True
    }
])

print("✅ Base de datos music_recommendations inicializada correctamente.")

client.close()