"""
Configuration settings for the application.
"""
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration."""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Server settings
    PORT = int(os.getenv('PORT', 8000))
    
    # Database settings
    # These defaults match your Neon DB credentials.
    # Override them in .env if needed.
    DB_PARAMS = {
        "dbname": os.getenv("DB_NAME", "neondb"),
        "user": os.getenv("DB_USER", "neondb_owner"),
        "password": os.getenv("DB_PASSWORD", "npg_X02rGjyNYvSu"),
        "host": os.getenv("DB_HOST", "ep-crimson-glitter-a44yhjju-pooler.us-east-1.aws.neon.tech"),
        "port": os.getenv("DB_PORT", "5432"),
        "sslmode": os.getenv("DB_SSLMODE", "require")
    }
    
    # Gemini API settings
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Set this in .env (or environment) if using Gemini

    # Chatbot settings (modify to fit your use case)
    DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gemini-default-model')
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', 1000))
    TEMPERATURE = float(os.getenv('TEMPERATURE', 0.7))
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration."""
    
    TESTING = True
    # Use an in-memory or local test DB for running tests
    DB_PARAMS = {
        "dbname": "test_db",
        "user": "test_user",
        "password": "test_password",
        "host": "localhost",
        "port": "5432"
    }


class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False


# Dictionary to select the appropriate configuration based on environment
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """
    Get the appropriate configuration based on the FLASK_ENV environment variable.
    Falls back to 'default' if FLASK_ENV is not set or unrecognized.
    """
    env = os.getenv('FLASK_ENV', 'default')
    return config.get(env, config['default'])
