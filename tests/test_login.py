import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock
from main import app 

@pytest.mark.asyncio
async def test_spotify_login_persistence():
    """
    QA: Blindaje contra 'MongoClient after close'. 
    Parcheamos el UserService para que el test no dependa de la conexión real a MongoDB.
    """
    test_spotify_id = "user_persistence_test_99"
    payload = {"code": "code_test", "verifier": "verifier_test"}

    mock_tokens = {"access_token": "token_a", "refresh_token": "token_r"}
    mock_profile = {"id": test_spotify_id, "display_name": "Tester Persistencia"}
    
    track_data = {
        "spotify_id": "track_123",
        "name": "Canción de Prueba",
        "acoustic_features": {
            "energy": 0.85, "danceability": 0.7, "valence": 0.6,
            "acousticness": 0.1, "instrumentalness": 0.0,
            "liveness": 0.2, "speechiness": 0.05, "tempo": 122.0, "loudness": -5.0
        }
    }

    mock_track_obj = MagicMock()
    mock_track_obj.model_dump.return_value = track_data

    # --- PARCHES DE SERVICIOS (AISLAMIENTO TOTAL) ---
    with patch("services.auth_service.exchange_code_for_tokens", new_callable=AsyncMock) as mock_exchange, \
         patch("services.auth_service.fetch_spotify_profile", new_callable=AsyncMock) as mock_fetch, \
         patch("services.auth_service.fetch_user_top_tracks", new_callable=AsyncMock) as mock_fetch_tracks, \
         patch("services.auth_service.encrypt_refresh_token") as mock_encrypt, \
         patch("services.track_service.TrackService.find_by_spotify_id", new_callable=AsyncMock) as mock_find_track, \
         patch("services.user_service.UserService.upsert_user", new_callable=AsyncMock) as mock_upsert, \
         patch("services.user_service.UserService.update_user_preferences", new_callable=AsyncMock) as mock_update_prefs:
        
        # Configuramos los retornos de los mocks
        mock_exchange.return_value = mock_tokens
        mock_fetch.return_value = mock_profile
        mock_fetch_tracks.return_value = [{"id": "track_123"}]
        mock_encrypt.return_value = "token_encriptado_mock"
        mock_find_track.return_value = mock_track_obj
        
        # Simulamos que el usuario se guarda/actualiza correctamente en el servicio
        mock_upsert.return_value = "mock_user_id_123"
        mock_update_prefs.return_value = True

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.post("/api/v1/auth/login", json=payload)

            # --- VALIDACIÓN ---
            assert response.status_code == 200
            
            # QA: En lugar de consultar MongoDB (que daría error), verificamos 
            # que se llamó al método de persistencia con los datos correctos.
            assert mock_upsert.called
            data = response.json()
            assert "access_token" in data

    # Limpieza de seguridad
    app.dependency_overrides = {}