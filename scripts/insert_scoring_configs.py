import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.connection import get_connection

def insert_configs():
    conn = get_connection()
    cur = conn.cursor()

    # List of weight combinations to insert
    configs = [
        (1.0, 1.0, 1.0),
        (2.0, 1.0, 1.0),
        (1.0, 2.0, 1.0),
        (1.0, 1.0, 2.0),
        (2.0, 2.0, 1.0),
        (2.0, 1.0, 2.0),
        (1.0, 2.0, 2.0),
        (3.0, 1.0, 1.0),
        (1.0, 3.0, 1.0),
        (1.0, 1.0, 3.0)
    ]

    for w1, w2, w3 in configs:
        cur.execute("""
            INSERT INTO scoring_configurations (w1, w2, w3, is_active)
            SELECT %s, %s, %s, TRUE
            WHERE NOT EXISTS (
                SELECT 1 FROM scoring_configurations
                WHERE w1 = %s AND w2 = %s AND w3 = %s
            );
        """, (w1, w2, w3, w1, w2, w3))

    conn.commit()
    conn.close()
    print("✅ Scoring configurations inserted with `is_active = TRUE`.")

if __name__ == "__main__":
    insert_configs()