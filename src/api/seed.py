import datetime
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# 1. Configuración de conexión dinámica
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI no está definida en el .env")

client = MongoClient(MONGO_URI)

# Seleccionar la base de datos 
db = client["music_recommendations"]

# 2. Esquemas de Validación (Industry Best Practice)
# Se ha agregado 'spotify_id' como campo REQUERIDO.
user_validator = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["spotify_id", "email", "created_at"], 
        "properties": {
            "spotify_id": {
                "bsonType": "string",
                "description": "ID único proporcionado por Spotify"
            },
            "username": {
                "bsonType": "string",
                "description": "Nombre de usuario interno o handle"
            },
            "display_name": {"bsonType": "string"},
            "email": {"bsonType": "string"},
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
            "spotify_refresh_token": {
                "bsonType": "string",
                "description": "Token necesario para el flujo de Discovery offline"
            },
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
            "genre": {"bsonType": "string"},
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

# 3. Creación de Colecciones
collections = db.list_collection_names()

if "users" not in collections:
    db.create_collection("users", validator=user_validator)
if "tracks" not in collections:
    db.create_collection("tracks", validator=track_validator)
if "recommendations" not in collections:
    db.create_collection("recommendations")
if "playlists" not in collections:
    db.create_collection("playlists")

# 4. Definición de Índices (Optimización de búsqueda)
# Crucial: El índice único en spotify_id para que el upsert sea O(1).
db.users.create_index("spotify_id", unique=True)
db.users.create_index("email", unique=True)
db.users.create_index("username", unique=True)

# Índices para algoritmos de recomendación
db.tracks.create_index([
    ("acoustic_features.energy", 1),
    ("acoustic_features.valence", 1),
    ("acoustic_features.danceability", 1)
])
db.tracks.create_index([("artist", 1), ("title", 1)])
db.tracks.create_index("genre")

# Índices de relación (Foreign Keys conceptuales)
db.recommendations.create_index([("user_id", 1), ("generated_at", -1)])
db.playlists.create_index([("user_id", 1), ("created_at", -1)])

# 5. Inserción de Usuario de Prueba Realista
# Ahora el usuario de prueba refleja los datos que enviará tu FastAPI.
try:
    db.users.delete_many({"username": "jfer_enriquez"}) # Limpiar antes de insertar
    db.users.insert_one({
        "spotify_id": "spotify_test_user_001",
        "username": "jfer_enriquez",
        "display_name": "Fernando Enríquez",
        "email": "fernando@example.com",
        "spotify_refresh_token": "dummy_refresh_token_for_testing",
        "created_at": datetime.datetime.now(datetime.timezone.utc),
        "updated_at": datetime.datetime.now(datetime.timezone.utc),
        "is_active": True
    })
    print("✅ Usuario de prueba insertado correctamente.")
except Exception as e:
    print(f"❌ Error al insertar usuario de prueba: {e}")

print("🚀 Base de datos music_recommendations inicializada y optimizada.")
client.close()