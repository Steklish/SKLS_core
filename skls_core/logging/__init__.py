"""
Centralized logging module for SKLS.

This module provides a unified logging configuration that can be used across
all SKLS modules. It supports custom loggers and maintains backward compatibility.
"""

import logging
import os
import sys
from typing import Optional, Union

# Global logger configuration
class SKLSLoggerConfig:
    _configured = False
    _custom_logger = None
    _custom_loggers = {}  # Store custom loggers by name

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
    def set_custom_logger(cls, logger_instance: logging.Logger, name: Optional[str] = None):
        """
        Allow setting a custom logger instance to be used globally or by name.

        Args:
            logger_instance: Custom logger instance to use
            name: Optional name to register the logger under. If None, sets the global custom logger.
        """
        if name is None:
            cls._custom_logger = logger_instance
        else:
            cls._custom_loggers[name] = logger_instance

    @classmethod
    def get_custom_logger(cls, name: Optional[str] = None) -> Optional[logging.Logger]:
        """
        Get a registered custom logger by name or the global custom logger.

        Args:
            name: Optional name of the custom logger to retrieve. If None, returns the global custom logger.

        Returns:
            Custom logger instance if found, None otherwise.
        """
        if name is None:
            return cls._custom_logger
        return cls._custom_loggers.get(name)

    @classmethod
    def reset_custom_logger(cls, name: Optional[str] = None):
        """
        Reset/remove a custom logger by name or the global custom logger.

        Args:
            name: Optional name of the custom logger to reset. If None, resets the global custom logger.
        """
        if name is None:
            cls._custom_logger = None
        else:
            cls._custom_loggers.pop(name, None)

    @classmethod
    def get_all_custom_loggers(cls) -> dict:
        """
        Get all registered custom loggers.

        Returns:
            Dictionary of all registered custom loggers by name.
        """
        return cls._custom_loggers.copy()

# Convenience function for getting a named logger
def get_skls_logger(name: str, use_custom: bool = True, custom_logger_name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name using the centralized SKLS logging configuration.

    Args:
        name: Name of the logger (typically __name__ from the calling module)
        use_custom: Whether to use custom logger if set
        custom_logger_name: Optional specific custom logger name to use

    Returns:
        Configured logger instance
    """
    # If custom logger name is specified, try to get that specific custom logger
    if custom_logger_name and use_custom:
        custom_logger = SKLSLoggerConfig.get_custom_logger(custom_logger_name)
        if custom_logger is not None:
            return custom_logger

    # If using custom logger globally and no specific name provided
    if use_custom and SKLSLoggerConfig._custom_logger is not None:
        return SKLSLoggerConfig._custom_logger

    return logging.getLogger(name)

# Set up default logging configuration
os.makedirs('log', exist_ok=True)
SKLSLoggerConfig.setup_logging(log_file='./log/application.log')