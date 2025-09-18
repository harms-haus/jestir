"""OpenAI API configuration models."""

from pydantic import BaseModel, Field


class ExtractionAPIConfig(BaseModel):
    """Configuration for OpenAI API used for information extraction."""

    api_key: str = Field(..., description="OpenAI API key for extraction endpoint")
    base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for extraction API",
    )
    model: str = Field(default="gpt-4o-mini", description="Model to use for extraction")
    max_tokens: int = Field(
        default=1000,
        description="Maximum tokens for extraction requests",
    )
    temperature: float = Field(
        default=0.1,
        description="Temperature setting for extraction (lower for consistency)",
    )


class CreativeAPIConfig(BaseModel):
    """Configuration for OpenAI API used for creative generation."""

    api_key: str = Field(..., description="OpenAI API key for creative endpoint")
    base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for creative API",
    )
    model: str = Field(
        default="gpt-4o",
        description="Model to use for creative generation",
    )
    max_tokens: int = Field(
        default=4000,
        description="Maximum tokens for creative requests",
    )
    temperature: float = Field(
        default=0.8,
        description="Temperature setting for creative generation (higher for creativity)",
    )


class LightRAGAPIConfig(BaseModel):
    """Configuration for LightRAG API used for entity retrieval."""

    base_url: str = Field(
        default="http://localhost:9621",
        description="Base URL for LightRAG API",
    )
    api_key: str | None = Field(
        default=None,
        description="API key for LightRAG API (optional)",
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    mock_mode: bool = Field(
        default=False,
        description="Enable mock mode for testing without API",
    )
