

import os
import logging
from flask import Flask, jsonify, send_from_directory
from app.config import get_config
from app.utils.logger import setup_logger

# Setup logging
logger = setup_logger(__name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                template_folder='../chatbot/build', 
                static_folder='../chatbot/build')
    
    # Load configuration
    config = get_config()
    app.config.from_object(config)
    
    if not app.debug:
        setup_logger('werkzeug', config.LOG_LEVEL, config.LOG_FORMAT, 'logs/werkzeug.log')
    
    register_error_handlers(app)
    register_blueprints(app)
    register_routes(app)
    
    return app

def register_error_handlers(app):
    """Register error handlers for the application."""
    @app.errorhandler(404)
    def page_not_found(e):
        """Serve React index.html for 404 errors."""
        return send_from_directory(app.static_folder, 'index.html'), 200
    
    @app.errorhandler(500)
    def internal_server_error(e):
        """Serve React index.html for 500 errors."""
        logger.error(f"Internal server error: {e}")
        return send_from_directory(app.static_folder, 'index.html'), 200

def register_blueprints(app):
    """Register blueprints for the application."""
    from app.api.routes import api_bp
    app.register_blueprint(api_bp)

def register_routes(app):
    """Register routes for the application."""
    @app.route('/health')
    def health():
        """Health check endpoint."""
        return jsonify({'status': 'ok'})

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        """Serve React static files and index.html for SPA routing."""
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"Starting application on port {port}")
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')
