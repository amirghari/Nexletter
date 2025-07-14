from pydantic import BaseModel
from typing import List

class Recommendation(BaseModel):
    article_id: int
    title: str
    score: int

class RecommendationResponse(BaseModel):
    recommendations: List[Recommendation]