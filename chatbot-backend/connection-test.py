import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try different connection strings from the project logs
connection_strings = [
    # From the .env file
    {
        "dbname": os.getenv("DB_NAME", "verceldb"),
        "user": os.getenv("DB_USER", "default"),
        "password": os.getenv("DB_PASSWORD", "kpRMePVX74wa"),
        "host": os.getenv("DB_HOST", "ep-patient-butterfly-a49jdxtx.us-east-1.aws.neon.tech"),
        "port": os.getenv("DB_PORT", "5432"),
        "sslmode": os.getenv("DB_SSLMODE", "require")
    },
    # From the original paste.txt
    {
        "dbname": "verceldb",
        "user": "default",
        "password": "kpRMePVX74wa",
        "host": "ep-patient-butterfly-a49jdxtx.us-east-1.aws.neon.tech",
        "port": "5432",
        "sslmode": "require"
    },
    # Another connection string from the logs
    {
        "dbname": "neondb",
        "user": "neondb_owner",
        "password": "npg_X02rGjyNYvSu",
        "host": "ep-crimson-glitter-a44yhjju-pooler.us-east-1.aws.neon.tech",
        "port": "5432",
        "sslmode": "require"
    },
    # Another option
    {
        "host": "ep-patient-butterfly-a49jdxtx.us-east-1.aws.neon.tech",
        "database": "verceldb",
        "user": "default",
        "password": "kpRMePVX74wa",
        "port": "5432",
    }
]

def test_connections():
    """Test all the connection strings."""
    for i, db_params in enumerate(connection_strings):
        print(f"\nTrying connection #{i+1}:")
        for key, value in db_params.items():
            # Mask password in output
            if key.lower() == 'password':
                masked_value = value[:3] + '*' * (len(value) - 3) if value else None
                print(f"  {key}: {masked_value}")
            else:
                print(f"  {key}: {value}")
        
        try:
            # Try to connect
            conn = psycopg2.connect(**db_params)
            
            # If connection successful, get some database info
            print("\n✅ Connection successful!")
            
            # Get database version
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                print(f"Database version: {version[0]}")
            
            # Get list of tables
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                
                if tables:
                    print(f"Found {len(tables)} tables:")
                    for table in tables:
                        print(f"  - {table[0]}")
                    
                    # Get columns of first table as sample
                    first_table = tables[0][0]
                    cursor.execute(f"""
                        SELECT column_name, data_type
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' AND table_name = '{first_table}'
                        ORDER BY ordinal_position
                    """)
                    columns = cursor.fetchall()
                    
                    print(f"\nColumns of table '{first_table}':")
                    for column in columns:
                        print(f"  - {column[0]} ({column[1]})")
                else:
                    print("No tables found in the database.")
            
            # Close connection
            conn.close()
            
            # Success! Return the working connection parameters
            return db_params
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
    
    print("\nAll connection attempts failed.")
    return None

if __name__ == "__main__":
    print("Testing database connections...")
    working_params = test_connections()
    
    if working_params:
        print("\n=======================================")
        print("Working connection parameters found!")
        print("=======================================")
        print("Update your .env file with these parameters:")
        for key, value in working_params.items():
            if key.lower() == 'password':
                masked_value = value[:3] + '*' * (len(value) - 3) if value else None
                print(f"{key.upper()}={masked_value}")
            else:
                print(f"{key.upper()}={value}")
    else:
        print("\nNo working connection found. Please check your database credentials.")