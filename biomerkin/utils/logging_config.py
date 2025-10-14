"""
Logging configuration for the Biomerkin multi-agent system.

This module provides centralized logging configuration with support for
different log levels, formatters, and output destinations.
"""

import logging
import logging.config
import sys
from typing import Dict, Any, Optional
from pathlib import Path

from .config import get_config


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    enable_console: bool = True,
    enable_structured: bool = False
) -> None:
    """
    Set up logging configuration for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        enable_console: Whether to enable console logging
        enable_structured: Whether to use structured logging format
    """
    config = get_config()
    
    # Determine log level
    if not log_level:
        log_level = config.get('log_level', 'INFO')
    
    # Create logging configuration
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'structured': {
                'format': '%(asctime)s | %(levelname)8s | %(name)s | %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {},
        'loggers': {
            'biomerkin': {
                'level': log_level,
                'handlers': [],
                'propagate': False
            },
            'boto3': {
                'level': 'WARNING',
                'handlers': [],
                'propagate': False
            },
            'botocore': {
                'level': 'WARNING',
                'handlers': [],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': []
        }
    }
    
    # Add console handler if enabled
    if enable_console:
        console_handler = {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'structured' if enable_structured else 'standard',
            'stream': 'ext://sys.stdout'
        }
        logging_config['handlers']['console'] = console_handler
        logging_config['loggers']['biomerkin']['handlers'].append('console')
        logging_config['root']['handlers'].append('console')
    
    # Add file handler if log file is specified
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'detailed',
            'filename': str(log_path),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }
        logging_config['handlers']['file'] = file_handler
        logging_config['loggers']['biomerkin']['handlers'].append('file')
        logging_config['root']['handlers'].append('file')
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Log configuration info
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level}")
    if log_file:
        logger.info(f"Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def configure_aws_logging(level: str = 'WARNING') -> None:
    """
    Configure logging for AWS SDK libraries to reduce noise.
    
    Args:
        level: Log level for AWS libraries
    """
    aws_loggers = [
        'boto3',
        'botocore',
        'urllib3',
        's3transfer'
    ]
    
    for logger_name in aws_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level.upper()))


def log_workflow_event(
    logger: logging.Logger,
    workflow_id: str,
    event_type: str,
    message: str,
    **kwargs
) -> None:
    """
    Log a workflow-related event with structured information.
    
    Args:
        logger: Logger instance to use
        workflow_id: Unique workflow identifier
        event_type: Type of event (start, progress, error, complete, etc.)
        message: Human-readable message
        **kwargs: Additional context information
    """
    context = {
        'workflow_id': workflow_id,
        'event_type': event_type,
        **kwargs
    }
    
    # Format context as key=value pairs
    context_str = ' '.join(f"{k}={v}" for k, v in context.items())
    
    full_message = f"{message} | {context_str}"
    
    # Choose log level based on event type
    if event_type in ['error', 'failed']:
        logger.error(full_message)
    elif event_type in ['warning', 'retry']:
        logger.warning(full_message)
    elif event_type in ['start', 'complete']:
        logger.info(full_message)
    else:
        logger.debug(full_message)


def log_agent_activity(
    logger: logging.Logger,
    agent_name: str,
    workflow_id: str,
    activity: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log agent-specific activity with structured information.
    
    Args:
        logger: Logger instance to use
        agent_name: Name of the agent
        workflow_id: Unique workflow identifier
        activity: Description of the activity
        details: Optional additional details
    """
    context = {
        'agent': agent_name,
        'workflow_id': workflow_id
    }
    
    if details:
        context.update(details)
    
    context_str = ' '.join(f"{k}={v}" for k, v in context.items())
    full_message = f"{activity} | {context_str}"
    
    logger.info(full_message)


# Default logging setup for when module is imported
def _setup_default_logging():
    """Set up default logging configuration if none exists."""
    if not logging.getLogger().handlers:
        setup_logging(
            log_level='INFO',
            enable_console=True,
            enable_structured=False
        )


# Initialize default logging when module is imported
_setup_default_logging()