from fastapi import APIRouter, Depends
from db.connection import get_connection
from recommender.recommender import recommend_articles
from api.models import RecommendationResponse, Recommendation

router = APIRouter()

@router.get("/recommendations/{user_id}", response_model=RecommendationResponse)
def get_recommendations(user_id: int):
    conn = get_connection()
    try:
        recommendations = recommend_articles(conn, user_id)
        return {"recommendations": recommendations}
    finally:
        conn.close()