"""
Database connection module for the construction chatbot.
"""

import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Setup logging
logger = logging.getLogger(__name__)

def connect_db():
    """
    Connect to the PostgreSQL database.
    
    Returns:
        Database connection object
    """
    try:
        # Get database connection parameters from environment variables
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'construction')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', 'password')
        
        # Connect to the database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password,
            cursor_factory=RealDictCursor
        )
        
        # Set autocommit to False to enable transactions
        conn.autocommit = False
        
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise

class DatabaseConnection:
    """Helper class for database connection and query execution."""
    
    @staticmethod
    def execute_query(conn, query, params=None, fetch_one=False):
        """
        Execute a SQL query with parameters.
        
        Args:
            conn: Database connection
            query: SQL query string
            params: Query parameters (optional)
            fetch_one: Whether to fetch one result or all results
            
        Returns:
            Query results
        """
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            
            if fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
                
            cursor.close()
            return result
        except Exception as e:
            conn.rollback()
            raise e