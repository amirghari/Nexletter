from nlp.liked_title_repo import fetch_liked_titles
from nlp.similarity import score_title_similarity
from recommender.utils import normalize_country_string

def calculate_score(article, user_profile, time_spent_map, conn, user_id):
    article_id, title, country, category = article
    score = 0

    # Normalize fields
    country = normalize_country_string(country)
    category = [c.lower() for c in category] if category else []

    # Preferred Country and Category (+5)
    if country in [c.lower() for c in user_profile['preferred_countries']]:
        score += 5
    if any(cat in [c.lower() for c in user_profile['preferred_categories']] for cat in category):
        score += 5

    # Liked Country and Category (dynamic score)
    score += int(user_profile['liked_countries'].get(country, 0))
    for cat in category:
        score += int(user_profile['liked_categories'].get(cat, 0))

    # Time Spent Bonus
    time_spent = time_spent_map.get(article_id, 0)
    if time_spent > 900:
        score += 5
    elif time_spent > 600:
        score += 2

    # === NEW: NLP Similarity Score ===
    liked_titles = fetch_liked_titles(conn, user_id)
    if liked_titles:
        similarity = score_title_similarity(title, liked_titles)
        if similarity > 0.3:
            score += int(similarity * 10)  # Scale similarity 0.0–1.0 into 0–10

    return {'article_id': article_id, 'title': title, 'score': score}