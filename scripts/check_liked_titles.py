# scripts/check_liked_titles.py
from db.connection import get_connection
from nlp.liked_title_repo import fetch_liked_titles

conn = get_connection()
user_id = 1
titles = fetch_liked_titles(conn, user_id)
conn.close()

print("Liked titles:", titles)