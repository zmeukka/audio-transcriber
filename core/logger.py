"""
Logging configuration for Audio Transcriber API
Provides structured logging with English-only messages
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output"""

    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record):
        """Format log record with colors"""
        # Add color to levelname
        levelname = record.levelname
        if levelname in self.COLORS:
            colored_levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            record.levelname = colored_levelname

        # Format the message
        formatted = super().format(record)

        # Reset levelname for future use
        record.levelname = levelname

        return formatted


def setup_logger(
    name: Optional[str] = None,
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True
) -> logging.Logger:
    """
    Setup logger with both file and console handlers

    Args:
        name: Logger name (default: root logger)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        console_output: Whether to output to console

    Returns:
        Configured logger instance
    """

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatters
    file_formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_formatter = ColoredFormatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%H:%M:%S'
    )

    # File handler (with rotation)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance with module name

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def setup_uvicorn_logger() -> None:
    """Setup uvicorn logger to use our format"""
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")

    # Use our formatter for uvicorn logs
    console_formatter = ColoredFormatter(
        fmt='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%H:%M:%S'
    )

    for handler in uvicorn_logger.handlers:
        handler.setFormatter(console_formatter)

    for handler in uvicorn_access_logger.handlers:
        handler.setFormatter(console_formatter)


def log_function_call(func):
    """
    Decorator to log function calls with parameters and execution time
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = datetime.now()

        # Log function entry
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")

        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Function {func.__name__} completed in {execution_time:.3f}s")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Function {func.__name__} failed after {execution_time:.3f}s: {e}")
            raise

    return wrapper


def log_api_request(request_info: dict) -> None:
    """
    Log API request information

    Args:
        request_info: Dictionary with request details
    """
    logger = get_logger("api.request")
    logger.info(f"API Request: {request_info}")


def log_api_response(response_info: dict) -> None:
    """
    Log API response information

    Args:
        response_info: Dictionary with response details
    """
    logger = get_logger("api.response")
    logger.info(f"API Response: {response_info}")


# Initialize default logger
def init_default_logger():
    """Initialize the default application logger"""
    setup_logger(
        name="audio_transcriber",
        level="INFO",
        log_file=None,  # No log file - use stdout/stderr for Docker
        console_output=True
    )

    # Setup uvicorn logging
    setup_uvicorn_logger()


# Auto-initialize when module is imported
if not logging.getLogger().handlers:
    init_default_logger()
