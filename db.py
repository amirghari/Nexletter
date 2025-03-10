import psycopg2
import requests
from datetime import datetime

# ========================
# Configuration Variables
# ========================

# NewsData.io API configuration
API_KEY = 'pub_73836cfc74f6119ac154819b00afe2285b9e3'
API_URL = f'https://newsdata.io/api/1/news?apikey={API_KEY}&language=en'

# PostgreSQL configuration
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'nexletter'
DB_USER = 'root'
DB_PASSWORD = 'Ag9776Hg0483'            

# ========================
# Database Functions
# ========================

def create_table(conn):
    """
    Create the articles table if it does not exist.
    """
    create_table_query = """    
    CREATE TABLE IF NOT EXISTS articles (
        id SERIAL PRIMARY KEY,
        title TEXT,
        content TEXT,
        link TEXT,
        pub_date TIMESTAMP,
        source TEXT,
        description TEXT,
        country TEXT,
        category TEXT[],
        language TEXT
    );
    """
    with conn.cursor() as cur:
        cur.execute(create_table_query)
        conn.commit()
    print("Table 'articles' is ready.")

# ========================
# API Data Fetch Function
# ========================

def fetch_articles():
    """
    Fetch articles from NewsData.io API.
    """
    response = requests.get(API_URL)
    if response.status_code == 200:
        data = response.json()
        articles = data.get('results', [])
        print(f"Fetched {len(articles)} articles from the API.")
        return articles
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return []

# ========================
# Data Insertion Function
# ========================

def insert_articles(conn, articles):
    """
    Insert articles into the database.
    """
    insert_query = """
    INSERT INTO articles (title, content, link, pub_date, source, description, country, category, language)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    with conn.cursor() as cur:
        for article in articles:
            title = article.get('title')
            content = article.get('content')
            link = article.get('link')
            pub_date_raw = article.get('pubDate')
            # Convert pub_date to a Python datetime object if available
            try:
                # Try parsing with format from API response: "2025-03-09 23:44:00"
                pub_date = datetime.strptime(pub_date_raw, "%Y-%m-%d %H:%M:%S") if pub_date_raw else None
            except ValueError:
                try:
                    # Fall back to alternative format if needed: "Mon, 09 Mar 2025 23:44:00 GMT"
                    pub_date = datetime.strptime(pub_date_raw, "%a, %d %b %Y %H:%M:%S %Z") if pub_date_raw else None
                except ValueError:
                    # If parsing fails, store None
                    print(f"Could not parse date: {pub_date_raw}")
                    pub_date = None
            source = article.get('source_id')
            description = article.get('description')
            country = article.get('country')
            # Category might be a list; store as array in Postgres
            category = article.get('category')
            language = article.get('language')
            
            cur.execute(insert_query, (title, content, link, pub_date, source, description, country, category, language))
        conn.commit()
    print(f"Inserted {len(articles)} articles into the database.")

# ========================
# Main Execution Flow
# ========================

def main():
    # Connect to PostgreSQL
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print("Connected to PostgreSQL database.")
    except Exception as e:
        print("Unable to connect to the database.")
        print(e)
        return

    # Create articles table if not exists
    create_table(conn)

    # Fetch articles from NewsData.io API
    articles = fetch_articles()

    # Insert articles into the database if available
    if articles:
        insert_articles(conn, articles)
    else:
        print("No articles were fetched from the API.")

    # Close the database connection
    conn.close()
    print("Database connection closed.")

if __name__ == '__main__':
    main()