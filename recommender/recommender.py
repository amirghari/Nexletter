import os
from datetime import datetime
from typing import Any, Dict, List, Tuple, Optional

from db.user_repo import fetch_user_profile
from db.article_repo import fetch_articles
from db.interaction_repo import fetch_time_spent

# ✅ use your scorer
from recommender.scorer import calculate_score


def get_best_scoring_config(conn) -> Optional[int]:
    """
    Return the scoring_configurations.id with the best observed CTR.
    Falls back to the most-recent active config if no logs exist.
    """
    with conn.cursor() as cur:
        # Try best-by-CTR first
        cur.execute("""
            SELECT scoring_config_id
            FROM recommendation_logs
            WHERE scoring_config_id IS NOT NULL
            GROUP BY scoring_config_id
            ORDER BY (COUNT(*) FILTER (WHERE clicked)=0) = TRUE,  -- avoid div by zero edge
                     (COUNT(*) FILTER (WHERE clicked))::float / NULLIF(COUNT(*), 0) DESC
            LIMIT 1;
        """)
        row = cur.fetchone()
        if row and row[0] is not None:
            return row[0]

        # Else most recent active
        cur.execute("""
            SELECT id
            FROM scoring_configurations
            WHERE is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 1;
        """)
        row = cur.fetchone()
        return row[0] if row else None


def get_active_weights(conn) -> Tuple[float, float, float, Optional[int]]:
    """
    Fetch (w1, w2, w3, config_id) from the most recent active config.
    Fallback to (1.0, 1.0, 1.0, None) if table is empty.
    """
    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT id, w1, w2, w3
                FROM scoring_configurations
                WHERE is_active = TRUE
                ORDER BY created_at DESC
                LIMIT 1;
            """)
            row = cur.fetchone()
            if row:
                config_id, w1, w2, w3 = row
                return float(w1), float(w2), float(w3), int(config_id)
        except Exception:
            pass
    return 1.0, 1.0, 1.0, None


def _row_to_score_tuple(row: Any) -> Tuple[int, str, Optional[str], Optional[List[str]]]:
    """
    Normalize an article row (dict or tuple) to (id, title, country, category_list)
    in the exact order your scorer expects.
    """
    if isinstance(row, dict):
        art_id = row.get("id")
        title = row.get("title")
        country = row.get("country")
        category = row.get("category")
    else:
        # Assume tuple order commonly used in repos: (id, title, country, category, ...)
        # Safely slice first 4 fields
        art_id = row[0]
        title = row[1]
        country = row[2] if len(row) > 2 else None
        category = row[3] if len(row) > 3 else None

    # Ensure category is a list[str] (handles TEXT[] or single TEXT)
    if category is None:
        cat_list: Optional[List[str]] = None
    elif isinstance(category, (list, tuple)):
        cat_list = [str(c) for c in category]
    else:
        cat_list = [str(category)]

    return int(art_id), str(title), (str(country) if country else None), cat_list


def recommend_articles(conn, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    End-to-end recommender:
      1) fetch user profile, articles, time spent
      2) get weights
      3) score with your calculate_score()
      4) return top-N, each with score injected:
         { article_id, title, country, category, score }
    """
    user_profile = fetch_user_profile(conn, user_id)
    if not user_profile:
        return []

    articles = fetch_articles(conn)
    time_spent_map = fetch_time_spent(conn, user_id)
    w1, w2, w3, _ = get_active_weights(conn)

    scored: List[Dict[str, Any]] = []
    for row in articles:
        art_id, title, country, category = _row_to_score_tuple(row)
        # Your scorer expects a 4-tuple
        scored_item = calculate_score(
            (art_id, title, country, category),
            user_profile,
            time_spent_map,
            conn,
            user_id,
            w1, w2, w3
        )
        # Ensure we also include basic article fields to print/log later
        scored_item.setdefault("article_id", art_id)
        scored_item.setdefault("title", title)
        # Try to pass through country/category so scripts can show them
        scored_item.setdefault("country", country)
        scored_item.setdefault("category", category or [])
        scored.append(scored_item)

    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    return scored[:limit]


def log_recommendations(conn, user_id: int, articles: List[Dict[str, Any]], scoring_config_id: Optional[int]) -> None:
    """
    Insert shown impressions into recommendation_logs (clicked defaults to FALSE).
    """
    with conn.cursor() as cur:
        for a in articles:
            cur.execute("""
                INSERT INTO recommendation_logs (user_id, article_id, scoring_config_id, clicked, timestamp)
                VALUES (%s, %s, %s, FALSE, %s)
            """, (user_id, a["article_id"], scoring_config_id, datetime.utcnow()))
    conn.commit()


def log_click(conn, user_id: int, article_id: int, scoring_config_id: Optional[int]) -> None:
    """
    Mark a recommendation as clicked. If no prior impression row exists, insert one as clicked.
    """
    with conn.cursor() as cur:
        # Try to update an existing impression
        cur.execute("""
            UPDATE recommendation_logs
            SET clicked = TRUE
            WHERE user_id = %s AND article_id = %s
              AND (scoring_config_id = %s OR (scoring_config_id IS NULL AND %s IS NULL))
            RETURNING id;
        """, (user_id, article_id, scoring_config_id, scoring_config_id))
        if cur.rowcount == 0:
            # No impression existed — insert as clicked
            cur.execute("""
                INSERT INTO recommendation_logs (user_id, article_id, scoring_config_id, clicked, timestamp)
                VALUES (%s, %s, %s, TRUE, %s)
            """, (user_id, article_id, scoring_config_id, datetime.utcnow()))
    conn.commit()