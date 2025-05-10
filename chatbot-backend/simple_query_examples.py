#!/usr/bin/env python3
import psycopg2
import sys
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

def run_query(query, params=None):
    """Run a query and return the results in a tabulated format."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if cursor.description:
            headers = [desc[0] for desc in cursor.description]
            result = tabulate(rows, headers=headers, tablefmt="grid")
        else:
            result = "Query executed successfully but returned no data."
        
        cursor.close()
        conn.close()
        
        return result
    except Exception as e:
        return f"Error executing query: {e}"

def run_examples():
    print("Database Query Examples")
    print("======================\n")
    
    # Example 1: List all projects
    print("Example 1: List all projects")
    query = """
    SELECT id, name, "startDate", "percentComplete"
    FROM projects
    ORDER BY name
    LIMIT 10
    """
    print(run_query(query))
    print("\n")
    
    # Example 2: Get details for a specific project
    print("Example 2: Get details for CABOT-1B project")
    query = """
    SELECT id, name, "startDate", "percentComplete", "createdAt", "updatedAt"
    FROM projects
    WHERE name LIKE '%CABOT-1B%'
    """
    print(run_query(query))
    print("\n")
    
    # Example 3: Find selection items for a project
    print("Example 3: Find selection items for CABOT-1B project")
    query = """
    SELECT ci.id, ci.label, ci.checked
    FROM checklist_items ci
    JOIN stages s ON ci.sub_phase_id = s.id
    JOIN phases ph ON s.phase_id = ph.id
    JOIN projects p ON ph.project_id = p.id
    WHERE p.name LIKE '%CABOT-1B%'
    AND ci.label ILIKE '%selection%'
    LIMIT 10
    """
    print(run_query(query))
    print("\n")
    
    # Example 4: Show phases for a project
    print("Example 4: Show phases for CABOT-1B project")
    query = """
    SELECT ph.name AS phase_name, ph.status AS phase_status
    FROM phases ph
    JOIN projects p ON ph.project_id = p.id
    WHERE p.name LIKE '%CABOT-1B%'
    """
    print(run_query(query))
    print("\n")
    
    # Example 5: Find incomplete checklist items
    print("Example 5: Find incomplete checklist items for a project")
    query = """
    SELECT ci.label, ci.checked
    FROM checklist_items ci
    JOIN stages s ON ci.sub_phase_id = s.id
    JOIN phases ph ON s.phase_id = ph.id
    JOIN projects p ON ph.project_id = p.id
    WHERE p.name LIKE '%CABOT-1B%'
    AND (ci.checked = FALSE OR ci.checked IS NULL)
    LIMIT 10
    """
    print(run_query(query))
    print("\n")
    
    # Example 6: Find walkthrough related items
    print("Example 6: Find walkthrough related items")
    query = """
    SELECT p.name AS project_name, ci.label
    FROM checklist_items ci
    JOIN stages s ON ci.sub_phase_id = s.id
    JOIN phases ph ON s.phase_id = ph.id
    JOIN projects p ON ph.project_id = p.id
    WHERE ci.label ILIKE '%walkthrough%'
    AND (ci.checked = FALSE OR ci.checked IS NULL)
    LIMIT 10
    """
    print(run_query(query))
    print("\n")
    
    # Example 7: Find purchase order related items
    print("Example 7: Find purchase order related items")
    query = """
    SELECT p.name AS project_name, ci.label
    FROM checklist_items ci
    JOIN stages s ON ci.sub_phase_id = s.id
    JOIN phases ph ON s.phase_id = ph.id
    JOIN projects p ON ph.project_id = p.id
    WHERE ci.label ILIKE '%purchase%'
    AND (ci.checked = FALSE OR ci.checked IS NULL)
    LIMIT 10
    """
    print(run_query(query))
    print("\n")
    
    # Example 8: Find tasks for a project
    print("Example 8: Find tasks for a project")
    query = """
    SELECT t.description, t.status
    FROM tasks t
    WHERE t."projectName" ILIKE '%CABOT%'
    OR t.description ILIKE '%CABOT%'
    LIMIT 10
    """
    print(run_query(query))
    print("\n")

if __name__ == "__main__":
    run_examples()