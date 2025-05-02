# queries.py
FETCH_USER_PROFILE = """
    SELECT preferred_categories, preferred_countries, liked_categories, liked_countries
    FROM users
    WHERE id = %s
"""

FETCH_ARTICLES = """
    SELECT id, title, country, category
    FROM articles
"""

FETCH_TIME_SPENT = """
    SELECT article_id, time_spent
    FROM interactions
    WHERE user_id = %s
"""