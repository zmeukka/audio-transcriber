"""
Logger module for Audio Transcriber
Handles console logging operations with configurable levels
"""

import logging


class Logger:
    """Handles logging operations for the application"""

    def __init__(self, output_dir: str, verbose: bool = False, debug: bool = False):
        """
        Initialize logger with console handler

        Args:
            output_dir: Directory (unused, kept for compatibility)
            verbose: Enable verbose console output (unused, kept for compatibility)
            debug: Enable debug mode (show warnings if True)
        """

        # Create logger
        self.logger = logging.getLogger('AudioTranscriber')
        self.logger.setLevel(logging.INFO)

        # Clear existing handlers
        self.logger.handlers.clear()

        # Create formatters
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )

        # Create console handler
        console_handler = logging.StreamHandler()
        # Если debug True, показываем WARNING, иначе только ERROR
        if debug:
            console_level = logging.WARNING
        else:
            console_level = logging.ERROR
        console_handler.setLevel(console_level)
        console_handler.setFormatter(console_formatter)

        # Add only console handler to logger
        self.logger.addHandler(console_handler)

    def info(self, message: str, module: str = "Main") -> None:
        """Log info message"""
        self.logger.info(f"[{module}] {message}")

    def warning(self, message: str, module: str = "Main") -> None:
        """Log warning message"""
        self.logger.warning(f"[{module}] {message}")

    def error(self, message: str, module: str = "Main") -> None:
        """Log error message"""
        self.logger.error(f"[{module}] {message}")

    def debug(self, message: str, module: str = "Main") -> None:
        """Log debug message"""
        self.logger.debug(f"[{module}] {message}")
