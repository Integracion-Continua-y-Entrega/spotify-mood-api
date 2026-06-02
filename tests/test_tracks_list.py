import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from main import app

@pytest.mark.asyncio
async def test_list_tracks_pagination_success():
    """
    QA: Valida que el listado de tracks soporte paginación 
    y devuelva una TrackCollection válida.
    """
    # 1. Definimos los parámetros de prueba
    params = {"page": 1, "limit": 2}

    # 2. Mock de TrackCollection (Ya conocemos este esquema por el bulk)
    mock_collection = {
        "tracks": [
            {
                "title": "Track Paginated 1",
                "external_ids": {"spotify_id": "sp_1"},
                "acoustic_features": {
                    "energy": 0.5, "danceability": 0.5, "valence": 0.5,
                    "acousticness": 0.5, "instrumentalness": 0.1,
                    "liveness": 0.1, "speechiness": 0.1, "tempo": 100.0,
                    "loudness": -8.0, "key": 1, "mode": 1
                },
                "artist": "Artist 1", "album": "Album 1", "duration_ms": 200000
            }
        ]
    }

    # --- PARCHE DEL SERVICIO ---
    # Usamos list_tracks que es el método encargado en el service
    with patch("services.track_service.TrackService.list_tracks", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_collection

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/tracks", params=params)

            # --- VALIDACIONES ---
            assert response.status_code == 200
            data = response.json()
            assert "tracks" in data
            assert len(data["tracks"]) > 0