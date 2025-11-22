"""
Development Configuration
"""

from app.config.config import Config

class DevelopmentConfig(Config):
    """Development environment configuration"""
    
    DEBUG = True
    TESTING = False
    
    # More verbose logging in development
    LOG_LEVEL = 'DEBUG'
    
    # Allow file uploads from localhost
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000']
