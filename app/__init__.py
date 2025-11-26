"""
Application Factory (Auth-only)
Sets up Flask app, loads environment, configures logging, DB, and auth.
"""

from flask import Flask, redirect
from flask_cors import CORS
from pathlib import Path
from dotenv import load_dotenv

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
    try:
        load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')
    except Exception:
        pass
    
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
    
    # Create required directories early
    try:
        from pathlib import Path as _P
        for folder_config in ['DATA_DIR', 'UPLOAD_FOLDER', 'WARDROBE_FOLDER', 'REPORT_FOLDER']:
            folder = _P(app.config.get(folder_config, 'data'))
            folder.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # Initialize database
    try:
        from app.models.database import db
        db.init_app(app)
        
        # Create tables
        with app.app_context():
            db.create_all()
            app.logger.info('✅ Database initialized')
            try:
                from sqlalchemy import inspect, text
                inspector = inspect(db.engine)
                cols = [c['name'] for c in inspector.get_columns('users')]
                with db.engine.connect() as conn:
                    if 'is_verified' not in cols:
                        conn.execute(text('ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0'))
                app.logger.info('✅ Users table schema ensured')
            except Exception as e:
                app.logger.warning(f'⚠️ Could not ensure users schema: {e}')
    except ImportError:
        app.logger.warning('⚠️ Database models not available - running without database')
    
    try:
        from flask_login import LoginManager
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        
        @login_manager.user_loader
        def load_user(user_id):
            from app.models.database import User
            return User.query.get(int(user_id))
    except ImportError:
        app.logger.warning('⚠️ Flask-Login not available')
    
    from app.api.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    # Add root route redirect
    @app.route('/')
    def root():
        from flask import url_for
        return redirect(url_for('auth.login'))
    
    app.logger.info('✅ Auth-only application initialized')
    
    return app
