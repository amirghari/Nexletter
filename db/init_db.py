from connection import get_connection 
def create_tables(conn):
    with conn.cursor() as cur:

        # Articles Table
        cur.execute("""
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
        """)

        # Users Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                preferred_categories TEXT[],
                preferred_countries TEXT[],
                liked_categories JSONB DEFAULT '{}'::JSONB,
                liked_countries JSONB DEFAULT '{}'::JSONB
            );
        """)

        # Interactions Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id SERIAL PRIMARY KEY,
                user_id INT NOT NULL REFERENCES users(id),
                article_id INT NOT NULL REFERENCES articles(id),
                interaction_type TEXT NOT NULL,
                time_spent INT DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Liked Titles Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS liked_titles (
                id SERIAL PRIMARY KEY,
                user_id INT NOT NULL REFERENCES users(id),
                title TEXT NOT NULL
            );
        """)

        # Scoring Configurations Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scoring_configurations (
                id SERIAL PRIMARY KEY,
                w1 FLOAT NOT NULL,
                w2 FLOAT NOT NULL,
                w3 FLOAT NOT NULL,
                UNIQUE(w1, w2, w3)
            );
        """)

        # Recommendation Logs Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recommendation_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
                scoring_config_id INTEGER REFERENCES scoring_configurations(id) ON DELETE CASCADE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                clicked BOOLEAN DEFAULT FALSE
            );
        """)

        conn.commit()
        print("✅ All tables are ensured.")


if __name__ == "__main__":
    conn = get_connection()
    create_tables(conn)
    conn.close()