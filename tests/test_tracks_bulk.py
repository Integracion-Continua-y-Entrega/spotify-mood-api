import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from main import app

@pytest.mark.asyncio
async def test_get_tracks_bulk_success():
    """
    QA: Valida el endpoint /bulk con un perfil acústico completo 
    que incluye loudness, key y mode.
    """
    track_ids = ["65f1a2b3c4d5e6f7a8b9c0d1", "65f1a2b3c4d5e6f7a8b9c0d2"]
    payload = {"ids": track_ids}

    # Mock con los campos técnicos faltantes agregados
    mock_tracks_list = [
        {
            "title": "Song Alpha",
            "external_ids": {"spotify_id": "4uLU61CZoI0pX3iZp9p93q"},
            "acoustic_features": {
                "energy": 0.8, "danceability": 0.7, "valence": 0.6,
                "acousticness": 0.2, "instrumentalness": 0.0,
                "liveness": 0.1, "speechiness": 0.05, "tempo": 120.0,
                "loudness": -5.5, "key": 5, "mode": 1 # <--- CAMPOS NUEVOS
            },
            "artist": "Artist One",
            "album": "Album Premiere",
            "duration_ms": 210000
        },
        {
            "title": "Song Beta",
            "external_ids": {"spotify_id": "1rgnp9vFCp9p93qZpI0pX3"},
            "acoustic_features": {
                "energy": 0.4, "danceability": 0.5, "valence": 0.3,
                "acousticness": 0.8, "instrumentalness": 0.1,
                "liveness": 0.2, "speechiness": 0.03, "tempo": 90.0,
                "loudness": -10.2, "key": 0, "mode": 0 # <--- CAMPOS NUEVOS
            },
            "artist": "Artist Two",
            "album": "Album Seconds",
            "duration_ms": 185000
        }
    ]
    
    # El servicio devuelve un objeto TrackCollection
    mock_response_data = {"tracks": mock_tracks_list}

    with patch("services.track_service.TrackService.find_by_ids", new_callable=AsyncMock) as mock_bulk:
        mock_bulk.return_value = mock_response_data

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.post("/api/v1/tracks/bulk", json=payload)

            # --- VALIDACIONES ---
            assert response.status_code == 200
            data = response.json()
            assert "tracks" in data
            assert data["tracks"][0]["acoustic_features"]["loudness"] == -5.5