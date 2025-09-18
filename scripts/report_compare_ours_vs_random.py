import sys, os
from typing import Dict, List, Tuple
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.connection import get_connection
from psycopg2.extras import RealDictCursor

# ====== USERS (labels → DB IDs) ======
USER_LABEL_TO_ID = {
    1: 12,  # U1
    2: 13,  # U2
    3: 14,  # U3
    4: 15,  # U4
    5: 16,  # U5
}

# ====== RANDOM BASELINE manual click positions (1-based in its random top-10) ======
RANDOM_CLICK_POSITIONS: Dict[int, List[int]] = {
    1: [10, 2, 4],           # User 1
    2: [3, 7],               # User 2
    4: [1, 3, 4, 7, 10],     # User 4
    3: [4, 7, 10],           # User 3
    5: [2, 4, 5, 10, 6],     # User 5
}
ARTICLES_PER_USER = 10  # you said 10 random shown per user

def fetch_ours_last10(conn, user_id: int) -> Tuple[int, int]:
    """
    Return (impressions, clicks) for the user's last 10 OUR recommender impressions.
    OUR = rows with scoring_config_id IS NOT NULL.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT clicked
            FROM recommendation_logs
            WHERE user_id = %s
              AND scoring_config_id IS NOT NULL
            ORDER BY timestamp DESC, id DESC
            LIMIT 10
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        impr = len(rows)
        clicks = sum(1 for r in rows if r.get("clicked"))
        return impr, clicks

def compute_random_metrics() -> Tuple[Dict[int, Tuple[int,int]], int, int]:
    """
    Compute per-user and total (impressions, clicks) for the RANDOM baseline
    from manual click positions. Assumes 10 shown per user.
    Returns (per_user_dict, total_impr, total_clicks)
    """
    per_user = {}
    total_impr = 0
    total_clicks = 0
    for label in sorted(USER_LABEL_TO_ID.keys()):
        positions = RANDOM_CLICK_POSITIONS.get(label, [])
        impr = ARTICLES_PER_USER
        clicks = len(positions)
        per_user[label] = (impr, clicks)
        total_impr += impr
        total_clicks += clicks
    return per_user, total_impr, total_clicks

def fmt_pct(numer: int, denom: int) -> str:
    return f"{(numer/denom):.2f}" if denom else "0.00"

def main():
    conn = get_connection()

    # ----- OUR recommender (from DB) -----
    print("🔍 Reading OUR recommender results from DB (last 10 per user) ...\n")
    ours_per_user = {}
    ours_total_impr = 0
    ours_total_clicks = 0

    for label in sorted(USER_LABEL_TO_ID.keys()):
        user_id = USER_LABEL_TO_ID[label]
        impr, clicks = fetch_ours_last10(conn, user_id)
        ours_per_user[label] = (impr, clicks)
        ours_total_impr += impr
        ours_total_clicks += clicks

    # ----- RANDOM baseline (from manual positions) -----
    print("🧪 Using manual RANDOM baseline clicks you provided ...\n")
    random_per_user, random_total_impr, random_total_clicks = compute_random_metrics()

    conn.close()

    # ----- Pretty report -----
    def print_section(title: str, per_user: Dict[int, Tuple[int,int]], total_impr: int, total_clicks: int):
        print(title)
        print("-" * 62)
        print(f"{'User':<6}{'Impr':>8}{'Clicks':>10}{'CTR':>10}")
        print("-" * 62)
        for label in sorted(USER_LABEL_TO_ID.keys()):
            impr, clicks = per_user.get(label, (0,0))
            ctr = fmt_pct(clicks, impr) if impr else "0.00"
            print(f"{('U'+str(label)):<6}{impr:>8}{clicks:>10}{ctr:>10}")
        print("-" * 62)
        total_ctr = fmt_pct(total_clicks, total_impr) if total_impr else "0.00"
        print(f"{'TOTAL':<6}{total_impr:>8}{total_clicks:>10}{total_ctr:>10}")
        print()

    print_section("📊 OUR Recommender (from DB logs)", ours_per_user, ours_total_impr, ours_total_clicks)
    print_section("🎲 RANDOM Baseline (manual clicks, 10 shown/user)", random_per_user, random_total_impr, random_total_clicks)

    # ----- Comparison summary -----
    ours_ctr = (ours_total_clicks / ours_total_impr) if ours_total_impr else 0.0
    rnd_ctr  = (random_total_clicks / random_total_impr) if random_total_impr else 0.0

    print("============== COMPARISON ==============")
    print(f"{'Metric':<14}{'Ours':>12}{'Random':>12}")
    print("----------------------------------------")
    print(f"{'Impressions':<14}{ours_total_impr:>12}{random_total_impr:>12}")
    print(f"{'Clicks':<14}{ours_total_clicks:>12}{random_total_clicks:>12}")
    print(f"{'CTR':<14}{ours_ctr:>12.2f}{rnd_ctr:>12.2f}")
    print("========================================")

if __name__ == "__main__":
    main()