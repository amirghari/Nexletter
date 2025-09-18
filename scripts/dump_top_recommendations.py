import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.connection import get_connection
from recommender.recommender import recommend_articles, get_best_scoring_config

USERS = [12, 13, 14, 15, 16]  # U1–U5

def dump_top_recommendations():
    conn = get_connection()

    scoring_config_id = get_best_scoring_config(conn)
    print(f"✅ Using scoring config ID: {scoring_config_id}\n")

    for user_id in USERS:
        print(f"📌 Top recommendations for User {user_id}:\n")
        try:
            recs = recommend_articles(conn, user_id, limit=10)
            if not recs:
                print("  (no recommendations)\n")
                continue

            for i, a in enumerate(recs,  start=1):
                aid = a.get("article_id")
                title = a.get("title", "")
                score = a.get("score", 0.0)
                country = a.get("country") or ""
                cats = a.get("category") or []
                cats_txt = ", ".join(cats) if isinstance(cats, (list, tuple)) else str(cats)

                print(f"{i:2d}. [AID:{aid}] score={score:.2f} | country={country} | cats=[{cats_txt}]")
                print(f"    {title}")
            print("")  # blank line
        except Exception as e:
            print(f"❌ Error for user {user_id}: {e}\n")

    conn.close()

if __name__ == "__main__":
    dump_top_recommendations()