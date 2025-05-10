"""
Entry point for the construction project management chatbot application.
"""

import os
import logging
from app.main import create_app
from app.utils.logger import setup_logger
from datetime import datetime, timedelta

# Set up logger
logger = setup_logger(__name__, log_file='logs/app.log')

def main():
    """Run the application."""
    try:
        # Get port from environment or use default
        port = int(os.environ.get('PORT', 8000))
        
        # Create Flask app
        app = create_app()
        
        # Run the app
        logger.info(f"Starting application on port {port}")
        app.run(host='0.0.0.0', port=port)
        
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        raise

if __name__ == '__main__':
    main()