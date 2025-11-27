"""
AR API Request Logger
Logs all requests and validation errors
"""

import logging
from typing import List, Dict
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class ARRequestLogger:
    """Log AR API requests and errors"""
    
    def __init__(self, max_logs: int = 100):
        """Initialize logger"""
        self.max_logs = max_logs
        self.request_logs = deque(maxlen=max_logs)
        self.error_logs = deque(maxlen=max_logs)
    
    def log_request(self, endpoint: str, method: str, status: str, details: Dict = None):
        """Log API request"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'status': status,
            'details': details or {}
        }
        self.request_logs.append(log_entry)
        logger.info(f"AR Request: {method} {endpoint} - {status}")
    
    def log_error(self, endpoint: str, error_type: str, error_message: str, details: Dict = None):
        """Log validation error"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'endpoint': endpoint,
            'error_type': error_type,
            'error_message': error_message,
            'details': details or {}
        }
        self.error_logs.append(log_entry)
        logger.error(f"AR Error: {endpoint} - {error_type}: {error_message}")
    
    def get_recent_errors(self, limit: int = 20) -> List[Dict]:
        """Get recent error logs"""
        return list(self.error_logs)[-limit:]
    
    def get_recent_requests(self, limit: int = 20) -> List[Dict]:
        """Get recent request logs"""
        return list(self.request_logs)[-limit:]


# Global logger instance
ar_logger = ARRequestLogger()

