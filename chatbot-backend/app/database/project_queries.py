"""
Project-related database queries.
"""

import logging
from typing import List, Dict, Any, Optional
from app.database.connection import DatabaseConnection
from app.database.base_queries import BaseQueries

# Setup logging
logger = logging.getLogger(__name__)

class ProjectQueries(BaseQueries):
    """Project database query methods."""
    
    def __init__(self, conn=None, phase_queries=None):
        """
        Initialize project queries with optional connection and phase_queries.
        
        Args:
            conn: Database connection (optional)
            phase_queries: PhaseQueries instance for cross-module calls (optional)
        """
        super().__init__(conn)
        self._phase_queries = phase_queries
    
    def get_all_projects(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all projects from the database.
        
        Args:
            limit: Maximum number of projects to return
            
        Returns:
            List of project dictionaries
        """
        try:
            # Use the execute_query helper to handle transactions
            query = """
                SELECT id, name, "startDate", "percentComplete", 
                       "createdAt", "updatedAt", user_id, project_template_id,
                       created_by, project_designer_id, project_developer_id,
                       client_id, project_junior_designer_id, warranty_mode
                FROM projects
                ORDER BY "updatedAt" DESC
                LIMIT %s
            """
            projects = DatabaseConnection.execute_query(self.conn, query, (limit,))
            
            # Convert to list of dictionaries
            result = []
            for project in projects:
                # Get client name from client_id if available
                client_name = "Unknown"
                if project.get('client_id'):
                    client_name = self._get_client_name(project['client_id'])
                
                # Add client name to project data
                project_data = dict(project)
                project_data['client_name'] = client_name
                
                # Get phase information
                try:
                    if self._phase_queries:
                        phase_info = self._phase_queries.get_project_phase_info(project['id'])
                        if phase_info and phase_info.get('current_phase'):
                            project_data['current_phase'] = phase_info['current_phase']['name']
                            project_data['phase_progress'] = phase_info['current_phase']['progress']
                        else:
                            # Add status based on percentComplete if phase info not available
                            project_data['status'] = self._get_project_status(project.get('percentComplete', 0))
                    else:
                        # Add status based on percentComplete if phase_queries not available
                        project_data['status'] = self._get_project_status(project.get('percentComplete', 0))
                except Exception as e:
                    logger.error(f"Error getting phase info for project {project['id']}: {e}")
                    # Add status based on percentComplete
                    project_data['status'] = self._get_project_status(project.get('percentComplete', 0))
                
                result.append(project_data)
                
            return result
        except Exception as e:
            logger.error(f"Error getting all projects: {e}")
            return []
    
    def get_project_details(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific project.
        
        Args:
            project_id: Either the UUID or name of the project
            
        Returns:
            Project details dictionary or None if not found
        """
        try:
            # First try name match (more likely what users will use)
            query = """
                SELECT id, name, "startDate", "percentComplete", 
                       "createdAt", "updatedAt", user_id, project_template_id,
                       created_by, project_designer_id, project_developer_id,
                       client_id, project_junior_designer_id, warranty_mode
                FROM projects
                WHERE name = %s
            """
            project = DatabaseConnection.execute_query(self.conn, query, (project_id,), fetch_one=True)
            
            # If not found by name, try ID match if it looks like a UUID
            if not project and len(project_id) > 30:
                query = """
                    SELECT id, name, "startDate", "percentComplete", 
                           "createdAt", "updatedAt", user_id, project_template_id,
                           created_by, project_designer_id, project_developer_id,
                           client_id, project_junior_designer_id, warranty_mode
                    FROM projects
                    WHERE id = %s
                """
                project = DatabaseConnection.execute_query(self.conn, query, (project_id,), fetch_one=True)
            
            if not project:
                return None
            
            # Get additional project information
            project_data = dict(project)
            
            # Get client name
            if project_data.get('client_id'):
                project_data['client_name'] = self._get_client_name(project_data['client_id'])
            
            # Get designer name
            if project_data.get('project_designer_id'):
                project_data['designer_name'] = self._get_user_name(project_data['project_designer_id'])
            
            # Get developer name
            if project_data.get('project_developer_id'):
                project_data['developer_name'] = self._get_user_name(project_data['project_developer_id'])
            
            # Get phase information
            try:
                if self._phase_queries:
                    phase_info = self._phase_queries.get_project_phase_info(project['id'])
                    if phase_info:
                        project_data['phase_info'] = phase_info
            except Exception as e:
                logger.error(f"Error getting phase info for project {project['id']}: {e}")
            
            # Get project status
            project_data['status'] = self._get_project_status(project_data.get('percentComplete', 0))
            
            return project_data
        except Exception as e:
            logger.error(f"Error getting project details: {e}")
            return None
    
    def get_project_by_name(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a project by its name.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Project dictionary or None if not found
        """
        try:
            query = """
                SELECT id, name, "startDate", "percentComplete", 
                       "createdAt", "updatedAt"
                FROM projects
                WHERE name ILIKE %s
            """
            project = DatabaseConnection.execute_query(self.conn, query, (project_name,), fetch_one=True)
            
            # Try a partial match if exact match not found
            if not project:
                query = """
                    SELECT id, name, "startDate", "percentComplete", 
                           "createdAt", "updatedAt"
                    FROM projects
                    WHERE name ILIKE %s
                    ORDER BY "updatedAt" DESC
                    LIMIT 1
                """
                project = DatabaseConnection.execute_query(self.conn, query, (f'%{project_name}%',), fetch_one=True)
            
            return project
        except Exception as e:
            logger.error(f"Error getting project by name: {e}")
            return None
            
    def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status for a specific project by its ID or name.

        Args:
            project_id (str): Either the name (e.g., 'JAIN-1B') or UUID of the project.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with status information, or None if the project is not found.
        """
        # Reuse the existing get_project_details to avoid duplicating SQL or logic.
        project = self.get_project_details(project_id)
        if not project:
            # If the project isn't found by name or UUID, return None.
            return None

        # Build a minimal dictionary focusing on status/phase-related fields.
        return {
            "project_id": project["id"],
            "project_name": project["name"],
            "status": project.get("status", "Unknown"),
            "current_phase": project.get("phase_info", {}).get("current_phase", {}).get("name", "Unknown"),
            "phase_progress": project.get("phase_info", {}).get("current_phase", {}).get("progress", 0),
            "overall_progress": project.get("phase_info", {}).get("overall_progress", 0),
        }
        
    def find_project_by_partial_name(self, partial_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a project by a partial name match.
        
        Args:
            partial_name: Partial project name to search for
            
        Returns:
            Project dictionary or None if not found
        """
        try:
            query = """
                SELECT id, name, "startDate", "percentComplete", 
                       "createdAt", "updatedAt"
                FROM projects
                WHERE name ILIKE %s
                ORDER BY "updatedAt" DESC
                LIMIT 1
            """
            project = DatabaseConnection.execute_query(self.conn, query, (f'%{partial_name}%',), fetch_one=True)
            
            if not project:
                return None
                
            return self.get_project_details(project['id'])
        except Exception as e:
            logger.error(f"Error finding project by partial name '{partial_name}': {e}")
            return None