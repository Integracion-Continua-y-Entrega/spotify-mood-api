import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from main import app
from dependencies import get_current_user

@pytest.mark.asyncio
async def test_get_user_playlists_success():
    """
    QA: Valida la recuperación de playlists del usuario burlando la caché inicial.
    """
    # 1. Bypass de autenticación (Asignamos el string directo del id esperado por el router)
    test_spotify_id = "qa_user_123"
    app.dependency_overrides[get_current_user] = lambda: test_spotify_id

    # 2. Mock de la respuesta de la colección
    mock_playlists_response = {
        "playlists": [
            {
                "id": "playlist_abc123",
                "user_id": test_spotify_id, 
                "name": "Chill Vibes QA",
                "description": "Playlist de prueba",
                "is_generated": False,
                "recommendation_id": "rec_id_123",
                "tracks": [],
                "created_at": "2026-05-27T10:00:00Z", 
                "updated_at": "2026-05-27T10:00:00Z",
                "is_public": False
            }
        ]
    }

    # Interceptamos el warm-up de la caché de main.py y mapeamos el método real del servicio
    with patch("main._warm_cache", new_callable=AsyncMock), \
         patch("services.playlist_service.PlaylistService.list_user_playlists", new_callable=AsyncMock) as mock_get:
        
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
    QA: Valida la creación de una nueva playlist enviando el payload regulado de 10 canciones.
    """
    test_spotify_id = "qa_user_123"
    app.dependency_overrides[get_current_user] = lambda: test_spotify_id

    # Payload adaptado con un arreglo exacto de 10 IDs para satisfacer al validador CreatePlaylistRequest
    payload = {
        "name": "Mi Playlist Generada por QA",
        "description": "Creada automáticamente desde los tests",
        "public": False,
        "track_ids": [f"69f8994f736605d2666559a{i}" for i in range(10)]
    }

    mock_created_playlist = {
        "id": "new_playlist_999",
        "user_id": test_spotify_id,
        "name": payload["name"],
        "description": payload["description"],
        "is_generated": True,
        "recommendation_id": None,
        "tracks": [],
        "is_public": False,
        "created_at": "2026-05-27T10:00:00Z",
        "updated_at": "2026-05-27T10:00:00Z",
    }

    # ⚡ CORREGIDO: El parche ahora apunta al nombre de método correcto 'create_spotify_playlist'
    with patch("main._warm_cache", new_callable=AsyncMock), \
         patch("services.playlist_service.PlaylistService.create_spotify_playlist", new_callable=AsyncMock) as mock_create:
        
        mock_create.return_value = mock_created_playlist

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.post("/api/v1/users/me/playlists", json=payload)

            # --- VALIDACIONES ---
            assert response.status_code in [200, 201] 
            assert response.json()["name"] == payload["name"]

    app.dependency_overrides = {}