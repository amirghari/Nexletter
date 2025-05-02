import json
from db.connection import get_connection
from recommender.recommender import recommend_articles

def main():
    try:
        conn = get_connection()
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