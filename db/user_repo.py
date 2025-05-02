from .queries import FETCH_USER_PROFILE

def fetch_user_profile(conn, user_id):
    with conn.cursor() as cur:
        cur.execute(FETCH_USER_PROFILE, (user_id,))
        row = cur.fetchone()
        if row:
            return {
                'preferred_categories': row[0] or [],
                'preferred_countries': row[1] or [],
                'liked_categories': row[2] or {},
                'liked_countries': row[3] or {}
            }
        return None