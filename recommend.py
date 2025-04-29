import psycopg2
from dotenv import load_dotenv
import os
import json

load_dotenv()

# ========================
# Configuration
# ========================
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# ========================
# Helper Functions
# ========================

def fetch_user_profile(conn, user_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT preferred_categories, preferred_countries, liked_categories, liked_countries
            FROM users
            WHERE id = %s
        """, (user_id,))
        row = cur.fetchone()
        if row:
            return {
                'preferred_categories': row[0] or [],
                'preferred_countries': row[1] or [],
                'liked_categories': json.loads(row[2]) if row[2] else {},
                'liked_countries': json.loads(row[3]) if row[3] else {}
            }
        return None

def fetch_articles(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, title, country, category
            FROM articles
        """)
        return cur.fetchall()

def fetch_time_spent(conn, user_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT article_id, time_spent
            FROM interactions
            WHERE user_id = %s
        """, (user_id,))
        return dict(cur.fetchall())

def normalize_country_string(country):
    if country and country.startswith('{') and country.endswith('}'):
        return country.strip('{}').replace('"', '').split(',')[0].strip().lower()
    return country.lower() if country else ""

def calculate_score(article, user_profile, time_spent_map):
    article_id, title, country, category = article
    score = 0

    # Normalize fields
    country = normalize_country_string(country)
    category = [c.lower() for c in category] if category else []

    # Preferred Country and Category (each +5)
    if country in [c.lower() for c in user_profile['preferred_countries']]:
        score += 5
    if any(cat in [c.lower() for c in user_profile['preferred_categories']] for cat in category):
        score += 5

    # Liked Country and Category (add like values)
    score += int(user_profile['liked_countries'].get(country, 0))
    for cat in category:
        score += int(user_profile['liked_categories'].get(cat, 0))

    # Time Spent Bonus
    time_spent = time_spent_map.get(article_id, 0)
    if time_spent > 900:
        score += 5
    elif time_spent > 600:
        score += 2

    return {'article_id': article_id, 'title': title, 'score': score}

def recommend_articles(conn, user_id, limit=50):
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

# ========================
# Main
# ========================

def main():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("Connected to PostgreSQL.")
    except Exception as e:
        print("Database connection failed:", e)
        return

    user_id = 1
    recommendations = recommend_articles(conn, user_id)

    print(json.dumps(recommendations, indent=4))
    conn.close()

if __name__ == '__main__':
    main()
