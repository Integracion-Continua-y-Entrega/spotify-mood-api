# 🎵 Spotify Mood API (Monorepo)

API para recomendación musical basada en estados de ánimo utilizando los atributos de audio (Audio Features) de Spotify. Este proyecto utiliza una arquitectura de monorepo que integra un Frontend en React/Vite y un Backend en FastAPI.

---

## 🏗️ Estructura del Proyecto

El repositorio está organizado de la siguiente manera:

- `/frontend`: Aplicación cliente desarrollada con React y Vite.
- `/backend`: API desarrollada con FastAPI, ubicada específicamente en `src/api`.

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
SPOTIFY_REDIRECT_URI=http://localhost:5173/callback

# Generar con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
TOKEN_ENCRYPTION_KEY=tu_fernet_key

# Generar con: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=tu_jwt_secret

MONGO_URI=mongodb://localhost:27017
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
VITE_REDIRECT_URI=http://localhost:5173/callback
VITE_API_URL=http://localhost:8000
```

---

## ▶️ Ejecución del Proyecto

Para trabajar en el proyecto, debes iniciar ambos servicios:

**Ejecutar Backend:**

```bash
cd backend/src/api
uvicorn main:app --reload
```

La API estará en `http://localhost:8000` y la documentación en `/docs`.

**Ejecutar Frontend:**

```bash
cd frontend
npm run dev
```

El cliente estará disponible en `http://localhost:5173`.

---

## 🌐 Endpoints Principales

| Método | Ruta                 | Descripción                                                             |
| ------ | -------------------- | ----------------------------------------------------------------------- |
| `POST` | `/api/v1/auth/login` | Intercambia el código de Spotify por tokens, cifra y guarda al usuario. |
| `GET`  | `/recommendations`   | Genera tracks basados en el `mood` solicitado.                          |
| `GET`  | `/history`           | Recupera el historial almacenado en MongoDB.                            |

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

---

## 🔐 Seguridad

- **Fail-fast:** El sistema valida las variables de entorno al arranque para evitar errores en tiempo de ejecución.
- **Cifrado Simétrico:** Uso de la librería `cryptography` para proteger tokens sensibles.
- **Validación de Esquemas:** Uso de Pydantic v2 para asegurar que los datos en la base de datos coincidan con la lógica del negocio.
