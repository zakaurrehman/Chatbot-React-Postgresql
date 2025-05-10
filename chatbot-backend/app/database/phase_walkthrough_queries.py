# NEW: Phase and walkthrough queries
"""
Database queries for Project Phase Tracking and Walkthrough Management.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database.connection import DatabaseConnection

# Setup logging
logger = logging.getLogger(__name__)

# =============== Project Phase Tracking Functions ===============

def get_project_phase_info_enhanced(conn, project_id: str = None, search_term: str = None) -> Dict[str, Any]:
    """
    Get detailed phase and subphase information for a project.
    
    Args:
        conn: Database connection
        project_id: UUID of the project or project name
        search_term: Project name to search for
        
    Returns:
        Dictionary with detailed phase information
    """
    try:
        project = None
        
        # If search_term is provided, use it first
        if search_term:
            query = """
                SELECT id, name FROM projects WHERE name ILIKE %s
            """
            project = DatabaseConnection.execute_query(conn, query, (f'%{search_term}%',), fetch_one=True)
        
        # If not found by search term or no search term provided, try project_id
        if not project and project_id:
            query = """
                SELECT id, name FROM projects WHERE id = %s OR name = %s
            """
            project = DatabaseConnection.execute_query(conn, query, (project_id, project_id), fetch_one=True)
        
        if not project:
            return {
                "error": "Project not found",
                "phases": [],
                "current_phase": None,
                "overall_progress": 0,
                "phase_count": 0
            }
        
        # Get all phases for this project
        phases_query = """
            SELECT id, name, status, "order", start_date, 
                   target_end_date, actual_end_date
            FROM phases
            WHERE project_id = %s
            ORDER BY "order"
        """
        phases = DatabaseConnection.execute_query(conn, phases_query, (project['id'],))
        
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
                    SELECT id, name, status, "order", start_date, end_date, dependencies
                    FROM subphases
                    WHERE phase_id = %s
                    ORDER BY "order"
                """
                subphases = DatabaseConnection.execute_query(conn, subphases_query, (phase['id'],))
                
                # Get tasks for each subphase
                enhanced_subphases = []
                for subphase in subphases:
                    tasks_query = """
                        SELECT id, name, description, status, due_date, 
                               completion_date, assigned_to
                        FROM phase_tasks
                        WHERE subphase_id = %s
                        ORDER BY due_date
                    """
                    tasks = DatabaseConnection.execute_query(conn, tasks_query, (subphase['id'],))
                    
                    # Add user names to tasks
                    for task in tasks:
                        if task.get('assigned_to'):
                            task['assigned_to_name'] = _get_user_name(conn, task['assigned_to'])
                    
                    # Add tasks to subphase
                    subphase_with_tasks = dict(subphase)
                    subphase_with_tasks['tasks'] = tasks
                    
                    # Calculate subphase progress based on tasks
                    completed_tasks = sum(1 for task in tasks if task.get('status') == 'Completed')
                    total_tasks = len(tasks)
                    if total_tasks > 0:
                        subphase_with_tasks['progress'] = (completed_tasks / total_tasks) * 100
                    else:
                        # If no tasks, estimate based on subphase status
                        subphase_with_tasks['progress'] = _get_progress_from_status(subphase.get('status', 'Not Started'))
                    
                    enhanced_subphases.append(subphase_with_tasks)
                
                # Calculate phase progress based on subphases
                completed_subphases = 0
                total_subphases = len(enhanced_subphases)
                subphase_progress_sum = 0
                
                for subphase in enhanced_subphases:
                    subphase_progress_sum += subphase.get('progress', 0)
                    if subphase.get('status') == 'Completed':
                        completed_subphases += 1
                
                if total_subphases > 0:
                    phase_progress = subphase_progress_sum / total_subphases
                else:
                    # If no subphases, estimate from phase status
                    phase_progress = _get_progress_from_status(phase.get('status', 'Not Started'))
                
                # Weight each phase equally for overall progress
                weight = 1
                total_weight += weight
                weighted_sum += weight * phase_progress
                
                # Track if this is the current active phase
                if phase.get('status') == 'Progress':
                    # Find the current active subphase
                    active_subphase = None
                    incomplete_tasks = []
                    
                    for subphase in enhanced_subphases:
                        if subphase.get('status') in ['Progress', 'Todo']:
                            active_subphase = subphase
                            # Collect incomplete tasks for this subphase
                            incomplete_tasks = [
                                task for task in subphase.get('tasks', [])
                                if task.get('status') != 'Completed'
                            ]
                            break
                    
                    current_phase = {
                        'name': phase.get('name'),
                        'progress': phase_progress,
                        'subphases': enhanced_subphases,
                        'order': phase.get('order'),
                        'current_subphase': active_subphase,
                        'incomplete_tasks': incomplete_tasks
                    }
                
                # Add to phase info
                phase_info.append({
                    'id': phase['id'],
                    'name': phase['name'],
                    'status': phase['status'],
                    'progress': phase_progress,
                    'start_date': phase.get('start_date'),
                    'target_end_date': phase.get('target_end_date'),
                    'actual_end_date': phase.get('actual_end_date'),
                    'subphases': enhanced_subphases,
                    'order': phase.get('order')
                })
            
            if total_weight > 0:
                overall_progress = weighted_sum / total_weight
        
        return {
            'project_id': project['id'],
            'project_name': project['name'],
            'phases': phase_info,
            'current_phase': current_phase,
            'overall_progress': overall_progress,
            'phase_count': phase_count
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced project phase info: {e}")
        return {
            "error": str(e),
            "phases": [],
            "current_phase": None,
            "overall_progress": 0,
            "phase_count": 0
        }

def get_current_phase_incomplete_items(conn, project_id: str = None, search_term: str = None) -> List[Dict[str, Any]]:
    """
    Get items that still need to be completed in the current phase and stage.
    
    Args:
        conn: Database connection
        project_id: UUID of the project or project name
        search_term: Project name to search for
        
    Returns:
        List of incomplete items
    """
    try:
        # Get project phase info which includes incomplete tasks
        phase_info = get_project_phase_info_enhanced(conn, project_id, search_term)
        
        if phase_info.get('error'):
            return [{"error": phase_info['error']}]
        
        # Extract the current phase information
        current_phase = phase_info.get('current_phase')
        
        if not current_phase:
            return [{"message": f"No active phase found for project {phase_info.get('project_name')}"}]
        
        # Get the current subphase
        current_subphase = current_phase.get('current_subphase')
        
        if not current_subphase:
            return [{"message": f"No active subphase found in phase {current_phase.get('name')}"}]
        
        # Get incomplete tasks for the current subphase
        incomplete_tasks = current_phase.get('incomplete_tasks', [])
        
        if not incomplete_tasks:
            return [{
                "message": f"All tasks in the current subphase '{current_subphase.get('name')}' are completed",
                "phase": current_phase.get('name'),
                "subphase": current_subphase.get('name')
            }]
        
        # Enhance the result with project and phase information
        for task in incomplete_tasks:
            task['project_name'] = phase_info.get('project_name')
            task['phase_name'] = current_phase.get('name')
            task['subphase_name'] = current_subphase.get('name')
        
        return incomplete_tasks
        
    except Exception as e:
        logger.error(f"Error getting current phase incomplete items: {e}")
        return [{"error": str(e)}]

def _get_progress_from_status(status: str) -> float:
    """
    Convert a status string to a progress percentage.
    
    Args:
        status: Status string
        
    Returns:
        Progress percentage
    """
    status_map = {
        'Not Started': 0.0,
        'Todo': 0.0,
        'In Progress': 50.0,
        'Progress': 50.0,
        'Review': 90.0,
        'Completed': 100.0
    }
    
    return status_map.get(status, 0.0)

# =============== Walkthrough Management Functions ===============

def get_pending_walkthroughs(conn, walkthrough_type: str = None, project_id: str = None, search_term: str = None) -> List[Dict[str, Any]]:
    """
    Get walkthroughs that need to be scheduled.
    
    Args:
        conn: Database connection
        walkthrough_type: Type of walkthrough (PD, Client, etc.)
        project_id: UUID of the project or project name
        search_term: Project name to search for
        
    Returns:
        List of walkthroughs that need scheduling
    """
    try:
        project_condition = ""
        project_params = []
        
        if project_id or search_term:
            project = None
            
            # If search_term is provided, use it first
            if search_term:
                query = """
                    SELECT id FROM projects WHERE name ILIKE %s
                """
                project = DatabaseConnection.execute_query(conn, query, (f'%{search_term}%',), fetch_one=True)
            
            # If not found by search term or no search term provided, try project_id
            if not project and project_id:
                query = """
                    SELECT id FROM projects WHERE id = %s OR name = %s
                """
                project = DatabaseConnection.execute_query(conn, query, (project_id, project_id), fetch_one=True)
            
            if project:
                project_condition = "AND w.project_id = %s"
                project_params.append(project['id'])
        
        type_condition = ""
        if walkthrough_type:
            type_condition = """
                AND wt.name ILIKE %s
            """
            project_params.append(f'%{walkthrough_type}%')
        
        # Get walkthroughs that need to be scheduled
        query = f"""
            SELECT w.id, w.project_id, w.status, w.required_date, 
                   w.scheduled_date, w.notes, w."createdAt",
                   p.name as project_name,
                   wt.name as walkthrough_type
            FROM walkthroughs w
            JOIN projects p ON w.project_id = p.id
            JOIN walkthrough_types wt ON w.walkthrough_type_id = wt.id
            WHERE w.status = 'Pending'
            {project_condition}
            {type_condition}
            ORDER BY w.required_date ASC
        """
        
        walkthroughs = DatabaseConnection.execute_query(conn, query, project_params)
        
        return walkthroughs
        
    except Exception as e:
        logger.error(f"Error getting pending walkthroughs: {e}")
        return []

def get_walkthrough_status(conn, project_id: str = None, search_term: str = None, walkthrough_type: str = None) -> Dict[str, Any]:
    """
    Get status of the most recent walkthrough of a certain type.
    
    Args:
        conn: Database connection
        project_id: UUID of the project or project name
        search_term: Project name to search for
        walkthrough_type: Type of walkthrough (e.g., 'Client')
        
    Returns:
        Dictionary with walkthrough status information
    """
    try:
        project = None
        
        # If search_term is provided, use it first
        if search_term:
            query = """
                SELECT id, name FROM projects WHERE name ILIKE %s
            """
            project = DatabaseConnection.execute_query(conn, query, (f'%{search_term}%',), fetch_one=True)
        
        # If not found by search term or no search term provided, try project_id
        if not project and project_id:
            query = """
                SELECT id, name FROM projects WHERE id = %s OR name = %s
            """
            project = DatabaseConnection.execute_query(conn, query, (project_id, project_id), fetch_one=True)
        
        if not project:
            return {"error": "Project not found"}
        
        type_condition = ""
        params = [project['id']]
        
        if walkthrough_type:
            type_condition = "AND wt.name ILIKE %s"
            params.append(f'%{walkthrough_type}%')
        
        # Get the most recent walkthrough of the specified type
        query = f"""
            SELECT w.id, w.status, w.required_date, w.scheduled_date, 
                   w.completion_date, w.notes, w."createdAt",
                   wt.name as walkthrough_type
            FROM walkthroughs w
            JOIN walkthrough_types wt ON w.walkthrough_type_id = wt.id
            WHERE w.project_id = %s
            {type_condition}
            ORDER BY w.scheduled_date DESC, w."createdAt" DESC
            LIMIT 1
        """
        
        walkthrough = DatabaseConnection.execute_query(conn, query, params, fetch_one=True)
        
        if not walkthrough:
            return {
                "project_id": project['id'],
                "project_name": project['name'],
                "walkthrough_found": False,
                "message": f"No {walkthrough_type if walkthrough_type else ''} walkthrough found for this project"
            }
        
        # Get participants for this walkthrough
        participants_query = """
            SELECT wp.role, u."firstName", u."lastName", u.email
            FROM walkthrough_participants wp
            JOIN users u ON wp.user_id = u.id
            WHERE wp.walkthrough_id = %s
        """
        participants = DatabaseConnection.execute_query(conn, participants_query, (walkthrough['id'],))
        
        # Get checklist items for this walkthrough
        items_query = """
            SELECT description, status, notes
            FROM walkthrough_items
            WHERE walkthrough_id = %s
        """
        items = DatabaseConnection.execute_query(conn, items_query, (walkthrough['id'],))
        
        # Calculate some metrics
        completed_items = sum(1 for item in items if item.get('status') == 'Approved')
        total_items = len(items)
        
        has_been_completed = walkthrough.get('status') == 'Completed'
        
        result = {
            "project_id": project['id'],
            "project_name": project['name'],
            "walkthrough_id": walkthrough['id'],
            "walkthrough_type": walkthrough['walkthrough_type'],
            "status": walkthrough['status'],
            "required_date": walkthrough.get('required_date'),
            "scheduled_date": walkthrough.get('scheduled_date'),
            "completion_date": walkthrough.get('completion_date'),
            "participants": participants,
            "checklist_items": items,
            "items_completed": completed_items,
            "total_items": total_items,
            "completion_percentage": (completed_items / total_items * 100) if total_items > 0 else 0,
            "walkthrough_found": True,
            "has_been_completed": has_been_completed
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting walkthrough status: {e}")
        return {"error": str(e)}

def _get_user_name(conn, user_id: str) -> str:
    """
    Get user name from user_id.
    
    Args:
        conn: Database connection
        user_id: UUID of the user
        
    Returns:
        User name as string
    """
    try:
        query = """
            SELECT "firstName", "lastName", email FROM users WHERE id = %s
        """
        user = DatabaseConnection.execute_query(conn, query, (user_id,), fetch_one=True)
        
        if user:
            return f"{user['firstName']} {user['lastName']}"
        return "Unknown User"
    except Exception as e:
        logger.error(f"Error getting user name: {e}")
        return "Unknown User"