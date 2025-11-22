"""
VastraVista Application Factory
"""

from flask import Flask, redirect
from flask_cors import CORS
from pathlib import Path

# Import centralized logging configuration
from app.config.logging_config import setup_production_logging, configure_app_logging

# Suppress warnings at import time
setup_production_logging()

def create_app(config_name='development'):
    """
    Application factory pattern
    
    Args:
        config_name: Configuration to use (development/production)
    """
    app = Flask(__name__,
                static_folder='../static',
                template_folder='../templates')
    
    # Load configuration
    if config_name == 'production':
        from app.config.production import ProductionConfig
        app.config.from_object(ProductionConfig)
    else:
        from app.config.development import DevelopmentConfig
        app.config.from_object(DevelopmentConfig)
    
    # Enable CORS
    CORS(app)
    
    # Setup logging
    configure_app_logging(app)
    
    # Initialize database
    try:
        from app.models.database import db
        db.init_app(app)
        
        # Create tables
        with app.app_context():
            db.create_all()
            app.logger.info('✅ Database initialized')
    except ImportError:
        app.logger.warning('⚠️ Database models not available - running without database')
    
    # Initialize Flask-Login
    try:
        from flask_login import LoginManager
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'api.login'
        
        @login_manager.user_loader
        def load_user(user_id):
            from app.models.database import User
            return User.query.get(int(user_id))
    except ImportError:
        app.logger.warning('⚠️ Flask-Login not available')
    
    # Register blueprints
    from app.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Register extended features blueprint
    try:
        from app.api.extended_routes import extended_bp
        app.register_blueprint(extended_bp, url_prefix='/api/extended')
        app.logger.info('✅ Extended features enabled')
    except ImportError as e:
        app.logger.warning(f'⚠️ Extended features not available: {e}')
    
    # Register AI-powered routes (Monk Scale + OpenRouter DeepSeek R1)
    try:
        from app.api.ai_routes import ai_bp
        app.register_blueprint(ai_bp)
        app.logger.info('✅ AI-powered features enabled (Monk Scale + DeepSeek R1)')
    except ImportError as e:
        app.logger.warning(f'⚠️ AI features not available: {e}')
    
    # Add root route redirect
    @app.route('/')
    def root():
        """Redirect root to main page"""
        return redirect('/api/')
    
    # Create required directories
    for folder_config in ['UPLOAD_FOLDER', 'WARDROBE_FOLDER', 'REPORT_FOLDER']:
        folder = Path(app.config.get(folder_config, 'data'))
        folder.mkdir(parents=True, exist_ok=True)
    
    app.logger.info('✅ VastraVista application initialized with all features')
    
    return app
