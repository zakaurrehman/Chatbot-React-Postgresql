"""
Walkthrough-related database queries.
"""

import logging
from typing import List, Dict, Any, Optional
from app.database.connection import DatabaseConnection
from app.database.base_queries import BaseQueries

# Setup logging
logger = logging.getLogger(__name__)

class WalkthroughQueries(BaseQueries):
    """Walkthrough database query methods."""
    def __init__(self, conn=None):
        """
        Initialize with optional connection.
        
        Args:
            conn: Database connection (optional)
        """
        super().__init__(conn)
    
    def get_walkthroughs_by_type(self, walkthrough_type: str, status: str = "Not Scheduled") -> List[Dict[str, Any]]:
        """
        Get walkthroughs of a specific type with the given status.
        
        Args:
            walkthrough_type: Type of walkthrough (e.g., "PD", "Client")
            status: Status of walkthroughs to retrieve
            
        Returns:
            List of walkthroughs
        """
        try:
            # Since we might not have a dedicated walkthroughs table yet, let's use subphases
            # that represent walkthroughs in the project phases
            query = """
                SELECT s.id, s.name, s.status, s."order", s."startDate", s."endDate",
                       p.name as phase_name, p.id as phase_id, p.project_id,
                       pr.name as project_name
                FROM subphases s
                JOIN phases p ON s.phase_id = p.id
                JOIN projects pr ON p.project_id = pr.id
                WHERE s.name ILIKE %s
                ORDER BY s."endDate" NULLS LAST, pr.name
            """
            
            # Adjust search pattern based on walkthrough type
            if walkthrough_type.lower() == "pd":
                search_pattern = '%pd%walkthrough%'
            elif walkthrough_type.lower() == "client":
                search_pattern = '%client%walkthrough%'
            else:
                search_pattern = f'%{walkthrough_type}%walkthrough%'
            
            walkthroughs = DatabaseConnection.execute_query(self.conn, query, (search_pattern,))
            
            # Transform into walkthrough items
            result = []
            for item in walkthroughs:
                # Map the subphase status to walkthrough status
                walkthrough_status = "Not Scheduled"
                if item.get('status') == 'Completed':
                    walkthrough_status = "Completed"
                elif item.get('status') == 'Progress':
                    walkthrough_status = "Scheduled"
                
                # Only include items with matching status (if specified)
                if status and status != "All" and walkthrough_status != status:
                    continue
                
                result.append({
                    'id': item['id'],
                    'title': item['name'],
                    'status': walkthrough_status,
                    'project_id': item['project_id'],
                    'project_name': item.get('project_name', 'Unknown Project'),
                    'phase_name': item.get('phase_name'),
                    'scheduled_date': item.get('startDate'),
                    'completed_date': item.get('endDate') if walkthrough_status == "Completed" else None,
                    'type': walkthrough_type
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting {walkthrough_type} walkthroughs: {e}")
            return []
    
    def get_project_recent_walkthrough(self, project_id: str, walkthrough_type: str) -> Optional[Dict[str, Any]]:
        """
        Get most recent walkthrough of a specific type for a project.
        
        Args:
            project_id: UUID of the project
            walkthrough_type: Type of walkthrough (e.g., "PD", "Client")
            
        Returns:
            Most recent walkthrough or None if not found
        """
        try:
            # Get phase info to identify the walkthrough-related subphases
            query = """
                SELECT s.id, s.name, s.status, s."order", s."startDate", s."endDate",
                       p.name as phase_name, p.id as phase_id
                FROM subphases s
                JOIN phases p ON s.phase_id = p.id
                WHERE p.project_id = %s
                  AND s.name ILIKE %s
                ORDER BY s."startDate" DESC NULLS LAST
                LIMIT 1
            """
            
            # Adjust search pattern based on walkthrough type
            if walkthrough_type.lower() == "pd":
                search_pattern = '%pd%walkthrough%'
            elif walkthrough_type.lower() == "client":
                search_pattern = '%client%walkthrough%'
            else:
                search_pattern = f'%{walkthrough_type}%walkthrough%'
            
            walkthrough = DatabaseConnection.execute_query(self.conn, query, (project_id, search_pattern), fetch_one=True)
            
            if not walkthrough:
                return None
            
            # Get project info for context
            project_query = """
                SELECT name FROM projects WHERE id = %s
            """
            project = DatabaseConnection.execute_query(self.conn, project_query, (project_id,), fetch_one=True)
            project_name = project['name'] if project else "Unknown Project"
            
            # Map the subphase status to walkthrough status
            walkthrough_status = "Not Scheduled"
            if walkthrough.get('status') == 'Completed':
                walkthrough_status = "Completed"
            elif walkthrough.get('status') == 'Progress':
                walkthrough_status = "Scheduled"
            
            return {
                'id': walkthrough['id'],
                'title': walkthrough['name'],
                'status': walkthrough_status,
                'project_id': project_id,
                'project_name': project_name,
                'phase_name': walkthrough.get('phase_name'),
                'scheduled_date': walkthrough.get('startDate'),
                'completed_date': walkthrough.get('endDate') if walkthrough_status == "Completed" else None,
                'type': walkthrough_type
            }
        except Exception as e:
            logger.error(f"Error getting recent {walkthrough_type} walkthrough: {e}")
            return None