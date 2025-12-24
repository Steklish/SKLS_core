"""
SKLS Generator Package

This module provides functionality for generating Pydantic models using LLMs.
"""

try:
    # Try relative import first (when used as part of the package)
    from ..skls_core.logging import get_skls_logger as get_logger, SKLSLoggerConfig as LoggerConfig
except (ImportError, ValueError):
    try:
        # Fallback to absolute import (when used as standalone package)
        from skls_core.logging import get_skls_logger as get_logger, SKLSLoggerConfig as LoggerConfig
    except ImportError:
        # Final fallback when used as part of larger project
        # This creates a simple logger when the centralized logging isn't available
        import logging

        class FallbackLoggerConfig:
            @classmethod
            def set_custom_logger(cls, logger_instance, name=None):
                pass

            @classmethod
            def get_custom_logger(cls, name=None):
                return None

            @classmethod
            def reset_custom_logger(cls, name=None):
                pass

            @classmethod
            def get_all_custom_loggers(cls):
                return {}

        def get_fallback_logger(name, use_custom=True, custom_logger_name=None):
            return logging.getLogger(name)

        get_logger = get_fallback_logger
        LoggerConfig = FallbackLoggerConfig

from .generator import Generator

__all__ = [
    'Generator',
    'get_logger',
    'LoggerConfig'
]