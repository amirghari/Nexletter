import random
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.connection import get_connection
import psycopg2.extras

def merge_json_count(existing, key):
    """Returns updated JSONB object with key count incremented."""
    if existing is None:
        return {key: 1}
    updated = dict(existing)
    updated[key] = updated.get(key, 0) + 1
    return updated

def insert_realistic_interactions_with_likes():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Fetch users
    cur.execute("SELECT id, preferred_categories, preferred_countries FROM users")
    users = cur.fetchall()

    # Fetch articles
    cur.execute("SELECT id, country, category, title FROM articles")
    articles = cur.fetchall()
    article_data = [
        {
            "id": a["id"],
            "country": a["country"].lower().strip() if a["country"] else "",
            "category": [c.strip().lower() for c in a["category"]] if a["category"] else [],
            "title": a["title"]
        }
        for a in articles
    ]

    all_article_ids = [a["id"] for a in article_data]

    for user in users:
        user_id = user["id"]
        preferred_categories = [c.strip().lower() for c in user["preferred_categories"] or []]
        preferred_countries = [c.strip().lower() for c in user["preferred_countries"] or []]

        # Find matching articles
        matching_articles = [
            a for a in article_data
            if any(cat in a["category"] for cat in preferred_categories) or a["country"] in preferred_countries
        ]

        # Fallback logic if less than 3 matches
        selected_articles = matching_articles[:3] if len(matching_articles) >= 3 else matching_articles.copy()
        if len(selected_articles) < 3:
            remaining = [a for a in article_data if a not in selected_articles]
            while len(selected_articles) < 3 and remaining:
                selected_articles.append(random.choice(remaining))

        for article in selected_articles:
            # Insert into interactions
            cur.execute("""
                INSERT INTO interactions (user_id, article_id, interaction_type, time_spent, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                user_id,
                article["id"],
                "liked",
                random.choice([15, 18, 25]),
                datetime.now() - timedelta(days=random.randint(1, 60))
            ))

            # Insert into liked_titles
            cur.execute("""
                INSERT INTO liked_titles (user_id, title)
                VALUES (%s, %s)
            """, (user_id, article["title"]))

            # Get current liked_categories & liked_countries
            cur.execute("SELECT liked_categories, liked_countries FROM users WHERE id = %s", (user_id,))
            current = cur.fetchone()
            liked_countries = current["liked_countries"] or {}
            liked_categories = current["liked_categories"] or {}

            # Update liked_countries
            if article["country"]:
                liked_countries = merge_json_count(liked_countries, article["country"])

            # Update liked_categories
            for cat in article["category"]:
                liked_categories = merge_json_count(liked_categories, cat)

            # Update user row
            cur.execute("""
                UPDATE users
                SET liked_categories = %s, liked_countries = %s
                WHERE id = %s
            """, (
                psycopg2.extras.Json(liked_categories),
                psycopg2.extras.Json(liked_countries),
                user_id
            ))

    conn.commit()
    conn.close()
    print("✅ Interactions, liked_titles, and liked_categories/countries inserted and updated.")

if __name__ == "__main__":
    insert_realistic_interactions_with_likes()