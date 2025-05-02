def normalize_country_string(country):
    if country and country.startswith('{') and country.endswith('}'):
        return country.strip('{}').replace('"', '').split(',')[0].strip().lower()
    return country.lower() if country else ""

def calculate_score(article, user_profile, time_spent_map):
    article_id, title, country, category = article
    score = 0

    country = normalize_country_string(country)
    category = [c.lower() for c in category] if category else []

    if country in [c.lower() for c in user_profile['preferred_countries']]:
        score += 5
    if any(cat in [c.lower() for c in user_profile['preferred_categories']] for cat in category):
        score += 5

    score += int(user_profile['liked_countries'].get(country, 0))
    for cat in category:
        score += int(user_profile['liked_categories'].get(cat, 0))

    time_spent = time_spent_map.get(article_id, 0)
    if time_spent > 900:
        score += 5
    elif time_spent > 600:
        score += 2

    return {'article_id': article_id, 'title': title, 'score': score}