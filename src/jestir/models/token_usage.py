"""Token usage tracking models for OpenAI API calls."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token usage for a single API call."""

    timestamp: datetime = Field(default_factory=datetime.now)
    service: str = Field(
        ...,
        description="Service that made the call (context_generator, outline_generator, story_writer)",
    )
    operation: str = Field(
        ...,
        description="Operation performed (extract_entities, generate_outline, generate_story)",
    )
    model: str = Field(..., description="OpenAI model used")
    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(
        ...,
        description="Number of tokens in the completion",
    )
    total_tokens: int = Field(..., description="Total tokens used")
    cost_usd: float = Field(..., description="Cost in USD")
    input_text_length: int = Field(default=0, description="Length of input text")
    output_text_length: int = Field(default=0, description="Length of output text")


class TokenUsageSummary(BaseModel):
    """Summary of token usage across all operations."""

    total_tokens: int = Field(default=0, description="Total tokens used")
    total_cost_usd: float = Field(default=0.0, description="Total cost in USD")
    total_calls: int = Field(default=0, description="Total number of API calls")
    by_service: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Usage by service",
    )
    by_operation: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Usage by operation",
    )
    by_model: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Usage by model",
    )
    daily_usage: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Daily usage breakdown",
    )
    weekly_usage: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Weekly usage breakdown",
    )
    monthly_usage: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Monthly usage breakdown",
    )


class TokenPricing(BaseModel):
    """OpenAI model pricing configuration."""

    model: str = Field(..., description="Model name")
    input_price_per_1k: float = Field(
        ...,
        description="Price per 1K input tokens in USD",
    )
    output_price_per_1k: float = Field(
        ...,
        description="Price per 1K output tokens in USD",
    )
    description: str = Field(default="", description="Model description")


class TokenOptimizationSuggestion(BaseModel):
    """Token optimization suggestion."""

    type: str = Field(
        ...,
        description="Type of suggestion (cost_reduction, efficiency, model_choice)",
    )
    title: str = Field(..., description="Suggestion title")
    description: str = Field(..., description="Detailed description")
    potential_savings: float = Field(
        default=0.0,
        description="Potential cost savings in USD",
    )
    confidence: float = Field(default=0.0, description="Confidence level (0-1)")
    action_required: str = Field(default="", description="Action required to implement")


class TokenUsageReport(BaseModel):
    """Comprehensive token usage report."""

    period: str = Field(..., description="Report period (daily, weekly, monthly)")
    start_date: datetime = Field(..., description="Report start date")
    end_date: datetime = Field(..., description="Report end date")
    summary: TokenUsageSummary = Field(..., description="Usage summary")
    top_operations: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Top operations by token usage",
    )
    cost_trends: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Cost trends over time",
    )
    optimization_suggestions: list[TokenOptimizationSuggestion] = Field(
        default_factory=list,
        description="Optimization suggestions",
    )
    export_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw data for export",
    )
