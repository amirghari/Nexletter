from db.connection import get_connection
from db.interaction_repo import insert_interaction
from db.article_repo import fetch_articles
from nlp.liked_title_repo import save_liked_title

def main():
    conn = get_connection()

    user_id = 1
    article_id = 109  # <-- Pick one from `articles` table
    title = "Crypto Short Sellers Took A Hit Following De-escalation Of Conflict Between Israel and Iran"

    # Insert "liked" interaction
    insert_interaction(conn, user_id, article_id, "liked", time_spent=120)

    # Save title to liked_titles
    save_liked_title(conn, user_id, title)

    conn.close()

if __name__ == "__main__":
    main()