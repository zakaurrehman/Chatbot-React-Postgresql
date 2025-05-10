# API middleware
"""Middleware for API request handling."""

import time
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import request, jsonify, g

# Setup logging
logger = logging.getLogger(__name__)

def log_request(f):
    """Middleware to log API requests."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Start timer
        start_time = time.time()
        
        # Store request info
        g.request_start_time = start_time
        g.request_path = request.path
        g.request_method = request.method
        
        # Log request
        logger.info(f"Request: {request.method} {request.path}")
        
        # Process request
        response = f(*args, **kwargs)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(f"Response: {request.method} {request.path} - "
                    f"Status: {response.status_code} - "
                    f"Duration: {duration:.4f}s")
        
        return response
    return decorated_function

def handle_errors(f):
    """Middleware to handle errors in API requests."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {request.method} {request.path}: {str(e)}")
            return jsonify({
                'error': 'Internal server error',
                'message': str(e)
            }), 500
    return decorated_function

def require_json(f):
    """Middleware to ensure request has JSON data."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type must be application/json'
            }), 415
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(limit=100, period=60):
    """Middleware to apply rate limiting to API requests.
    
    Args:
        limit: Maximum number of requests allowed in the period
        period: Time period in seconds
    """
    def decorator(f):
        # Simple in-memory cache for rate limiting
        # In production, use Redis or similar
        cache = {}
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP
            client_ip = request.remote_addr
            
            # Get current time
            current_time = time.time()
            
            # Initialize or clean up cache for this client
            if client_ip not in cache:
                cache[client_ip] = []
            
            # Remove old entries
            cache[client_ip] = [t for t in cache[client_ip] if current_time - t < period]
            
            # Check if limit exceeded
            if len(cache[client_ip]) >= limit:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum of {limit} requests per {period} seconds'
                }), 429
            
            # Add current request timestamp
            cache[client_ip].append(current_time)
            
            # Process request
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator