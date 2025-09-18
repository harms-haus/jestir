"""Centralized LightRAG configuration utility."""

import os

from ..models.api_config import LightRAGAPIConfig


def load_lightrag_config() -> LightRAGAPIConfig:
    """
    Load LightRAG configuration from environment variables.

    This centralizes all LightRAG configuration loading to ensure consistency
    across the application and makes it easier to maintain.

    Returns:
        LightRAGAPIConfig: Configured LightRAG API settings
    """
    return LightRAGAPIConfig(
        base_url=os.getenv("LIGHTRAG_BASE_URL", "http://localhost:9621"),
        api_key=os.getenv("LIGHTRAG_API_KEY"),
        timeout=int(os.getenv("LIGHTRAG_TIMEOUT", "30")),
        mock_mode=os.getenv("LIGHTRAG_MOCK_MODE", "false").lower() == "true",
    )


def get_lightrag_base_url() -> str:
    """Get the LightRAG base URL from environment or default."""
    return os.getenv("LIGHTRAG_BASE_URL", "http://localhost:9621")


def get_lightrag_api_key() -> str | None:
    """Get the LightRAG API key from environment."""
    return os.getenv("LIGHTRAG_API_KEY")


def get_lightrag_timeout() -> int:
    """Get the LightRAG timeout from environment or default."""
    return int(os.getenv("LIGHTRAG_TIMEOUT", "30"))


def is_lightrag_mock_mode() -> bool:
    """Check if LightRAG is in mock mode."""
    return os.getenv("LIGHTRAG_MOCK_MODE", "false").lower() == "true"
