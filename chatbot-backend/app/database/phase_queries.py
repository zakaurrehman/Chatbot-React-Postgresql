"""
Phase and stage related database queries.
"""
import uuid
import logging
from typing import List, Dict, Any, Optional
import uuid
from app.database.connection import DatabaseConnection
from app.database.base_queries import BaseQueries

# Setup logging
logger = logging.getLogger(__name__)

class PhaseQueries(BaseQueries):
    """Phase and stage database query methods."""
    
    def __init__(self, conn=None):
        """
        Initialize phase queries with optional connection.
        
        Args:
            conn: Database connection (optional)
        """
        super().__init__()
        if conn:
            self.conn = conn
    
    def get_project_phase_info(self, project_id: str) -> Dict[str, Any]:
        """
        Get phase and subphase information for a project.
    
        Args:
            project_id: UUID of the project
        
        Returns:
            Dictionary with phase information
        """
        try:
            # Get all phases for this project
            phases_query = """
                SELECT id, name, status, "order"
                FROM phases
                WHERE project_id = %s
                ORDER BY "order"
            """
            phases = DatabaseConnection.execute_query(self.conn, phases_query, (project_id,))
        
            phase_info = []
            current_phase = None
            overall_progress = 0
            phase_count = len(phases)
        
            if phases:
                # Calculate a weighted progress percentage
                total_weight = 0
                weighted_sum = 0
            
                for phase in phases:
                    # Get subphases for this phase
                    subphases_query = """
                        SELECT id, name, status, "order"
                        FROM subphases
                        WHERE phase_id = %s
                        ORDER BY "order"
                    """
                    subphases = DatabaseConnection.execute_query(self.conn, subphases_query, (phase['id'],))
                
                    # Calculate phase progress based on subphases
                    completed_subphases = 0
                    total_subphases = len(subphases) if subphases else 0
                
                    if total_subphases > 0:
                        for subphase in subphases:
                            if subphase.get('status') == 'Completed':
                                completed_subphases += 1
                    
                        phase_progress = (completed_subphases / total_subphases) * 100
                    else:
                        # If no subphases, estimate from phase status
                        if phase.get('status') == 'Completed':
                            phase_progress = 100
                        elif phase.get('status') == 'Progress':
                            phase_progress = 50
                        else:
                            phase_progress = 0
                
                    # We'll weight each phase equally
                    weight = 1
                    total_weight += weight
                    weighted_sum += weight * phase_progress
                
                    # Track if this is the current active phase
                    if phase.get('status') == 'Progress':
                        # Get the current active subphase
                        active_subphase = None
                        for subphase in subphases:
                            if subphase.get('status') in ['Progress', 'Todo']:
                                active_subphase = subphase
                                break
                    
                        current_phase = {
                            'id': phase.get('id'),
                            'name': phase.get('name'),
                            'progress': phase_progress,
                            'subphases': subphases,
                            'order': phase.get('order'),
                            'current_subphase': active_subphase
                        }
                
                    # Add to phase info
                    phase_info.append({
                        'id': phase['id'],
                        'name': phase['name'],
                        'status': phase['status'],
                        'progress': phase_progress,
                        'subphases': subphases,
                        'order': phase.get('order')
                    })
            
                if total_weight > 0:
                    overall_progress = weighted_sum / total_weight
        
            return {
                'phases': phase_info,
                'current_phase': current_phase,
                'overall_progress': overall_progress,
                'phase_count': phase_count
            }
        
        except Exception as e:
            logger.error(f"Error getting project phase info: {e}")
            return {
                'phases': [],
                'current_phase': None,
                'overall_progress': 0,
                'phase_count': 0
            }
    
    # In app/database/phase_queries.py
    def get_project_phase_status(self, project_id=None):
        """
        Get the current phase and stage status for a project.
        
        Args:
            project_id (str, optional): Project ID or name.
            
        Returns:
            Dict with phase info or None if not found
        """
        try:
            # Handle case where project_id is None
            if project_id is None:
                logger.error("Project name is required")
                return None
                
            # Try to get project directly first (handle both UUID and name)
            project = None
            try:
                # Try as UUID
                project = self._project.get_project_details(project_id)
            except:
                # Not a UUID, try as name
                pass
                
            # If not found by ID, try by name
            if not project:
                try:
                    project = self._project.get_project_by_name(project_id)
                except:
                    logger.error(f"Project not found: {project_id}")
                    return None
            
            # If still not found, return None
            if not project:
                logger.error(f"Project not found: {project_id}")
                return None
                
            # Extract phase info
            return {
                "project_id": project.get('id'),
                "project_name": project.get('name', 'Unknown'),
                "status": project.get('status', 'Unknown'),
                "current_phase": project.get('current_phase', 'Unknown'),
                "phase_info": project.get('phase_info', {}),
                "overall_progress": project.get('phase_info', {}).get('overall_progress', 0),
                "startDate": project.get('startDate')
            }
            
        except Exception as e:
            logger.error(f"Error getting project phase status: {e}")
            return None

    def get_pending_phase_tasks(self, project_id, phase_id=None, stage_id=None):
        """
        Get pending tasks for a specific phase and stage of a project.
        
        Args:
            project_id (str): Project ID or name
            phase_id (str, optional): Phase ID. If not provided, uses current phase.
            stage_id (str, optional): Stage ID. If not provided, uses current stage.
            
        Returns:
            List of pending tasks
        """
        try:
            # Handle case where project_id is None
            if not project_id:
                logger.error("Project ID or name is required")
                return None
                
            # Try to get project directly (handle both UUID and name)
            project = None
            try:
                # Try as UUID
                project = self._project.get_project_details(project_id)
            except:
                # Not a UUID, try as name
                pass
                
            # If not found by ID, try by name
            if not project:
                try:
                    project = self._project.get_project_by_name(project_id)
                except:
                    logger.error(f"Project not found: {project_id}")
                    return None
            
            # If still not found, return None
            if not project:
                logger.error(f"Project not found: {project_id}")
                return None
                
            # Project found, now we can proceed with getting phase information
            return project
            
        except Exception as e:
            logger.error(f"Error getting pending phase tasks: {e}")
            return None
                
    def _is_uuid(self, value):
        """Check if a string is a valid UUID."""
        try:
            uuid.UUID(str(value))
            return True
        except (ValueError, AttributeError):
            return False
