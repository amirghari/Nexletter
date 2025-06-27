from db.connection import get_connection
from db.init_db import create_tables

def main():
    conn = get_connection()
    create_tables(conn)
    conn.close()

if __name__ == "__main__":
    main()