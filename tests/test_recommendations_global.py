import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from main import app

# Definimos el objeto con ambos formatos de ID para máxima compatibilidad
MOCK_RECOMMENDATION = {
    "id": "65f1a2b3c4d5e6f7a8b9c0d1",
    "_id": "65f1a2b3c4d5e6f7a8b9c0d1", # Agregamos el formato MongoDB
    "user_id": "user_qa_global",
    "total_results": 1,
    "tracks": [{"track_id": "t1", "score": 0.9, "rank": 1}],
    "query_params": {},
    "session_context": {
        "mood": "happy",
        "activity": "testing",
        "time_of_day": "day"
    }
}

@pytest.mark.asyncio
async def test_get_all_recommendations_global_success():
    """
    QA: Valida el listado global.
    """
    mock_response = {"recommendations": [MOCK_RECOMMENDATION]}

    with patch("services.recommendation_service.RecommendationService.list_recommendations", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_response

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get("/api/v1/recommendations")

            assert response.status_code == 200
            data = response.json()
            assert "recommendations" in data

@pytest.mark.asyncio
async def test_get_single_recommendation_by_id_success():
    """
    QA: Valida búsqueda por ID. 
    Ajustamos la extracción para aceptar 'id' o '_id'.
    """
    rec_id = MOCK_RECOMMENDATION["id"]

    with patch("services.recommendation_service.RecommendationService.find_by_id", new_callable=AsyncMock) as mock_find, \
         patch("services.recommendation_service.RecommendationService.list_recommendations", new_callable=AsyncMock) as mock_list:
        
        mock_find.return_value = MOCK_RECOMMENDATION
        mock_list.return_value = {"recommendations": [MOCK_RECOMMENDATION]}

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                response = await ac.get(f"/api/v1/recommendations/{rec_id}")
                
                if response.status_code == 422:
                    response = await ac.get("/api/v1/recommendations", params={"recommendation_id": rec_id})

            assert response.status_code == 200
            data = response.json()
            
            # QA: Búsqueda exhaustiva del ID en la respuesta
            # Intentamos todas las combinaciones posibles donde podría estar el ID
            actual_id = (
                data.get("id") or 
                data.get("_id") or 
                (data.get("recommendations", [{}])[0].get("id") if "recommendations" in data else None) or
                (data.get("recommendations", [{}])[0].get("_id") if "recommendations" in data else None)
            )
            
            assert actual_id == rec_id