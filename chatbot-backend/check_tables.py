import psycopg2

# Database connection parameters
DB_PARAMS = {
    "dbname": "neondb",
    "user": "neondb_owner",
    "password": "npg_X02rGjyNYvSu",
    "host": "ep-crimson-glitter-a44yhjju-pooler.us-east-1.aws.neon.tech",
    "port": "5432",
    "sslmode": "require"
}

# Expected tables for chatbot support
expected_tables = {
    "selection_items",
    "walkthroughs",
    "milestones",
    "procurements"
}

def check_missing_tables():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = {row[0] for row in cursor.fetchall()}
        missing = expected_tables - existing_tables

        print("\nExisting tables in DB:")
        print(existing_tables)
        print("\nMissing tables needed for chatbot:")
        print(missing if missing else "All required tables are present.")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_missing_tables()
