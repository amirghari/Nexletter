import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.connection import get_connection
from collections import defaultdict

def evaluate_ctr_and_precision():
    conn = get_connection()
    cur = conn.cursor()

    # Fetch system recommendations
    cur.execute("""
        SELECT user_id, article_id, clicked 
        FROM recommendation_logs 
        WHERE scoring_config_id IS NOT NULL
    """)
    system_logs = cur.fetchall()

    # Fetch random baseline recommendations
    cur.execute("""
        SELECT user_id, article_id, clicked 
        FROM recommendation_logs 
        WHERE scoring_config_id IS NULL
    """)
    random_logs = cur.fetchall()

    conn.close()

    def calc_ctr(logs):
        if not logs:
            return 0.0
        total = len(logs)
        clicks = sum(1 for row in logs if row[2])
        return round(clicks / total, 2)

    def calc_precision_at_n(logs, N=5):
        user_recs = defaultdict(list)
        for user_id, article_id, clicked in logs:
            user_recs[user_id].append(clicked)

        precisions = []
        for user_id, clicks in user_recs.items():
            top_n = clicks[:N]
            precision = sum(top_n) / len(top_n) if top_n else 0.0
            precisions.append(precision)

        return round(sum(precisions) / len(precisions), 2) if precisions else 0.0

    system_ctr = calc_ctr(system_logs)
    random_ctr = calc_ctr(random_logs)

    system_precision = calc_precision_at_n(system_logs)
    random_precision = calc_precision_at_n(random_logs)

    # Output comparison table
    print("\n📊 Evaluation Results:")
    print(f"{'Metric':<20}{'Our System':<15}{'Random Baseline'}")
    print(f"{'-'*50}")
    print(f"{'CTR':<20}{system_ctr:<15}{random_ctr}")
    print(f"{'Precision@5':<20}{system_precision:<15}{random_precision}")

if __name__ == "__main__":
    evaluate_ctr_and_precision()