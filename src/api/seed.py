import datetime
import os
from anyio import ConnectionFailed, Path
from pymongo import MongoClient
from dotenv import load_dotenv
import pandas as pd
import ast

from models.track import AcousticFeatures, ExternalIds, Track
import logging

load_dotenv()
logging.basicConfig(
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuración de conexión dinámica
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

if not MONGO_URI:
    raise ValueError("MONGO_URI no está definida en el .env")

client = MongoClient(MONGO_URI)
try:
    client.admin.command('ping')
    logger.info("¡Conexión exitosa!")
except Exception:
    logger.info("El servidor no está disponible.")

# Seleccionar la base de datos 
db = client.get_default_database()
base_path = Path(__file__).parent
file_path = base_path / "dataset.csv"

def load_tracks():
    try:
        df = pd.read_csv(
            file_path,
            dtype={'genre': str, 'year': pd.Int64Dtype(), 'release_date': str}, 
            low_memory=False
        )
    except FileNotFoundError as e:
        logging.error("Archivo dataset no encontrado")

    # Fix Pandas4Warning: 'str' en lugar de 'object'
    df[df.select_dtypes(include='str').columns] = df.select_dtypes(include='str').fillna("")
    df[df.select_dtypes(include='number').columns] = df.select_dtypes(include='number').fillna(0)

    tracks_collection = db.get_collection("tracks")

    try:
        def create_track_dict(row):
            artists_list = row['artists']
            main_artist = "Unknown Artist"

            if isinstance(artists_list, str) and artists_list:
                try:
                    parsed_list = ast.literal_eval(artists_list)
                    if isinstance(parsed_list, list) and len(parsed_list) > 0:
                        main_artist = parsed_list[0]
                    else:
                        main_artist = artists_list
                except (ValueError, SyntaxError):  # Fix SyntaxWarning: captura explícita
                    main_artist = artists_list
            elif isinstance(artists_list, list) and len(artists_list) > 0:
                main_artist = artists_list[0]

            track_obj = Track(
                title=row['name'],
                artist=main_artist,
                album=row['album'],
                duration_ms=row['duration_ms'],
                external_ids=ExternalIds(spotify_id=row['id']),
                acoustic_features=AcousticFeatures(
                    energy=row['energy'],
                    danceability=row['danceability'],
                    valence=row['valence'],
                    acousticness=row['acousticness'],
                    instrumentalness=row['instrumentalness'],
                    liveness=row['liveness'],
                    speechiness=row['speechiness'],
                    loudness=row['loudness'],
                    tempo=row['tempo'],
                    key=row['key'],
                    mode=row['mode'],
                    time_signature=row['time_signature']
                ),
                genre=[row['genre']],
                release_year=row['year'] if row['year'] != 0 else None
            )
            return track_obj.model_dump()

        tracks_data = df.apply(lambda row: create_track_dict(row), axis=1).tolist()

        if tracks_data:
            BATCH_SIZE = 5000
            LIMIT = 850000
            for i in range(0, LIMIT, BATCH_SIZE):
                batch = tracks_data[i:i + BATCH_SIZE]
                tracks_collection.insert_many(batch)
                logger.info(f"Insertados {min(i + BATCH_SIZE, len(tracks_data))}/{len(tracks_data)}")

    except Exception as e:
        logger.warning(e)

# Esquemas de Validación
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
            "genre": {
                "bsonType": "array",
                "description": "Debe ser una lista de strings",
                "items": {
                    "bsonType": "string"
                }
            },
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

# Creación de Colecciones
collections = db.list_collection_names()

if "users" not in collections:
    db.create_collection("users", validator=user_validator)
if "tracks" not in collections:
    db.create_collection("tracks", validator=track_validator)
if "recommendations" not in collections:
    db.create_collection("recommendations")
if "playlists" not in collections:
    db.create_collection("playlists")

# Definición de Índices (Optimización de búsqueda)
db.users.create_index("spotify_id", unique=True)
db.users.create_index("email", unique=True)
db.users.create_index("username", unique=True)

# Índices para algoritmos de recomendación
# db.tracks.create_index([
#     ("acoustic_features.energy", 1),
#     ("acoustic_features.valence", 1),
#     ("acoustic_features.danceability", 1)
# ])
# db.tracks.create_index([("artist", 1), ("title", 1)])
# db.tracks.create_index("genre")

# Índices de relación (Foreign Keys conceptuales)
db.recommendations.create_index([("user_id", 1), ("generated_at", -1)])
db.playlists.create_index([("user_id", 1), ("created_at", -1)])

# Inserción de Usuario de Prueba
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
    print("Usuario de prueba insertado correctamente.")
except Exception as e:
    print(f"Error al insertar usuario de prueba: {e}")

print("Base de datos music_recommendations inicializada y optimizada.")

load_tracks()
client.close()