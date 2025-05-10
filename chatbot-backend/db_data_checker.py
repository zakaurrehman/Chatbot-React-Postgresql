#!/usr/bin/env python3
import psycopg2
import psycopg2.extras
import sys

# Database connection parameters
DB_PARAMS = {
    "dbname": "neondb",
    "user": "neondb_owner",
    "password": "npg_X02rGjyNYvSu",
    "host": "ep-crimson-glitter-a44yhjju-pooler.us-east-1.aws.neon.tech",
    "port": "5432",
    "sslmode": "require"
}

def check_data():
    try:
        # Connect to the database
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        print("Connection established successfully.")
        
        # Get list of tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        print(f"\nFound {len(tables)} tables in database:")
        
        # Check row counts for each table
        for i, table in enumerate(tables):
            table_name = table[0]
            try:
                # Count rows in the table
                cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
                row_count = cursor.fetchone()[0]
                print(f"{i+1}. {table_name}: {row_count} rows")
                
                # If table has data, show a sample row
                if row_count > 0:
                    try:
                        cursor.execute(f"SELECT * FROM \"{table_name}\" LIMIT 1")
                        sample = cursor.fetchone()
                        column_names = [desc[0] for desc in cursor.description]
                        
                        print(f"   Sample row columns: {', '.join(column_names)}")
                    except Exception as e:
                        print(f"   Error getting sample: {e}")
            except Exception as e:
                print(f"{i+1}. {table_name}: Error counting rows - {e}")
        
        # Check specific key tables for your queries
        key_tables = ['projects', 'tasks', 'phases', 'stages', 'checklist_items']
        print("\nDetailed check of key tables:")
        
        for table in key_tables:
            try:
                print(f"\nTable: {table}")
                cursor.execute(f"SELECT COUNT(*) FROM \"{table}\"")
                row_count = cursor.fetchone()[0]
                print(f"Total rows: {row_count}")
                
                if row_count > 0:
                    # Get column names
                    cursor.execute(f"""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = '{table}'
                    """)
                    columns = cursor.fetchall()
                    print("Columns:")
                    for col in columns:
                        print(f"  - {col[0]} ({col[1]})")
                    
                    # Get sample data
                    cursor.execute(f"SELECT * FROM \"{table}\" LIMIT 3")
                    sample_rows = cursor.fetchall()
                    print(f"Sample data ({min(3, len(sample_rows))} rows):")
                    for row in sample_rows:
                        print(f"  {row}")
            except Exception as e:
                print(f"Error checking {table}: {e}")
        
        # Close connection
        cursor.close()
        conn.close()
        print("\nDatabase connection closed.")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_data()