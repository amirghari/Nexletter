import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.connection import get_connection
from recommender.recommender import (
    recommend_articles,
    get_best_scoring_config,
    log_recommendations,
    log_click,
)

# --- MAPPING ---
# Assuming your "User 1..5" are U1..U5 with DB IDs 12..16 respectively.
# If your IDs differ, just change this map.
USER_LABEL_TO_ID = {
    1: 12,  # U1
    2: 13,  # U2
    3: 14,  # U3
    4: 15,  # U4
    5: 16,  # U5
}

# Positions are 1-based indexes in the top-10 list (exactly as you provided)
CLICK_POSITIONS = {
    1: [1, 2, 3, 7, 9],           # User 1
    2: [1, 2, 3, 4, 5, 7],        # User 2
    3: [1, 3, 4, 7, 8, 9],        # User 3
    4: [1, 2, 3, 4, 5, 8, 9],     # User 4
    5: [1, 2, 5, 6, 10],          # User 5
}

def ensure_config(conn):
    """Get an active scoring config id; if none, fall back to any, else insert a default (1,1,1)."""
    sc_id = get_best_scoring_config(conn)
    if sc_id:
        return sc_id

    with conn.cursor() as cur:
        cur.execute("SELECT id FROM scoring_configurations ORDER BY created_at DESC NULLS LAST, id DESC LIMIT 1;")
        row = cur.fetchone()
        if row:
            return row[0]

        # Insert default
        cur.execute("""
            INSERT INTO scoring_configurations (w1, w2, w3, is_active)
            VALUES (1.0, 1.0, 1.0, TRUE)
            RETURNING id;
        """)
        sc_id = cur.fetchone()[0]
        conn.commit()
        return sc_id

def _extract_article_id(rec):
    """
    Be tolerant of different shapes:
    - dict from your recommender: {'article_id', 'title', 'score', 'country', 'category'}
    - dict from other code:       {'id', ...}
    - tuple from fetch:           (id, title, country, category)
    """
    if isinstance(rec, dict):
        return rec.get("article_id") or rec.get("id")
    if isinstance(rec, (list, tuple)) and len(rec) >= 1:
        return rec[0]
    return None

def main():
    conn = get_connection()

    scoring_config_id = ensure_config(conn)
    print(f"✅ Using scoring config ID: {scoring_config_id}\n")

    total_impressions = 0
    total_clicks = 0

    for user_label, user_id in USER_LABEL_TO_ID.items():
        print(f"📌 Processing User {user_label} (db_id={user_id})")

        # Get current top-10 recommendations using your recommender pipeline
        try:
            recs = recommend_articles(conn, user_id, limit=10)
        except Exception as e:
            print(f"  ❌ Failed to get recommendations: {e}")
            continue

        if not recs:
            print("  ⚠️ No recommendations returned; skipping.")
            continue

        # Ensure each rec has an article_id so log_recommendations works cleanly
        # If your log_recommendations expects dicts with 'article_id', create a safe copy.
        safe_recs = []
        for r in recs:
            aid = _extract_article_id(r)
            if aid is None:
                continue
            if isinstance(r, dict):
                safe_recs.append(r)
            else:
                # Make a minimal dict the logger understands
                safe_recs.append({"article_id": aid, "title": None, "score": None})

        if not safe_recs:
            print("  ⚠️ Could not normalize recommendations to article ids; skipping.")
            continue

        # Log the impressions first
        try:
            log_recommendations(conn, user_id, safe_recs, scoring_config_id)
            total_impressions += len(safe_recs)
            print(f"  🧾 Logged {len(safe_recs)} impressions.")
        except Exception as e:
            print(f"  ❌ Failed to log impressions: {e}")
            # If impressions fail, clicks won't update anything; continue to next user
            continue

        # Determine which positions to click for this user
        positions = CLICK_POSITIONS.get(user_label, [])
        clicked_ids = []
        for pos in positions:
            if 1 <= pos <= len(recs):
                aid = _extract_article_id(recs[pos - 1])
                if aid is not None:
                    clicked_ids.append(aid)
                else:
                    print(f"    ⚠️ Could not extract article_id at position {pos}; skipping.")
            else:
                print(f"    ⚠️ Position {pos} out of range (1..{len(recs)}); skipping.")

        # Update clicks
        clicked_ok = 0
        for aid in clicked_ids:
            try:
                log_click(conn, user_id, aid, scoring_config_id)
                clicked_ok += 1
            except Exception as e:
                print(f"    ❌ Failed to log click for article_id={aid}: {e}")

        total_clicks += clicked_ok
        print(f"  ✅ Logged {clicked_ok} clicks for user {user_label}.\n")

    conn.close()
    print("🎯 Done.")
    print(f"📈 Totals — impressions: {total_impressions}, clicks: {total_clicks}")

if __name__ == "__main__":
    main()