from models.recommendations_collection import RecommendationCollection

class RecommendationService:
    def __init__(self, collection):
        self.recommendations = collection

    async def list_recommendations(self):
        try:
            return RecommendationCollection(
                recommendations=await self.recommendations.find().to_list(1000))
        except Exception as e:
            raise Exception(e)
        
    async def recommend():
        pass