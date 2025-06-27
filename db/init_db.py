def create_tables(conn):
    with conn.cursor() as cur:
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

        cur.execute("""
            CREATE TABLE IF NOT EXISTS liked_titles (
                id SERIAL PRIMARY KEY,
                user_id INT NOT NULL REFERENCES users(id),
                title TEXT NOT NULL
            );
        """)

        conn.commit()
        print("✅ All tables are ensured.")