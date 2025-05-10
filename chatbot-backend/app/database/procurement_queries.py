"""
Procurement-related database queries.
"""

import logging
from typing import List, Dict, Any, Optional
from app.database.connection import DatabaseConnection
from app.database.base_queries import BaseQueries

# Setup logging
logger = logging.getLogger(__name__)

class ProcurementQueries(BaseQueries):
    """Procurement database query methods."""
    def __init__(self, conn=None):
        """
        Initialize with optional connection.
        
        Args:
            conn: Database connection (optional)
        """
        super().__init__(conn)
    
    def get_trades_needing_po(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trades that still need purchase orders.
        
        Args:
            project_id: Optional UUID of the project
            
        Returns:
            List of trades needing purchase orders
        """
        try:
            # Since we might not have dedicated procurement tables yet, let's identify
            # procurement-related tasks from our subphases
            base_query = """
                SELECT s.id, s.name, s.status, s."order", s."startDate", s."endDate",
                       p.name as phase_name, p.id as phase_id, p.project_id,
                       pr.name as project_name
                FROM subphases s
                JOIN phases p ON s.phase_id = p.id
                JOIN projects pr ON p.project_id = pr.id
                WHERE (s.name ILIKE '%purchase order%' OR s.name ILIKE '%po%' 
                       OR s.name ILIKE '%procurement%' OR s.name ILIKE '%buy out%')
                  AND s.status != 'Completed'
            """
            
            if project_id:
                query = base_query + " AND p.project_id = %s"
                trades = DatabaseConnection.execute_query(self.conn, query, (project_id,))
            else:
                query = base_query + " ORDER BY pr.name"
                trades = DatabaseConnection.execute_query(self.conn, query)
            
            # Transform into trade items
            result = []
            for item in trades:
                # Extract trade name from the subphase name
                trade_name = "Unknown Trade"
                name_parts = item['name'].split()
                for i, part in enumerate(name_parts):
                    if part.lower() in ['po', 'purchase', 'order', 'procurement'] and i > 0:
                        trade_name = name_parts[i-1].capitalize()
                        break
                
                result.append({
                    'id': item['id'],
                    'trade_name': trade_name,
                    'task_name': item['name'],
                    'status': item['status'],
                    'project_id': item['project_id'],
                    'project_name': item.get('project_name', 'Unknown Project'),
                    'phase_name': item.get('phase_name'),
                    'due_date': item.get('endDate')
                })
            
            return result
        except Exception as e:
            logger.error(f"Error getting trades needing PO: {e}")
            return []