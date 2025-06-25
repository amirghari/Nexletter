import psycopg2
from db.connection import get_connection

def insert_articles(conn, articles):
    query = """
    INSERT INTO articles (title, content, link, pub_date, source, description, country, category, language, image_url)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT DO NOTHING;
    """
    with conn.cursor() as cur:
        for article in articles:
            cur.execute(query, (
                article.get('title'),
                article.get('content'),
                article.get('link'),
                article.get('pubDate'),
                article.get('source_id'),
                article.get('description'),
                article.get('country'),
                article.get('category'),
                article.get('language'),
                article.get('image_url')
            ))
        conn.commit()