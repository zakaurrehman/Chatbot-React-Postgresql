"""
Base database query class with common utilities.
"""

import logging
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from app.database.connection import DatabaseConnection, connect_db

# Setup logging
logger = logging.getLogger(__name__)

class BaseQueries:
    """Base class with common database utility methods."""
    
    def __init__(self, conn=None):
        """
        Initialize with a database connection.
        
        Args:
            conn: Optional database connection to use
        """
        # Use provided connection or create a new one
        self.conn = conn if conn is not None else connect_db()
    
    def _get_client_name(self, client_id: str) -> str:
        """
        Get client name from client_id.
        
        Args:
            client_id: UUID of the client
            
        Returns:
            Client name as string
        """
        try:
            # Check if client exists in leads table
            query = """
                SELECT "firstName", "lastName" FROM leads WHERE id = %s
            """
            client = DatabaseConnection.execute_query(self.conn, query, (client_id,), fetch_one=True)
            
            if client:
                return f"{client['firstName']} {client['lastName']}"
            
            # If not in leads, try users table
            query = """
                SELECT "firstName", "lastName" FROM users WHERE id = %s
            """
            user = DatabaseConnection.execute_query(self.conn, query, (client_id,), fetch_one=True)
            
            if user:
                return f"{user['firstName']} {user['lastName']}"
            
            return "Unknown Client"
        except Exception as e:
            logger.error(f"Error getting client name: {e}")
            return "Unknown Client"
    
    def _get_user_name(self, user_id: str) -> str:
        """
        Get user name from user_id.
        
        Args:
            user_id: UUID of the user
            
        Returns:
            User name as string
        """
        try:
            query = """
                SELECT "firstName", "lastName", email FROM users WHERE id = %s
            """
            user = DatabaseConnection.execute_query(self.conn, query, (user_id,), fetch_one=True)
            
            if user:
                return f"{user['firstName']} {user['lastName']}"
            return "Unknown User"
        except Exception as e:
            logger.error(f"Error getting user name: {e}")
            return "Unknown User"
    
    def _get_project_status(self, percent_complete: float) -> str:
        """
        Determine project status based on percent complete.
        
        Args:
            percent_complete: Percentage of project completion
            
        Returns:
            Status string
        """
        if percent_complete == 0:
            return "Not Started"
        elif percent_complete < 25:
            return "Planning"
        elif percent_complete < 100:
            return "In Progress"
        else:
            return "Completed"