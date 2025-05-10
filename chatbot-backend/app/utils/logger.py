# Logging setup
"""Logging setup for the application."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(name: str, 
                 log_level: str = 'INFO', 
                 log_format: Optional[str] = None,
                 log_file: Optional[str] = None,
                 max_size: int = 10485760,  # 10 MB
                 backup_count: int = 3) -> logging.Logger:
    """Set up a logger with standard configuration.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log message format
        log_file: Path to log file (if None, log to console only)
        max_size: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        
    Returns:
        Configured logger
    """
    # Convert log level string to constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Use default format if not provided
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Get logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = []  # Clear existing handlers
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log file is specified
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_request_logger():
    """Get logger for HTTP requests."""
    return setup_logger(
        'app.request',
        log_file='logs/request.log',
        log_format='%(asctime)s - %(levelname)s - %(message)s'
    )

def get_db_logger():
    """Get logger for database operations."""
    return setup_logger(
        'app.database',
        log_file='logs/database.log',
        log_format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
    )

def get_chatbot_logger():
    """Get logger for chatbot operations."""
    return setup_logger(
        'app.chatbot',
        log_file='logs/chatbot.log',
        log_format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
    )

def get_error_logger():
    """Get logger for errors."""
    return setup_logger(
        'app.error',
        log_level='ERROR',
        log_file='logs/error.log',
        log_format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s\n%(pathname)s:%(lineno)d\n'
    )