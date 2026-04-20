# Diseño del Esquema de Base de Datos — MongoDB
**Proyecto:** API de Recomendaciones Musicales  
**Equipo:** I.C.E  
**Rol:** Data / Docs — Carlos de Jesús Miranda Becerra  
**Hito:** Diseño del esquema de base de datos en MongoDB  
**Fecha de entrega:** 02/04/2026 | Release: R1  
**Repositorio:** https://github.com/Integracion-Continua-y-Entrega

---

## 1. Contexto y Decisiones de Diseño

La API genera recomendaciones musicales precisas basadas en **parámetros acústicos** y **preferencias del usuario**, con persistencia de selecciones para experiencia personalizada. Se eligió MongoDB como base de datos NoSQL por su flexibilidad de esquema y escalabilidad horizontal, adecuada para documentos de audio con atributos variables.

### Principios aplicados
- **Documentos embebidos** para datos que siempre se leen juntos (p. ej., parámetros acústicos dentro de una pista).
- **Referencias por `_id`** entre colecciones cuando los datos se consultan de forma independiente.
- **Índices** definidos desde el diseño para soportar las consultas de búsqueda y filtrado del hito 16/04/2026.
- **Variables de entorno** para credenciales de conexión (alineado con las observaciones del maestro sobre gestión de secretos en GitHub Actions).

---

## 2. Colecciones

### 2.1 `users`

Almacena los perfiles de usuario, sus credenciales y sus preferencias acústicas persistidas.

```json
{
  "_id": "ObjectId",
  "username": "string",
  "email": "string",
  "password_hash": "string",
  "created_at": "ISODate",
  "updated_at": "ISODate",
  "preferences": {
    "favorite_genres": ["string"],
    "language": "string",
    "acoustic_profile": {
      "energy":           { "min": 0.0, "max": 1.0, "target": 0.7 },
      "danceability":     { "min": 0.0, "max": 1.0, "target": 0.6 },
      "valence":          { "min": 0.0, "max": 1.0, "target": 0.5 },
      "acousticness":     { "min": 0.0, "max": 1.0, "target": 0.3 },
      "instrumentalness": { "min": 0.0, "max": 1.0, "target": 0.1 },
      "tempo_range":      { "min": 60,  "max": 180 }
    }
  },
  "is_active": "boolean"
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `_id` | ObjectId | Identificador único generado por MongoDB |
| `username` | String | Nombre de usuario, único |
| `email` | String | Correo electrónico, único |
| `password_hash` | String | Hash bcrypt de la contraseña |
| `created_at` | Date | Fecha de registro |
| `updated_at` | Date | Última actualización del perfil |
| `preferences.favorite_genres` | Array[String] | Géneros musicales favoritos |
| `preferences.acoustic_profile` | Object | Rangos y objetivos acústicos del usuario |
| `is_active` | Boolean | Estado de la cuenta |

**Índices:**
```js
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "username": 1 }, { unique: true })
```

---

### 2.2 `tracks`

Almacena la información de cada pista musical junto con sus parámetros acústicos. Es la colección central para el motor de recomendaciones.

```json
{
  "_id": "ObjectId",
  "title": "string",
  "artist": "string",
  "album": "string",
  "release_year": "integer",
  "duration_ms": "integer",
  "genre": ["string"],
  "language": "string",
  "external_ids": {
    "spotify_id": "string",
    "isrc": "string"
  },
  "acoustic_features": {
    "energy":           "float [0.0–1.0]",
    "danceability":     "float [0.0–1.0]",
    "valence":          "float [0.0–1.0]",
    "acousticness":     "float [0.0–1.0]",
    "instrumentalness": "float [0.0–1.0]",
    "liveness":         "float [0.0–1.0]",
    "speechiness":      "float [0.0–1.0]",
    "loudness":         "float [dB, típico: -60 a 0]",
    "tempo":            "float [BPM]",
    "key":              "integer [0–11, notación Pitch Class]",
    "mode":             "integer [0=menor, 1=mayor]",
    "time_signature":   "integer [pulsos por compás]"
  },
  "added_at": "ISODate"
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `title` | String | Nombre de la canción |
| `artist` | String | Artista principal |
| `album` | String | Álbum al que pertenece |
| `release_year` | Int | Año de lanzamiento |
| `duration_ms` | Int | Duración en milisegundos |
| `genre` | Array[String] | Géneros musicales (multivaluado) |
| `external_ids.spotify_id` | String | ID en Spotify (para ingesta de datos) |
| `acoustic_features` | Object | Parámetros acústicos normalizados |
| `acoustic_features.energy` | Float | Intensidad y actividad percibida |
| `acoustic_features.danceability` | Float | Qué tan bailable es la pista |
| `acoustic_features.valence` | Float | Positividad musical transmitida |
| `acoustic_features.tempo` | Float | Velocidad en pulsaciones por minuto |
| `acoustic_features.key` | Int | Tonalidad (0=Do, 1=Do#, ..., 11=Si) |
| `acoustic_features.mode` | Int | Modo: 0=menor, 1=mayor |

**Índices:**
```js
db.tracks.createIndex({ "acoustic_features.energy": 1 })
db.tracks.createIndex({ "acoustic_features.danceability": 1 })
db.tracks.createIndex({ "acoustic_features.valence": 1 })
db.tracks.createIndex({ "acoustic_features.tempo": 1 })
db.tracks.createIndex({ "genre": 1 })
db.tracks.createIndex({ "artist": 1, "title": 1 })
db.tracks.createIndex({ "external_ids.spotify_id": 1 }, { sparse: true })
// Índice compuesto para filtros acústicos combinados
db.tracks.createIndex({
  "acoustic_features.energy": 1,
  "acoustic_features.valence": 1,
  "acoustic_features.danceability": 1
})
```

---

### 2.3 `recommendations`

Persiste cada sesión de recomendación generada para un usuario, permitiendo historial y retroalimentación. Esto es clave para la "experiencia personalizada" descrita en el planteamiento.

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId (ref: users)",
  "generated_at": "ISODate",
  "query_params": {
    "energy":           { "min": 0.6, "max": 0.9 },
    "danceability":     { "min": 0.5, "max": 1.0 },
    "valence":          { "min": 0.4, "max": 0.8 },
    "tempo":            { "min": 100, "max": 140 },
    "genre":            ["pop", "electronic"]
  },
  "tracks": [
    {
      "track_id": "ObjectId (ref: tracks)",
      "score": "float",
      "rank": "integer",
      "user_feedback": "string [null | 'like' | 'dislike' | 'skip']",
      "feedback_at": "ISODate"
    }
  ],
  "total_results": "integer",
  "session_context": {
    "mood": "string",
    "activity": "string",
    "time_of_day": "string"
  }
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `user_id` | ObjectId | Referencia al usuario que solicitó la recomendación |
| `generated_at` | Date | Timestamp de generación |
| `query_params` | Object | Parámetros acústicos usados en la consulta |
| `tracks` | Array[Object] | Lista ordenada de pistas recomendadas |
| `tracks[].score` | Float | Puntuación de similitud/relevancia |
| `tracks[].user_feedback` | String | Retroalimentación del usuario |
| `session_context.mood` | String | Estado de ánimo indicado (p. ej., "energético") |
| `session_context.activity` | String | Actividad (p. ej., "entrenamiento", "estudio") |

**Índices:**
```js
db.recommendations.createIndex({ "user_id": 1, "generated_at": -1 })
db.recommendations.createIndex({ "generated_at": -1 })
```

---

### 2.4 `playlists`

Almacena playlists creadas o guardadas por el usuario, ya sea generadas por la API o definidas manualmente.

```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId (ref: users)",
  "name": "string",
  "description": "string",
  "is_generated": "boolean",
  "recommendation_id": "ObjectId (ref: recommendations, nullable)",
  "tracks": [
    {
      "track_id": "ObjectId (ref: tracks)",
      "added_at": "ISODate",
      "position": "integer"
    }
  ],
  "created_at": "ISODate",
  "updated_at": "ISODate",
  "is_public": "boolean"
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `user_id` | ObjectId | Propietario de la playlist |
| `name` | String | Nombre de la playlist |
| `is_generated` | Boolean | `true` si fue generada automáticamente por la API |
| `recommendation_id` | ObjectId | Referencia a la recomendación origen (si aplica) |
| `tracks` | Array[Object] | Pistas con su posición en la playlist |
| `is_public` | Boolean | Visibilidad de la playlist |

**Índices:**
```js
db.playlists.createIndex({ "user_id": 1, "created_at": -1 })
db.playlists.createIndex({ "is_public": 1 })
```

---

## 3. Diagrama de Relaciones

```
users (1) ──────────────── (N) recommendations
  │                                │
  │                                │ tracks[] refs
  │                                ▼
  └──── (N) playlists ──── (N) tracks
                │
                └── recommendation_id (opcional)
```

- Un `user` puede tener muchas `recommendations` y `playlists`.
- Cada `recommendation` referencia múltiples `tracks` por `track_id`.
- Una `playlist` puede originarse desde una `recommendation`.

---

### 4. Archivo `.env` (local, excluido del repositorio en `.gitignore`)

```env
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=music_recommendations
MONGO_USERNAME=api_user
MONGO_PASSWORD=<contraseña_segura>
MONGO_AUTH_SOURCE=admin
MONGO_URI=mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@${MONGO_HOST}:${MONGO_PORT}/${MONGO_DB}?authSource=${MONGO_AUTH_SOURCE}
```

### 5. GitHub Actions Secrets (Settings > Secrets and variables > Actions)

```
MONGO_URI          → URI completa de conexión
MONGO_USERNAME     → Usuario de base de datos
MONGO_PASSWORD     → Contraseña de base de datos
```

### 5.1  Uso en el pipeline CI/CD (`.github/workflows/ci.yml`)

```yaml
env:
  MONGO_URI: ${{ secrets.MONGO_URI }}
  MONGO_USERNAME: ${{ secrets.MONGO_USERNAME }}
  MONGO_PASSWORD: ${{ secrets.MONGO_PASSWORD }}
```

### 6. Conexión desde Python (`db/connection.py`)

```python
import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

def get_database():
    """
    Retorna la instancia de la base de datos.
    Lee las credenciales exclusivamente desde variables de entorno.
    """
    mongo_uri = os.getenv("MONGO_URI")
    db_name   = os.getenv("MONGO_DB", "music_recommendations")

    if not mongo_uri:
        raise EnvironmentError("MONGO_URI no está definida en las variables de entorno.")

    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

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
```

---

## 7. Consideraciones para Hitos Futuros

| Hito | Fecha | Impacto en el esquema |
|------|-------|-----------------------|
| Primer prototipo funcional | 08/04/2026 | Endpoints CRUD sobre `users` y `tracks` |
| Lógica de búsqueda y filtrado | 16/04/2026 | Queries sobre `acoustic_features` usando los índices compuestos definidos en §2.2 |
| Pruebas unitarias e integrales | 22/04/2026 | Fixtures de MongoDB con datos de prueba; el maestro indica adelantar estas pruebas al pipeline CI/CD |
| API v1.0 + Documentación Técnica | 30/04/2026 | Documentación de endpoints y esquemas en formato OpenAPI |

> **Nota sobre pruebas (observación del maestro):** Se recomienda agregar una base de datos de prueba separada (`music_recommendations_test`) gestionada por GitHub Actions, con secretos propios, para que cada push valide automáticamente la lógica de búsqueda y filtrado sin afectar datos de producción.

---

*Documento para el Release R1 — Equipo I.C.E*
