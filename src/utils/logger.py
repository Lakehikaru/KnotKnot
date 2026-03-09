"""Structured logging setup."""

import structlog
import logging
from pathlib import Path
from src.utils.config import settings


def setup_logging():
    """Configure structured logging."""

    # Create logs directory
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.log_level.upper()),
        handlers=[
            logging.FileHandler(settings.log_file),
            logging.StreamHandler()
        ]
    )

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
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """Get a logger instance."""
    return structlog.get_logger(name)
