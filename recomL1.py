import psycopg2
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

def get_recommendations(conn, user_country, user_interests, limit=10):
    """
    Retrieve articles from the database sorted by:
    1. Country match (articles matching user's country come first)
    2. Category match (articles that match user's interests come next)

    :param conn: psycopg2 connection object
    :param user_country: User's country as a string (e.g., "US")
    :param user_interests: List of user's newsletter interests (e.g., ["technology", "business"])
    :param limit: Maximum number of recommendations to return
    :return: List of recommended article rows
    """
    # This query calculates a priority based on:
    # - country_priority: 1 if the article's country matches the user's country, else 2.
    # - category_priority: 1 if the article's category overlaps with the user's interests, else 2.
    # We order by these priorities, so country match always comes first.
    query = """
    SELECT *,
           CASE WHEN country = %s THEN 1 ELSE 2 END AS country_priority,
           CASE WHEN category && %s THEN 1 ELSE 2 END AS category_priority
    FROM articles
    ORDER BY country_priority, category_priority
    LIMIT %s;
    """
    with conn.cursor() as cur:
        cur.execute(query, (user_country, user_interests, limit))
        recommendations = cur.fetchall()
    return recommendations

# Example usage:
if __name__ == '__main__':
    # Assuming your connection setup is similar to the one in your main() function.
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("Connected to PostgreSQL database.")
    except Exception as e:
        print("Unable to connect to the database.")
        print(e)
        exit(1)

    # For demonstration, define a sample user profile:
    user_country = "US"  # Example: user is located in the United States
    user_interests = ["technology", "business"]  # The categories the user is interested in

    recommendations = get_recommendations(conn, user_country, user_interests, limit=10)
    for rec in recommendations:
        print(rec)

    conn.close()