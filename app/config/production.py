"""
Production Configuration
"""

from app.config.config import Config
import os

class ProductionConfig(Config):
    """Production environment configuration"""
    
    DEBUG = False
    TESTING = False
    
    # Use environment variable for secret key
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # CORS - configure for your domain
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',')
    
    # Security headers
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
