"""
VastraVista - Centralized Logging Configuration
Suppresses unnecessary TensorFlow, MediaPipe, and ABSL warnings
"""

import logging
import os
import warnings
from pathlib import Path


def setup_production_logging():
    """Suppress all unnecessary warnings for production"""
    # Suppress TensorFlow warnings
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 0=all, 1=info, 2=warning, 3=error
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    
    # Suppress ABSL warnings (used by TensorFlow)
    import absl.logging
    absl.logging.set_verbosity(absl.logging.ERROR)
    absl.logging.set_stderrthreshold(absl.logging.ERROR)
    
    # Suppress Python warnings
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', category=UserWarning)
    
    # Suppress specific TensorFlow/MediaPipe logs
    logging.getLogger('tensorflow').setLevel(logging.ERROR)
    logging.getLogger('mediapipe').setLevel(logging.ERROR)
    logging.getLogger('absl').setLevel(logging.ERROR)


def configure_app_logging(app, log_level=logging.INFO):
    """
    Configure Flask application logging
    
    Args:
        app: Flask application instance
        log_level: Logging level (default: INFO)
    """
    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Configure formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
    )
    
    error_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(name)s [%(pathname)s:%(lineno)d]: %(message)s'
    )
    
    # File handler for general logs
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    
    # File handler for errors only
    error_handler = logging.FileHandler('logs/error.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(error_formatter)
    
    # Configure app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.setLevel(log_level)
    
    # Remove default Flask handler to avoid duplicates
    app.logger.handlers = [h for h in app.logger.handlers if not isinstance(h, logging.StreamHandler)]


def get_clean_logger(name: str, level=logging.INFO) -> logging.Logger:
    """
    Get a clean logger without duplicate handlers
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Remove existing handlers to prevent duplicates
    logger.handlers.clear()
    
    # Set level
    logger.setLevel(level)
    
    # Add console handler with clean format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s in %(name)s: %(message)s'))
    
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger
