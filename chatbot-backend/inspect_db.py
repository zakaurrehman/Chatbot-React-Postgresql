#!/usr/bin/env python3
import psycopg2
import psycopg2.extras
import sys
import csv

# Database connection parameters
DB_PARAMS = {
    "dbname": "neondb",
    "user": "neondb_owner",
    "password": "npg_X02rGjyNYvSu",
    "host": "ep-crimson-glitter-a44yhjju-pooler.us-east-1.aws.neon.tech",
    "port": "5432",
    "sslmode": "require"
}

def get_connection():
    """Get a fresh database connection."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return conn, cursor
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        sys.exit(1)


def close_connection(conn, cursor):
    """Close a database connection."""
    if cursor:
        cursor.close()
    if conn:
        conn.close()


def get_table_info(table_name):
    """Get information about a specific table and export its data to CSV."""
    conn, cursor = get_connection()
    print(f"\n==== Table: {table_name} ====")
    
    try:
        # Get column information
        cursor.execute(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            """, (table_name,)
        )
        columns = cursor.fetchall()
        
        if not columns:
            print(f"No columns found for table '{table_name}'.")
        else:
            print("\nColumns:")
            for column in columns:
                nullable = "NULL" if column[2] == "YES" else "NOT NULL"
                print(f"- {column[0]}: {column[1]} {nullable}")
        
        # Get row count
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        count = cursor.fetchone()[0]
        print(f"\nTotal rows: {count}")
        
        # Export all data to CSV
        if count > 0:
            cursor.execute(f'SELECT * FROM "{table_name}"')
            rows = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]

            filename = f"{table_name}_data.csv"
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(column_names)  # Header
                writer.writerows(rows)         # All rows

            print(f"\n✅ Data exported to '{filename}'.")

            # Show sample data (first 5 rows)
            print("\nSample data (up to 5 rows):")
            for row in rows[:5]:
                print(dict(zip(column_names, row)))
    except Exception as e:
        print(f"Error getting information for table '{table_name}': {e}")
    finally:
        close_connection(conn, cursor)


def main():
    conn, cursor = get_connection()
    print("Database connection established successfully.")
    
    try:
        # Get list of tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the database.")
            return
        
        print("\nTables found in the database:")
        for i, table in enumerate(tables):
            print(f"{i+1}. {table[0]}")
        
        # Ask user which tables to inspect
        print("\nWhich tables would you like to inspect? (Enter numbers separated by commas, or 'all' for all tables)")
        user_input = input("> ")
        
        if user_input.lower() == 'all':
            tables_to_inspect = [table[0] for table in tables]
        else:
            try:
                selected_indices = [int(idx.strip()) - 1 for idx in user_input.split(',')]
                tables_to_inspect = [tables[idx][0] for idx in selected_indices if 0 <= idx < len(tables)]
            except ValueError:
                print("Invalid input. Please enter numbers separated by commas.")
                return

    finally:
        close_connection(conn, cursor)
    
    # Inspect selected tables
    for table in tables_to_inspect:
        get_table_info(table)
    
    print("\nDatabase inspection complete.")

if __name__ == "__main__":
    main()
