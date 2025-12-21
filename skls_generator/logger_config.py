import logging
import os
import sys
from typing import Optional

# Global logger configuration
class LoggerConfig:
    _configured = False
    
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
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        cls._configured = True
        return root_logger

# Convenience function for getting a named logger
def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger (typically __name__ from the calling module)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

# Set up default logging configuration
os.mkdir('log') if not os.path.exists('log') else None
LoggerConfig.setup_logging(log_file='./log/application.log')