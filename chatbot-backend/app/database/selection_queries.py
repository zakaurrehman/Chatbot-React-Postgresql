"""
Selection-related database queries.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.database.connection import DatabaseConnection
from app.database.base_queries import BaseQueries

# Setup logging
logger = logging.getLogger(__name__)

class SelectionQueries(BaseQueries):
    """Selection database query methods."""
    
    def __init__(self, conn=None):
        """
        Initialize with optional connection.
        
        Args:
            conn: Database connection (optional)
        """
        super().__init__(conn)
    
    def get_selections_by_project(self, project_id: str, status: str = "Open") -> List[Dict[str, Any]]:
        """
        Get selection items for a specific project.
        
        Args:
            project_id: UUID of the project
            status: Status of selection items to retrieve
            
        Returns:
            List of selection items
        """
        try:
            # Since selection items might not exist in the database yet, let's query our subphases
            # that involve selections or decision points
            query = """
                SELECT s.id, s.name, s.status, s."order", s."startDate", s."endDate",
                       p.name as phase_name, p.id as phase_id
                FROM subphases s
                JOIN phases p ON s.phase_id = p.id
                WHERE p.project_id = %s
                  AND (s.name ILIKE '%selection%' OR s.name ILIKE '%choose%' OR s.name ILIKE '%decide%' 
                       OR s.name ILIKE '%pick%' OR s.name ILIKE '%select%')
                ORDER BY p."order", s."order"
            """
            selections = DatabaseConnection.execute_query(self.conn, query, (project_id,))
            
            # Get project info for context
            project_query = """
                SELECT name FROM projects WHERE id = %s
            """
            project = DatabaseConnection.execute_query(self.conn, project_query, (project_id,), fetch_one=True)
            project_name = project['name'] if project else "Unknown Project"
            
            # Transform into selection items
            result = []
            for item in selections:
                # Map the subphase status to selection status
                selection_status = "Open"
                if item.get('status') == 'Completed':
                    selection_status = "Completed"
                elif item.get('status') == 'Progress':
                    selection_status = "In Progress"
                elif item.get('status') == 'Review':
                    selection_status = "Under Review"
                
                # Only include items with matching status (if specified)
                if status and status != "All" and selection_status != status:
                    continue
                
                # Calculate days overdue if item has a deadline
                days_overdue = None
                if item.get('endDate') and selection_status != "Completed":
                    end_date = item['endDate']
                    if isinstance(end_date, str):
                        end_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    
                    if datetime.now() > end_date:
                        days_overdue = (datetime.now() - end_date).days
                
                result.append({
                    'id': item['id'],
                    'title': item['name'],
                    'status': selection_status,
                    'project_id': project_id,
                    'project_name': project_name,
                    'phase_name': item.get('phase_name'),
                    'required_date': item.get('endDate'),
                    'days_overdue': days_overdue,
                    'sequence': item.get('order', 0)
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting selections by project: {e}")
            return []
    
    def get_all_selections(self, status: str = "Open") -> List[Dict[str, Any]]:
        """
        Get all selection items across all projects.
        
        Args:
            status: Status of selection items to retrieve
            
        Returns:
            List of selection items
        """
        try:
            # Query all selection-related subphases across all projects
            query = """
                SELECT s.id, s.name, s.status, s."order", s."startDate", s."endDate",
                       p.name as phase_name, p.id as phase_id, p.project_id,
                       pr.name as project_name
                FROM subphases s
                JOIN phases p ON s.phase_id = p.id
                JOIN projects pr ON p.project_id = pr.id
                WHERE (s.name ILIKE '%selection%' OR s.name ILIKE '%choose%' OR s.name ILIKE '%decide%' 
                       OR s.name ILIKE '%pick%' OR s.name ILIKE '%select%')
                ORDER BY pr.name, p."order", s."order"
            """
            selections = DatabaseConnection.execute_query(self.conn, query)
            
            # Transform into selection items
            result = []
            for item in selections:
                # Map the subphase status to selection status
                selection_status = "Open"
                if item.get('status') == 'Completed':
                    selection_status = "Completed"
                elif item.get('status') == 'Progress':
                    selection_status = "In Progress"
                elif item.get('status') == 'Review':
                    selection_status = "Under Review"
                
                # Only include items with matching status (if specified)
                if status and status != "All" and selection_status != status:
                    continue
                
                # Calculate days overdue if item has a deadline
                days_overdue = None
                if item.get('endDate') and selection_status != "Completed":
                    end_date = item['endDate']
                    if isinstance(end_date, str):
                        end_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    
                    if datetime.now() > end_date:
                        days_overdue = (datetime.now() - end_date).days
                
                result.append({
                    'id': item['id'],
                    'title': item['name'],
                    'status': selection_status,
                    'project_id': item['project_id'],
                    'project_name': item.get('project_name', 'Unknown Project'),
                    'phase_name': item.get('phase_name'),
                    'required_date': item.get('endDate'),
                    'days_overdue': days_overdue,
                    'sequence': item.get('order', 0)
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting all selections: {e}")
            return []
    
    def get_selection_by_name(self, selection_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a selection item by its name.
        
        Args:
            selection_name: Name of the selection
            
        Returns:
            Selection item or None if not found
        """
        try:
            # Query selection-related subphases by name
            query = """
                SELECT s.id, s.name, s.status, s."order", s."startDate", s."endDate",
                       p.name as phase_name, p.id as phase_id, p.project_id,
                       pr.name as project_name
                FROM subphases s
                JOIN phases p ON s.phase_id = p.id
                JOIN projects pr ON p.project_id = pr.id
                WHERE s.name ILIKE %s
                LIMIT 1
            """
            selection = DatabaseConnection.execute_query(self.conn, query, (f'%{selection_name}%',), fetch_one=True)
            
            if not selection:
                return None
            
            # Map the subphase status to selection status
            selection_status = "Open"
            if selection.get('status') == 'Completed':
                selection_status = "Completed"
            elif selection.get('status') == 'Progress':
                selection_status = "In Progress"
            elif selection.get('status') == 'Review':
                selection_status = "Under Review"
            
            # Calculate days overdue if item has a deadline
            days_overdue = None
            if selection.get('endDate') and selection_status != "Completed":
                end_date = selection['endDate']
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                
                if datetime.now() > end_date:
                    days_overdue = (datetime.now() - end_date).days
            
            result = {
                'id': selection['id'],
                'title': selection['name'],
                'status': selection_status,
                'project_id': selection['project_id'],
                'project_name': selection.get('project_name', 'Unknown Project'),
                'phase_name': selection.get('phase_name'),
                'required_date': selection.get('endDate'),
                'days_overdue': days_overdue,
                'sequence': selection.get('order', 0)
            }
            
            return result
        except Exception as e:
            logger.error(f"Error getting selection by name: {e}")
            return None
    
    def get_upcoming_selections_by_project(self, project_id: str, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get upcoming selection items for a specific project.
        
        Args:
            project_id: UUID of the project
            end_date: End date for the timeframe
            
        Returns:
            List of upcoming selection items
        """
        try:
            # Format date for SQL query
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # Query selection-related subphases with upcoming deadlines
            query = """
                SELECT s.id, s.name, s.status, s."order", s."startDate", s."endDate",
                       p.name as phase_name, p.id as phase_id
                FROM subphases s
                JOIN phases p ON s.phase_id = p.id
                WHERE p.project_id = %s
                  AND (s.name ILIKE '%selection%' OR s.name ILIKE '%choose%' OR s.name ILIKE '%decide%' 
                       OR s.name ILIKE '%pick%' OR s.name ILIKE '%select%')
                  AND s.status != 'Completed'
                  AND s."endDate" IS NOT NULL
                  AND s."endDate" <= %s
                ORDER BY s."endDate"
            """
            selections = DatabaseConnection.execute_query(self.conn, query, (project_id, end_date_str))
            
            # Get project info for context
            project_query = """
                SELECT name FROM projects WHERE id = %s
            """
            project = DatabaseConnection.execute_query(self.conn, project_query, (project_id,), fetch_one=True)
            project_name = project['name'] if project else "Unknown Project"
            
            # Transform into selection items
            result = []
            for item in selections:
                # Map the subphase status to selection status
                selection_status = "Open"
                if item.get('status') == 'Progress':
                    selection_status = "In Progress"
                elif item.get('status') == 'Review':
                    selection_status = "Under Review"
                
                # Calculate days until due
                days_until_due = None
                if item.get('endDate'):
                    end_date_value = item['endDate']
                    if isinstance(end_date_value, str):
                        end_date_value = datetime.strptime(end_date_value, "%Y-%m-%dT%H:%M:%S.%fZ")
                    
                    days_until_due = (end_date_value - datetime.now()).days
                
                result.append({
                    'id': item['id'],
                    'title': item['name'],
                    'status': selection_status,
                    'project_id': project_id,
                    'project_name': project_name,
                    'phase_name': item.get('phase_name'),
                    'required_date': item.get('endDate'),
                    'days_until_due': days_until_due,
                    'sequence': item.get('order', 0)
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting upcoming selections by project: {e}")
            return []
    
    def get_all_upcoming_selections(self, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get all upcoming selection items across all projects.
        
        Args:
            end_date: End date for the timeframe
            
        Returns:
            List of upcoming selection items
        """
        try:
            # Format date for SQL query
            end_date_str = end_date.strftime("%Y-%m-%d")
            
            # Query all selection-related subphases with upcoming deadlines
            query = """
                SELECT s.id, s.name, s.status, s."order", s."startDate", s."endDate",
                    p.name as phase_name, p.id as phase_id, p.project_id,
                    pr.name as project_name
                FROM subphases s
                JOIN phases p ON s.phase_id = p.id
                JOIN projects pr ON p.project_id = pr.id
                WHERE (s.name ILIKE '%selection%' OR s.name ILIKE '%choose%' OR s.name ILIKE '%decide%' 
                    OR s.name ILIKE '%pick%' OR s.name ILIKE '%select%')
                AND s.status != 'Completed'
                AND s."endDate" IS NOT NULL
                AND s."endDate" <= %s
                ORDER BY s."endDate"
            """
            
            # Let's add some debug logging
            logger.debug(f"Running query with end_date: {end_date_str}")
            
            # Make sure we're passing a single-item tuple
            selections = DatabaseConnection.execute_query(self.conn, query, (end_date_str,))
            
            # Transform into selection items
            result = []
            if selections:
                for item in selections:
                    # Defensive programming: check if item exists
                    if not item:
                        continue
                    
                    # Map the subphase status to selection status
                    selection_status = "Open"
                    if item.get('status') == 'Progress':
                        selection_status = "In Progress"
                    elif item.get('status') == 'Review':
                        selection_status = "Under Review"
                    
                    # Calculate days until due
                    days_until_due = None
                    if item.get('endDate'):
                        try:
                            end_date_value = item['endDate']
                            if isinstance(end_date_value, str):
                                end_date_value = datetime.strptime(end_date_value, "%Y-%m-%dT%H:%M:%S.%fZ")
                            
                            days_until_due = (end_date_value - datetime.now()).days
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error calculating days until due: {e}")
                    
                    result.append({
                        'id': item['id'],
                        'title': item['name'],
                        'status': selection_status,
                        'project_id': item.get('project_id'),
                        'project_name': item.get('project_name', 'Unknown Project'),
                        'phase_name': item.get('phase_name'),
                        'required_date': item.get('endDate'),
                        'days_until_due': days_until_due,
                        'sequence': item.get('order', 0)
                    })
            
            logger.debug(f"Found {len(result)} upcoming selections")
            return result
        except Exception as e:
            logger.error(f"Error getting all upcoming selections: {e}")
            import traceback
            logger.error(traceback.format_exc())  # Add stack trace for debugging
            return []
    
    def find_selection_by_partial_name(self, partial_name: str, project_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Find a selection item by a partial name, optionally filtered by project.
        
        Args:
            partial_name: Partial name of the selection to find
            project_name: Optional project name to filter by
            
        Returns:
            Selection item or None if not found
        """
        try:
            # Base query
            base_query = """
                SELECT s.id, s.name, s.status, s."order", s."startDate", s."endDate",
                       p.name as phase_name, p.id as phase_id, p.project_id,
                       pr.name as project_name
                FROM subphases s
                JOIN phases p ON s.phase_id = p.id
                JOIN projects pr ON p.project_id = pr.id
                WHERE s.name ILIKE %s
            """
            
            params = [f'%{partial_name}%']
            
            # Add project filter if provided
            if project_name:
                base_query += " AND pr.name ILIKE %s"
                params.append(f'%{project_name}%')
            
            base_query += " LIMIT 1"
            
            selection = DatabaseConnection.execute_query(self.conn, base_query, tuple(params), fetch_one=True)
            
            if not selection:
                return None
            
            # Map the subphase status to selection status
            selection_status = "Open"
            if selection.get('status') == 'Completed':
                selection_status = "Completed"
            elif selection.get('status') == 'Progress':
                selection_status = "In Progress"
            elif selection.get('status') == 'Review':
                selection_status = "Under Review"
            
            # Calculate days overdue if item has a deadline
            days_overdue = None
            if selection.get('endDate') and selection_status != "Completed":
                end_date = selection['endDate']
                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                
                if datetime.now() > end_date:
                    days_overdue = (datetime.now() - end_date).days
            
            result = {
                'id': selection['id'],
                'title': selection['name'],
                'status': selection_status,
                'project_id': selection['project_id'],
                'project_name': selection.get('project_name', 'Unknown Project'),
                'phase_name': selection.get('phase_name'),
                'required_date': selection.get('endDate'),
                'days_overdue': days_overdue,
                'sequence': selection.get('order', 0)
            }
            
            return result
        except Exception as e:
            logger.error(f"Error finding selection by partial name '{partial_name}': {e}")
            return None
    
    # Compatibility methods
    
    def get_selection_list(self, project_id=None, status="Open"):
        """
        Get a list of selections for a project with the specified status.
        
        Args:
            project_id (str, optional): Project ID to filter by. If None, returns all.
            status (str, optional): Selection status to filter by. Default is "Open".
            
        Returns:
            List of selection items
        """
        try:
            # Handle the case where project_id is a name, not an ID
            if project_id and not self._is_uuid(project_id):
                project = self.get_project_by_name(project_id)
                if project:
                    project_id = project['id']
                else:
                    return []
                    
            # Get the project details with phase info
            if project_id:
                project = self._project.get_project_details(project_id)
                
                # Error handling for database access
                if not project:
                    return []
                    
                # Process selections from the project data
                selections = []
                
                # TODO: Implement proper selection retrieving logic
                # This is a placeholder that returns an empty list
                # Actual implementation would access proper tables/fields
                
                return selections
            else:
                # Get selections across all projects
                selections = []
                
                # TODO: Implement proper selection retrieving logic
                # This is a placeholder that returns an empty list
                
                return selections
                
        except Exception as e:
            logger.error(f"Error getting selection list: {e}")
            return []
            
    def _is_uuid(self, value):
        """Check if a string is a valid UUID."""
        try:
            uuid.UUID(str(value))
            return True
        except (ValueError, AttributeError):
            return False

    def get_upcoming_selections(self, days=14):
        """
        Compatibility method for retrieving upcoming selections.
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of upcoming selection items
        """
        try:
            # Create end_date by adding days to current date
            end_date = datetime.now() + timedelta(days=days)
            
            # Call our internal method with proper date formatting
            return self.get_all_upcoming_selections(end_date)
        except Exception as e:
            logger.error(f"Error getting upcoming selections: {e}")
            return []