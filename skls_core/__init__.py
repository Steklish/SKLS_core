"""
SKLS Core Package

This is the main package for SKLS (Semantic Knowledge & Language Suite) modules.
"""

# Import the centralized logging functionality to make it available at package level
from .logging import get_skls_logger, SKLSLoggerConfig

__all__ = [
    'get_skls_logger',
    'SKLSLoggerConfig'
]