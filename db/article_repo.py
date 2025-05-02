from .queries import FETCH_ARTICLES

def fetch_articles(conn):
    with conn.cursor() as cur:
        cur.execute(FETCH_ARTICLES)
        return cur.fetchall()
    
