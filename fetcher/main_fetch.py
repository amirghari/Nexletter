from newsdata_client import fetch_articles_from_api
from save_articles import insert_articles
from db.connection import get_connection

def main():
    articles = fetch_articles_from_api()
    if not articles:
        print("No articles fetched.")
        return

    conn = get_connection()
    insert_articles(conn, articles)
    conn.close()
    print("Articles saved to DB.")

if __name__ == "__main__":
    main()