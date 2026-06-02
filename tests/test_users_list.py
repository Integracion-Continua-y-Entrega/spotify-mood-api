import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from main import app
from dependencies import get_current_user

@pytest.mark.asyncio
async def test_get_all_users_success():
    """
    QA: Valida el listado de usuarios confirmando que los campos 
    sensibles son filtrados correctamente en la respuesta.
    """
    app.dependency_overrides[get_current_user] = lambda: "admin_user_qa"

    # El Mock sigue teniendo el token porque el Servicio lo necesita para validar el modelo
    mock_users_collection = {
        "users": [
            {
                "spotify_id": "user_1",
                "display_name": "Test User 1",
                "email": "user1@test.com",
                "spotify_refresh_token": "token_secreto_123", 
                "created_at": "2026-05-13T10:00:00Z"
            }
        ]
    }

    with patch("services.user_service.UserService.list_users", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_users_collection

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/users")

            # --- VALIDACIONES ---
            assert response.status_code == 200
            data = response.json()
            
            assert "users" in data
            # Validamos campos públicos
            assert data["users"][0]["display_name"] == "Test User 1"
            
            # QA: Verificamos que el token NO esté en la respuesta (Seguridad confirmada)
            assert "spotify_refresh_token" not in data["users"][0]

    app.dependency_overrides = {}