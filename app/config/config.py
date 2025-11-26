"""
Base Configuration
"""

import os
from pathlib import Path

class Config:
    """Base configuration"""
    
    # Application
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    # Allow overriding upload folder via environment variable (can be absolute or relative)
    env_upload = os.environ.get('UPLOAD_FOLDER', '')
    if env_upload:
        env_path = Path(env_upload)
        # If relative path provided, resolve relative to project root
        UPLOAD_FOLDER = (BASE_DIR / env_path).resolve() if not env_path.is_absolute() else env_path
    else:
        UPLOAD_FOLDER = BASE_DIR / 'static' / 'uploads'
    MODEL_DIR = BASE_DIR / 'ml' / 'saved_models'
    DATA_DIR = BASE_DIR / 'data'
    WARDROBE_FOLDER = BASE_DIR / 'data' / 'wardrobe'
    REPORT_FOLDER = BASE_DIR / 'data' / 'reports'
    
    # File upload
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    
    # CORS
    CORS_HEADERS = 'Content-Type'
    
    # Logging
    LOG_LEVEL = 'INFO'
    
    # Model settings
    FACE_DETECTION_CONFIDENCE = 0.5
    MIN_FACE_SIZE = 50
    
    # Color analysis
    N_COLORS = 15  # Number of colors to recommend
    
    # Cache
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Database
    _env_db = os.environ.get('DATABASE_URL', '')
    if _env_db.startswith('sqlite:///'):
        _p = _env_db.replace('sqlite:///', '')
        if os.path.isabs(_p):
            SQLALCHEMY_DATABASE_URI = _env_db
        else:
            SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str((BASE_DIR / _p).resolve())
    else:
        SQLALCHEMY_DATABASE_URI = _env_db or 'sqlite:///' + str(BASE_DIR / 'data' / 'vastravista.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    
    # Affiliate API Configuration
    AMAZON_AFFILIATE_ID = os.environ.get('AMAZON_AFFILIATE_ID', '')
    AMAZON_ACCESS_KEY = os.environ.get('AMAZON_ACCESS_KEY', '')
    AMAZON_SECRET_KEY = os.environ.get('AMAZON_SECRET_KEY', '')
    
    FLIPKART_AFFILIATE_ID = os.environ.get('FLIPKART_AFFILIATE_ID', '')
    FLIPKART_AFFILIATE_TOKEN = os.environ.get('FLIPKART_AFFILIATE_TOKEN', '')
    
    CUELINKS_API_KEY = os.environ.get('CUELINKS_API_KEY', '')
    
    # Feature flags
    ENABLE_WARDROBE = False
    ENABLE_AR_FEATURES = True
    ENABLE_AFFILIATE_RECOMMENDATIONS = False
    ENABLE_PDF_REPORTS = False
    ENABLE_STYLE_QUIZ = True
