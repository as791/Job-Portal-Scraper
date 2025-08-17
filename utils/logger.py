"""
Structured logging configuration for the Slack RAG Bot.
"""
import logging
import sys
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory

from configs.settings import settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def log_function_call(logger: structlog.stdlib.BoundLogger, func_name: str, **kwargs: Any) -> None:
    """Log function calls with parameters."""
    logger.info(
        "Function called",
        function=func_name,
        parameters=kwargs
    )


def log_error(logger: structlog.stdlib.BoundLogger, error: Exception, context: Dict[str, Any] = None) -> None:
    """Log errors with context."""
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {}
    ) 