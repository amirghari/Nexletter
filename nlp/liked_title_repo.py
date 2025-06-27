def save_liked_title(conn, user_id, title):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO liked_titles (user_id, title)
            VALUES (%s, %s)
        """, (user_id, title))
        conn.commit()


def fetch_liked_titles(conn, user_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT title FROM liked_titles
            WHERE user_id = %s
        """, (user_id,))
        return [row[0] for row in cur.fetchall()]