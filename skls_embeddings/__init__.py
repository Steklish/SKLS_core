"""
SKLS Embeddings Package

This module provides functionality for creating and managing text embeddings
using various backend services and storing them in vector databases.
"""

from .embedding_client import EmbeddingClient
from .chroma_client import ChromaClient
from .logger_config import get_logger, LoggerConfig

__all__ = [
    'EmbeddingClient',
    'ChromaClient', 
    'get_logger',
    'LoggerConfig'
]