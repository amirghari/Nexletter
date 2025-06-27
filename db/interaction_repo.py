from .queries import FETCH_TIME_SPENT

def fetch_time_spent(conn, user_id):
    with conn.cursor() as cur:
        cur.execute(FETCH_TIME_SPENT, (user_id,))
        return dict(cur.fetchall())
    
def insert_interaction(conn, user_id, article_id, interaction_type, time_spent=0):
    """
    Insert a new interaction into the interactions table.
    """
    query = """
        INSERT INTO interactions (user_id, article_id, interaction_type, time_spent)
        VALUES (%s, %s, %s, %s)
    """
    with conn.cursor() as cur:
        cur.execute(query, (user_id, article_id, interaction_type, time_spent))
        conn.commit()