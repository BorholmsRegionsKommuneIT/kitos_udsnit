"""
Logging configuration for the Kitos data extraction script.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_level=logging.INFO):
    """
    Configure logging with rotating file handler and console output.

    Args:
        log_level: The logging level (default: logging.INFO)

    Returns:
        logger: Configured logger instance
    """
    # Configure logging with rotating file handler
    log_file = Path(__file__).parent / "log.log"
    log_file.parent.mkdir(exist_ok=True)  # Ensure directory exists

    # Remove any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Create rotating file handler (max 10MB, keep 5 backup files)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )

    # Create console handler for immediate feedback
    console_handler = (
        logging.StreamHandler()
    )  # Create formatter - use module name instead of function name for better readability
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s:%(lineno)d - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Set formatter for both handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Configure root logger
    logging.basicConfig(level=log_level, handlers=[file_handler, console_handler])

    # Return the root logger so all modules use the same configuration
    return logging.getLogger()
