from db.user_repo import fetch_user_profile
from db.article_repo import fetch_articles
from db.interaction_repo import fetch_time_spent
from recommender.scorer import calculate_score

def recommend_articles(conn, user_id, limit=100):
    user_profile = fetch_user_profile(conn, user_id)
    if not user_profile:
        return []

    articles = fetch_articles(conn)
    time_spent_map = fetch_time_spent(conn, user_id)

    scored = [
        calculate_score(article, user_profile, time_spent_map)
        for article in articles
    ]

    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored[:limit]