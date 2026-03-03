import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(app):
    """Setup comprehensive logging for the application."""
    
    # Create logs directory if it doesn't exist
    log_dir = "/var/log/nophish-panel"
    os.makedirs(log_dir, exist_ok=True)
    
    # Formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handlers
    access_log_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'access.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    access_log_handler.setFormatter(detailed_formatter)
    
    error_log_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_log_handler.setFormatter(detailed_formatter)
    
    # Application logger
    app_logger = logging.getLogger('nophish')
    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(error_log_handler)
    
    # Security logger
    security_logger = logging.getLogger('nophish.security')
    security_logger.setLevel(logging.INFO)
    security_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'security.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    security_handler.setFormatter(detailed_formatter)
    security_logger.addHandler(security_handler)
    
    # Campaign logger
    campaign_logger = logging.getLogger('nophish.campaigns')
    campaign_logger.setLevel(logging.INFO)
    campaign_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'campaigns.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    campaign_handler.setFormatter(detailed_formatter)
    campaign_logger.addHandler(campaign_handler)
    
    return {
        'app': app_logger,
        'security': security_logger,
        'campaign': campaign_logger
    }

def log_security_event(logger, event_type, user=None, details=None):
    """Log security events."""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'user': user,
        'details': details or {}
    }
    logger.info(f"SECURITY_EVENT: {log_entry}")

def log_campaign_action(logger, campaign_id, action, user=None, details=None):
    """Log campaign actions."""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'campaign_id': campaign_id,
        'action': action,
        'user': user,
        'details': details or {}
    }
    logger.info(f"CAMPAIGN_ACTION: {log_entry}")