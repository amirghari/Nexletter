from .queries import FETCH_TIME_SPENT

def fetch_time_spent(conn, user_id):
    with conn.cursor() as cur:
        cur.execute(FETCH_TIME_SPENT, (user_id,))
        return dict(cur.fetchall())