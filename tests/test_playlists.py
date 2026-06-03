import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from main import app
from dependencies import get_current_user

@pytest.mark.asyncio
async def test_get_user_playlists_success():
    """
    QA: Valida la recuperación de playlists del usuario.
    """
    # 1. Bypass de autenticación
    test_spotify_id = "qa_user_123"
    app.dependency_overrides[get_current_user] = lambda: {"spotify_id": test_spotify_id}

    # 2. Mock de la respuesta del servicio (Actualizado para Pydantic)
    mock_playlists_response = {
        "playlists": [
            {
                "id": "playlist_abc123",
                "user_id": test_spotify_id, 
                "name": "Chill Vibes QA",
                "url": "https://open.spotify.com/playlist/playlist_abc123",
                "image_url": "https://image.spotify.com/xyz",
                "created_at": "2026-05-27T10:00:00Z", 
                "updated_at": "2026-05-27T10:00:00Z"  
            }
        ]
    }

    # CORRECCIÓN: Usamos 'list_playlists' como descubrimos en tu router
    with patch("services.playlist_service.PlaylistService.list_playlists", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_playlists_response

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/users/me/playlists")

            # --- VALIDACIONES ---
            assert response.status_code == 200
            data = response.json()
            assert "playlists" in data
            assert len(data["playlists"]) > 0

    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_create_user_playlist_success():
    """
    QA: Valida la creación de una nueva playlist en la cuenta del usuario.
    """
    test_spotify_id = "qa_user_123"
    app.dependency_overrides[get_current_user] = lambda: {"spotify_id": test_spotify_id}

    payload = {
        "name": "Mi Playlist Generada por QA",
        "description": "Creada automáticamente desde los tests",
    }

    mock_created_playlist = {
        "id": "new_playlist_999",
        "name": payload["name"],
        "url": "https://open.spotify.com/playlist/new_playlist_999"
    }

    # Asumimos que el método para el POST se llama 'create_playlist'
    with patch("services.playlist_service.PlaylistService.create_playlist", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_created_playlist

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.post("/api/v1/users/me/playlists", json=payload)

            # --- VALIDACIONES ---
            assert response.status_code in [200, 201] 
            assert response.json()["name"] == payload["name"]

    app.dependency_overrides = {}