#!/usr/bin/env python3
import psycopg2
import psycopg2.extras
import argparse
import datetime
import sys
import re
from tabulate import tabulate

# Database connection parameters
DB_PARAMS = {
    "dbname": "neondb",
    "user": "neondb_owner",
    "password": "npg_X02rGjyNYvSu",
    "host": "ep-crimson-glitter-a44yhjju-pooler.us-east-1.aws.neon.tech",
    "port": "5432",
    "sslmode": "require"
}

class ConstructionDatabaseQueryTool:
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish a connection to the database."""
        try:
            self.conn = psycopg2.connect(**DB_PARAMS)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            print("Database connection established successfully.")
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
            
    def disconnect(self):
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Database connection closed.")
            
    def execute_query(self, query, params=None):
        """Execute a query and return the results."""
        try:
            self.cursor.execute(query, params)
            if self.cursor.description:
                rows = self.cursor.fetchall()
                description = self.cursor.description
                return rows, description, None
            return [], None, None
        except Exception as e:
            return [], None, str(e)
            
    def format_results(self, rows, description, title):
        """Format query results as a table."""
        if not rows or not description:
            return "No results found."
            
        # Create header from column names
        headers = [col.name for col in description]
        
        # Format data for tabulate
        table_data = []
        for row in rows:
            # Convert to a list with proper handling of None values
            table_row = []
            for value in row:
                if isinstance(value, datetime.datetime) or isinstance(value, datetime.date):
                    table_row.append(value.strftime('%Y-%m-%d'))
                elif value is None:
                    table_row.append('')
                else:
                    table_row.append(str(value))
            table_data.append(table_row)
            
        # Format the table
        table = tabulate(table_data, headers=headers, tablefmt="grid")
        return f"{title}:\n\n{table}"
    
    # Selection Management Functions
    def open_selection_items(self, project_name):
        """Get open selection items for a specific project."""
        query = """
        SELECT ci.id, ci.label, ci."createdAt" AS created, ci."updatedAt" AS updated
        FROM checklist_items ci
        JOIN checklists c ON ci."checklistId" = c.id
        JOIN projects p ON c."projectId" = p.id
        WHERE p.name ILIKE %s
        AND ci.label ILIKE %s
        AND ci.checked = false
        ORDER BY ci."createdAt" DESC
        """
        rows, description, error = self.execute_query(query, (f"%{project_name}%", "%selection%"))
        
        if error:
            # Try a simpler query as fallback
            query = """
            SELECT ci.id, ci.label, ci."createdAt" AS created, ci."updatedAt" AS updated
            FROM checklist_items ci
            JOIN checklists c ON ci."checklistId" = c.id
            JOIN projects p ON c."projectId" = p.id
            WHERE p.name ILIKE %s
            AND ci.checked = false
            ORDER BY ci."createdAt" DESC
            LIMIT 20
            """
            rows, description, error = self.execute_query(query, (f"%{project_name}%",))
            
        if error:
            return f"Error retrieving open selection items: {error}"
            
        return self.format_results(rows, description, f"Open selection items for project {project_name}")
    
    def selection_overdue(self, selection_name):
        """Check how overdue a specific selection is."""
        query = """
        SELECT ci.id, ci.label, ci."createdAt" AS created, 
               CURRENT_DATE - ci."createdAt"::date AS days_overdue
        FROM checklist_items ci
        WHERE ci.label ILIKE %s
        AND ci.checked = false
        ORDER BY days_overdue DESC
        """
        rows, description, error = self.execute_query(query, (f"%{selection_name}%",))
        
        if error:
            return f"Error checking selection overdue: {error}"
            
        return self.format_results(rows, description, f"Overdue status for selection '{selection_name}'")
    
    def upcoming_selections(self, weeks=2):
        """Get selection items coming up in the next X weeks."""
        query = """
        SELECT ci.id, ci.label, p.name AS project_name
        FROM checklist_items ci
        JOIN checklists c ON ci."checklistId" = c.id
        JOIN projects p ON c."projectId" = p.id
        WHERE ci.label ILIKE %s
        AND ci.checked = false
        ORDER BY ci."createdAt" DESC
        LIMIT 20
        """
        rows, description, error = self.execute_query(query, ("%selection%",))
        
        if error:
            return f"Error retrieving upcoming selections: {error}"
            
        return self.format_results(rows, description, f"Selections coming up in the next {weeks} weeks")
    
    # Project Phase Tracking Functions
    def project_stage_phase(self, project_name):
        """Get the current phase and stage information for a project."""
        query = """
        SELECT p.name AS project_name, ph.name AS phase_name, s.name AS stage_name,
               ph.status AS phase_status, s.status AS stage_status
        FROM projects p
        JOIN phases ph ON p.id = ph."projectId"
        JOIN stages s ON ph.id = s."phaseId"
        WHERE p.name ILIKE %s
        ORDER BY ph."order", s."order"
        """
        rows, description, error = self.execute_query(query, (f"%{project_name}%",))
        
        if error:
            # Try a simpler query
            query = """
            SELECT p.name AS project_name, ph.name AS phase_name, ph.status AS phase_status
            FROM projects p
            JOIN phases ph ON p.id = ph."projectId"
            WHERE p.name ILIKE %s
            ORDER BY ph."order"
            """
            rows, description, error = self.execute_query(query, (f"%{project_name}%",))
            
        if error:
            return f"Error retrieving project phase: {error}"
            
        return self.format_results(rows, description, f"Phase information for project {project_name}")
    
    def incomplete_phase_items(self, project_name):
        """Get items that still need to be completed in the current phase and stage."""
        query = """
        SELECT ci.id, ci.label, ph.name AS phase_name, s.name AS stage_name
        FROM checklist_items ci
        JOIN checklists c ON ci."checklistId" = c.id
        JOIN projects p ON c."projectId" = p.id
        JOIN phases ph ON p.id = ph."projectId"
        JOIN stages s ON ph.id = s."phaseId"
        WHERE p.name ILIKE %s
        AND ci.checked = false
        AND ph.status = 'active'
        ORDER BY ph."order", s."order"
        """
        rows, description, error = self.execute_query(query, (f"%{project_name}%",))
        
        if error:
            # Try a simpler query
            query = """
            SELECT ci.id, ci.label
            FROM checklist_items ci
            JOIN checklists c ON ci."checklistId" = c.id
            JOIN projects p ON c."projectId" = p.id
            WHERE p.name ILIKE %s
            AND ci.checked = false
            LIMIT 20
            """
            rows, description, error = self.execute_query(query, (f"%{project_name}%",))
            
        if error:
            return f"Error retrieving incomplete phase items: {error}"
            
        return self.format_results(rows, description, f"Incomplete items in current phase for project {project_name}")
    
    # Walkthrough Management Functions
    def pd_walkthroughs_needed(self):
        """Find PD walkthroughs that need to be scheduled."""
        query = """
        SELECT p.name AS project_name, ci.label
        FROM checklist_items ci
        JOIN checklists c ON ci."checklistId" = c.id
        JOIN projects p ON c."projectId" = p.id
        WHERE ci.label ILIKE %s
        AND ci.checked = false
        ORDER BY p.name
        """
        rows, description, error = self.execute_query(query, ("%PD walkthrough%",))
        
        if error:
            return f"Error retrieving PD walkthroughs: {error}"
            
        return self.format_results(rows, description, "PD Walkthroughs that need to be scheduled")
    
    def client_walkthroughs_needed(self):
        """Find client walkthroughs that need to be scheduled."""
        query = """
        SELECT p.name AS project_name, ci.label
        FROM checklist_items ci
        JOIN checklists c ON ci."checklistId" = c.id
        JOIN projects p ON c."projectId" = p.id
        WHERE ci.label ILIKE %s
        AND ci.checked = false
        ORDER BY p.name
        """
        rows, description, error = self.execute_query(query, ("%client walkthrough%",))
        
        if error:
            return f"Error retrieving client walkthroughs: {error}"
            
        return self.format_results(rows, description, "Client Walkthroughs that need to be scheduled")
    
    def recent_client_walkthrough(self, project_name):
        """Check if the most recent client walkthrough has been completed."""
        query = """
        SELECT ci.id, ci.label, ci.checked, ci."updatedAt" AS last_updated
        FROM checklist_items ci
        JOIN checklists c ON ci."checklistId" = c.id
        JOIN projects p ON c."projectId" = p.id
        WHERE p.name ILIKE %s
        AND ci.label ILIKE %s
        ORDER BY ci."createdAt" DESC
        LIMIT 1
        """
        rows, description, error = self.execute_query(query, (f"%{project_name}%", "%client walkthrough%"))
        
        if error:
            return f"Error checking client walkthrough status: {error}"
            
        return self.format_results(rows, description, f"Recent client walkthrough for project {project_name}")
    
    # Procurement Tracking Functions
    def pending_purchase_orders(self, project_name=None):
        """Find trades/items that still need purchase orders."""
        if project_name:
            query = """
            SELECT p.name AS project_name, ci.label
            FROM checklist_items ci
            JOIN checklists c ON ci."checklistId" = c.id
            JOIN projects p ON c."projectId" = p.id
            WHERE p.name ILIKE %s
            AND (
                ci.label ILIKE %s OR
                ci.label ILIKE %s
            )
            AND ci.checked = false
            ORDER BY p.name
            """
            rows, description, error = self.execute_query(
                query, 
                (f"%{project_name}%", "%purchase order%", "%PO%")
            )
        else:
            query = """
            SELECT p.name AS project_name, ci.label
            FROM checklist_items ci
            JOIN checklists c ON ci."checklistId" = c.id
            JOIN projects p ON c."projectId" = p.id
            WHERE (
                ci.label ILIKE %s OR
                ci.label ILIKE %s
            )
            AND ci.checked = false
            ORDER BY p.name
            """
            rows, description, error = self.execute_query(
                query, 
                ("%purchase order%", "%PO%")
            )
            
        if error:
            return f"Error retrieving pending purchase orders: {error}"
            
        return self.format_results(rows, description, "Items needing purchase orders")
    
    # Financial Milestone Tracking Functions
    def payment_milestone_status(self, project_name):
        """Get the current payment milestone for a project."""
        query = """
        SELECT p.name AS project_name, ci.label, ci.checked
        FROM checklist_items ci
        JOIN checklists c ON ci."checklistId" = c.id
        JOIN projects p ON c."projectId" = p.id
        WHERE p.name ILIKE %s
        AND (
            ci.label ILIKE %s OR
            ci.label ILIKE %s
        )
        ORDER BY ci."createdAt" DESC
        """
        rows, description, error = self.execute_query(
            query, 
            (f"%{project_name}%", "%payment%", "%milestone%")
        )
        
        if error:
            return f"Error retrieving payment milestone status: {error}"
            
        return self.format_results(rows, description, f"Payment milestone status for project {project_name}")
    
    def billable_projects(self):
        """Find projects that can be billed this week."""
        query = """
        SELECT p.name AS project_name, ci.label, ci.checked
        FROM checklist_items ci
        JOIN checklists c ON ci."checklistId" = c.id
        JOIN projects p ON c."projectId" = p.id
        WHERE (
            ci.label ILIKE %s OR
            ci.label ILIKE %s OR
            ci.label ILIKE %s
        )
        AND ci.checked = false
        ORDER BY p.name
        """
        rows, description, error = self.execute_query(
            query, 
            ("%payment%", "%milestone%", "%invoice%")
        )
        
        if error:
            return f"Error retrieving billable projects: {error}"
            
        return self.format_results(rows, description, "Projects that can be billed this week")
    
    def check_specific_milestone(self, project_name, milestone_info):
        """Check if a specific payment milestone has been issued."""
        query = """
        SELECT p.name AS project_name, ci.label, ci.checked
        FROM checklist_items ci
        JOIN checklists c ON ci."checklistId" = c.id
        JOIN projects p ON c."projectId" = p.id
        WHERE p.name ILIKE %s
        AND ci.label ILIKE %s
        """
        rows, description, error = self.execute_query(
            query, 
            (f"%{project_name}%", f"%{milestone_info}%")
        )
        
        if error:
            return f"Error checking specific milestone: {error}"
            
        return self.format_results(rows, description, f"Status of milestone '{milestone_info}' for project {project_name}")
    
    # General Project Functions
    def list_projects(self):
        """List all projects in the database."""
        query = """
        SELECT id, name, "startDate", "percentComplete", "createdAt", "updatedAt"
        FROM projects
        ORDER BY name
        """
        rows, description, error = self.execute_query(query)
        
        if error:
            return f"Error retrieving projects: {error}"
            
        return self.format_results(rows, description, "List of Projects")
    
    def get_project_details(self, project_name):
        """Get detailed information about a specific project."""
        query = """
        SELECT p.*
        FROM projects p
        WHERE p.name ILIKE %s
        """
        rows, description, error = self.execute_query(query, (f"%{project_name}%",))
        
        if error:
            return f"Error retrieving project details: {error}"
            
        return self.format_results(rows, description, f"Details for project {project_name}")
    
    def get_project_tasks(self, project_name):
        """Get tasks for a specific project."""
        query = """
        SELECT t.id, t.description, t.status, t."dueDate"
        FROM tasks t
        JOIN projects p ON t."projectId" = p.id
        WHERE p.name ILIKE %s
        ORDER BY t."dueDate"
        """
        rows, description, error = self.execute_query(query, (f"%{project_name}%",))
        
        if error:
            return f"Error retrieving project tasks: {error}"
            
        return self.format_results(rows, description, f"Tasks for project {project_name}")
    
    def parse_and_execute_query(self, query_text):
        """Parse the user's query and execute the appropriate function."""
        # Selection Management
        if re.search(r"open selection items? for (.+?)( project)?", query_text, re.IGNORECASE):
            project_name = re.search(r"open selection items? for (.+?)( project)?", query_text, re.IGNORECASE).group(1)
            return self.open_selection_items(project_name)
            
        elif re.search(r"how overdue is (.+?)( selection)?", query_text, re.IGNORECASE):
            selection_name = re.search(r"how overdue is (.+?)( selection)?", query_text, re.IGNORECASE).group(1)
            return self.selection_overdue(selection_name)
            
        elif re.search(r"selections coming up in the next (\d+) weeks?", query_text, re.IGNORECASE):
            weeks = int(re.search(r"selections coming up in the next (\d+) weeks?", query_text, re.IGNORECASE).group(1))
            return self.upcoming_selections(weeks)
            
        elif re.search(r"what selections are coming up", query_text, re.IGNORECASE):
            return self.upcoming_selections()
            
        # Project Phase Tracking
        elif re.search(r"what stage and phase is (.+?)( project)? in", query_text, re.IGNORECASE):
            project_name = re.search(r"what stage and phase is (.+?)( project)? in", query_text, re.IGNORECASE).group(1)
            return self.project_stage_phase(project_name)
            
        elif re.search(r"items? (?:still )?need(?:ing|s)? to be completed in (?:the )?current phase (?:and stage )?(?:for )?(.+?)( project)?", query_text, re.IGNORECASE):
            project_name = re.search(r"items? (?:still )?need(?:ing|s)? to be completed in (?:the )?current phase (?:and stage )?(?:for )?(.+?)( project)?", query_text, re.IGNORECASE).group(1)
            return self.incomplete_phase_items(project_name)
            
        # Walkthrough Management
        elif re.search(r"(?:do )?any PD walkthroughs? need(?:ing|s)? to be scheduled", query_text, re.IGNORECASE):
            return self.pd_walkthroughs_needed()
            
        elif re.search(r"(?:do )?any client walkthroughs? need(?:ing|s)? to be scheduled", query_text, re.IGNORECASE):
            return self.client_walkthroughs_needed()
            
        elif re.search(r"(?:has )?(?:the )?most recent client walkthrough (?:been )?completed (?:for )?(.+?)( project)?", query_text, re.IGNORECASE):
            project_name = re.search(r"(?:has )?(?:the )?most recent client walkthrough (?:been )?completed (?:for )?(.+?)( project)?", query_text, re.IGNORECASE).group(1)
            return self.recent_client_walkthrough(project_name)
            
        # Procurement Tracking
        elif re.search(r"(?:what )?(?:still )?needs? to be bought out|(?:what )?trades (?:still )?need a purchase order", query_text, re.IGNORECASE):
            # Extract project name if given
            project_match = re.search(r"for (.+?)( project)?", query_text, re.IGNORECASE)
            if project_match:
                project_name = project_match.group(1)
                return self.pending_purchase_orders(project_name)
            else:
                return self.pending_purchase_orders()
                
        # Financial Milestone Tracking
        elif re.search(r"what payment milestone is (?:project )?(.+?)( project)? currently at", query_text, re.IGNORECASE):
            project_name = re.search(r"what payment milestone is (?:project )?(.+?)( project)? currently at", query_text, re.IGNORECASE).group(1)
            return self.payment_milestone_status(project_name)
            
        elif re.search(r"what projects can be billed this week", query_text, re.IGNORECASE):
            return self.billable_projects()
            
        elif re.search(r"has payment milestone (.+?) (?:been )?issued (?:for )?(.+?)( project)?", query_text, re.IGNORECASE):
            match = re.search(r"has payment milestone (.+?) (?:been )?issued (?:for )?(.+?)( project)?", query_text, re.IGNORECASE)
            milestone_info = match.group(1)
            project_name = match.group(2)
            return self.check_specific_milestone(project_name, milestone_info)
            
        # General Project Queries
        elif re.search(r"list (?:all )?projects", query_text, re.IGNORECASE):
            return self.list_projects()
            
        elif re.search(r"show details (?:for|of) (.+?)( project)?", query_text, re.IGNORECASE):
            project_name = re.search(r"show details (?:for|of) (.+?)( project)?", query_text, re.IGNORECASE).group(1)
            return self.get_project_details(project_name)
            
        elif re.search(r"show tasks (?:for|of) (.+?)( project)?", query_text, re.IGNORECASE):
            project_name = re.search(r"show tasks (?:for|of) (.+?)( project)?", query_text, re.IGNORECASE).group(1)
            return self.get_project_tasks(project_name)
            
        # If no pattern matches, return a message with examples of valid queries
        return """
        Query not recognized. Please try one of the following formats:
        
        Selection Management:
        - "What are the open selection items for X project?"
        - "How overdue is X selection?"
        - "What selections are coming up in the next 2 weeks?"
        
        Project Phase Tracking:
        - "What stage and phase is X project in?"
        - "What items still need to be completed in the current phase for X project?"
        
        Walkthrough Management:
        - "Do any PD Walkthroughs need to be scheduled?"
        - "Do any Client walkthroughs need to be scheduled?"
        - "Has the most recent client walkthrough been completed for X project?"
        
        Procurement Tracking:
        - "What still needs to be bought out?"
        - "What trades still need a purchase order issued for X project?"
        
        Financial Milestone Tracking:
        - "What payment milestone is project X currently at?"
        - "What projects can be billed this week?"
        - "Has payment milestone #2/demolition been issued for X project?"
        
        General Project Queries:
        - "List all projects"
        - "Show details for X project"
        - "Show tasks for X project"
        """

def main():
    parser = argparse.ArgumentParser(description='Construction Project Database Query Tool')
    parser.add_argument('query', nargs='*', help='The query to execute')
    args = parser.parse_args()
    
    # Create database connection
    db = ConstructionDatabaseQueryTool()
    if not db.connect():
        sys.exit(1)
    
    try:
        # If query is provided as command line argument
        if args.query:
            query_text = ' '.join(args.query)
            result = db.parse_and_execute_query(query_text)
            print("\nQuery Result:")
            print(result)
        else:
            # Interactive mode
            print("Interactive mode. Type 'exit' to quit.\n")
            while True:
                query_text = input("Enter your query: ")
                if query_text.lower() == 'exit':
                    break
                    
                result = db.parse_and_execute_query(query_text)
                print("\nQuery Result:")
                print(result)
                print()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        db.disconnect()

if __name__ == "__main__":
    main()