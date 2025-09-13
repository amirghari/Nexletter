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

    # ✅ Automatically get the best-performing config
    scoring_config_id = get_best_scoring_config(conn)

    # Fetch weights for that config
    with conn.cursor() as cur:
        cur.execute("""
            SELECT w1, w2, w3 FROM scoring_configurations WHERE id = %s
        """, (scoring_config_id,))
        w1, w2, w3 = cur.fetchone()

    # Score articles using that config
    scored = [
        calculate_score(article, user_profile, time_spent_map, conn, user_id, w1, w2, w3)
        for article in articles
    ]
    scored.sort(key=lambda x: x['score'], reverse=True)
    top_articles = scored[:limit]

    # Log recommendations for evaluation
    log_recommendations(conn, user_id, top_articles, scoring_config_id)

    return top_articles

def ensure_scoring_config(conn, w1, w2, w3):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO scoring_configurations (w1, w2, w3)
            VALUES (%s, %s, %s)
            ON CONFLICT (w1, w2, w3) DO NOTHING
            RETURNING id;
        """, (w1, w2, w3))
        result = cur.fetchone()

        if result:
            return result[0]  # Newly inserted ID
        else:
            cur.execute("""
                SELECT id FROM scoring_configurations WHERE w1 = %s AND w2 = %s AND w3 = %s;
            """, (w1, w2, w3))
            return cur.fetchone()[0]

def log_recommendations(conn, user_id, articles, scoring_config_id):
    with conn.cursor() as cur:
        for article in articles:
            cur.execute("""
                INSERT INTO recommendation_logs (user_id, article_id, scoring_config_id)
                VALUES (%s, %s, %s)
            """, (user_id, article['article_id'], scoring_config_id))
    conn.commit()

def log_click(conn, user_id, article_id, scoring_config_id):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE recommendation_logs
            SET clicked = TRUE
            WHERE user_id = %s AND article_id = %s AND scoring_config_id = %s
        """, (user_id, article_id, scoring_config_id))
    conn.commit()

def get_best_scoring_config(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                scoring_config_id,
                COUNT(*) FILTER (WHERE clicked = TRUE) AS clicks,
                COUNT(*) AS total,
                (COUNT(*) FILTER (WHERE clicked = TRUE)::FLOAT / NULLIF(COUNT(*), 0)) AS ctr
            FROM recommendation_logs
            GROUP BY scoring_config_id
            ORDER BY ctr DESC
            LIMIT 1;
        """)
        result = cur.fetchone()
        if result:
            return result[0]  # scoring_config_id
        else:
            # Default fallback if no logs exist yet
            return ensure_scoring_config(conn, 0.4, 0.3, 0.3)