import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from main import app

@pytest.mark.asyncio
async def test_get_track_by_id_success():
    """
    QA: Valida la recuperación de una pista individual por su ID de base de datos. 
    """
    test_track_id = "65f1a2b3c4d5e6f7a8b9c0d1" # Un ID con formato ObjectId válido

    # Mock del objeto Track individual (Sin el wrapper de tracks)
    mock_track = {
        "title": "Solo Track",
        "external_ids": {"spotify_id": "sp_solo_1"},
        "acoustic_features": {
            "energy": 0.6, "danceability": 0.6, "valence": 0.6,
            "acousticness": 0.1, "instrumentalness": 0.0,
            "liveness": 0.1, "speechiness": 0.05, "tempo": 115.0,
            "loudness": -6.0, "key": 4, "mode": 1
        },
        "artist": "Artist Solo",
        "album": "Single Album",
        "duration_ms": 220000
    }

    # --- PARCHE DEL SERVICIO ---
    with patch("services.track_service.TrackService.find_by_id", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = mock_track

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get(f"/api/v1/tracks/{test_track_id}")

            # --- VALIDACIONES ---
            assert response.status_code == 200
            data = response.json()
            # OJO QA: Aquí la respuesta es el objeto directo, NO una lista
            assert data["title"] == "Solo Track"
            assert "acoustic_features" in data