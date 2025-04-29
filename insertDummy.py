import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# PostgreSQL configuration
DB_HOST = os.getenv('DB_HOST')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# ========================
# Database Functions
# ========================

def insert_user(conn, username, preferred_categories=None, preferred_countries=None):
    """
    Insert a new user into the users table.
    """
    insert_query = """
    INSERT INTO users (username, preferred_categories, preferred_countries)
    VALUES (%s, %s, %s)
    RETURNING id;
    """
    with conn.cursor() as cur:
        cur.execute(insert_query, (
            username,
            preferred_categories if preferred_categories else [],
            preferred_countries if preferred_countries else []
        ))
        user_id = cur.fetchone()[0]
        conn.commit()
    print(f"Inserted user '{username}' with ID {user_id}.")
    return user_id

def insert_interaction(conn, user_id, article_id, interaction_type, time_spent=0):
    """
    Insert a new interaction into the interactions table.
    """
    insert_query = """
    INSERT INTO interactions (user_id, article_id, interaction_type, time_spent)
    VALUES (%s, %s, %s, %s)
    RETURNING id;
    """
    with conn.cursor() as cur:
        cur.execute(insert_query, (
            user_id,
            article_id,
            interaction_type,
            time_spent
        ))
        interaction_id = cur.fetchone()[0]
        conn.commit()
    print(f"Inserted interaction with ID {interaction_id} for user {user_id} on article {article_id}.")
    return interaction_id

# ========================
# Main Execution Flow
# ========================

def main():
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

    # Example: Insert a sample user
    user_id = insert_user(
        conn,
        username="amir_ghari",
        preferred_categories=["technology", "sports"],
        preferred_countries=["united states of america"]
    )

    # Example: Insert a sample interaction (you must know an article_id exists)
    article_id = 1  # Replace this with a valid article id from your articles table
    insert_interaction(
        conn,
        user_id=user_id,
        article_id=article_id,
        interaction_type="liked",
        time_spent=12
    )

    conn.close()
    print("Database connection closed.")

if __name__ == '__main__':
    main()
