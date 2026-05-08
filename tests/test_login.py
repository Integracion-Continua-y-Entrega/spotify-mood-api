import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock
from main import app 

@pytest.mark.asyncio
async def test_spotify_login_persistence():
    """
    Verifica la persistencia tras la modularización, satisfaciendo 
    las validaciones de tracks y analítica de Pandas.
    """
    test_spotify_id = "user_persistence_test_99"
    payload = {"code": "code_test", "verifier": "verifier_test"}

    mock_tokens = {"access_token": "token_a", "refresh_token": "token_r"}
    mock_profile = {"id": test_spotify_id, "display_name": "Tester Persistencia"}
    
    # 1. Datos del track con la estructura anidada que busca la analítica (acoustic_features)
    track_data = {
        "spotify_id": "track_123",
        "name": "Canción de Prueba",
        "acoustic_features": {
            "energy": 0.85,
            "danceability": 0.7,
            "valence": 0.6,
            "acousticness": 0.1,
            "instrumentalness": 0.0,
            "liveness": 0.2,
            "speechiness": 0.05,
            "tempo": 122.0,
            "loudness": -5.0
        }
    }

    # 2. Mock sincrónico para evitar el error de corrutina en model_dump()
    mock_track_obj = MagicMock()
    mock_track_obj.model_dump.return_value = track_data

    # --- PARCHES EN LAS RUTAS CORRECTAS (SERVICES) ---
    with patch("services.auth_service.exchange_code_for_tokens", new_callable=AsyncMock) as mock_exchange, \
         patch("services.auth_service.fetch_spotify_profile", new_callable=AsyncMock) as mock_fetch, \
         patch("services.auth_service.fetch_user_top_tracks", new_callable=AsyncMock) as mock_fetch_tracks, \
         patch("services.track_service.TrackService.find_by_spotify_id", new_callable=AsyncMock) as mock_find_track:
        
        mock_exchange.return_value = mock_tokens
        mock_fetch.return_value = mock_profile
        mock_fetch_tracks.return_value = [{"id": "track_123"}]
        mock_find_track.return_value = mock_track_obj

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.post("/api/v1/auth/login", json=payload)

            # Validaciones finales
            assert response.status_code == 200
            collection = app.state.users_collection
            user_in_db = await collection.find_one({"spotify_id": test_spotify_id})

            assert user_in_db is not None
            assert "preferences" in user_in_db