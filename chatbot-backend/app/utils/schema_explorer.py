"""
Utility to explore and extract database schema information.
"""

import logging
from typing import Dict, Any, List

# Setup logging
logger = logging.getLogger(__name__)

def get_db_schema_summary(conn) -> str:
    """
    Get a summary of the database schema.
    
    Args:
        conn: Database connection
        
    Returns:
        String summary of database schema
    """
    try:
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        schema_summary = "Database Schema Summary:\n\n"
        
        # Get columns for each table
        for table in tables:
            cursor.execute(f"""
                SELECT column_name, data_type, column_default, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = '{table}'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            
            # Add table and columns to summary
            schema_summary += f"Table: {table}\n"
            schema_summary += "Columns:\n"
            for col in columns:
                col_default = f" DEFAULT {col[2]}" if col[2] else ""
                nullable = "NULL" if col[3] == "YES" else "NOT NULL"
                schema_summary += f"  - {col[0]} ({col[1]}{col_default}) {nullable}\n"
            schema_summary += "\n"
        
        cursor.close()
        return schema_summary
        
    except Exception as e:
        logger.error(f"Error getting database schema: {e}")
        return f"Error retrieving database schema: {str(e)}"