import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock
from main import app
from dependencies import get_current_user

@pytest.mark.asyncio
async def test_create_recommendations_success():
    """
    QA: Valida el endpoint POST /me/recommendations. 
    Configuramos session_context con strings reales para pasar la validación.
    """
    app.dependency_overrides[get_current_user] = lambda: "user_test_123"
    
    # 1. Mock de la Recomendación con session_context completo
    mock_rec = MagicMock()
    mock_rec.user_id = "user_test_123"
    mock_rec.tracks = [{"track_id": "sp_1", "score": 0.99, "rank": 1}]
    
    # IMPORTANTE: Definimos los strings que Pydantic espera
    mock_rec.session_context = MagicMock()
    mock_rec.session_context.mood = "energetic"
    mock_rec.session_context.activity = "testing"
    mock_rec.session_context.time_of_day = "now"
    
    # 2. Mock del contenedor RecommendationCollection
    mock_collection = MagicMock()
    mock_collection.recommendations = [mock_rec]

    # --- PARCHE DEL MÉTODO REAL 'recommend' ---
    with patch("services.recommendation_service.RecommendationService.recommend", new_callable=AsyncMock) as mock_method:
        mock_method.return_value = mock_collection

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # Enviamos el mood por Query Params
                response = await ac.post("/api/v1/users/me/recommendations", params={"mood": "energetic"})

            # --- VALIDACIONES ---
            assert response.status_code == 200
            data = response.json()
            assert "recommendations" in data 
    
    app.dependency_overrides = {}