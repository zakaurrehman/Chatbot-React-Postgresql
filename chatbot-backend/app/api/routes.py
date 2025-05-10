"""API routes for the chatbot application."""

from flask import Blueprint, request, jsonify, current_app, render_template, make_response
import logging
import traceback
from datetime import datetime, timedelta
import os
from app.chatbot.engine import ConstructionChatbot
from dotenv import load_dotenv
from app.utils.pdf_generator import PDFGenerator  # Import the PDF generator

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Initialize chatbot (will be initialized per-request)
chatbot = None

@api_bp.before_app_first_request
def initialize_chatbot():
    """Initialize the chatbot before the first request."""
    global chatbot
    logger.info("Initializing chatbot...")
    try:
        chatbot = ConstructionChatbot()
        logger.info("Chatbot initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing chatbot: {e}")
        logger.error(traceback.format_exc())

@api_bp.route('/chat', methods=['POST'])
def chat():
    """Process a chat message and return a response."""
    global chatbot
    
    if chatbot is None:
        try:
            chatbot = ConstructionChatbot()
        except Exception as e:
            logger.error(f"Error initializing chatbot: {e}")
            
            # Get database connection details for error page
            db_params = {
                "db_host": os.getenv("DB_HOST", ""),
                "db_name": os.getenv("DB_NAME", ""),
                "db_user": os.getenv("DB_USER", ""),
                "db_port": os.getenv("DB_PORT", ""),
                "db_sslmode": os.getenv("DB_SSLMODE", "")
            }
            
            # If AJAX request, return JSON error
            if request.is_json:
                return jsonify({
                    'error': 'Database connection error',
                    'message': str(e),
                    'db_params': db_params
                }), 500
            
            # If regular request, render error page
            return render_template('db_error.html', 
                                  error_message=str(e), 
                                  **db_params), 500
    
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'No message provided'}), 400
        
        user_message = data['message']
        logger.info(f"Received message: {user_message}")
        
        # Process user message
        chat_id = data.get('chat_id')
        result = chatbot.process_query(user_message, chat_id)
        
        # Get the raw message content, which should contain the natural language response
        # This is the key change - ensuring we're getting the conversational response
        message_content = result.get('message', 'I couldn\'t process your request.')
        
        # Log the response for debugging
        logger.info(f"Chatbot response: {message_content[:100]}...")  # Log first 100 chars
        
        # Prepare response with the natural language content
        response = {
            'message': message_content,
            'success': True
        }
        
        # Add chat_id if provided in the result
        if 'chat_id' in result:
            response['chat_id'] = result['chat_id']
        
        # Include chart if available
        if 'chart' in result:
            response['chart'] = result['chart']
        
        # Include data if available (for debugging)
        if 'data' in result:
            response['data'] = result['data']
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Failed to process message',
            'message': str(e)
        }), 500

@api_bp.route('/healthcheck', methods=['GET'])
def healthcheck():
    """Simple health check endpoint."""
    global chatbot
    
    if chatbot is None:
        try:
            chatbot = ConstructionChatbot()
        except Exception as e:
            logger.error(f"Error initializing chatbot: {e}")
            return jsonify({
                'status': 'error',
                'message': 'Database connection error',
                'error': str(e)
            }), 500
    
    try:
        # Test database connection
        tables = chatbot.db.db.get_tables()
        db_status = len(tables) > 0
        
        return jsonify({
            'status': 'ok',
            'database': 'connected' if db_status else 'disconnected',
            'tables_found': len(tables),
            'table_names': tables[:10]  # Show first 10 tables
        })
    except Exception as e:
        logger.error(f"Error in healthcheck: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@api_bp.route('/tables', methods=['GET'])
def get_tables():
    """Get list of tables in the database."""
    global chatbot
    
    if chatbot is None:
        try:
            chatbot = ConstructionChatbot()
        except Exception as e:
            logger.error(f"Error initializing chatbot: {e}")
            return jsonify({
                'error': 'Failed to initialize chatbot',
                'message': str(e)
            }), 500
    
    try:
        tables = chatbot.db.db.get_tables()
        return jsonify({
            'tables': tables,
            'count': len(tables)
        })
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        return jsonify({
            'error': 'Failed to get tables',
            'message': str(e)
        }), 500

@api_bp.route('/schema/<table_name>', methods=['GET'])
def get_table_schema(table_name):
    """Get schema for a specific table."""
    global chatbot
    
    if chatbot is None:
        try:
            chatbot = ConstructionChatbot()
        except Exception as e:
            logger.error(f"Error initializing chatbot: {e}")
            return jsonify({
                'error': 'Failed to initialize chatbot',
                'message': str(e)
            }), 500
    
    try:
        schema = chatbot.db.db.get_table_schema(table_name)
        
        # Format schema for response
        formatted_schema = []
        for col in schema:
            formatted_schema.append({
                'column_name': col[0],
                'data_type': col[1],
                'is_nullable': col[2] == 'YES',
                'default_value': col[3]
            })
        
        return jsonify({
            'table': table_name,
            'columns': formatted_schema
        })
    except Exception as e:
        logger.error(f"Error getting schema for table {table_name}: {e}")
        return jsonify({
            'error': f'Failed to get schema for table {table_name}',
            'message': str(e)
        }), 500

@api_bp.route('/sample/<table_name>', methods=['GET'])
def get_table_sample(table_name):
    """Get a sample of data from a table."""
    global chatbot
    
    if chatbot is None:
        try:
            chatbot = ConstructionChatbot()
        except Exception as e:
            logger.error(f"Error initializing chatbot: {e}")
            return jsonify({
                'error': 'Failed to initialize chatbot',
                'message': str(e)
            }), 500
    
    try:
        limit = request.args.get('limit', default=5, type=int)
        sample = chatbot.db.db.get_table_sample(table_name, limit)
        
        # Convert sample to list of dictionaries
        formatted_sample = [dict(row) for row in sample] if sample else []
        
        return jsonify({
            'table': table_name,
            'samples': formatted_sample,
            'count': len(formatted_sample)
        })
    except Exception as e:
        logger.error(f"Error getting sample for table {table_name}: {e}")
        return jsonify({
            'error': f'Failed to get sample for table {table_name}',
            'message': str(e)
        }), 500

@api_bp.route('/generate-pdf/<project_id>', methods=['GET'])
def generate_pdf(project_id):
    """Generate a PDF report for a project."""
    global chatbot
    
    if chatbot is None:
        try:
            chatbot = ConstructionChatbot()
        except Exception as e:
            logger.error(f"Error initializing chatbot: {e}")
            return jsonify({
                'error': 'Failed to initialize chatbot',
                'message': str(e)
            }), 500
    
    try:
        # Initialize the PDF generator
        pdf_generator = PDFGenerator()
        
        # Get project data from the chatbot
        project_data = chatbot.db._project.get_project_details(project_id)
        
        if not project_data:
            return jsonify({
                'error': 'Project not found',
                'message': f'Could not find project with ID {project_id}'
            }), 404
        
        # Generate the PDF
        pdf = pdf_generator.generate_project_report(project_data)
        
        # Return the PDF as a response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=project_report_{project_id}.pdf'
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Failed to generate PDF',
            'message': str(e)
        }), 500

@api_bp.route('/generate-chart/<project_id>', methods=['GET'])
def generate_chart(project_id):
    """Generate a chart for a project."""
    global chatbot
    
    if chatbot is None:
        try:
            chatbot = ConstructionChatbot()
        except Exception as e:
            logger.error(f"Error initializing chatbot: {e}")
            return jsonify({
                'error': 'Failed to initialize chatbot',
                'message': str(e)
            }), 500
    
    try:
        # Get chart type from query parameters
        chart_type = request.args.get('type', default='phase_progress', type=str)
        
        # Get project data from the chatbot
        project_data = chatbot.db._project.get_project_details(project_id)
        
        if not project_data:
            return jsonify({
                'error': 'Project not found',
                'message': f'Could not find project with ID {project_id}'
            }), 404
        
        # Generate chart based on type
        import matplotlib.pyplot as plt
        import io
        import base64
        
        plt.figure(figsize=(10, 6))
        
        if chart_type == 'phase_progress':
            # Extract phase data
            phase_info = project_data.get('phase_info', {})
            phases = phase_info.get('phases', [])
            
            if not phases:
                return jsonify({
                    'error': 'No phase data',
                    'message': 'No phase data available for this project'
                }), 404
            
            # Extract data for the chart
            phase_names = [phase.get('name', 'Unknown').replace('Phase ', 'P') for phase in phases]
            phase_progress = [phase.get('progress', 0) for phase in phases]
            
            # Create the bar chart
            plt.bar(phase_names, phase_progress)
            plt.title(f'Phase Progress for {project_data["name"]}')
            plt.xlabel('Phases')
            plt.ylabel('Progress (%)')
            plt.ylim(0, 100)
            
        elif chart_type == 'tasks':
            # Extract current phase data
            phase_info = project_data.get('phase_info', {})
            current_phase = phase_info.get('current_phase', {})
            
            if not current_phase or 'subphases' not in current_phase:
                return jsonify({
                    'error': 'No task data',
                    'message': 'No task data available for this project'
                }), 404
            
            # Count tasks by status
            status_counts = {}
            for subphase in current_phase['subphases']:
                status = None
                if hasattr(subphase, 'get'):
                    status = subphase.get('status')
                elif isinstance(subphase, dict):
                    status = subphase.get('status')
                
                if status:
                    if status not in status_counts:
                        status_counts[status] = 0
                    status_counts[status] += 1
            
            # Create the pie chart
            plt.pie(status_counts.values(), labels=status_counts.keys(), autopct='%1.1f%%')
            plt.title(f'Task Status Distribution for {project_data["name"]}')
            
        else:
            return jsonify({
                'error': 'Invalid chart type',
                'message': f'Chart type {chart_type} is not supported'
            }), 400
        
        # Save the chart to a buffer and encode as base64
        buffer = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        chart_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        # Return the chart as a base64 encoded string
        return jsonify({
            'chart': f'data:image/png;base64,{chart_data}',
            'project': project_data['name']
        })
        
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Failed to generate chart',
            'message': str(e)
        }), 500

@api_bp.errorhandler(404)
def handle_404(e):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Endpoint not found',
        'message': str(e)
    }), 404

@api_bp.errorhandler(500)
def handle_500(e):
    """Handle 500 errors."""
    return jsonify({
        'error': 'Internal server error',
        'message': str(e)
    }), 500