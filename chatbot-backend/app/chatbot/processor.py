"""Query processor for the chatbot with improved natural language understanding."""

import json
import re
import logging
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta

# Import the OpenAI compatibility wrapper
from app.utils.openai_compat import OpenAIClient
from app.config import get_config
from app.database.queries import DatabaseQueries

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QueryProcessor:
    """Process user queries and execute database operations with improved NLU capabilities."""
    
    def __init__(self):
        """Initialize the query processor."""
        config = get_config()
        # Changed OPENAI_API_KEY to GEMINI_API_KEY
        self.openai_client = OpenAIClient(api_key=config.GEMINI_API_KEY)
        self.db = DatabaseQueries()
        self.model = config.DEFAULT_MODEL  # This should now be gpt-3.5-turbo from config
        self.max_tokens = config.MAX_TOKENS
        self.temperature = config.TEMPERATURE
        # Initialize conversation memory
        self.conversation_context = {}
    
    def analyze_query(self, user_query: str, db_schema: str, conversation_id: str = None) -> Dict[str, Any]:
        """Analyze the user query to determine intent and required operations with improved understanding."""
        from app.chatbot.prompts import QUERY_ANALYSIS_PROMPT
        
        # Add conversation context if available
        context_info = ""
        if conversation_id and conversation_id in self.conversation_context:
            context_info = f"\n\nConversation context:\n{json.dumps(self.conversation_context[conversation_id])}"
        
        # Enhance the user query with context about previous interactions
        enhanced_query = self._enhance_query_with_context(user_query)
        
        messages = [
            {"role": "system", "content": QUERY_ANALYSIS_PROMPT},
            {"role": "user", "content": f"User query: {enhanced_query}\n\nDatabase schema summary:\n{db_schema[:4000]}{context_info}"}
        ]
        
        try:
            response = self.openai_client.create_chat_completion(
                model=self.model,  # Using the model from config
                messages=messages,
                temperature=0,  # Use 0 for deterministic results
                max_tokens=500
            )
            
            # Get content from the response
            analysis_text = response["choices"][0]["message"]["content"]
            
            # Extract JSON from the response text - this handles code blocks from Gemini
            extracted_json = self._extract_json(analysis_text)
            
            if extracted_json:
                analysis = extracted_json
                logger.info(f"Query analysis: {analysis}")
                
                # Enhance the analysis with additional entity extraction
                analysis = self._enhance_analysis_with_entities(analysis, user_query)
                
                return analysis
            else:
                # Try to parse directly if extraction fails
                try:
                    analysis = json.loads(analysis_text)
                    logger.info(f"Query analysis (direct parse): {analysis}")
                    
                    # Enhance the analysis with additional entity extraction
                    analysis = self._enhance_analysis_with_entities(analysis, user_query)
                    
                    return analysis
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse query analysis as JSON: {analysis_text}")
                    
                    # Pattern matching fallback for construction-specific intents
                    analysis = self._pattern_matching_fallback(user_query)
                    if analysis:
                        return analysis
                        
                    # Original fallback patterns
                    if "list" in user_query.lower() and "project" in user_query.lower():
                        logger.info("Fallback to list_projects intent based on keywords")
                        return {
                            "intent": "list_projects",
                            "tables": ["projects"],
                            "filters": {},
                            "explanation": "Listing all projects based on query keywords"
                        }
                    if "status" in user_query.lower() and "project" in user_query.lower():
                        logger.info("Fallback to project_status intent based on keywords")
                        return {
                            "intent": "project_status",
                            "tables": ["projects"],
                            "filters": {},
                            "explanation": "Getting project status based on query keywords"
                        }
                    if "budget" in user_query.lower():
                        logger.info("Fallback to budget_info intent based on keywords")
                        return {
                            "intent": "budget_info",
                            "tables": ["budgets"],
                            "filters": {},
                            "explanation": "Getting budget information based on query keywords"
                        }
                    # Return a default structure for other cases
                    return {
                        "intent": "unknown",
                        "tables": [],
                        "filters": {},
                        "explanation": "Failed to analyze query"
                    }
                
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            # Attempt to extract intent from query on error
            if "list" in user_query.lower() and "project" in user_query.lower():
                return {
                    "intent": "list_projects",
                    "tables": ["projects"],
                    "filters": {},
                    "explanation": "Falling back to basic intent detection due to error"
                }
            return {
                "intent": "unknown",
                "tables": [],
                "filters": {},
                "explanation": f"Error: {str(e)}"
            }
    
    def _enhance_query_with_context(self, user_query: str) -> str:
        """
        Enhance the user query with context information to improve analysis.
        For example, detect references to "it" or "this project" and resolve them.
        """
        # Check for pronouns that might need context resolution
        pronouns = ["it", "this project", "this", "that", "they", "them", "their"]
        has_pronoun = any(pronoun in user_query.lower() for pronoun in pronouns)
        
        # If no contextual references found, return the original query
        if not has_pronoun:
            return user_query
        
        # Add context resolution prompt if needed
        # In a full implementation, you would look at conversation history
        # to resolve what "it" or "this project" refers to
        return user_query
    
    def _enhance_analysis_with_entities(self, analysis: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        """
        Enhance the analysis with additional entity extraction beyond what the LLM provides.
        This helps identify project IDs, dates, and other specific entities in the query.
        """
        # Ensure filters dict exists
        if "filters" not in analysis:
            analysis["filters"] = {}
        
        # Extract project IDs using pattern matching
        project_id_match = re.search(r'(CABOT-1B|JAIN-1B|ELMGROVE-1B|MCKIERNAN-1B)', user_query, re.IGNORECASE)
        if project_id_match and "project_id" not in analysis["filters"]:
            analysis["filters"]["project_id"] = project_id_match.group(1).upper()
        
        # Extract dates
        date_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
            r'(\d{1,2}-\d{1,2}-\d{4})',  # MM-DD-YYYY
            r'(\d{4}-\d{1,2}-\d{1,2})'   # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, user_query)
            if date_match and "date" not in analysis["filters"]:
                analysis["filters"]["date"] = date_match.group(1)
        
        # Extract time periods
        time_period_match = re.search(r'(this|next|last) (week|month|quarter|year)', user_query, re.IGNORECASE)
        if time_period_match and "time_period" not in analysis["filters"]:
            analysis["filters"]["time_period"] = f"{time_period_match.group(1)} {time_period_match.group(2)}"
        
        # Extract status values
        status_match = re.search(r'(completed|in progress|todo|pending|active|done)', user_query, re.IGNORECASE)
        if status_match and "status" not in analysis["filters"]:
            analysis["filters"]["status"] = status_match.group(1).title()
        
        # Detect if chart generation is needed
        if "chart" in user_query.lower() or "graph" in user_query.lower() or "visual" in user_query.lower():
            analysis["generate_chart"] = True
            
            # Determine chart type
            if "bar" in user_query.lower():
                analysis["chart_type"] = "bar"
            elif "pie" in user_query.lower():
                analysis["chart_type"] = "pie"
            elif "line" in user_query.lower():
                analysis["chart_type"] = "line"
            elif "progress" in user_query.lower():
                analysis["chart_type"] = "phase_progress"
            elif "budget" in user_query.lower():
                analysis["chart_type"] = "budget"
            else:
                analysis["chart_type"] = "phase_progress"  # Default chart type
        
        # Detect if comparisons are needed
        if "compare" in user_query.lower() or "comparison" in user_query.lower() or "versus" in user_query.lower() or " vs " in user_query.lower():
            analysis["comparison"] = True
        
        return analysis
    
    def _pattern_matching_fallback(self, user_query: str) -> Optional[Dict[str, Any]]:
        """Use pattern matching to identify query intent when LLM parsing fails."""
        # Normalize the query for easier matching
        query = user_query.lower().strip()
        
        # 1. Selection Management patterns
        if re.search(r"open selection(s| item| items| tasks)?", query):
            # Extract project name if present
            project_match = re.search(r"for (?:project |the )?([\w\s-]+)(?:\?|$)", query)
            project_name = project_match.group(1).strip() if project_match else None
            
            return {
                "intent": "list_selections",
                "tables": ["selection_items", "projects"],
                "filters": {"status": "Open", "project_name": project_name},
                "explanation": "Listing open selection items"
            }
        
        if re.search(r"(how )?overdue is .* selection", query):
            # Extract selection name
            selection_match = re.search(r"overdue is ([\w\s-]+) selection", query)
            selection_name = selection_match.group(1).strip() if selection_match else None
            
            return {
                "intent": "selection_overdue",
                "tables": ["selection_items"],
                "filters": {"selection_name": selection_name},
                "explanation": "Checking how overdue a selection item is"
            }
        
        if re.search(r"selection.* (coming|due|upcoming).*(\d+)?\s+(week|day)", query):
            # Extract timeframe
            time_match = re.search(r"next (\d+)?\s+(week|day)", query)
            if time_match:
                number = int(time_match.group(1)) if time_match.group(1) else 1
                unit = time_match.group(2)
            else:
                number = 2  # Default to 2 weeks
                unit = "week"
            
            return {
                "intent": "upcoming_selections",
                "tables": ["selection_items"],
                "filters": {"timeframe": {"number": number, "unit": unit}},
                "explanation": f"Listing selection items due in the next {number} {unit}{'s' if number > 1 else ''}"
            }
        
        # 2. Project Phase Tracking patterns
        if re.search(r"(what|which) (stage|phase) is", query):
            # Extract project name
            project_match = re.search(r"(stage|phase) is (?:project |the )?([\w\s-]+)(?:\?|$|in)", query)
            project_name = project_match.group(2).strip() if project_match else None
            
            return {
                "intent": "project_phase_status",
                "tables": ["projects", "project_phase_assignments", "project_phases", "project_stages"],
                "filters": {"project_name": project_name},
                "explanation": "Retrieving current phase and stage for a project"
            }
        
        if re.search(r"(what|which) items.*(need|pending|remaining).*(complete|finish)", query) and re.search(r"(current|this) (phase|stage)", query):
            # Extract project context if present
            project_match = re.search(r"for (?:project |the )?([\w\s-]+)(?:\?|$)", query)
            project_name = project_match.group(1).strip() if project_match else None
            
            return {
                "intent": "phase_pending_tasks",
                "tables": ["projects", "project_phase_assignments", "phase_tasks", "phase_task_assignments"],
                "filters": {"project_name": project_name},
                "explanation": "Listing remaining tasks in the current phase/stage"
            }
        
        # 3. Walkthrough Management patterns
        if re.search(r"(any )?pd walkthrough.*(need|schedule|due)", query):
            return {
                "intent": "pd_walkthroughs_needed",
                "tables": ["walkthroughs", "walkthrough_types", "projects"],
                "filters": {"walkthrough_type": "PD", "status": "Not Scheduled"},
                "explanation": "Checking for PD walkthroughs that need scheduling"
            }
        
        if re.search(r"(any )?client walkthrough.*(need|schedule|due)", query):
            return {
                "intent": "client_walkthroughs_needed",
                "tables": ["walkthroughs", "walkthrough_types", "projects"],
                "filters": {"walkthrough_type": "Client", "status": "Not Scheduled"},
                "explanation": "Checking for Client walkthroughs that need scheduling"
            }
        
        if re.search(r"(recent|last) client walkthrough.*(complete|finish)", query):
            # Extract project context if present
            project_match = re.search(r"for (?:project |the )?([\w\s-]+)(?:\?|$)", query)
            project_name = project_match.group(1).strip() if project_match else None
            
            return {
                "intent": "recent_walkthrough_status",
                "tables": ["walkthroughs", "walkthrough_types", "projects"],
                "filters": {"walkthrough_type": "Client", "project_name": project_name},
                "explanation": "Checking if the most recent client walkthrough is completed"
            }
        
        # 4. Procurement Tracking patterns
        if re.search(r"(what|which) (still )?need.*(buy|purchase|bought|order|po)", query) or re.search(r"trades.*(need|missing).*(po|purchase order)", query):
            # Extract project context if present
            project_match = re.search(r"for (?:project |the )?([\w\s-]+)(?:\?|$)", query)
            project_name = project_match.group(1).strip() if project_match else None
            
            return {
                "intent": "trades_needing_po",
                "tables": ["trades", "bid_packages", "purchase_orders", "projects"],
                "filters": {"project_name": project_name},
                "explanation": "Listing trades that still need purchase orders"
            }
        
        # 5. Financial Milestone Tracking patterns
        if re.search(r"(what|which) payment milestone.*(currently|now) at", query):
            # Extract project name
            project_match = re.search(r"(milestone).*(project |the )?([\w\s-]+)(?:\?|$)", query)
            project_name = project_match.group(3).strip() if project_match else None
            
            return {
                "intent": "current_payment_milestone",
                "tables": ["payment_milestones", "projects"],
                "filters": {"project_name": project_name},
                "explanation": "Retrieving current payment milestone for a project"
            }
        
        if re.search(r"(what|which) project.*bill.*(this|next) week", query):
            return {
                "intent": "billable_projects",
                "tables": ["payment_milestones", "projects"],
                "filters": {"status": "Ready for Billing"},
                "explanation": "Listing projects that can be billed this week"
            }
        
        if re.search(r"(has|have|is) payment milestone.*(issue|invoice)", query):
            # Extract milestone info
            milestone_match = re.search(r"milestone [#]?(\d+)", query)
            milestone_number = int(milestone_match.group(1)) if milestone_match else None
            
            # Extract milestone name
            milestone_name_match = re.search(r"milestone [^0-9#]*?([a-zA-Z\s-]+)", query)
            milestone_name = milestone_name_match.group(1).strip() if milestone_name_match else None
            
            # Extract project context if present
            project_match = re.search(r"for (?:project |the )?([\w\s-]+)(?:\?|$)", query)
            project_name = project_match.group(1).strip() if project_match else None
            
            return {
                "intent": "payment_milestone_status",
                "tables": ["payment_milestones", "projects"],
                "filters": {
                    "milestone_number": milestone_number,
                    "milestone_name": milestone_name,
                    "project_name": project_name
                },
                "explanation": "Checking if a specific payment milestone has been issued"
            }
        
        # Project Details patterns
        if re.search(r"(who|what) is the (designer|developer|client) (for|of)", query):
            # Extract project name
            project_match = re.search(r"(for|of) (?:project |the )?([\w\s-]+)(?:\?|$)", query)
            project_name = project_match.group(2).strip() if project_match else None
            
            # Extract role being asked about
            role_match = re.search(r"(designer|developer|client)", query)
            role = role_match.group(1) if role_match else None
            
            return {
                "intent": "project_details",
                "tables": ["projects", "users", "leads"],
                "filters": {"project_name": project_name, "requested_role": role},
                "explanation": f"Getting {role} information for project {project_name}"
            }
        
        # Project Status patterns
        if re.search(r"(what('s| is) the |current )status (of|for)", query):
            # Extract project name
            project_match = re.search(r"(of|for) (?:project |the )?([\w\s-]+)(?:\?|$)", query)
            project_name = project_match.group(2).strip() if project_match else None
            
            return {
                "intent": "project_status",
                "tables": ["projects", "phases"],
                "filters": {"project_name": project_name},
                "explanation": f"Getting status information for project {project_name}"
            }
        
        # Project Progress patterns
        if re.search(r"(progress|complete|percent|completion).*(of|for)", query):
            # Extract project name
            project_match = re.search(r"(of|for) (?:project |the )?([\w\s-]+)(?:\?|$)", query)
            project_name = project_match.group(2).strip() if project_match else None
            
            intent = "project_details"
            if "chart" in query or "graph" in query or "visual" in query:
                intent = "project_status"
            
            return {
                "intent": intent,
                "tables": ["projects", "phases"],
                "filters": {"project_name": project_name},
                "generate_chart": "chart" in query or "graph" in query or "visual" in query,
                "chart_type": "phase_progress",
                "explanation": f"Getting progress information for project {project_name}"
            }
        
        # Subphase and task patterns
        if re.search(r"(what('s| is) the |current |show me )(subphase|sub-phase|task)", query):
            # Extract project name
            project_match = re.search(r"for (?:project |the )?([\w\s-]+)(?:\?|$)", query)
            project_name = project_match.group(1).strip() if project_match else None
            
            return {
                "intent": "project_details",
                "tables": ["projects", "phases", "subphases"],
                "filters": {"project_name": project_name, "detail_type": "current_task"},
                "explanation": f"Getting current task/subphase information for project {project_name}"
            }
        
        # Show all projects pattern
        if re.search(r"(show|list|get) (me |all )?(the |active |completed )?(projects|project list)", query):
            # Check if status filter is specified
            status = None
            if "active" in query:
                status = "active"
            elif "completed" in query:
                status = "Completed"
            
            return {
                "intent": "list_projects",
                "tables": ["projects"],
                "filters": {"status": status} if status else {},
                "explanation": "Listing projects with optional status filter"
            }
        
        # No matching pattern found
        return None
    
    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from text, handling code blocks."""
        # First try to extract JSON from code blocks
        json_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        match = re.search(json_pattern, text)
        
        if match:
            try:
                # Try to parse the extracted content
                json_str = match.group(1).strip()
                return json.loads(json_str)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse extracted JSON from code block: {match.group(1)}")
        
        # If no code blocks or parsing failed, try to find JSON object directly
        try:
            # Look for text that looks like a JSON object
            json_pattern = r"\{[\s\S]*\}"
            match = re.search(json_pattern, text)
            if match:
                return json.loads(match.group(0))
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON directly from text")
        
        # If all attempts fail, return None
        return None
    
    def generate_chart(self, data: Dict[str, float], chart_type: str, title: str) -> str:
        """Generate a chart based on data and return as base64 encoded string."""
        plt.figure(figsize=(10, 6))
        
        if chart_type == 'bar':
            plt.bar(data.keys(), data.values())
            plt.xticks(rotation=45, ha='right')
        elif chart_type == 'pie':
            plt.pie(data.values(), labels=data.keys(), autopct='%1.1f%%')
        elif chart_type == 'line':
            plt.plot(list(data.keys()), list(data.values()), marker='o')
            plt.xticks(rotation=45, ha='right')
        
        plt.title(title)
        plt.tight_layout()
        
        # Save plot to bytes buffer
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        
        # Encode plot as base64 string
        image_png = buffer.getvalue()
        image_base64 = base64.b64encode(image_png).decode('utf-8')
        
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def execute_database_operation(self, analysis: Dict[str, Any], conversation_id: str = None) -> Dict[str, Any]:
        """Execute database operations based on query analysis."""
        intent = analysis.get("intent", "unknown")
        result = {"success": False, "data": None, "message": "Operation not supported"}
        
        # Update conversation context if provided
        if conversation_id:
            if conversation_id not in self.conversation_context:
                self.conversation_context[conversation_id] = {}
            
            # Update context with current intent and filters
            self.conversation_context[conversation_id]["last_intent"] = intent
            self.conversation_context[conversation_id]["last_filters"] = analysis.get("filters", {})
        
        try:
            # Original intents (from existing code)
            if intent == "list_projects":
                projects = self.db.get_all_projects()
                
                # Apply status filter if specified
                status_filter = analysis.get("filters", {}).get("status")
                if status_filter:
                    # Handle both "active" and specific status values like "In Progress"
                    if status_filter.lower() == "active":
                        # "Active" could mean "In Progress" or "Planning" (not "Completed" or "Cancelled")
                        active_statuses = ["In Progress", "Planning", "Not Started"]
                        projects = [p for p in projects if p.get("status") in active_statuses]
                    else:
                        projects = [p for p in projects if p.get("status", "").lower() == status_filter.lower()]
                
                result = {"success": True, "data": projects, "message": "Projects retrieved successfully"}
            
            # Project details
            elif intent == "project_details":
                # Check for project_id or project_name in filters
                project_id = analysis.get("filters", {}).get("project_id")
                project_name = analysis.get("filters", {}).get("project_name")
                
                # Use either project_id or project_name to get project details
                project = None
                if project_id:
                    project = self.db.get_project_details(project_id)
                elif project_name:
                    # First try to get project by exact name
                    project = self.db.get_project_by_name(project_name)
                    
                    # If not found, try partial name match
                    if not project and project_name:
                        project = self.db.find_project_by_partial_name(project_name)
                
                if project:
                    result = {"success": True, "data": project, "message": "Project details retrieved successfully"}
                else:
                    result = {"success": False, "message": "Project not found"}
            
            # Project status
            elif intent == "project_status":
                # Check for project_id or project_name in filters
                project_id = analysis.get("filters", {}).get("project_id")
                project_name = analysis.get("filters", {}).get("project_name")
                
                # Use either project_id or project_name to get project status
                status = None
                if project_id:
                    status = self.db.get_project_status(project_id)
                elif project_name:
                    # First try to get project by exact name
                    project = self.db.get_project_by_name(project_name)
                    
                    # If not found, try partial name match
                    if not project and project_name:
                        project = self.db.find_project_by_partial_name(project_name)
                    
                    if project:
                        status = self.db.get_project_status(project["id"])
                
                if status:
                    result = {"success": True, "data": status, "message": "Project status retrieved successfully"}
                else:
                    result = {"success": False, "message": "Project status not found"}
            
            # Budget information
            elif intent == "budget_info":
                # Check for project_id or project_name in filters
                project_id = analysis.get("filters", {}).get("project_id")
                project_name = analysis.get("filters", {}).get("project_name")
                
                # Use either project_id or project_name to get budget info
                budget = None
                if project_id:
                    budget = self.db.get_budget_info(project_id)
                elif project_name:
                    # First try to get project by exact name
                    project = self.db.get_project_by_name(project_name)
                    
                    # If not found, try partial name match
                    if not project and project_name:
                        project = self.db.find_project_by_partial_name(project_name)
                    
                    if project:
                        budget = self.db.get_budget_info(project["id"])
                
                if budget:
                    result = {"success": True, "data": budget, "message": "Budget information retrieved successfully"}
                    
                    # Generate budget chart if needed
                    if analysis.get("generate_chart", False):
                        if isinstance(budget, list) and len(budget) > 0:
                            # Multiple projects budget chart
                            chart_data = {item["project_name"]: float(item["total_budget"]) for item in budget}
                            result["chart"] = self.generate_chart(chart_data, "bar", "Project Budgets")
                        else:
                            # Single project budget breakdown
                            chart_data = {
                                "Total Budget": float(budget["total_budget"]),
                                "Spent": float(budget["spent"]),
                                "Remaining": float(budget["remaining"])
                            }
                            result["chart"] = self.generate_chart(chart_data, "pie", f"Budget for {budget['project_name']}")
                else:
                    result = {"success": False, "message": "Budget information not found"}
            
            # Project tasks
            elif intent == "project_tasks":
                # Check for project_id or project_name in filters
                project_id = analysis.get("filters", {}).get("project_id")
                project_name = analysis.get("filters", {}).get("project_name")
                
                # Use either project_id or project_name to get project tasks
                tasks = None
                if project_id:
                    tasks = self.db.get_project_tasks(project_id)
                elif project_name:
                    # First try to get project by exact name
                    project = self.db.get_project_by_name(project_name)
                    
                    # If not found, try partial name match
                    if not project and project_name:
                        project = self.db.find_project_by_partial_name(project_name)
                    
                    if project:
                        tasks = self.db.get_project_tasks(project["id"])
                
                if tasks is not None:
                    result = {"success": True, "data": tasks, "message": "Project tasks retrieved successfully"}
                else:
                    result = {"success": False, "message": "Project tasks not found"}
            
            # Project timeline
            elif intent == "project_timeline":
                # Check for project_id or project_name in filters
                project_id = analysis.get("filters", {}).get("project_id")
                project_name = analysis.get("filters", {}).get("project_name")
                
                # Use either project_id or project_name to get project timeline
                timeline = None
                if project_id:
                    timeline = self.db.get_project_timeline(project_id)
                elif project_name:
                    # First try to get project by exact name
                    project = self.db.get_project_by_name(project_name)
                    
                    # If not found, try partial name match
                    if not project and project_name:
                        project = self.db.find_project_by_partial_name(project_name)
                    
                    if project:
                        timeline = self.db.get_project_timeline(project["id"])
                
                if timeline:
                    result = {"success": True, "data": timeline, "message": "Project timeline retrieved successfully"}
                else:
                    result = {"success": False, "message": "Project timeline not found"}
            
            # Project search
            elif intent == "search_projects":
                search_term = analysis.get("filters", {}).get("search_term")
                if search_term:
                    projects = self.db.search_projects(search_term)
                    result = {"success": True, "data": projects, "message": f"Search results for '{search_term}'"}
                else:
                    result = {"success": False, "message": "Search term is required"}
            
            # General search
            elif intent == "general_search":
                search_term = analysis.get("filters", {}).get("search_term")
                if search_term:
                    data = self.db.search_across_tables(search_term)
                    result = {"success": True, "data": data, "message": f"Search results for '{search_term}' across all tables"}
                else:
                    result = {"success": False, "message": "Search term is required"}
            
            # Generate report
            elif intent == "generate_report":
                # Check for project_id or project_name in filters
                project_id = analysis.get("filters", {}).get("project_id")
                project_name = analysis.get("filters", {}).get("project_name")
                
                # Use either project_id or project_name to generate report
                if project_id:
                    # Collect all relevant data for the report
                    report_data = {
                        "project": self.db.get_project_details(project_id),
                        "status": self.db.get_project_status(project_id),
                        "budget": self.db.get_budget_info(project_id),
                        "tasks": self.db.get_project_tasks(project_id),
                        "milestones": self.db.get_project_milestones(project_id),
                        "team": self.db.get_project_team(project_id),
                        "issues": self.db.get_project_issues(project_id)
                    }
                    result = {"success": True, "data": report_data, "message": "Report data retrieved successfully"}
                elif project_name:
                    # First try to get project by exact name
                    project = self.db.get_project_by_name(project_name)
                    
                    # If not found, try partial name match
                    if not project and project_name:
                        project = self.db.find_project_by_partial_name(project_name)
                    
                    if project:
                        # Collect all relevant data for the report
                        report_data = {
                            "project": project,
                            "status": self.db.get_project_status(project["id"]),
                            "budget": self.db.get_budget_info(project["id"]),
                            "tasks": self.db.get_project_tasks(project["id"]),
                            "milestones": self.db.get_project_milestones(project["id"]),
                            "team": self.db.get_project_team(project["id"]),
                            "issues": self.db.get_project_issues(project["id"])
                        }
                        result = {"success": True, "data": report_data, "message": "Report data retrieved successfully"}
                    else:
                        result = {"success": False, "message": "Project not found"}
                else:
                    result = {"success": False, "message": "Project ID or name is required for report generation"}
            
            # Project milestones
            elif intent == "project_milestones":
                # Check for project_id or project_name in filters
                project_id = analysis.get("filters", {}).get("project_id")
                project_name = analysis.get("filters", {}).get("project_name")
                
                # Use either project_id or project_name to get project milestones
                milestones = None
                if project_id:
                    milestones = self.db.get_project_milestones(project_id)
                elif project_name:
                    # First try to get project by exact name
                    project = self.db.get_project_by_name(project_name)
                    
                    # If not found, try partial name match
                    if not project and project_name:
                        project = self.db.find_project_by_partial_name(project_name)
                    
                    if project:
                        milestones = self.db.get_project_milestones(project["id"])
                
                if milestones is not None:
                    result = {"success": True, "data": milestones, "message": "Project milestones retrieved successfully"}
                else:
                    result = {"success": False, "message": "Project milestones not found"}
            
            # Project team
            elif intent == "project_team":
                # Check for project_id or project_name in filters
                project_id = analysis.get("filters", {}).get("project_id")
                project_name = analysis.get("filters", {}).get("project_name")
                
                # Use either project_id or project_name to get project team
                team = None
                if project_id:
                    team = self.db.get_project_team(project_id)
                elif project_name:
                    # First try to get project by exact name
                    project = self.db.get_project_by_name(project_name)
                    
                    # If not found, try partial name match
                    if not project and project_name:
                        project = self.db.find_project_by_partial_name(project_name)
                    
                    if project:
                        team = self.db.get_project_team(project["id"])
                
                if team is not None:
                    result = {"success": True, "data": team, "message": "Project team retrieved successfully"}
                else:
                    result = {"success": False, "message": "Project team not found"}
            
            # Project issues
            elif intent == "project_issues":
                # Check for project_id or project_name in filters
                project_id = analysis.get("filters", {}).get("project_id")
                project_name = analysis.get("filters", {}).get("project_name")
                
                # Use either project_id or project_name to get project issues
                issues = None
                if project_id:
                    issues = self.db.get_project_issues(project_id)
                elif project_name:
                    # First try to get project by exact name
                    project = self.db.get_project_by_name(project_name)
                    
                    # If not found, try partial name match
                    if not project and project_name:
                        project = self.db.find_project_by_partial_name(project_name)
                    
                    if project:
                        issues = self.db.get_project_issues(project["id"])
                
                if issues is not None:
                    result = {"success": True, "data": issues, "message": "Project issues retrieved successfully"}
                else:
                    result = {"success": False, "message": "Project issues not found"}
            
            # Project documents
            elif intent == "project_documents":
                # Check for project_id or project_name in filters
                project_id = analysis.get("filters", {}).get("project_id")
                project_name = analysis.get("filters", {}).get("project_name")
                
                # Use either project_id or project_name to get project documents
                documents = None
                if project_id:
                    documents = self.db.get_project_documents(project_id)
                elif project_name:
                    # First try to get project by exact name
                    project = self.db.get_project_by_name(project_name)
                    
                    # If not found, try partial name match
                    if not project and project_name:
                        project = self.db.find_project_by_partial_name(project_name)
                    
                    if project:
                        documents = self.db.get_project_documents(project["id"])
                
                if documents is not None:
                    result = {"success": True, "data": documents, "message": "Project documents retrieved successfully"}
                else:
                    result = {"success": False, "message": "Project documents not found"}
            
            # 1. Selection Management Intents
            elif intent == "list_selections":
                project_name = analysis.get("filters", {}).get("project_name")
                status = analysis.get("filters", {}).get("status", "Open")
                
                search_term = analysis.get("filters", {}).get("search_term")
                if search_term and not project_name:
                    project_name = search_term
                
                if project_name:
                    # Get project ID from name
                    project = self.db.get_project_by_name(project_name)
                    if not project:
                        return {"success": False, "message": f"Project '{project_name}' not found"}
                    
                    selections = self.db.get_selection_list(project["id"], status)
                else:
                    # Get all selections with given status
                    selections = self.db.get_selection_list(None, status)
                
                result = {
                    "success": True, 
                    "data": selections,
                    "message": f"{status} selection items retrieved successfully"
                }
            
            elif intent == "selection_overdue":
                selection_name = analysis.get("filters", {}).get("selection_name")
                
                if selection_name:
                    selection = self.db.get_selection_by_name(selection_name)
                    if not selection:
                        return {"success": False, "message": f"Selection '{selection_name}' not found"}
                    
                    # Calculate overdue days
                    overdue_days = selection.get('days_overdue')
                    
                    if overdue_days and overdue_days > 0:
                        result = {
                            "success": True,
                            "data": {"selection": selection, "days_overdue": overdue_days},
                            "message": f"Selection '{selection_name}' is {overdue_days} days overdue"
                        }
                    else:
                        result = {
                            "success": True,
                            "data": {"selection": selection, "days_overdue": 0},
                            "message": f"Selection '{selection_name}' is not overdue"
                        }
                else:
                    result = {"success": False, "message": "Selection name is required"}
            
            elif intent == "upcoming_selections":
                timeframe = analysis.get("filters", {}).get("timeframe", {"number": 2, "unit": "week"})
                project_name = analysis.get("filters", {}).get("project_name")
                
                date_range = analysis.get("filters", {}).get("date_range", {})
                days = 14  # Default to 2 weeks
                
                # Extract days from timeframe if available
                if timeframe:
                    number = timeframe.get("number", 2)
                    unit = timeframe.get("unit", "week")
                    if unit == "week":
                        days = number * 7
                    else:  # Assume days
                        days = number
                
                if project_name:
                    # Get project ID from name
                    project = self.db.get_project_by_name(project_name)
                    if not project:
                        return {"success": False, "message": f"Project '{project_name}' not found"}
                    
                    end_date = datetime.now() + timedelta(days=days)
                    upcoming_selections = self.db.get_upcoming_selections_by_project(project["id"], end_date)
                else:
                    # Get all upcoming selections
                    upcoming_selections = self.db.get_upcoming_selections(days)
                
                result = {
                    "success": True,
                    "data": upcoming_selections,
                    "message": f"Upcoming selections due in the next {days} days"
                }
            
            # 2. Project Phase Tracking Intents
            elif intent == "project_phase_status":
                project_name = analysis.get("filters", {}).get("project_name")
                
                if project_name:
                    # Get project ID from name
                    project = self.db.get_project_by_name(project_name)
                    if not project:
                        return {"success": False, "message": f"Project '{project_name}' not found"}
                    
                    phase_status = self.db.get_project_phase_status(project["id"])
                    result = {
                        "success": True,
                        "data": phase_status,
                        "message": f"Current phase and stage for project '{project_name}' retrieved successfully"
                    }
                else:
                    result = {"success": False, "message": "Project name is required"}
            
            elif intent == "phase_pending_tasks":
                project_name = analysis.get("filters", {}).get("project_name")
                
                if project_name:
                    # Get project ID from name
                    project = self.db.get_project_by_name(project_name)
                    if not project:
                        return {"success": False, "message": f"Project '{project_name}' not found"}
                    
                    # Get current phase and stage
                    phase_status = self.db.get_project_phase_status(project["id"])
                    if not phase_status:
                        return {"success": False, "message": f"No phase information found for project '{project_name}'"}
                    
                    # Get pending tasks for current phase and stage
                    pending_tasks = self.db.get_pending_phase_tasks(
                        project["id"], 
                        phase_status["phase_id"], 
                        phase_status["stage_id"]
                    )
                    
                    result = {
                        "success": True,
                        "data": {
                            "phase": phase_status["phase_name"],
                            "stage": phase_status["stage_name"],
                            "pending_tasks": pending_tasks
                        },
                        "message": f"Pending tasks for current phase retrieved successfully"
                    }
                else:
                    result = {"success": False, "message": "Project name is required"}
            
            # 3. Walkthrough Management Intents
            elif intent == "pd_walkthroughs_needed":
                walkthroughs = self.db.get_walkthroughs_by_type("PD", "Not Scheduled")
                result = {
                    "success": True,
                    "data": walkthroughs,
                    "message": f"{len(walkthroughs)} PD walkthroughs need to be scheduled"
                }
            
            elif intent == "client_walkthroughs_needed":
                walkthroughs = self.db.get_walkthroughs_by_type("Client", "Not Scheduled")
                result = {
                    "success": True,
                    "data": walkthroughs,
                    "message": f"{len(walkthroughs)} Client walkthroughs need to be scheduled"
                }
            
            elif intent == "recent_walkthrough_status":
                project_name = analysis.get("filters", {}).get("project_name")
                walkthrough_type = analysis.get("filters", {}).get("walkthrough_type", "Client")
                
                if project_name:
                    # Get project ID from name
                    project = self.db.get_project_by_name(project_name)
                    if not project:
                        return {"success": False, "message": f"Project '{project_name}' not found"}
                    
                    walkthrough = self.db.get_project_recent_walkthrough(project["id"], walkthrough_type)
                    
                    if not walkthrough:
                        result = {
                            "success": True,
                            "data": None,
                            "message": f"No {walkthrough_type} walkthroughs found for project '{project_name}'"
                        }
                    elif walkthrough["status"] == "Completed":
                        result = {
                            "success": True,
                            "data": walkthrough,
                            "message": f"The most recent {walkthrough_type} walkthrough for project '{project_name}' was completed on {walkthrough['completed_date']}"
                        }
                    else:
                        result = {
                            "success": True,
                            "data": walkthrough,
                            "message": f"The most recent {walkthrough_type} walkthrough for project '{project_name}' has not been completed. Current status: {walkthrough['status']}"
                        }
                else:
                    result = {"success": False, "message": "Project name is required"}
            
            # 4. Procurement Tracking Intents
            elif intent == "trades_needing_po":
                project_name = analysis.get("filters", {}).get("project_name")
                
                if project_name:
                    # Get project ID from name
                    project = self.db.get_project_by_name(project_name)
                    if not project:
                        return {"success": False, "message": f"Project '{project_name}' not found"}
                    
                    trades = self.db.get_trades_needing_po(project["id"])
                    result = {
                        "success": True,
                        "data": trades,
                        "message": f"{len(trades)} trades still need purchase orders for project '{project_name}'"
                    }
                else:
                    # Get trades needing PO across all projects
                    trades = self.db.get_trades_needing_po()
                    result = {
                        "success": True,
                        "data": trades,
                        "message": f"{len(trades)} trades still need purchase orders across all projects"
                    }
            
            # 5. Financial Milestone Tracking Intents
            elif intent == "current_payment_milestone":
                project_name = analysis.get("filters", {}).get("project_name")
                
                if project_name:
                    # Get project ID from name
                    project = self.db.get_project_by_name(project_name)
                    if not project:
                        return {"success": False, "message": f"Project '{project_name}' not found"}
                    
                    milestone = self.db.get_current_payment_milestone(project["id"])
                    
                    if not milestone:
                        result = {
                            "success": True,
                            "data": None,
                            "message": f"No payment milestones found for project '{project_name}'"
                        }
                    else:
                        result = {
                            "success": True,
                            "data": milestone,
                            "message": f"Current payment milestone for project '{project_name}' is: {milestone['title']} (Status: {milestone['status']})"
                        }
                else:
                    result = {"success": False, "message": "Project name is required"}
            
            elif intent == "billable_projects":
                projects = self.db.get_billable_projects()
                result = {
                    "success": True,
                    "data": projects,
                    "message": f"{len(projects)} projects are ready to be billed this week"
                }
            
            elif intent == "payment_milestone_status":
                project_name = analysis.get("filters", {}).get("project_name")
                milestone_number = analysis.get("filters", {}).get("milestone_number")
                milestone_name = analysis.get("filters", {}).get("milestone_name")
                
                if not project_name:
                    return {"success": False, "message": "Project name is required"}
                
                # Get project ID from name
                project = self.db.get_project_by_name(project_name)
                if not project:
                    return {"success": False, "message": f"Project '{project_name}' not found"}
                
                # If milestone number is provided, get that specific milestone
                if milestone_number:
                    milestone = self.db.get_payment_milestone_by_number(project["id"], milestone_number)
                    
                    if not milestone:
                        result = {
                            "success": True,
                            "data": None,
                            "message": f"Payment milestone #{milestone_number} not found for project '{project_name}'"
                        }
                    else:
                        status_msg = "has been issued" if milestone["status"] in ["Invoiced", "Paid"] else "has not been issued yet"
                        result = {
                            "success": True,
                            "data": milestone,
                            "message": f"Payment milestone #{milestone_number} ({milestone['title']}) for project '{project_name}' {status_msg}. Current status: {milestone['status']}"
                        }
                
                # Otherwise, try to find by name if provided
                elif milestone_name:
                    # Get all milestones and filter by name
                    milestones = self.db.get_payment_milestones(project["id"])
                    matching_milestones = [m for m in milestones if milestone_name.lower() in m['title'].lower()]
                    
                    if not matching_milestones:
                        result = {
                            "success": True,
                            "data": None,
                            "message": f"No payment milestones matching '{milestone_name}' found for project '{project_name}'"
                        }
                    else:
                        milestone = matching_milestones[0]  # Take the first match
                        status_msg = "has been issued" if milestone["status"] in ["Invoiced", "Paid"] else "has not been issued yet"
                        result = {
                            "success": True,
                            "data": milestone,
                            "message": f"Payment milestone '{milestone['title']}' for project '{project_name}' {status_msg}. Current status: {milestone['status']}"
                        }
                
                # If neither number nor name provided, get the current milestone
                else:
                    milestone = self.db.get_current_payment_milestone(project["id"])
                    
                    if not milestone:
                        result = {
                            "success": True,
                            "data": None,
                            "message": f"No payment milestones found for project '{project_name}'"
                        }
                    else:
                        status_msg = "has been issued" if milestone["status"] in ["Invoiced", "Paid"] else "has not been issued yet"
                        result = {
                            "success": True,
                            "data": milestone,
                            "message": f"Current payment milestone for project '{project_name}' is: {milestone['title']} and {status_msg}. Status: {milestone['status']}"
                        }
            
            else:
                result = {"success": False, "message": f"Unsupported intent: {intent}"}
                
        except Exception as e:
            logger.error(f"Error executing database operation: {e}")
            result = {"success": False, "message": f"Error: {str(e)}"}
            
        return result