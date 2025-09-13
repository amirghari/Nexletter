from nlp.liked_title_repo import fetch_liked_titles
from nlp.similarity import score_title_similarity
from recommender.utils import normalize_country_string

def calculate_score(article, user_profile, time_spent_map, conn, user_id, w1, w2, w3):
    article_id, title, country, category = article
    score = 0

    # Normalize
    country = normalize_country_string(country)
    category = [c.lower() for c in category] if category else []

    # === Weighted components ===
    preferred_country_match = country in [c.lower() for c in user_profile['preferred_countries']]
    preferred_category_match = any(cat in [c.lower() for c in user_profile['preferred_categories']] for cat in category)

    # w1: Explicit preferences
    if preferred_country_match:
        score += w1 * 5
    if preferred_category_match:
        score += w1 * 5

    # w2: Behavior
    score += w2 * user_profile['liked_countries'].get(country, 0)
    score += w2 * sum(user_profile['liked_categories'].get(cat, 0) for cat in category)

    time_spent = time_spent_map.get(article_id, 0)
    if time_spent > 900:
        score += w2 * 5
    elif time_spent > 600:
        score += w2 * 2

    # w3: NLP Similarity
    liked_titles = fetch_liked_titles(conn, user_id)
    if liked_titles:
        similarity = score_title_similarity(title, liked_titles)
        if similarity > 0.3:
            score += w3 * (similarity * 10)

    return {'article_id': article_id, 'title': title, 'score': score}