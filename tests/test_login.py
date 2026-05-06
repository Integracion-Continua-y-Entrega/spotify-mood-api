import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
# Importamos la aplicación desde tu archivo principal
from main import app 

@pytest.mark.asyncio
async def test_spotify_login_persistence():
    """
    Verifica la persistencia real: El usuario debe guardarse en 
    MongoDB bajo el campo 'spotify_id'.
    """
    test_spotify_id = "user_persistence_test_99"
    payload = {
        "code": "code_test",
        "verifier": "verifier_test"
    }

    mock_tokens = {"access_token": "token_a", "refresh_token": "token_r"}
    mock_profile = {"id": test_spotify_id, "display_name": "Tester Persistencia"}

    # Simulamos las llamadas a Spotify
    with patch("main.exchange_code_for_tokens", new_callable=AsyncMock) as mock_exchange, \
         patch("main.fetch_spotify_profile", new_callable=AsyncMock) as mock_fetch:
        
        mock_exchange.return_value = mock_tokens
        mock_fetch.return_value = mock_profile

        # Iniciamos el ciclo de vida de la app para conectar a la DB
        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # Realizamos la petición de login
                await ac.post("/api/v1/auth/login", json=payload)

            # Validamos la persistencia en la colección 'users'[cite: 1]
            collection = app.state.users_collection
            
            # CORRECCIÓN: Buscamos por 'spotify_id' según vimos en el DEBUG[cite: 1]
            user_in_db = await collection.find_one({"spotify_id": test_spotify_id})

            # Verificaciones finales
            assert user_in_db is not None, f"No se encontró el usuario con spotify_id: {test_spotify_id}"
            assert user_in_db["display_name"] == "Tester Persistencia"
            assert "spotify_refresh_token" in user_in_db