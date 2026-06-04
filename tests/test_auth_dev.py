import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from main import app

@pytest.mark.asyncio
async def test_auth_refresh_dev_success():
    """
    QA: Valida el endpoint de auth-dev. Parcheamos 'refresh_session' 
    porque es el método que el controlador está utilizando actualmente.
    """
    test_id = "qa_dev_user_99"
    
    # Respuesta simulada que cumple con el contrato de refresh_session
    mock_token_response = {
        "access_token": "mocked_jwt_token_123",
        "token_type": "bearer",
        "expires_in": 28800
    }

    # CORRECCIÓN: Parcheamos el método real existente en auth_service.py
    with patch("services.auth_service.AuthService.refresh_session", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = mock_token_response

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # Enviamos el id por Query Params como descubrimos antes
                response = await ac.post("/api/v1/auth/refresh-dev", params={"spotify_id": test_id})

            # --- VALIDACIONES ---
            assert response.status_code == 200
            data = response.json()
            assert data["access_token"] == "mocked_jwt_token_123"