"""
Database queries for the construction chatbot.
This module provides methods to interact with the database.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.database.base_queries import BaseQueries
from app.database.project_queries import ProjectQueries
from app.database.phase_queries import PhaseQueries
from app.database.selection_queries import SelectionQueries
from app.database.walkthrough_queries import WalkthroughQueries
from app.database.procurement_queries import ProcurementQueries
from app.database.financial_queries import FinancialQueries

# Setup logging
logger = logging.getLogger(__name__)

# Use composition instead of inheritance to avoid MRO issues
class DatabaseQueries:
    """
    Database query methods for the chatbot.
    
    This class uses composition to incorporate all specialized query classes.
    """
    
    def __init__(self):
        """Initialize the database queries."""
        # Initialize the base query object
        self._base = BaseQueries()
        
        # Share connection among all query objects
        self.conn = self._base.conn
        
        # Create specialized query objects
        # Initialize phase queries first since other modules depend on it
        self._phase = PhaseQueries(self.conn)
        
        # Initialize other query objects with proper dependencies
        self._project = ProjectQueries(self.conn, self._phase)
        self._selection = SelectionQueries(self.conn)
        self._walkthrough = WalkthroughQueries(self.conn)
        self._procurement = ProcurementQueries(self.conn)
        self._financial = FinancialQueries(self.conn)
        
    # Forward method calls to the appropriate query object
    
    # Base query methods
    def _get_client_name(self, client_id):
        return self._base._get_client_name(client_id)
        
    def _get_user_name(self, user_id):
        return self._base._get_user_name(user_id)
        
    def _get_project_status(self, percent_complete):
        return self._base._get_project_status(percent_complete)
    
    # Project query methods
    def get_all_projects(self, limit=100):
        return self._project.get_all_projects(limit)
        
    def get_project_details(self, project_id):
        return self._project.get_project_details(project_id)
        
    def get_project_by_name(self, project_name):
        return self._project.get_project_by_name(project_name)
        
    def get_project_status(self, project_id):
        return self._project.get_project_status(project_id)
        
    def find_project_by_partial_name(self, partial_name):
        return self._project.find_project_by_partial_name(partial_name)
    
    # Phase query methods
    def get_project_phase_info(self, project_id):
        return self._phase.get_project_phase_info(project_id)
        
    def get_project_phase_status(self, project_id):
        return self._phase.get_project_phase_status(project_id)
        
    def get_pending_phase_tasks(self, project_id, phase_id, stage_id):
        return self._phase.get_pending_phase_tasks(project_id, phase_id, stage_id)
    
    # Selection query methods
    def get_selections_by_project(self, project_id, status="Open"):
        return self._selection.get_selections_by_project(project_id, status)
        
    def get_all_selections(self, status="Open"):
        return self._selection.get_all_selections(status)
        
    def get_selection_by_name(self, selection_name):
        return self._selection.get_selection_by_name(selection_name)
        
    def find_selection_by_partial_name(self, partial_name, project_name=None):
        return self._selection.find_selection_by_partial_name(partial_name, project_name)
        
    def get_upcoming_selections_by_project(self, project_id, end_date):
        return self._selection.get_upcoming_selections_by_project(project_id, end_date)
        
    def get_all_upcoming_selections(self, end_date):
        return self._selection.get_all_upcoming_selections(end_date)
        
    def get_selection_list(self, project_id=None, status="Open"):
        return self._selection.get_selection_list(project_id, status)
        
    def get_upcoming_selections(self, days=14):
        return self._selection.get_upcoming_selections(days)
    
    # Walkthrough query methods
    def get_walkthroughs_by_type(self, walkthrough_type, status="Not Scheduled"):
        return self._walkthrough.get_walkthroughs_by_type(walkthrough_type, status)
        
    def get_project_recent_walkthrough(self, project_id, walkthrough_type):
        return self._walkthrough.get_project_recent_walkthrough(project_id, walkthrough_type)
    
    # Procurement query methods
    def get_trades_needing_po(self, project_id=None):
        return self._procurement.get_trades_needing_po(project_id)
    
    # Financial query methods
    def get_payment_milestones(self, project_id):
        return self._financial.get_payment_milestones(project_id)
        
    def get_current_payment_milestone(self, project_id):
        return self._financial.get_current_payment_milestone(project_id)
        
    def get_payment_milestone_by_number(self, project_id, milestone_number):
        return self._financial.get_payment_milestone_by_number(project_id, milestone_number)
        
    def get_billable_projects(self):
        return self._financial.get_billable_projects()