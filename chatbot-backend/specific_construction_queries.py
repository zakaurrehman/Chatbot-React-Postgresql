#!/usr/bin/env python3
import psycopg2
import sys
import datetime
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

def run_query(query, params=None, title=None):
    """Run a query and return the results in a tabulated format."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if cursor.description:
            headers = [desc[0] for desc in cursor.description]
            if rows:
                result = f"\n{title if title else 'Query Results'}:\n"
                result += tabulate(rows, headers=headers, tablefmt="grid")
            else:
                result = f"\n{title if title else 'Query Results'}:\nNo results found."
        else:
            result = "Query executed successfully but returned no data."
        
        cursor.close()
        conn.close()
        
        return result
    except Exception as e:
        return f"Error executing query: {e}"

def list_all_projects():
    """List all projects in the database."""
    query = """
    SELECT id, name, "startDate", "percentComplete"
    FROM projects
    ORDER BY name
    """
    return run_query(query, title="All Projects")

# SELECTION MANAGEMENT QUERIES

def open_selection_items(project_name):
    """What are the open selection items for X project?"""
    query = """
    SELECT ci.id, ci.label, s.name AS stage_name, ph.name AS phase_name
    FROM checklist_items ci
    JOIN stages s ON ci.sub_phase_id = s.id
    JOIN phases ph ON s.phase_id = ph.id
    JOIN projects p ON ph.project_id = p.id
    WHERE p.name LIKE %s
    AND (ci.label ILIKE '%selection%' OR s.name ILIKE '%selection%' OR ph.name ILIKE '%selection%')
    AND (ci.checked = FALSE OR ci.checked IS NULL)
    ORDER BY ph.name, s.name, ci.label
    """
    return run_query(query, (f'%{project_name}%',), f"Open Selection Items for {project_name}")

def selection_overdue(selection_name):
    """How overdue is X selection?"""
    current_date = datetime.datetime.now().date()
    query = """
    SELECT ci.id, ci.label, p.name AS project_name, 
           ph.name AS phase_name, s.name AS stage_name,
           p."startDate", CURRENT_DATE - p."startDate" AS days_since_start
    FROM checklist_items ci
    JOIN stages s ON ci.sub_phase_id = s.id
    JOIN phases ph ON s.phase_id = ph.id
    JOIN projects p ON ph.project_id = p.id
    WHERE ci.label ILIKE %s
    AND (ci.checked = FALSE OR ci.checked IS NULL)
    ORDER BY p."startDate"
    """
    return run_query(query, (f'%{selection_name}%',), f"Status of Selection: {selection_name}")

def upcoming_selections(weeks=2):
    """What selections are coming up in the next 2 weeks?"""
    current_date = datetime.datetime.now().date()
    future_date = current_date + datetime.timedelta(weeks=weeks)
    query = """
    SELECT ci.id, ci.label, p.name AS project_name, 
           ph.name AS phase_name, s.name AS stage_name
    FROM checklist_items ci
    JOIN stages s ON ci.sub_phase_id = s.id
    JOIN phases ph ON s.phase_id = ph.id
    JOIN projects p ON ph.project_id = p.id
    WHERE (ci.label ILIKE '%selection%' OR s.name ILIKE '%selection%' OR ph.name ILIKE '%selection%')
    AND (ci.checked = FALSE OR ci.checked IS NULL)
    AND p."startDate" IS NOT NULL
    AND p."startDate" BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '%s weeks'
    ORDER BY p."startDate", ph.name, s.name
    """
    return run_query(query, (weeks,), f"Selections Coming Up in the Next {weeks} Weeks")

# PROJECT PHASE TRACKING QUERIES

def project_stage_phase(project_name):
    """What stage and phase is X project in?"""
    query = """
    SELECT p.name AS project_name, 
           ph.name AS phase_name, ph.status AS phase_status,
           s.name AS stage_name
    FROM projects p
    JOIN phases ph ON p.id = ph.project_id
    JOIN stages s ON ph.id = s.phase_id
    WHERE p.name LIKE %s
    ORDER BY ph.name, s.name
    """
    return run_query(query, (f'%{project_name}%',), f"Stages and Phases for Project: {project_name}")

def incomplete_phase_items(project_name):
    """What items still need to be completed in the current phase and stage?"""
    query = """
    SELECT ci.id, ci.label, ph.name AS phase_name, s.name AS stage_name
    FROM checklist_items ci
    JOIN stages s ON ci.sub_phase_id = s.id
    JOIN phases ph ON s.phase_id = ph.id
    JOIN projects p ON ph.project_id = p.id
    WHERE p.name LIKE %s
    AND ph.status = 'InProgress'
    AND (ci.checked = FALSE OR ci.checked IS NULL)
    ORDER BY ph.name, s.name, ci.label
    """
    return run_query(query, (f'%{project_name}%',), f"Incomplete Items in Current Phase for Project: {project_name}")

# WALKTHROUGH MANAGEMENT QUERIES

def pd_walkthroughs_needed():
    """Do any PD Walkthroughs need to be scheduled?"""
    query = """
    SELECT p.name AS project_name, ci.label, ph.name AS phase_name, s.name AS stage_name
    FROM checklist_items ci
    JOIN stages s ON ci.sub_phase_id = s.id
    JOIN phases ph ON s.phase_id = ph.id
    JOIN projects p ON ph.project_id = p.id
    WHERE ci.label ILIKE '%PD%walkthrough%'
    AND (ci.checked = FALSE OR ci.checked IS NULL)
    ORDER BY p.name
    """
    return run_query(query, title="PD Walkthroughs Needing to be Scheduled")

def client_walkthroughs_needed():
    """Do any Client walkthroughs need to be scheduled?"""
    query = """
    SELECT p.name AS project_name, ci.label, ph.name AS phase_name, s.name AS stage_name
    FROM checklist_items ci
    JOIN stages s ON ci.sub_phase_id = s.id
    JOIN phases ph ON s.phase_id = ph.id
    JOIN projects p ON ph.project_id = p.id
    WHERE ci.label ILIKE '%client%walkthrough%'
    AND (ci.checked = FALSE OR ci.checked IS NULL)
    ORDER BY p.name
    """
    return run_query(query, title="Client Walkthroughs Needing to be Scheduled")

def recent_client_walkthrough(project_name):
    """Has the most recent client walkthrough been completed?"""
    query = """
    SELECT p.name AS project_name, ci.label, ci.checked, ph.name AS phase_name, s.name AS stage_name
    FROM checklist_items ci
    JOIN stages s ON ci.sub_phase_id = s.id
    JOIN phases ph ON s.phase_id = ph.id
    JOIN projects p ON ph.project_id = p.id
    WHERE p.name LIKE %s
    AND ci.label ILIKE '%client%walkthrough%'
    ORDER BY ci.checked DESC, ci."updatedAt" DESC
    LIMIT 5
    """
    return run_query(query, (f'%{project_name}%',), f"Recent Client Walkthroughs for Project: {project_name}")

# PROCUREMENT TRACKING QUERIES

def pending_purchase_orders():
    """What still needs to be bought out/what trades still need a purchase order issued?"""
    query = """
    SELECT p.name AS project_name, ci.label, ph.name AS phase_name, s.name AS stage_name
    FROM checklist_items ci
    JOIN stages s ON ci.sub_phase_id = s.id
    JOIN phases ph ON s.phase_id = ph.id
    JOIN projects p ON ph.project_id = p.id
    WHERE (ci.label ILIKE '%purchase order%' OR ci.label ILIKE '%PO%' OR ci.label ILIKE '%procurement%' OR ci.label ILIKE '%bought out%')
    AND (ci.checked = FALSE OR ci.checked IS NULL)
    ORDER BY p.name
    """
    return run_query(query, title="Items Needing Purchase Orders")

# FINANCIAL MILESTONE TRACKING QUERIES

def payment_milestone_status(project_name):
    """What payment milestone is project X currently at?"""
    query = """
    SELECT p.name AS project_name, ci.label, ci.checked, ph.name AS phase_name, s.name AS stage_name
    FROM checklist_items ci
    JOIN stages s ON ci.sub_phase_id = s.id
    JOIN phases ph ON s.phase_id = ph.id
    JOIN projects p ON ph.project_id = p.id
    WHERE p.name LIKE %s
    AND (ci.label ILIKE '%payment%' OR ci.label ILIKE '%milestone%' OR ci.label ILIKE '%invoice%' OR ci.label ILIKE '%billing%')
    ORDER BY ci.checked, ph.name, s.name
    """
    return run_query(query, (f'%{project_name}%',), f"Payment Milestone Status for Project: {project_name}")

def billable_projects():
    """What projects can be billed this week?"""
    query = """
    SELECT DISTINCT p.name AS project_name
    FROM projects p
    JOIN phases ph ON p.id = ph.project_id
    JOIN stages s ON ph.id = s.phase_id
    JOIN checklist_items ci ON s.id = ci.sub_phase_id
    WHERE (ci.label ILIKE '%payment%' OR ci.label ILIKE '%invoice%' OR ci.label ILIKE '%billing%')
    AND (ci.checked = FALSE OR ci.checked IS NULL)
    ORDER BY p.name
    """_query(query, title="Projects That Can Be Billed This Week")

    return run
def check_specific_milestone(project_name, milestone_info):
    """Has payment milestone #2/demolition been issued?"""
    query = """
    SELECT p.name AS project_name, ci.label, ci.checked, ph.name AS phase_name, s.name AS stage_name
    FROM checklist_items ci
    JOIN stages s ON ci.sub_phase_id = s.id
    JOIN phases ph ON s.phase_id = ph.id
    JOIN projects p ON ph.project_id = p.id
    WHERE p.name LIKE %s
    AND ci.label ILIKE %s
    ORDER BY ci.checked, ph.name, s.name
    """
    return run_query(query, (f'%{project_name}%', f'%{milestone_info}%'), f"Status of Milestone '{milestone_info}' for Project: {project_name}")

def main():
    print("Running specific construction database queries...\n")

    # List all projects first to see what's available
    print(list_all_projects())
    
    # SELECTION MANAGEMENT
    print("\n===== SELECTION MANAGEMENT =====")
    # Using CABOT-1B as example project
    print(open_selection_items("CABOT-1B"))
    print(selection_overdue("flooring"))
    print(upcoming_selections(2))
    
    # PROJECT PHASE TRACKING
    print("\n===== PROJECT PHASE TRACKING =====")
    print(project_stage_phase("CABOT-1B"))
    print(incomplete_phase_items("CABOT-1B"))
    
    # WALKTHROUGH MANAGEMENT
    print("\n===== WALKTHROUGH MANAGEMENT =====")
    print(pd_walkthroughs_needed())
    print(client_walkthroughs_needed())
    print(recent_client_walkthrough("CABOT-1B"))
    
    # PROCUREMENT TRACKING
    print("\n===== PROCUREMENT TRACKING =====")
    print(pending_purchase_orders())
    
    # FINANCIAL MILESTONE TRACKING
    print("\n===== FINANCIAL MILESTONE TRACKING =====")
    print(payment_milestone_status("CABOT-1B"))
    print(billable_projects())
    print(check_specific_milestone("CABOT-1B", "demolition"))
    
    print("\nAll queries completed.")

if __name__ == "__main__":
    main()