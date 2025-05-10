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

class DatabaseQuery:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        """Establish a connection to the database."""
        try:
            self.conn = psycopg2.connect(**DB_PARAMS)
            self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            print("Database connection established successfully.")
        except Exception as e:
            print(f"Error connecting to the database: {e}")
            sys.exit(1)

    def close(self):
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    def execute_query(self, query, params=None):
        """Execute a query and return the results."""
        conn = None
        cursor = None
        try:
            # Use a fresh connection for each query to avoid transaction issues
            conn = psycopg2.connect(**DB_PARAMS)
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return rows, cursor.description, None
        except Exception as e:
            error_msg = f"Error executing query: {e}"
            return [], None, error_msg
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def format_results(self, rows, description, title=None):
        """Format the results for display."""
        if not rows:
            return "No results found."
        
        if description:
            headers = [desc[0] for desc in description]
        else:
            headers = ["Column" + str(i) for i in range(len(rows[0]))]
        
        result = ""
        if title:
            result += f"\n{title}:\n"
        
        result += tabulate(rows, headers=headers, tablefmt="grid")
        return result

    # Project Information Queries
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
        
        return self.format_results(rows, description, "All Projects")
    
    def get_project_details(self, project_name):
        """Get details for a specific project."""
        query = """
        SELECT p.id, p.name, p."startDate", p."percentComplete", p."createdAt", p."updatedAt",
               u1."firstName" || ' ' || u1."lastName" AS designer,
               u2."firstName" || ' ' || u2."lastName" AS developer,
               u3."firstName" || ' ' || u3."lastName" AS junior_designer
        FROM projects p
        LEFT JOIN users u1 ON p.project_designer_id = u1.id
        LEFT JOIN users u2 ON p.project_developer_id = u2.id
        LEFT JOIN users u3 ON p.project_junior_designer_id = u3.id
        WHERE p.name ILIKE %s
        """
        rows, description, error = self.execute_query(query, (f"%{project_name}%",))
        
        if error:
            return f"Error retrieving project details: {error}"
        
        return self.format_results(rows, description, f"Details for project matching '{project_name}'")

    # Selection Management
    def get_project_selection_items(self, project_name):
        """Get selection items for a specific project."""
        query = """
        SELECT ci.id, ci.label, ci.checked, ci.non_applicable, s.name AS stage_name, ph.name AS phase_name
        FROM checklist_items ci
        JOIN stages s ON ci.sub_phase_id = s.id
        JOIN phases ph ON s.phase_id = ph.id
        JOIN projects p ON ph.project_id = p.id
        WHERE p.name ILIKE %s
        AND (ci.label ILIKE '%selection%' OR s.name ILIKE '%selection%')
        AND (ci.checked = FALSE OR ci.checked IS NULL)
        ORDER BY ph."order", s."order", ci."order"
        """
        rows, description, error = self.execute_query(query, (f"%{project_name}%",))
        
        if error:
            return f"Error retrieving selection items: {error}"
        
        return self.format_results(rows, description, f"Open selection items for project matching '{project_name}'")

    def get_upcoming_selections(self, days=14):
        """Get selection items due in the next X days."""
        future_date = datetime.datetime.now() + datetime.timedelta(days=days)
        
        query = """
        SELECT ci.id, ci.label, p.name AS project_name, s.name AS stage_name, ph.name AS phase_name
        FROM checklist_items ci
        JOIN stages s ON ci.sub_phase_id = s.id
        JOIN phases ph ON s.phase_id = ph.id
        JOIN projects p ON ph.project_id = p.id
        WHERE (ci.label ILIKE '%selection%' OR s.name ILIKE '%selection%')
        AND (ci.checked = FALSE OR ci.checked IS NULL)
        AND p."startDate" <= %s 
        ORDER BY p."startDate", ph."order", s."order", ci."order"
        """
        rows, description, error = self.execute_query(query, (future_date,))
        
        if error:
            return f"Error retrieving upcoming selections: {error}"
        
        return self.format_results(rows, description, f"Selection items coming up in the next {days} days")

    # Project Phase Tracking
    def get_project_phase(self, project_name):
        """Get the current phase and stage information for a project."""
        query = """
        SELECT p.name AS project_name, ph.name AS phase_name, ph."order" AS phase_order,
               ph.status AS phase_status, s.name AS stage_name, s."order" AS stage_order
        FROM projects p
        JOIN phases ph ON p.id = ph.project_id
        JOIN stages s ON ph.id = s.phase_id
        WHERE p.name ILIKE %s
        ORDER BY ph."order", s."order"
        """
        rows, description, error = self.execute_query(query, (f"%{project_name}%",))
        
        if error or not rows:
            # Fallback to just getting the project info if phase/stage join fails
            query = """
            SELECT p.id, p.name, p."startDate", p."percentComplete" 
            FROM projects p
            WHERE p.name ILIKE %s
            """
            rows, description, error = self.execute_query(query, (f"%{project_name}%",))
            
            if error:
                return f"Error retrieving project information: {error}"
            elif not rows:
                return f"No project found matching '{project_name}'"
            else:
                return self.format_results(rows, description, f"Project information for '{project_name}' (phase/stage info not available)")
        
        return self.format_results(rows, description, f"Phase and stage information for project matching '{project_name}'")

    def get_incomplete_phase_items(self, project_name):
        """Get items that still need to be completed in the current phases."""
        query = """
        SELECT ci.label, ph.name AS phase_name, s.name AS stage_name
        FROM checklist_items ci
        JOIN stages s ON ci.sub_phase_id = s.id
        JOIN phases ph ON s.phase_id = ph.id
        JOIN projects p ON ph.project_id = p.id
        WHERE p.name ILIKE %s
        AND (ci.checked = FALSE OR ci.checked IS NULL)
        AND ph.status = 'InProgress'
        ORDER BY ph."order", s."order", ci."order"
        """
        rows, description, error = self.execute_query(query, (f"%{project_name}%",))
        
        if error:
            return f"Error retrieving incomplete phase items: {error}"
        
        return self.format_results(rows, description, f"Incomplete items in current phases for project matching '{project_name}'")

    # Walkthrough Management
    def get_pending_walkthroughs(self, walkthrough_type=None):
        """Get walkthroughs that need to be scheduled."""
        where_clause = "(ci.label ILIKE '%walkthrough%' OR s.name ILIKE '%walkthrough%') AND (ci.checked = FALSE OR ci.checked IS NULL)"
        params = []
        
        if walkthrough_type:
            where_clause += f" AND (ci.label ILIKE %s OR s.name ILIKE %s)"
            walkthrough_pattern = f"%{walkthrough_type}%walkthrough%"
            params.extend([walkthrough_pattern, walkthrough_pattern])
        
        query = f"""
        SELECT p.name AS project_name, ci.label, ph.name AS phase_name, s.name AS stage_name
        FROM checklist_items ci
        JOIN stages s ON ci.sub_phase_id = s.id
        JOIN phases ph ON s.phase_id = ph.id
        JOIN projects p ON ph.project_id = p.id
        WHERE {where_clause}
        ORDER BY p.name, ph."order", s."order"
        """
        rows, description, error = self.execute_query(query, tuple(params) if params else None)
        
        if error:
            return f"Error retrieving walkthrough information: {error}"
        
        title = "Pending walkthroughs"
        if walkthrough_type:
            title += f" ({walkthrough_type})"
        
        return self.format_results(rows, description, title)

    def check_recent_client_walkthrough(self, project_name):
        """Check if the most recent client walkthrough has been completed."""
        query = """
        SELECT p.name AS project_name, ci.label, ci.checked, ph.name AS phase_name, s.name AS stage_name
        FROM checklist_items ci
        JOIN stages s ON ci.sub_phase_id = s.id
        JOIN phases ph ON s.phase_id = ph.id
        JOIN projects p ON ph.project_id = p.id
        WHERE p.name ILIKE %s
        AND ci.label ILIKE '%client%walkthrough%'
        ORDER BY ph."order" DESC, s."order" DESC, ci."order" DESC
        LIMIT 5
        """
        rows, description, error = self.execute_query(query, (f"%{project_name}%",))
        
        if error:
            return f"Error checking client walkthrough status: {error}"
        
        return self.format_results(rows, description, f"Recent client walkthroughs for project matching '{project_name}'")

    # Procurement Tracking
    def get_pending_purchase_orders(self, project_name=None):
        """Get items that still need purchase orders issued."""
        where_clause = "(ci.label ILIKE '%purchase order%' OR ci.label ILIKE '%PO%') AND (ci.checked = FALSE OR ci.checked IS NULL)"
        params = []
        
        if project_name:
            where_clause += " AND p.name ILIKE %s"
            params.append(f"%{project_name}%")
        
        query = f"""
        SELECT p.name AS project_name, ci.label, ph.name AS phase_name, s.name AS stage_name
        FROM checklist_items ci
        JOIN stages s ON ci.sub_phase_id = s.id
        JOIN phases ph ON s.phase_id = ph.id
        JOIN projects p ON ph.project_id = p.id
        WHERE {where_clause}
        ORDER BY p.name, ph."order", s."order"
        """
        rows, description, error = self.execute_query(query, tuple(params) if params else None)
        
        if error:
            return f"Error retrieving purchase order information: {error}"
        
        title = "Items needing purchase orders"
        if project_name:
            title += f" for project matching '{project_name}'"
        
        return self.format_results(rows, description, title)

    # Financial Milestone Tracking
    def get_payment_milestones(self, project_name):
        """Get payment milestones for a project."""
        query = """
        SELECT p.name AS project_name, ci.label, ci.checked, ph.name AS phase_name, s.name AS stage_name
        FROM checklist_items ci
        JOIN stages s ON ci.sub_phase_id = s.id
        JOIN phases ph ON s.phase_id = ph.id
        JOIN projects p ON ph.project_id = p.id
        WHERE p.name ILIKE %s
        AND (ci.label ILIKE '%payment%' OR ci.label ILIKE '%invoice%' OR ci.label ILIKE '%billing%' OR ci.label ILIKE '%milestone%')
        ORDER BY ph."order", s."order", ci."order"
        """
        rows, description, error = self.execute_query(query, (f"%{project_name}%",))
        
        if error:
            return f"Error retrieving payment milestone information: {error}"
        
        return self.format_results(rows, description, f"Payment milestones for project matching '{project_name}'")

    def get_billable_projects(self):
        """Get projects that can be billed."""
        query = """
        SELECT p.name AS project_name, COUNT(ci.id) as pending_payment_items
        FROM projects p
        JOIN phases ph ON p.id = ph.project_id
        JOIN stages s ON ph.id = s.phase_id
        JOIN checklist_items ci ON s.id = ci.sub_phase_id
        WHERE (ci.label ILIKE '%payment%' OR ci.label ILIKE '%invoice%' OR ci.label ILIKE '%billing%')
        AND (ci.checked = FALSE OR ci.checked IS NULL)
        GROUP BY p.id, p.name
        ORDER BY pending_payment_items DESC
        """
        rows, description, error = self.execute_query(query)
        
        if error:
            return f"Error retrieving billable projects: {error}"
        
        return self.format_results(rows, description, "Projects with pending billing/payment items")

    def check_milestone_issued(self, project_name, milestone_info):
        """Check if a specific payment milestone has been issued."""
        query = """
        SELECT p.name AS project_name, ci.label, ci.checked, ph.name AS phase_name, s.name AS stage_name
        FROM checklist_items ci
        JOIN stages s ON ci.sub_phase_id = s.id
        JOIN phases ph ON s.phase_id = ph.id
        JOIN projects p ON ph.project_id = p.id
        WHERE p.name ILIKE %s
        AND ci.label ILIKE %s
        ORDER BY ph."order", s."order", ci."order"
        """
        rows, description, error = self.execute_query(query, (f"%{project_name}%", f"%{milestone_info}%"))
        
        if error:
            return f"Error checking milestone status: {error}"
        
        return self.format_results(rows, description, f"Status of milestone '{milestone_info}' for project matching '{project_name}'")

    # Tasks queries
    def get_project_tasks(self, project_name):
        """Get tasks for a specific project."""
        query = """
        SELECT t.id, t.description, t.status, t."dueDate", 
               u."firstName" || ' ' || u."lastName" AS assigned_to
        FROM tasks t
        LEFT JOIN users u ON t.user_id = u.id
        WHERE (t.project_id IN (SELECT id FROM projects WHERE name ILIKE %s)
               OR t."projectName" ILIKE %s)
        ORDER BY t."dueDate"
        """
        rows, description, error = self.execute_query(query, (f"%{project_name}%", f"%{project_name}%"))
        
        if error:
            # Try a simpler query without the join if there's an error
            query = """
            SELECT t.id, t.description, t.status, t."dueDate"
            FROM tasks t
            WHERE t.project_id IN (SELECT id FROM projects WHERE name ILIKE %s)
               OR t."projectName" ILIKE %s
            ORDER BY t."dueDate"
            """
            rows, description, error = self.execute_query(query, (f"%{project_name}%", f"%{project_name}%"))
            
            if error:
                return f"Error retrieving project tasks: {error}"
        
        if not rows:
            return f"No tasks found for project matching '{project_name}'"
            
        return self.format_results(rows, description, f"Tasks for project matching '{project_name}'")

    def parse_and_execute_query(self, query_text):
        """Parse the user's query and execute the appropriate function."""        
        # Selection Management
        if re.search(r"(?:what are|show|get) (?:the )?open selection(?:s)? (?:items )?for (.+?)( project)?", query_text, re.IGNORECASE):
            project_name = re.search(r"(?:what are|show|get) (?:the )?open selection(?:s)? (?:items )?for (.+?)( project)?", query_text, re.IGNORECASE).group(1).strip()
            return self.get_project_selection_items(project_name)
            
        elif re.search(r"how overdue is (.+?) selection", query_text, re.IGNORECASE):
            selection_name = re.search(r"how overdue is (.+?) selection", query_text, re.IGNORECASE).group(1).strip()
            # For now, we'll just search for the selection by name across all projects
            query = """
            SELECT p.name AS project_name, ci.label, ph.name AS phase_name, s.name AS stage_name,
                   ph.status AS phase_status, p."startDate"
            FROM checklist_items ci
            JOIN stages s ON ci.sub_phase_id = s.id
            JOIN phases ph ON s.phase_id = ph.id
            JOIN projects p ON ph.project_id = p.id
            WHERE ci.label ILIKE %s
            AND (ci.checked = FALSE OR ci.checked IS NULL)
            """
            rows, description, error = self.execute_query(query, (f"%{selection_name}%",))
            
            if error:
                return f"Error checking selection status: {error}"
            
            return self.format_results(rows, description, f"Status of selection items matching '{selection_name}'")
            
        elif re.search(r"(?:what )?selection(?:s)? (?:are )?coming up in the next (\d+) (days|weeks)", query_text, re.IGNORECASE):
            match = re.search(r"(?:what )?selection(?:s)? (?:are )?coming up in the next (\d+) (days|weeks)", query_text, re.IGNORECASE)
            time_value = int(match.group(1))
            time_unit = match.group(2).lower()
            days = time_value if time_unit == 'days' else time_value * 7
            return self.get_upcoming_selections(days)
            
        # Project Phase Tracking
        elif re.search(r"what stage and phase is (.+?)( project)? in", query_text, re.IGNORECASE):
            project_name = re.search(r"what stage and phase is (.+?)( project)? in", query_text, re.IGNORECASE).group(1).strip()
            return self.get_project_phase(project_name)
            
        elif re.search(r"(?:what )?items? (?:still )?need(?:s)? to be completed in (?:the )?current phase", query_text, re.IGNORECASE):
            # Extract project name if given, otherwise ask for it
            project_match = re.search(r"for (.+?)( project)?", query_text, re.IGNORECASE)
            if project_match:
                project_name = project_match.group(1).strip()
                return self.get_incomplete_phase_items(project_name)
            else:
                return "Please specify a project name."
                
        # Walkthrough Management
        elif re.search(r"(?:do any )?PD walkthroughs? need to be scheduled", query_text, re.IGNORECASE):
            return self.get_pending_walkthroughs("PD")
            
        elif re.search(r"(?:do any )?client walkthroughs? need to be scheduled", query_text, re.IGNORECASE):
            return self.get_pending_walkthroughs("client")
            
        elif re.search(r"(?:has the )?(?:most )?recent client walkthrough been completed", query_text, re.IGNORECASE):
            # Extract project name if given, otherwise ask for it
            project_match = re.search(r"for (.+?)( project)?", query_text, re.IGNORECASE)
            if project_match:
                project_name = project_match.group(1).strip()
                return self.check_recent_client_walkthrough(project_name)
            else:
                return "Please specify a project name."
                
        # Procurement Tracking
        elif re.search(r"(?:what )?(?:still )?needs? to be bought out|(?:what )?trades (?:still )?need a purchase order|find items needing purchase orders", query_text, re.IGNORECASE):
            # Extract project name if given
            project_match = re.search(r"for (.+?)( project)?", query_text, re.IGNORECASE)
            if project_match:
                project_name = project_match.group(1).strip()
                return self.get_pending_purchase_orders(project_name)
            else:
                return self.get_pending_purchase_orders()
                
        # Financial Milestone Tracking
        elif re.search(r"(?:what )?payment milestone is (.+?)( project)? currently at", query_text, re.IGNORECASE):
            project_name = re.search(r"(?:what )?payment milestone is (.+?)( project)? currently at", query_text, re.IGNORECASE).group(1).strip()
            return self.get_payment_milestones(project_name)
            
        elif re.search(r"(?:what )?projects? can be billed this week", query_text, re.IGNORECASE):
            return self.get_billable_projects()
            
        elif re.search(r"has payment milestone #?(\d+)(?:/|\s)?(.+?) been issued", query_text, re.IGNORECASE):
            match = re.search(r"has payment milestone #?(\d+)(?:/|\s)?(.+?) been issued for (.+?)( project)?", query_text, re.IGNORECASE)
            if match:
                milestone_id = match.group(1)
                milestone_name = match.group(2)
                project_name = match.group(3).strip()
                milestone_info = f"{milestone_id} {milestone_name}"
                return self.check_milestone_issued(project_name, milestone_info)
            else:
                match = re.search(r"has payment milestone #?(\d+) been issued for (.+?)( project)?", query_text, re.IGNORECASE)
                if match:
                    milestone_id = match.group(1)
                    project_name = match.group(2).strip()
                    return self.check_milestone_issued(project_name, milestone_id)
                else:
                    match = re.search(r"has payment milestone (.+?) been issued for (.+?)( project)?", query_text, re.IGNORECASE)
                    if match:
                        milestone_name = match.group(1).strip()
                        project_name = match.group(2).strip()
                        return self.check_milestone_issued(project_name, milestone_name)
                    else:
                        return "Please specify a project name and milestone."
                        
        # Generic Project Queries
        elif re.search(r"(?:list|show|get) (?:all )?projects", query_text, re.IGNORECASE):
            return self.list_projects()
            
        elif re.search(r"(?:show|get) (?:details|info) (?:for|about) (.+?)( project)?", query_text, re.IGNORECASE) or re.search(r"detailed project information including team members", query_text, re.IGNORECASE):
            if re.search(r"detailed project information including team members", query_text, re.IGNORECASE):
                project_match = re.search(r"for (.+?)( project)?", query_text, re.IGNORECASE)
                if project_match:
                    project_name = project_match.group(1).strip()
                    return self.get_project_details(project_name)
                else:
                    return "Please specify a project name."
            else:
                project_name = re.search(r"(?:show|get) (?:details|info) (?:for|about) (.+?)( project)?", query_text, re.IGNORECASE).group(1).strip()
                return self.get_project_details(project_name)
            
        elif re.search(r"(?:show|get) (?:all )?tasks for (.+?)( project)?", query_text, re.IGNORECASE):
            project_name = re.search(r"(?:show|get) (?:all )?tasks for (.+?)( project)?", query_text, re.IGNORECASE).group(1).strip()
            return self.get_project_tasks(project_name)

        elif re.search(r"check on specific selections across all projects", query_text, re.IGNORECASE):
            # Handle the generic query by asking for more specifics
            return "Please provide a specific selection name to check across projects. Try 'How overdue is [selection name] selection'."
        
        # Fallback message
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
        - "Find items needing purchase orders"
        
        Financial Milestone Tracking:
        - "What payment milestone is project X currently at?"
        - "What projects can be billed this week?"
        - "Has payment milestone #2/demolition been issued for X project?"
        
        General Queries:
        - "List all projects"
        - "Show details for X project"
        - "Show tasks for X project"
        """

def main():
    parser = argparse.ArgumentParser(description='Construction Project Database Query Tool')
    parser.add_argument('query', nargs='*', help='The query to execute')
    args = parser.parse_args()
    
    # Create database connection
    db = DatabaseQuery()
    
    # Join the query arguments into a single string
    query_text = ' '.join(args.query)
    
    # If no query provided, enter interactive mode
    if not query_text:
        print("Interactive mode. Type 'exit' to quit.")
        while True:
            query_text = input("\nEnter your query: ")
            
            if query_text.lower() == 'exit':
                break
                
            try:
                result = db.parse_and_execute_query(query_text)
                print("\nQuery Result:")
                print(result)
            except Exception as e:
                print(f"Error processing query: {e}")
    else:
        try:
            result = db.parse_and_execute_query(query_text)
            print("\nQuery Result:")
            print(result)
        except Exception as e:
            print(f"Error processing query: {e}")
    
    # Close the database connection
    db.close()

if __name__ == "__main__":
    main()