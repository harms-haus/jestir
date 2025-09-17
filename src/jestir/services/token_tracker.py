"""Token usage tracking service for OpenAI API calls."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import ClassVar, TypedDict

import yaml

from ..models.token_usage import (
    TokenOptimizationSuggestion,
    TokenPricing,
    TokenUsage,
    TokenUsageReport,
    TokenUsageSummary,
)

logger = logging.getLogger(__name__)


class OperationData(TypedDict):
    """Data structure for operation statistics."""

    total_tokens: int
    total_cost: float
    total_calls: int


class ServiceData(TypedDict):
    """Data structure for service statistics."""

    total_tokens: int
    total_cost: float
    total_calls: int
    operations: dict[str, OperationData]


class OperationServiceData(TypedDict):
    """Data structure for operation service statistics."""

    total_tokens: int
    total_cost: float
    total_calls: int


class OperationDataWithServices(TypedDict):
    """Data structure for operation statistics with services."""

    total_tokens: int
    total_cost: float
    total_calls: int
    services: dict[str, OperationServiceData]


class ModelData(TypedDict):
    """Data structure for model statistics."""

    total_tokens: int
    total_cost: float
    total_calls: int
    avg_tokens_per_call: float


class DailyData(TypedDict):
    """Data structure for daily statistics."""

    total_tokens: int
    total_cost: float
    total_calls: int


class TokenTracker:
    """Tracks token usage across all OpenAI API calls."""

    # OpenAI pricing as of December 2024 (per 1K tokens)
    DEFAULT_PRICING: ClassVar[dict[str, TokenPricing]] = {
        "gpt-4o": TokenPricing(
            model="gpt-4o",
            input_price_per_1k=0.005,
            output_price_per_1k=0.015,
            description="GPT-4 Omni - Most capable model",
        ),
        "gpt-4o-mini": TokenPricing(
            model="gpt-4o-mini",
            input_price_per_1k=0.00015,
            output_price_per_1k=0.0006,
            description="GPT-4 Omni Mini - Fast and efficient",
        ),
        "gpt-4": TokenPricing(
            model="gpt-4",
            input_price_per_1k=0.03,
            output_price_per_1k=0.06,
            description="GPT-4 - High capability model",
        ),
        "gpt-3.5-turbo": TokenPricing(
            model="gpt-3.5-turbo",
            input_price_per_1k=0.0015,
            output_price_per_1k=0.002,
            description="GPT-3.5 Turbo - Fast and cost-effective",
        ),
    }

    def __init__(self, pricing_config: dict[str, TokenPricing] | None = None):
        """Initialize the token tracker with pricing configuration."""
        self.pricing = pricing_config or self.DEFAULT_PRICING
        self.usage_history: list[TokenUsage] = []

    def track_usage(
        self,
        service: str,
        operation: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        input_text: str = "",
        output_text: str = "",
    ) -> TokenUsage:
        """Track token usage for a single API call."""
        total_tokens = prompt_tokens + completion_tokens

        # Calculate cost based on model pricing
        pricing = self.pricing.get(model, self.pricing["gpt-4o-mini"])
        input_cost = (prompt_tokens / 1000) * pricing.input_price_per_1k
        output_cost = (completion_tokens / 1000) * pricing.output_price_per_1k
        total_cost = input_cost + output_cost

        usage = TokenUsage(
            service=service,
            operation=operation,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=total_cost,
            input_text_length=len(input_text),
            output_text_length=len(output_text),
        )

        self.usage_history.append(usage)
        logger.debug(
            f"Tracked token usage: {total_tokens} tokens, ${total_cost:.4f} for {service}.{operation}",
        )

        return usage

    def get_usage_summary(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> TokenUsageSummary:
        """Get usage summary for a date range."""
        if not self.usage_history:
            return TokenUsageSummary()

        # Filter by date range if provided
        filtered_usage = self.usage_history
        if start_date:
            filtered_usage = [u for u in filtered_usage if u.timestamp >= start_date]
        if end_date:
            filtered_usage = [u for u in filtered_usage if u.timestamp <= end_date]

        if not filtered_usage:
            return TokenUsageSummary()

        # Calculate totals
        total_tokens = sum(u.total_tokens for u in filtered_usage)
        total_cost = sum(u.cost_usd for u in filtered_usage)
        total_calls = len(filtered_usage)

        # Group by service
        by_service: dict[str, ServiceData] = {}
        for usage in filtered_usage:
            if usage.service not in by_service:
                by_service[usage.service] = {
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_calls": 0,
                    "operations": {},
                }
            by_service[usage.service]["total_tokens"] += usage.total_tokens
            by_service[usage.service]["total_cost"] += usage.cost_usd
            by_service[usage.service]["total_calls"] += 1

            if usage.operation not in by_service[usage.service]["operations"]:
                by_service[usage.service]["operations"][usage.operation] = {
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_calls": 0,
                }
            by_service[usage.service]["operations"][usage.operation][
                "total_tokens"
            ] += usage.total_tokens
            by_service[usage.service]["operations"][usage.operation]["total_cost"] += (
                usage.cost_usd
            )
            by_service[usage.service]["operations"][usage.operation]["total_calls"] += 1

        # Group by operation
        by_operation: dict[str, OperationDataWithServices] = {}
        for usage in filtered_usage:
            if usage.operation not in by_operation:
                by_operation[usage.operation] = {
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_calls": 0,
                    "services": {},
                }
            by_operation[usage.operation]["total_tokens"] += usage.total_tokens
            by_operation[usage.operation]["total_cost"] += usage.cost_usd
            by_operation[usage.operation]["total_calls"] += 1

            if usage.service not in by_operation[usage.operation]["services"]:
                by_operation[usage.operation]["services"][usage.service] = {
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_calls": 0,
                }
            by_operation[usage.operation]["services"][usage.service][
                "total_tokens"
            ] += usage.total_tokens
            by_operation[usage.operation]["services"][usage.service]["total_cost"] += (
                usage.cost_usd
            )
            by_operation[usage.operation]["services"][usage.service]["total_calls"] += 1

        # Group by model
        by_model: dict[str, ModelData] = {}
        for usage in filtered_usage:
            if usage.model not in by_model:
                by_model[usage.model] = {
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_calls": 0,
                    "avg_tokens_per_call": 0.0,
                }
            by_model[usage.model]["total_tokens"] += usage.total_tokens
            by_model[usage.model]["total_cost"] += usage.cost_usd
            by_model[usage.model]["total_calls"] += 1

        # Calculate averages
        for model_data in by_model.values():
            if model_data["total_calls"] > 0:
                model_data["avg_tokens_per_call"] = (
                    model_data["total_tokens"] / model_data["total_calls"]
                )

        # Group by day
        daily_usage: dict[str, DailyData] = {}
        for usage in filtered_usage:
            day_key = usage.timestamp.strftime("%Y-%m-%d")
            if day_key not in daily_usage:
                daily_usage[day_key] = {
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_calls": 0,
                }
            daily_usage[day_key]["total_tokens"] += usage.total_tokens
            daily_usage[day_key]["total_cost"] += usage.cost_usd
            daily_usage[day_key]["total_calls"] += 1

        # Group by week
        weekly_usage: dict[str, DailyData] = {}
        for usage in filtered_usage:
            # Get Monday of the week
            monday = usage.timestamp - timedelta(days=usage.timestamp.weekday())
            week_key = monday.strftime("%Y-W%U")
            if week_key not in weekly_usage:
                weekly_usage[week_key] = {
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_calls": 0,
                }
            weekly_usage[week_key]["total_tokens"] += usage.total_tokens
            weekly_usage[week_key]["total_cost"] += usage.cost_usd
            weekly_usage[week_key]["total_calls"] += 1

        # Group by month
        monthly_usage: dict[str, DailyData] = {}
        for usage in filtered_usage:
            month_key = usage.timestamp.strftime("%Y-%m")
            if month_key not in monthly_usage:
                monthly_usage[month_key] = {
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_calls": 0,
                }
            monthly_usage[month_key]["total_tokens"] += usage.total_tokens
            monthly_usage[month_key]["total_cost"] += usage.cost_usd
            monthly_usage[month_key]["total_calls"] += 1

        return TokenUsageSummary(
            total_tokens=total_tokens,
            total_cost_usd=total_cost,
            total_calls=total_calls,
            by_service=by_service,  # type: ignore[arg-type]
            by_operation=by_operation,  # type: ignore[arg-type]
            by_model=by_model,  # type: ignore[arg-type]
            daily_usage=daily_usage,  # type: ignore[arg-type]
            weekly_usage=weekly_usage,  # type: ignore[arg-type]
            monthly_usage=monthly_usage,  # type: ignore[arg-type]
        )

    def generate_optimization_suggestions(
        self,
        summary: TokenUsageSummary,
    ) -> list[TokenOptimizationSuggestion]:
        """Generate optimization suggestions based on usage patterns."""
        suggestions = []

        # Check for high-cost models
        for model, data in summary.by_model.items():
            if data["total_cost"] > 1.0:  # More than $1
                if model == "gpt-4o" and data["total_cost"] > 5.0:
                    suggestions.append(
                        TokenOptimizationSuggestion(
                            type="model_choice",
                            title=f"Consider using GPT-4o-mini for {model} operations",
                            description=f"You've spent ${data['total_cost']:.2f} on {model}. GPT-4o-mini offers similar quality at much lower cost.",
                            potential_savings=data["total_cost"]
                            * 0.7,  # Estimate 70% savings
                            confidence=0.8,
                            action_required="Switch to gpt-4o-mini model in your API configuration",
                        ),
                    )

        # Check for inefficient operations
        for operation, data in summary.by_operation.items():
            if data["total_calls"] > 10:  # Only for frequently used operations
                avg_tokens = data["total_tokens"] / data["total_calls"]
                if avg_tokens > 2000:  # High token usage per call
                    suggestions.append(
                        TokenOptimizationSuggestion(
                            type="efficiency",
                            title=f"Optimize {operation} prompts",
                            description=f"{operation} uses {avg_tokens:.0f} tokens per call on average. Consider shortening prompts or using more specific instructions.",
                            potential_savings=data["total_cost"]
                            * 0.2,  # Estimate 20% savings
                            confidence=0.6,
                            action_required="Review and optimize prompt templates for this operation",
                        ),
                    )

        # Check for cost trends
        if len(summary.daily_usage) > 7:  # More than a week of data
            recent_days = sorted(summary.daily_usage.keys())[-7:]
            recent_costs = [
                summary.daily_usage[day]["total_cost"] for day in recent_days
            ]
            avg_daily_cost = sum(recent_costs) / len(recent_costs)

            if avg_daily_cost > 2.0:  # More than $2 per day
                suggestions.append(
                    TokenOptimizationSuggestion(
                        type="cost_reduction",
                        title="High daily usage detected",
                        description=f"Average daily cost is ${avg_daily_cost:.2f}. Consider implementing usage limits or batch processing.",
                        potential_savings=avg_daily_cost * 0.3,  # Estimate 30% savings
                        confidence=0.7,
                        action_required="Set up usage monitoring and consider batching operations",
                    ),
                )

        return suggestions

    def generate_report(
        self,
        period: str = "monthly",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> TokenUsageReport:
        """Generate a comprehensive usage report."""
        if not start_date:
            if period == "daily":
                start_date = datetime.now().replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )
            elif period == "weekly":
                # Start of current week (Monday)
                today = datetime.now()
                start_date = today - timedelta(days=today.weekday())
            else:  # monthly
                start_date = datetime.now().replace(
                    day=1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )

        if not end_date:
            end_date = datetime.now()

        summary = self.get_usage_summary(start_date, end_date)
        suggestions = self.generate_optimization_suggestions(summary)

        # Get top operations by token usage
        top_operations = []
        for operation, data in summary.by_operation.items():
            top_operations.append(
                {
                    "operation": operation,
                    "total_tokens": data["total_tokens"],
                    "total_cost": data["total_cost"],
                    "total_calls": data["total_calls"],
                    "avg_tokens_per_call": data["total_tokens"] / data["total_calls"]
                    if data["total_calls"] > 0
                    else 0,
                },
            )
        top_operations.sort(key=lambda x: x["total_tokens"], reverse=True)

        # Generate cost trends
        cost_trends = []
        if period == "daily":
            for day, data in summary.daily_usage.items():
                cost_trends.append(
                    {
                        "date": day,
                        "cost": data["total_cost"],
                        "tokens": data["total_tokens"],
                        "calls": data["total_calls"],
                    },
                )
        elif period == "weekly":
            for week, data in summary.weekly_usage.items():
                cost_trends.append(
                    {
                        "week": week,
                        "cost": data["total_cost"],
                        "tokens": data["total_tokens"],
                        "calls": data["total_calls"],
                    },
                )
        else:  # monthly
            for month, data in summary.monthly_usage.items():
                cost_trends.append(
                    {
                        "month": month,
                        "cost": data["total_cost"],
                        "tokens": data["total_tokens"],
                        "calls": data["total_calls"],
                    },
                )

        return TokenUsageReport(
            period=period,
            start_date=start_date,
            end_date=end_date,
            summary=summary,
            top_operations=top_operations[:10],  # Top 10 operations
            cost_trends=cost_trends,
            optimization_suggestions=suggestions,
            export_data={
                "usage_history": [u.model_dump() for u in self.usage_history],
                "pricing_config": {k: v.model_dump() for k, v in self.pricing.items()},
            },
        )

    def save_usage_to_context(self, context_file: str) -> None:
        """Save current usage to a context file."""
        try:
            context_path = Path(context_file)
            if context_path.exists():
                with open(context_path, encoding="utf-8") as f:
                    context_data = yaml.safe_load(f) or {}
            else:
                context_data = {}

            # Update token usage in metadata
            if "metadata" not in context_data:
                context_data["metadata"] = {}

            context_data["metadata"]["token_usage"] = {
                "total_tokens": sum(u.total_tokens for u in self.usage_history),
                "total_cost_usd": sum(u.cost_usd for u in self.usage_history),
                "total_calls": len(self.usage_history),
                "last_updated": datetime.now().isoformat(),
                "usage_history": [
                    u.model_dump() for u in self.usage_history[-50:]
                ],  # Keep last 50 calls
            }

            with open(context_path, "w", encoding="utf-8") as f:
                yaml.dump(context_data, f, default_flow_style=False, allow_unicode=True)

            logger.debug(f"Saved token usage to context file: {context_file}")

        except Exception as e:
            logger.error(f"Failed to save token usage to context file: {e}")

    def load_usage_from_context(self, context_file: str) -> None:
        """Load usage history from a context file."""
        try:
            context_path = Path(context_file)
            if not context_path.exists():
                return

            with open(context_path, encoding="utf-8") as f:
                context_data = yaml.safe_load(f)

            if "metadata" in context_data and "token_usage" in context_data["metadata"]:
                usage_data = context_data["metadata"]["token_usage"]
                if "usage_history" in usage_data:
                    # Load usage history
                    self.usage_history = []
                    for usage_dict in usage_data["usage_history"]:
                        if isinstance(usage_dict["timestamp"], str):
                            usage_dict["timestamp"] = datetime.fromisoformat(
                                usage_dict["timestamp"],
                            )
                        self.usage_history.append(TokenUsage(**usage_dict))

                    logger.debug(
                        f"Loaded {len(self.usage_history)} usage records from context file",
                    )

        except Exception as e:
            logger.error(f"Failed to load token usage from context file: {e}")

    def export_report(self, report: TokenUsageReport, output_file: str) -> None:
        """Export a usage report to a file."""
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                if output_file.endswith(".json"):
                    json.dump(report.model_dump(), f, indent=2, default=str)
                else:  # Default to YAML
                    yaml.dump(
                        report.model_dump(),
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                    )

            logger.debug(f"Exported usage report to: {output_file}")

        except Exception as e:
            logger.error(f"Failed to export usage report: {e}")
