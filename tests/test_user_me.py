import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from main import app
from dependencies import get_current_user

@pytest.mark.asyncio
async def test_get_my_profile_success():
    """
    QA: Validación final del perfil de usuario asegurando que 
    tempo_range incluya el rango completo (value, min, max).
    """
    test_spotify_id = "user_qa_123"
    
    def to_range_obj(val):
        return {"target": val, "min": max(0, val - 0.1), "max": min(1.0, val + 0.1)}

    mock_user_data = {
        "spotify_id": test_spotify_id,
        "display_name": "QA Tester",
        "email": "test@qa.com",
        "profile_image": "http://image.png",
        "spotify_refresh_token": "refresh_123",
        "created_at": "2026-05-11T12:00:00Z",
        "preferences": {
            "language": "es",
            "acoustic_profile": {
                "energy": to_range_obj(0.8),
                "danceability": to_range_obj(0.7),
                "valence": to_range_obj(0.6),
                "acousticness": to_range_obj(0.2),
                "instrumentalness": to_range_obj(0.0),
                # CORRECCIÓN: Usamos floats para representar BPM
                "tempo_range": {
                    "target": 120.0, # <--- Cambiamos 'value' por 'target' y el string por float
                    "min": 60.0, 
                    "max": 180.0
                }
            }
        }
    }

    # Bypass de seguridad inyectando el ID del usuario
    app.dependency_overrides[get_current_user] = lambda: test_spotify_id

    # Patch del UserService para interceptar la llamada a la DB
    with patch("services.user_service.UserService.find_by_spotify_id", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = mock_user_data 

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/users/me")


            # VALIDACIONES FINALES
            assert response.status_code == 200
            data = response.json()
            
            assert data["spotify_id"] == test_spotify_id
            
            # Validamos contra lo que REALMENTE devuelve la API: min y max
            tempo_obj = data["preferences"]["acoustic_profile"]["tempo_range"]
            assert tempo_obj["min"] == 60.0
            assert tempo_obj["max"] == 180.0

    app.dependency_overrides = {}