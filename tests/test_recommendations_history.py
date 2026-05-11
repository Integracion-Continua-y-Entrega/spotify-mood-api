import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from main import app
from dependencies import get_current_user

@pytest.mark.asyncio
async def test_get_recommendations_history_success():
    """
    QA: Valida que el endpoint de historial recupere correctamente
    las recomendaciones previas del usuario desde MongoDB.
    """
    test_spotify_id = "user_qa_123"
    
    # 1. Simulación del usuario autenticado
    mock_user_data = {"spotify_id": test_spotify_id}
    app.dependency_overrides[get_current_user] = lambda: mock_user_data

    # 2. Simulación de los datos históricos (Lo que devolvería el Service)
    # 2. Simulación de los datos históricos (Mock 100% compatible)
    mock_history = {
        "recommendations": [
            {
                "id": "65f1a2b3c4d5e6f7a8b9c0d1", 
                "user_id": test_spotify_id,
                "total_results": 2,
                "tracks": [
                    {"track_id": "t1", "score": 0.9, "rank": 1}, # <--- Agregamos rank
                    {"track_id": "t2", "score": 0.8, "rank": 2}  # <--- Agregamos rank
                ],
                "session_context": {"mood": "happy"},
                "query_params": {},
                "created_at": "2026-05-11T10:00:00Z"
            }
        ]
    }

    # --- PARCHE DEL SERVICIO ---
    # Usamos find_by_user_id que es el método real en recommendation_service.py
    with patch("services.recommendation_service.RecommendationService.find_by_user_id", new_callable=AsyncMock) as mock_find:
        mock_find.return_value = mock_history

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/users/me/recommendations")

            # --- VALIDACIONES DE CALIDAD ---
            assert response.status_code == 200
            data = response.json()
            assert "recommendations" in data
            assert len(data["recommendations"]) > 0
            assert data["recommendations"][0]["user_id"] == test_spotify_id

    # Limpieza de seguridad
    app.dependency_overrides = {}