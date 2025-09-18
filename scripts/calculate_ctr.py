# scripts/calculate_ctr.py

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.connection import get_connection

def calculate_ctr():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT scoring_config_id,
               COUNT(*) FILTER (WHERE clicked = TRUE)::FLOAT / COUNT(*) AS ctr,
               COUNT(*) AS total
        FROM recommendation_logs
        GROUP BY scoring_config_id
        ORDER BY ctr DESC
    """)

    results = cur.fetchall()
    print("📊 CTR Results:")
    for config_id, ctr, total in results:
        print(f"• Config {config_id}: CTR = {ctr:.2f} ({total} recommendations)")

    conn.close()


if __name__ == "__main__":
    calculate_ctr()