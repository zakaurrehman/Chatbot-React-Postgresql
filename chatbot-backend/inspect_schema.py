"""
Script to inspect and display the database schema.
"""

import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def connect_db():
    """Connect to the database."""
    # Get database connection params from environment
    db_params = {
        "dbname": os.getenv("DB_NAME", "neondb"),
        "user": os.getenv("DB_USER", "neondb_owner"),
        "password": os.getenv("DB_PASSWORD", "npg_X02rGjyNYvSu"),
        "host": os.getenv("DB_HOST", "ep-crimson-glitter-a44yhjju-pooler.us-east-1.aws.neon.tech"),
        "port": os.getenv("DB_PORT", "5432"),
        "sslmode": os.getenv("DB_SSLMODE", "require")
    }
    
    # Connect to the database
    conn = psycopg2.connect(**db_params, cursor_factory=RealDictCursor)
    return conn

def inspect_schema():
    """Inspect and print the database schema."""
    conn = connect_db()
    logger.info("Inspecting database schema")
    
    try:
        # Get all tables
        with conn.cursor() as cur:
            # List all tables
            cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """)
            
            tables = cur.fetchall()
            
            print("\n==== DATABASE TABLES ====")
            for table in tables:
                table_name = table['table_name']
                print(f"\n-- Table: {table_name} --")
                
                # Get columns for this table
                cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
                """, (table_name,))
                
                columns = cur.fetchall()
                for col in columns:
                    col_name = col['column_name']
                    col_type = col['data_type']
                    col_nullable = col['is_nullable']
                    col_default = col['column_default'] or 'NULL'
                    
                    print(f"  {col_name}: {col_type}, {'NULL' if col_nullable == 'YES' else 'NOT NULL'}, Default: {col_default}")
                
                # Get foreign keys for this table
                cur.execute("""
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM
                    information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s;
                """, (table_name,))
                
                foreign_keys = cur.fetchall()
                if foreign_keys:
                    print("\n  Foreign Keys:")
                    for fk in foreign_keys:
                        fk_name = fk['constraint_name']
                        fk_column = fk['column_name']
                        fk_table = fk['foreign_table_name']
                        fk_ref_column = fk['foreign_column_name']
                        
                        print(f"    {fk_column} -> {fk_table}.{fk_ref_column}")
        
        return True
    except Exception as e:
        logger.error(f"Error inspecting schema: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # Run the inspection
    inspect_schema()