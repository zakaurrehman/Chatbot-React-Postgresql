# explore_db.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "sslmode": os.getenv("DB_SSLMODE", "require")
}

def get_tables():
    """Get all tables in the database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Query to get all tables
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    
    tables = cur.fetchall()
    
    # Close connection
    cur.close()
    conn.close()
    
    return [table['table_name'] for table in tables]

def get_table_columns(table_name):
    """Get all columns for a specific table."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Query to get all columns for the table
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))
    
    columns = cur.fetchall()
    
    # Close connection
    cur.close()
    conn.close()
    
    return columns

def explore_database():
    """Explore the database structure and print it."""
    tables = get_tables()
    
    print(f"Database contains {len(tables)} tables:")
    for table in tables:
        print(f"\n\nTABLE: {table}")
        columns = get_table_columns(table)
        print("Columns:")
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            print(f"  - {col['column_name']} ({col['data_type']}) {nullable}")

if __name__ == "__main__":
    explore_database()