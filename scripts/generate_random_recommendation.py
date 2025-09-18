# scripts/generate_random_recommendations.py
# Pure random sampler: NO DB WRITES. Prints 10 random articles per user.

import sys, os, random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.connection import get_connection
from psycopg2.extras import RealDictCursor

# ===== CONFIG =====
# Label -> DB user_id (for labeling only; we don't write anything)
USER_LABEL_TO_ID = {
    1: 12,  # U1
    2: 13,  # U2
    3: 14,  # U3
    4: 15,  # U4
    5: 16,  # U5
}

ARTICLES_POOL_LIMIT = 150  # newest N articles as the pool
ARTICLES_PER_USER   = 10   # random picks per user
RANDOM_SEED = None         # set to an int for reproducible picks, e.g., 42

def fetch_pool(conn, pool_limit=ARTICLES_POOL_LIMIT):
    """
    Return newest `pool_limit` articles as list of dicts:
    {id, title, country, category}
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT id, title, country, category
            FROM articles
            ORDER BY pub_date DESC NULLS LAST, id DESC
            LIMIT %s;
        """, (pool_limit,))
        return cur.fetchall()

def pretty_categories(cat_val):
    """
    Ensure categories print nicely whether TEXT[] or string/null.
    """
    if cat_val is None:
        return ""
    if isinstance(cat_val, (list, tuple)):
        return ", ".join([str(c) for c in cat_val])
    return str(cat_val)

def main():
    # Optional reproducibility
    if RANDOM_SEED is not None:
        random.seed(RANDOM_SEED)

    conn = get_connection()
    pool = fetch_pool(conn, ARTICLES_POOL_LIMIT)
    conn.close()

    if not pool:
        print("⚠️ No articles found. Aborting.")
        return

    print(f"🎲 Random pool size: {len(pool)} (newest first)\n")

    pool_ids = [row["id"] for row in pool]
    by_id = {row["id"]: row for row in pool}

    for label in sorted(USER_LABEL_TO_ID.keys()):
        user_id = USER_LABEL_TO_ID[label]
        print(f"📌 RANDOM picks for User {label} (db_id={user_id})")

        # Totally random, independent per user (duplicates across users allowed)
        k = min(ARTICLES_PER_USER, len(pool_ids))
        chosen = random.sample(pool_ids, k=k)

        for idx, aid in enumerate(chosen, start=1):
            rec = by_id.get(aid, {})
            title = rec.get("title") or "(no title)"
            country = rec.get("country") or ""
            cats_str = pretty_categories(rec.get("category"))
            print(f"  {idx}. [Article ID: {aid}] {title} — Country: {country} — Categories: [{cats_str}]")
        print("")  # spacer

    print("✅ Random baseline lists generated (no DB writes).")

if __name__ == "__main__":
    main()