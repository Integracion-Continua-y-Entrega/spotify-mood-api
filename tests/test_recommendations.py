import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock, MagicMock
from main import app
# Importamos la función original para poder sobreescribirla
from dependencies import get_current_user 

@pytest.mark.asyncio
async def test_generate_recommendations_success():
    """
    QA: Valida el motor de recomendaciones usando 'dependency_overrides'
    para saltar el error 403 de autorización.
    """
    test_spotify_id = "user_qa_123"
    mood_payload = {"mood": "energetic"}
    
    mock_user_data = {
        "spotify_id": test_spotify_id,
        "preferences": {
            "acoustic_profile": {
                "energy": 0.8, "danceability": 0.7, "valence": 0.6,
                "acousticness": 0.1, "instrumentalness": 0.0,
                "liveness": 0.2, "speechiness": 0.05, "tempo": 120.0
            }
        }
    }

    # --- CONFIGURACIÓN DE QA (Dependency Override) ---
    # Esto fuerza a FastAPI a ignorar el token real y usar nuestro mock
    app.dependency_overrides[get_current_user] = lambda: mock_user_data

    # ACTUALIZAMOS EL MOCK: Agregamos query_params para satisfacer el modelo
    mock_response = {
        "recommendations": [
            {
                "user_id": test_spotify_id,
                "total_results": 1,
                "tracks": [{"track_id": "t1", "score": 0.95, "rank": 1}],
                "session_context": {"mood": "energetic"},
                "query_params": {} # <--- ESTO ES LO QUE FALTABA
            }
        ]
    }

    with patch("services.recommendation_service.RecommendationService.recommend", new_callable=AsyncMock) as mock_recommend:
        mock_recommend.return_value = mock_response

        async with app.router.lifespan_context(app):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                # En lugar de enviar un JSON, lo enviamos como parámetro de URL
                response = await ac.post(
                    "/api/v1/users/me/recommendations", 
                    params={"mood": "energetic"} # <--- Cambiamos 'json' por 'params'
                )


            if response.status_code == 422:
                print(f"\n⚠️ Error de Validación (QA Debug): {response.json()}")

            # Validaciones
            assert response.status_code == 200 or response.status_code == 201
            data = response.json()
            assert "recommendations" in data
            

    # IMPORTANTE: Limpiamos los overrides después del test para no afectar otros
    app.dependency_overrides = {}