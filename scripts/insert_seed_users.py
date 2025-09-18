import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.connection import get_connection

# Define 5 simulated users with unique preferences
USERS = [
    {"username": "U1", "preferred_categories": ["business"], "preferred_countries": ["united states of america"]},
    {"username": "U2", "preferred_categories": ["technology"], "preferred_countries": ["united kingdom"]},
    {"username": "U3", "preferred_categories": ["health"], "preferred_countries": ["canada"]},
    {"username": "U4", "preferred_categories": ["sports"], "preferred_countries": ["japan"]},
    {"username": "U5", "preferred_categories": ["science"], "preferred_countries": ["india"]},
]

def insert_seed_users():
    conn = get_connection()
    cur = conn.cursor()

    for user in USERS:
        cur.execute("""
            INSERT INTO users (username, preferred_categories, preferred_countries)
            VALUES (%s, %s, %s)
            ON CONFLICT (username) DO NOTHING
        """, (
            user["username"],
            user["preferred_categories"],
            user["preferred_countries"]
        ))

    conn.commit()
    conn.close()
    print("✅ Seed users inserted successfully.")

if __name__ == "__main__":
    insert_seed_users()