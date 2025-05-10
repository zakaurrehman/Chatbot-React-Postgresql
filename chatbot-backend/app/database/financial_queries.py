"""
Financial-related database queries.
"""

import logging
from typing import List, Dict, Any, Optional
from app.database.connection import DatabaseConnection
from app.database.base_queries import BaseQueries

# Setup logging
logger = logging.getLogger(__name__)

class FinancialQueries(BaseQueries):
    """Financial database query methods."""
    def __init__(self, conn=None):
        """
        Initialize with optional connection.
        
        Args:
            conn: Database connection (optional)
        """
        super().__init__(conn)
    
    def get_payment_milestones(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get payment milestones for a specific project.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            List of payment milestones
        """
        try:
            # Query subphases that appear to be payment milestones
            query = """
                SELECT s.id, s.name, s.status, s."order", s."startDate", s."endDate",
                       p.name as phase_name, p.id as phase_id
                FROM subphases s
                JOIN phases p ON s.phase_id = p.id
                WHERE p.project_id = %s
                  AND (s.name ILIKE '%payment%' OR s.name ILIKE '%invoice%' OR s.name ILIKE '%billing%')
                ORDER BY p."order", s."order"
            """
            milestones = DatabaseConnection.execute_query(self.conn, query, (project_id,))
            
            # Get project info for context
            project_query = """
                SELECT name FROM projects WHERE id = %s
            """
            project = DatabaseConnection.execute_query(self.conn, project_query, (project_id,), fetch_one=True)
            project_name = project['name'] if project else "Unknown Project"
            
            # Transform into payment milestone items
            result = []
            for i, item in enumerate(milestones):
                # Map the subphase status to milestone status
                milestone_status = "Not Started"
                if item.get('status') == 'Completed':
                    milestone_status = "Paid"
                elif item.get('status') == 'Progress':
                    milestone_status = "Invoiced"
                elif item.get('status') == 'Review':
                    milestone_status = "Ready for Billing"
                
                # Extract milestone number if present in the name
                milestone_number = i + 1  # Default sequential number
                name_parts = item['name'].split()
                for part in name_parts:
                    if part.startswith('#') and part[1:].isdigit():
                        milestone_number = int(part[1:])
                        break
                
                result.append({
                    'id': item['id'],
                    'title': item['name'],
                    'status': milestone_status,
                    'project_id': project_id,
                    'project_name': project_name,
                    'phase_name': item.get('phase_name'),
                    'target_date': item.get('endDate'),
                    'completion_date': item.get('endDate') if milestone_status == "Paid" else None,
                    'sequence_number': milestone_number
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting payment milestones: {e}")
            return []
    
    def get_current_payment_milestone(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current payment milestone for a project.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            Current payment milestone or None if not found
        """
        try:
            # Get all payment milestones
            milestones = self.get_payment_milestones(project_id)
            
            # Find the first non-paid milestone
            for milestone in sorted(milestones, key=lambda x: x.get('sequence_number', 0)):
                if milestone['status'] != "Paid":
                    return milestone
            
            # If all milestones are paid, return the last one
            if milestones:
                return milestones[-1]
            
            return None
        except Exception as e:
            logger.error(f"Error getting current payment milestone: {e}")
            return None
    
    def get_payment_milestone_by_number(self, project_id: str, milestone_number: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific payment milestone by its number.
        
        Args:
            project_id: UUID of the project
            milestone_number: Sequential number of the milestone
            
        Returns:
            Payment milestone or None if not found
        """
        try:
            # Get all payment milestones
            milestones = self.get_payment_milestones(project_id)
            
            # Find the milestone with the specified number
            for milestone in milestones:
                if milestone.get('sequence_number') == milestone_number:
                    return milestone
            
            return None
        except Exception as e:
            logger.error(f"Error getting payment milestone #{milestone_number}: {e}")
            return None
    
    def get_billable_projects(self) -> List[Dict[str, Any]]:
        """
        Get projects that can be billed (have milestones ready for billing).
        
        Returns:
            List of billable projects
        """
        try:
            # Query subphases that appear to be payment milestones in 'Ready for Billing' status
            query = """
                SELECT s.id, s.name, s.status, s."order", s."startDate", s."endDate",
                       p.name as phase_name, p.id as phase_id, p.project_id,
                       pr.name as project_name
                FROM subphases s
                JOIN phases p ON s.phase_id = p.id
                JOIN projects pr ON p.project_id = pr.id
                WHERE (s.name ILIKE '%payment%' OR s.name ILIKE '%invoice%' OR s.name ILIKE '%billing%')
                  AND s.status = 'Review'  -- 'Review' maps to 'Ready for Billing'
                ORDER BY pr.name
            """
            billable_milestones = DatabaseConnection.execute_query(self.conn, query)
            
            # Group by project
            projects_dict = {}
            for item in billable_milestones:
                project_id = item['project_id']
                if project_id not in projects_dict:
                    projects_dict[project_id] = {
                        'project_id': project_id,
                        'project_name': item.get('project_name', 'Unknown Project'),
                        'billable_milestones': []
                    }
                
                # Add milestone to project
                projects_dict[project_id]['billable_milestones'].append({
                    'id': item['id'],
                    'title': item['name'],
                    'phase_name': item.get('phase_name'),
                    'target_date': item.get('endDate')
                })
            
            # Convert dictionary to list
            result = list(projects_dict.values())
            
            return result
        except Exception as e:
            logger.error(f"Error getting billable projects: {e}")
            return []