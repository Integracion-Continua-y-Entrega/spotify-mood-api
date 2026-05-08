# 🎵 Spotify Mood API (Monorepo)

API para recomendación musical basada en estados de ánimo utilizando los atributos de audio (Audio Features) de Spotify. Este proyecto utiliza una arquitectura de monorepo que integra un Frontend en React/Vite y un Backend en FastAPI.

---

## 🏗️ Estructura del Proyecto

El repositorio está organizado de la siguiente manera:

- `/frontend`: Aplicación cliente desarrollada con React y Vite.
- `/src/api`: API desarrollada con FastAPI, ubicada específicamente en `src/api`.

---

## 🔄 Flujo de Autenticación

El sistema implementa OAuth 2.0 con PKCE (Proof Key for Code Exchange), lo que permite una autenticación segura sin necesidad de exponer el `Client Secret` en el lado del cliente.

- **Cifrado:** Los `refresh_tokens` se almacenan en MongoDB cifrados mediante Fernet.
- **Sesión:** Una vez autenticado, el sistema genera un JWT (JSON Web Token) para manejar la sesión del usuario de forma segura.

---

## 🚀 Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/spotify-mood-api.git
cd spotify-mood-api
```

### 2. Configuración del Backend

Navega a la carpeta del backend e instala las dependencias:

```bash
cd backend
python -m venv venv
# Activa el entorno (Windows: venv\Scripts\activate | Unix: source venv/bin/activate)
pip install -r requirements.txt
```

Crea un archivo `.env` en la raíz del backend con los siguientes campos:

```env
SPOTIFY_CLIENT_ID=tu_client_id
SPOTIFY_CLIENT_SECRET=tu_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5173/callback

# Generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
TOKEN_ENCRYPTION_KEY=tu_fernet_key

# Generar con: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=tu_jwt_secret

MONGO_URI=mongodb://127.0.0.1:27017
MONGO_DB=spotify_mood_db
```

### 3. Configuración del Frontend

Navega a la carpeta del frontend e instala las dependencias de Node:

```bash
cd ../frontend
npm install
```

Crea un archivo `.env` en la raíz del frontend:

```env
VITE_SPOTIFY_CLIENT_ID=tu_client_id
VITE_REDIRECT_URI=http://127.0.0.1:5173/callback
VITE_API_URL=http://127.0.0.1:8000
```

---

## ▶️ Ejecución del Proyecto

Para trabajar en el proyecto, debes iniciar ambos servicios:

**Ejecutar Backend:**

```bash
cd backend/src/api
uvicorn main:app --reload
```

La API estará en `http://127.0.0.1:8000` y la documentación en `/docs`.

**Ejecutar Frontend:**

```bash
cd frontend
npm run dev
```

El cliente estará disponible en `http://127.0.0.1:5173`.

---

## 🐳 Docker

Es posible ejecutar el proyecto utilizando contenedores, lo que simplifica la configuración del entorno y evita dependencias locales.

Asegúrate de tener configurado correctamente el archivo `.env`, ya que contiene las variables necesarias para inicializar los servicios (base de datos, credenciales, claves de API, etc.). Si alguna falta o es incorrecta, la aplicación puede no iniciar.


Luego ejecuta:

```bash
docker-compose up --build
```

Para detener los servicios:
```bash
docker-compose down
```

> La API estará disponible en `http://127.0.0.1:8000` y la documentación en `/docs`.  


## 🌐 Endpoints

| Método | Ruta | Parámetros | Descripción | Disponible |
| :--- | :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/auth/login` | Ninguno | Intercambia el código de Spotify por tokens, cifra y guarda al usuario. | ✅ Sí |
| **POST** | `/api/v1/auth/refresh-dev` | `spotify_id` | **(Dev only)** Genera un access token directamente para el usuario dado, omitiendo el flujo OAuth. | ✅ Sí |
| **GET** | `/api/v1/users/me` | Ninguno | Obtiene el perfil de un usuario autenticado. | ✅ Sí |
| **GET** | `/api/v1/users` | Ninguno | Obtiene todos los usuarios. | ✅ Sí |
| **GET** | `/api/v1/users/me/recommendations` | `mood`, `limit`, `genres` | Recupera las sugerencias musicales de un usuario autenticado. | ✅ Sí |
| **GET** | `/api/v1/recommendations/{id}` | Ninguno | Recupera una recomendación musical de un usuario autenticado a través de su identificador. | ✅ Sí |
| **GET** | `/api/v1/recommendations` | Ninguno | Recupera todas las recomendaciones musicales de la base de datos. | ✅ Sí |
| **POST** | `/api/v1/users/me/recommendations` | `mood` | Genera una selección de recomendaciones de canciones en base al perfil musical de un usuario. | ✅ Sí |
| **GET** | `/api/v1/tracks` | `page`, `limit` | Busca pistas de audio en el catálogo local. | ✅ Sí |
| **GET** | `/api/v1/tracks/{id}` | Ninguno | Busca una pista de audio en el catálogo local a través de su identificador. | ✅ Sí |
| **POST** | `/api/v1/tracks/bulk` | `{ "ids": ["1", "2", "3"] }` | Busca múltiples pistas de audio en el catálogo local en una sola consulta. | ✅ Sí |
| **GET** | `/api/v1/users/me/playlists` | Ninguno | Recupera las playlists creadas o seguidas por el usuario. | No |
| **POST** | `/api/v1/users/me/playlists` | Ninguno | Crea una nueva playlist en la cuenta de Spotify del usuario. | No |

---

## 🗄️ Modelo de Datos (MongoDB)

El sistema utiliza un enfoque documental para evitar JOINs costosos y mejorar la velocidad de respuesta.

### Colección: `users`

Almacena el perfil y las credenciales cifradas:

```json
{
  "spotify_id": "string",
  "display_name": "string",
  "email": "string",
  "spotify_refresh_token": "cifrado_fernet",
  "last_login": "timestamp",
  "preferences": {
    "favorite_genres": ["string"],
    "acoustic_profile": {}
  }
}
```

### Tracks

Representa una pista musical almacenada en el catálogo local.

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :--- | :--- |
| `_id` | string (ObjectId) | No | Identificador único. |
| `title` | string | Sí | Título de la canción. |
| `artist` | string | Sí | Artista principal. |
| `album` | string | Sí | Álbum al que pertenece. |
| `release_year` | int | No | Año de lanzamiento. |
| `duration_ms` | int | Sí | Duración en milisegundos. |
| `genre` | array[string] | No | Géneros asociados. |
| `language` | string | No | Idioma de la canción. |
| `external_ids.spotify_id` | string | Sí | ID de Spotify. |
| `external_ids.isrc` | string | No | Código ISRC. |
| `acoustic_features.energy` | float (0–1) | Sí | Intensidad energética. |
| `acoustic_features.danceability` | float (0–1) | Sí | Facilidad para bailar. |
| `acoustic_features.valence` | float (0–1) | Sí | Positividad (felicidad). |
| `acoustic_features.acousticness` | float (0–1) | Sí | Nivel acústico. |
| `acoustic_features.instrumentalness` | float (0–1) | Sí | Instrumentalidad. |
| `acoustic_features.liveness` | float (0–1) | Sí | Presencia en vivo. |
| `acoustic_features.speechiness` | float (0–1) | Sí | Nivel de habla. |
| `acoustic_features.loudness` | float | Sí | Volumen en dB. |
| `acoustic_features.tempo` | float | Sí | Tempo (BPM). |
| `acoustic_features.key` | int (0–11) | Sí | Tonalidad musical. |
| `acoustic_features.mode` | int (0–1) | Sí | Mayor (1) / menor (0). |
| `acoustic_features.time_signature` | int | No | Compás. |
| `added_at` | datetime | Sí | Fecha de registro. |

### Recommendations

Representa una sesión de recomendaciones generadas para un usuario.

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :--- | :--- |
| `_id` | string (ObjectId) | No | Identificador único. |
| `user_id` | string (ObjectId) | Sí | Usuario asociado. |
| `generated_at` | datetime | Sí | Fecha de generación. |
| `query_params` | object | Sí | Parámetros usados para generar recomendaciones. |
| `tracks` | array | Sí | Lista de tracks recomendados. |
| `total_results` | int | Sí | Total de resultados generados. |
| `session_context` | object | No | Contexto de la sesión (mood, actividad, etc.). |

#### query_params
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `energy`, `danceability`, `valence` | object `{min, max}` | Filtros acústicos (0–1). |
| `tempo` | object `{min, max}` | Rango de BPM. |
| `genre` | array[string] | Géneros filtrados. |

#### tracks
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `track_id` | string | ID de la pista. |
| `score` | float (0–1) | Relevancia. |
| `rank` | int | Posición en ranking. |
| `user_feedback` | string | `like`, `dislike`, `skip`. |
| `feedback_at` | datetime | Fecha del feedback. |

#### session_context
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `mood` | string | Estado de ánimo. |
| `activity` | string | Actividad del usuario. |
| `time_of_day` | string | Momento del día. |

### Playlists

Representa listas de reproducción creadas por el usuario o generadas automáticamente.

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :--- | :--- |
| `_id` | string (ObjectId) | No | Identificador único. |
| `user_id` | string (ObjectId) | Sí | Usuario propietario. |
| `name` | string | Sí | Nombre de la playlist. |
| `description` | string | No | Descripción. |
| `is_generated` | bool | Sí | Indica si fue generada automáticamente. |
| `recommendation_id` | string | No | Recomendación origen. |
| `tracks` | array | Sí | Lista de tracks. |
| `created_at` | datetime | Sí | Fecha de creación. |
| `updated_at` | datetime | Sí | Última actualización. |
| `is_public` | bool | Sí | Visibilidad pública. |

#### tracks
| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `track_id` | string | ID de la pista. |
| `added_at` | datetime | Fecha en que se añadió. |
| `position` | int | Orden dentro de la playlist. |
---

## 🔐 Seguridad

- **Fail-fast:** El sistema valida las variables de entorno al arranque para evitar errores en tiempo de ejecución.
- **Cifrado Simétrico:** Uso de la librería `cryptography` para proteger tokens sensibles.
- **Validación de Esquemas:** Uso de Pydantic v2 para asegurar que los datos en la base de datos coincidan con la lógica del negocio.
