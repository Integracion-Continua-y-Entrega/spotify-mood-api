from models.recommendation import Recommendation
from pydantic import BaseModel

class RecommendationCollection(BaseModel):
    """
    A container holding a list of `Reccomendation` instances"""

    recommendations: list[Recommendation]