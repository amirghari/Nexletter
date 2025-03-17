import psycopg2
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# ========================
# Configuration Variables
# ========================

# NewsData.io API configuration
API_KEY = os.getenv('API_KEY')  # Get from .env file
if not API_KEY:
    raise ValueError("API_KEY environment variable is not set. Please check your .env file.")
API_URL = f'https://newsdata.io/api/1/news?apikey={API_KEY}&language=en'

# PostgreSQL configuration
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Verify all required environment variables are set
if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    raise ValueError("Database configuration environment variables are missing. Please check your .env file.")

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
        language TEXT,
        image_url TEXT
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
    INSERT INTO articles (title, content, link, pub_date, source, description, country, category, language, image_url)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    with conn.cursor() as cur:
        for article in articles:
            try:
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
                        print(f"Could not parse date: {pub_date_raw}")
                        pub_date = None
                
                source = article.get('source_id')
                description = article.get('description')
                country = article.get('country', [])
                category = article.get('category', [])  
                language = article.get('language')
                image = article.get('image_url')
                # Print debug information
                print(f"Inserting article: {title[:30]}...")
                
                cur.execute(insert_query, (
                    title,
                    content,
                    link,
                    pub_date,
                    source,
                    description,
                    country,
                    category if isinstance(category, list) else [],
                    language,
                    image
                ))
            except Exception as e:
                print(f"Error inserting article: {str(e)}")
                continue
        
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