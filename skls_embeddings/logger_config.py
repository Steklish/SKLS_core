import logging
import os
import sys
from typing import Optional

# Global logger configuration
class LoggerConfig:
    _configured = False
    _custom_logger = None

    @classmethod
    def setup_logging(cls, level: int = logging.INFO,
                     format_string: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     log_file: Optional[str] = None):
        """
        Set up root logging configuration once for the entire application.

        Args:
            level: Logging level (default: logging.INFO)
            format_string: Format for log messages
            log_file: Optional file path to write logs to
        """
        if cls._configured:
            # If already configured, just return the root logger
            return logging.getLogger()

        # Create formatter
        formatter = logging.Formatter(format_string)

        # Create handler for console output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        # Create root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Clear any existing handlers to avoid duplicates
        root_logger.handlers.clear()

        # Add console handler
        root_logger.addHandler(console_handler)

        # Add file handler if specified
        if log_file:
            # Create log directory if it doesn't exist
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        cls._configured = True
        return root_logger

    @classmethod
    def set_custom_logger(cls, logger_instance: logging.Logger):
        """
        Allow setting a custom logger instance to be used globally.

        Args:
            logger_instance: Custom logger instance to use
        """
        cls._custom_logger = logger_instance

# Convenience function for getting a named logger
def get_logger(name: str, use_custom: bool = True) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Name of the logger (typically __name__ from the calling module)
        use_custom: Whether to use custom logger if set

    Returns:
        Configured logger instance
    """
    if use_custom and LoggerConfig._custom_logger is not None:
        return LoggerConfig._custom_logger
    return logging.getLogger(name)

# Set up default logging configuration
os.makedirs('log', exist_ok=True)
LoggerConfig.setup_logging(log_file='./log/application.log')