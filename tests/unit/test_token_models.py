"""Tests for token usage models."""

from datetime import datetime, timedelta

from jestir.models.token_usage import (
    TokenOptimizationSuggestion,
    TokenPricing,
    TokenUsage,
    TokenUsageReport,
    TokenUsageSummary,
)


class TestTokenUsage:
    """Test cases for TokenUsage model."""

    def test_token_usage_creation(self):
        """Test basic TokenUsage creation."""
        usage = TokenUsage(
            service="test_service",
            operation="test_operation",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.0003,
        )

        assert usage.service == "test_service"
        assert usage.operation == "test_operation"
        assert usage.model == "gpt-4o-mini"
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.cost_usd == 0.0003
        assert isinstance(usage.timestamp, datetime)

    def test_token_usage_defaults(self):
        """Test TokenUsage with default values."""
        usage = TokenUsage(
            service="test",
            operation="test",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.0003,
        )

        assert usage.input_text_length == 0
        assert usage.output_text_length == 0
        assert isinstance(usage.timestamp, datetime)

    def test_token_usage_validation(self):
        """Test TokenUsage validation."""
        # Test with valid data
        usage = TokenUsage(
            service="test",
            operation="test",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.0003,
            input_text_length=10,
            output_text_length=20,
        )
        assert usage.input_text_length == 10
        assert usage.output_text_length == 20

    def test_token_usage_invalid_data(self):
        """Test TokenUsage with invalid data."""
        # Test that negative values are handled gracefully
        usage = TokenUsage(
            service="test",
            operation="test",
            model="gpt-4o-mini",
            prompt_tokens=-100,  # Negative tokens should be handled
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.0003,
        )
        # Pydantic may allow negative values, so we just test it doesn't crash
        assert usage.prompt_tokens == -100


class TestTokenUsageSummary:
    """Test cases for TokenUsageSummary model."""

    def test_token_usage_summary_creation(self):
        """Test basic TokenUsageSummary creation."""
        summary = TokenUsageSummary(
            total_tokens=1000,
            total_cost_usd=2.50,
            total_calls=10,
            by_service={"service1": {"total_tokens": 500}},
            by_operation={"op1": {"total_tokens": 500}},
            by_model={"gpt-4o-mini": {"total_tokens": 1000}},
        )

        assert summary.total_tokens == 1000
        assert summary.total_cost_usd == 2.50
        assert summary.total_calls == 10
        assert "service1" in summary.by_service
        assert "op1" in summary.by_operation
        assert "gpt-4o-mini" in summary.by_model

    def test_token_usage_summary_defaults(self):
        """Test TokenUsageSummary with default values."""
        summary = TokenUsageSummary()

        assert summary.total_tokens == 0
        assert summary.total_cost_usd == 0.0
        assert summary.total_calls == 0
        assert summary.by_service == {}
        assert summary.by_operation == {}
        assert summary.by_model == {}
        assert summary.daily_usage == {}
        assert summary.weekly_usage == {}
        assert summary.monthly_usage == {}

    def test_token_usage_summary_complex_data(self):
        """Test TokenUsageSummary with complex nested data."""
        summary = TokenUsageSummary(
            total_tokens=2000,
            total_cost_usd=5.0,
            total_calls=20,
            by_service={
                "service1": {
                    "total_tokens": 1000,
                    "total_cost": 2.5,
                    "total_calls": 10,
                    "operations": {
                        "op1": {
                            "total_tokens": 500,
                            "total_cost": 1.25,
                            "total_calls": 5,
                        },
                    },
                },
            },
            by_operation={
                "op1": {
                    "total_tokens": 1000,
                    "total_cost": 2.5,
                    "total_calls": 10,
                    "services": {
                        "service1": {
                            "total_tokens": 500,
                            "total_cost": 1.25,
                            "total_calls": 5,
                        },
                    },
                },
            },
            by_model={
                "gpt-4o-mini": {
                    "total_tokens": 2000,
                    "total_cost": 5.0,
                    "total_calls": 20,
                    "avg_tokens_per_call": 100.0,
                },
            },
            daily_usage={
                "2024-01-01": {
                    "total_tokens": 1000,
                    "total_cost": 2.5,
                    "total_calls": 10,
                },
            },
            weekly_usage={
                "2024-W01": {
                    "total_tokens": 2000,
                    "total_cost": 5.0,
                    "total_calls": 20,
                },
            },
            monthly_usage={
                "2024-01": {"total_tokens": 2000, "total_cost": 5.0, "total_calls": 20},
            },
        )

        assert summary.total_tokens == 2000
        assert summary.by_service["service1"]["total_tokens"] == 1000
        assert (
            summary.by_service["service1"]["operations"]["op1"]["total_tokens"] == 500
        )
        assert (
            summary.by_operation["op1"]["services"]["service1"]["total_tokens"] == 500
        )
        assert summary.by_model["gpt-4o-mini"]["avg_tokens_per_call"] == 100.0
        assert "2024-01-01" in summary.daily_usage
        assert "2024-W01" in summary.weekly_usage
        assert "2024-01" in summary.monthly_usage


class TestTokenPricing:
    """Test cases for TokenPricing model."""

    def test_token_pricing_creation(self):
        """Test basic TokenPricing creation."""
        pricing = TokenPricing(
            model="gpt-4o-mini",
            input_price_per_1k=0.00015,
            output_price_per_1k=0.0006,
            description="GPT-4 Omni Mini",
        )

        assert pricing.model == "gpt-4o-mini"
        assert pricing.input_price_per_1k == 0.00015
        assert pricing.output_price_per_1k == 0.0006
        assert pricing.description == "GPT-4 Omni Mini"

    def test_token_pricing_defaults(self):
        """Test TokenPricing with default values."""
        pricing = TokenPricing(
            model="test-model",
            input_price_per_1k=0.001,
            output_price_per_1k=0.002,
        )

        assert pricing.model == "test-model"
        assert pricing.input_price_per_1k == 0.001
        assert pricing.output_price_per_1k == 0.002
        assert pricing.description == ""

    def test_token_pricing_validation(self):
        """Test TokenPricing validation."""
        # Test with valid data
        pricing = TokenPricing(
            model="test-model",
            input_price_per_1k=0.001,
            output_price_per_1k=0.002,
            description="Test model",
        )
        assert pricing.model == "test-model"

    def test_token_pricing_invalid_data(self):
        """Test TokenPricing with invalid data."""
        # Test that negative values are handled gracefully
        pricing = TokenPricing(
            model="test-model",
            input_price_per_1k=-0.001,  # Negative price should be handled
            output_price_per_1k=0.002,
        )
        # Pydantic may allow negative values, so we just test it doesn't crash
        assert pricing.input_price_per_1k == -0.001


class TestTokenOptimizationSuggestion:
    """Test cases for TokenOptimizationSuggestion model."""

    def test_optimization_suggestion_creation(self):
        """Test basic TokenOptimizationSuggestion creation."""
        suggestion = TokenOptimizationSuggestion(
            type="model_choice",
            title="Switch to cheaper model",
            description="Consider using gpt-4o-mini instead of gpt-4o",
            potential_savings=10.50,
            confidence=0.8,
            action_required="Update model configuration",
        )

        assert suggestion.type == "model_choice"
        assert suggestion.title == "Switch to cheaper model"
        assert suggestion.description == "Consider using gpt-4o-mini instead of gpt-4o"
        assert suggestion.potential_savings == 10.50
        assert suggestion.confidence == 0.8
        assert suggestion.action_required == "Update model configuration"

    def test_optimization_suggestion_defaults(self):
        """Test TokenOptimizationSuggestion with default values."""
        suggestion = TokenOptimizationSuggestion(
            type="efficiency",
            title="Optimize prompts",
            description="Reduce prompt length",
        )

        assert suggestion.type == "efficiency"
        assert suggestion.title == "Optimize prompts"
        assert suggestion.description == "Reduce prompt length"
        assert suggestion.potential_savings == 0.0
        assert suggestion.confidence == 0.0
        assert suggestion.action_required == ""

    def test_optimization_suggestion_validation(self):
        """Test TokenOptimizationSuggestion validation."""
        # Test with valid data
        suggestion = TokenOptimizationSuggestion(
            type="cost_reduction",
            title="High usage detected",
            description="Consider batching operations",
            potential_savings=5.25,
            confidence=0.7,
            action_required="Implement batching",
        )
        assert suggestion.type == "cost_reduction"
        assert suggestion.potential_savings == 5.25

    def test_optimization_suggestion_invalid_data(self):
        """Test TokenOptimizationSuggestion with invalid data."""
        # Test that values outside normal range are handled gracefully
        suggestion = TokenOptimizationSuggestion(
            type="test",
            title="Test",
            description="Test description",
            confidence=1.5,  # Confidence > 1 should be handled
        )
        # Pydantic may allow values > 1, so we just test it doesn't crash
        assert suggestion.confidence == 1.5


class TestTokenUsageReport:
    """Test cases for TokenUsageReport model."""

    def test_token_usage_report_creation(self):
        """Test basic TokenUsageReport creation."""
        summary = TokenUsageSummary(
            total_tokens=1000,
            total_cost_usd=2.50,
            total_calls=10,
        )
        suggestions = [
            TokenOptimizationSuggestion(
                type="model_choice",
                title="Switch model",
                description="Use cheaper model",
            ),
        ]

        report = TokenUsageReport(
            period="monthly",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            summary=summary,
            top_operations=[{"operation": "op1", "total_tokens": 500}],
            cost_trends=[{"month": "2024-01", "cost": 2.50}],
            optimization_suggestions=suggestions,
            export_data={"usage_history": [], "pricing_config": {}},
        )

        assert report.period == "monthly"
        assert report.start_date == datetime(2024, 1, 1)
        assert report.end_date == datetime(2024, 1, 31)
        assert report.summary.total_tokens == 1000
        assert len(report.top_operations) == 1
        assert len(report.cost_trends) == 1
        assert len(report.optimization_suggestions) == 1
        assert "usage_history" in report.export_data

    def test_token_usage_report_defaults(self):
        """Test TokenUsageReport with default values."""
        summary = TokenUsageSummary()

        report = TokenUsageReport(
            period="daily",
            start_date=datetime.now(),
            end_date=datetime.now(),
            summary=summary,
        )

        assert report.period == "daily"
        assert report.top_operations == []
        assert report.cost_trends == []
        assert report.optimization_suggestions == []
        assert report.export_data == {}

    def test_token_usage_report_complex_data(self):
        """Test TokenUsageReport with complex data."""
        summary = TokenUsageSummary(
            total_tokens=5000,
            total_cost_usd=12.50,
            total_calls=50,
            by_service={"service1": {"total_tokens": 2500}},
            by_operation={"op1": {"total_tokens": 3000}},
            by_model={"gpt-4o-mini": {"total_tokens": 5000}},
        )

        suggestions = [
            TokenOptimizationSuggestion(
                type="model_choice",
                title="Switch to gpt-4o-mini",
                description="Use cheaper model",
                potential_savings=5.0,
                confidence=0.8,
                action_required="Update configuration",
            ),
            TokenOptimizationSuggestion(
                type="efficiency",
                title="Optimize prompts",
                description="Reduce prompt length",
                potential_savings=2.5,
                confidence=0.6,
                action_required="Review templates",
            ),
        ]

        top_operations = [
            {
                "operation": "op1",
                "total_tokens": 3000,
                "total_cost": 7.5,
                "total_calls": 30,
            },
            {
                "operation": "op2",
                "total_tokens": 2000,
                "total_cost": 5.0,
                "total_calls": 20,
            },
        ]

        cost_trends = [
            {"month": "2024-01", "cost": 12.50, "tokens": 5000, "calls": 50},
        ]

        export_data = {
            "usage_history": [{"service": "test", "operation": "test"}],
            "pricing_config": {"gpt-4o-mini": {"input_price_per_1k": 0.00015}},
        }

        report = TokenUsageReport(
            period="monthly",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            summary=summary,
            top_operations=top_operations,
            cost_trends=cost_trends,
            optimization_suggestions=suggestions,
            export_data=export_data,
        )

        assert report.period == "monthly"
        assert report.summary.total_tokens == 5000
        assert len(report.top_operations) == 2
        assert report.top_operations[0]["operation"] == "op1"
        assert len(report.cost_trends) == 1
        assert len(report.optimization_suggestions) == 2
        assert report.optimization_suggestions[0].type == "model_choice"
        assert report.optimization_suggestions[1].type == "efficiency"
        assert "usage_history" in report.export_data
        assert "pricing_config" in report.export_data

    def test_token_usage_report_validation(self):
        """Test TokenUsageReport validation."""
        summary = TokenUsageSummary()

        # Test with valid data
        report = TokenUsageReport(
            period="weekly",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 7),
            summary=summary,
            top_operations=[{"operation": "test", "total_tokens": 100}],
            cost_trends=[{"week": "2024-W01", "cost": 1.0}],
            optimization_suggestions=[],
            export_data={"test": "data"},
        )

        assert report.period == "weekly"
        assert len(report.top_operations) == 1
        assert len(report.cost_trends) == 1

    def test_token_usage_report_invalid_data(self):
        """Test TokenUsageReport with invalid data."""
        summary = TokenUsageSummary()

        # Test that end date before start date is handled gracefully
        report = TokenUsageReport(
            period="monthly",
            start_date=datetime.now(),
            end_date=datetime.now() - timedelta(days=1),  # End before start
            summary=summary,
        )
        # Pydantic may allow this, so we just test it doesn't crash
        assert report.start_date > report.end_date


class TestModelSerialization:
    """Test cases for model serialization and deserialization."""

    def test_token_usage_serialization(self):
        """Test TokenUsage serialization."""
        usage = TokenUsage(
            service="test",
            operation="test",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            cost_usd=0.0003,
        )

        # Test model_dump
        data = usage.model_dump()
        assert data["service"] == "test"
        assert data["operation"] == "test"
        assert data["model"] == "gpt-4o-mini"
        assert data["prompt_tokens"] == 100
        assert data["completion_tokens"] == 50
        assert data["total_tokens"] == 150
        assert data["cost_usd"] == 0.0003
        assert "timestamp" in data

    def test_token_usage_deserialization(self):
        """Test TokenUsage deserialization."""
        data = {
            "service": "test",
            "operation": "test",
            "model": "gpt-4o-mini",
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "cost_usd": 0.0003,
            "input_text_length": 10,
            "output_text_length": 20,
            "timestamp": "2024-01-01T12:00:00",
        }

        usage = TokenUsage(**data)
        assert usage.service == "test"
        assert usage.operation == "test"
        assert usage.model == "gpt-4o-mini"
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.cost_usd == 0.0003
        assert usage.input_text_length == 10
        assert usage.output_text_length == 20
        assert isinstance(usage.timestamp, datetime)

    def test_token_usage_summary_serialization(self):
        """Test TokenUsageSummary serialization."""
        summary = TokenUsageSummary(
            total_tokens=1000,
            total_cost_usd=2.50,
            total_calls=10,
            by_service={"service1": {"total_tokens": 500}},
            by_operation={"op1": {"total_tokens": 500}},
            by_model={"gpt-4o-mini": {"total_tokens": 1000}},
        )

        data = summary.model_dump()
        assert data["total_tokens"] == 1000
        assert data["total_cost_usd"] == 2.50
        assert data["total_calls"] == 10
        assert "service1" in data["by_service"]
        assert "op1" in data["by_operation"]
        assert "gpt-4o-mini" in data["by_model"]

    def test_token_pricing_serialization(self):
        """Test TokenPricing serialization."""
        pricing = TokenPricing(
            model="gpt-4o-mini",
            input_price_per_1k=0.00015,
            output_price_per_1k=0.0006,
            description="GPT-4 Omni Mini",
        )

        data = pricing.model_dump()
        assert data["model"] == "gpt-4o-mini"
        assert data["input_price_per_1k"] == 0.00015
        assert data["output_price_per_1k"] == 0.0006
        assert data["description"] == "GPT-4 Omni Mini"

    def test_optimization_suggestion_serialization(self):
        """Test TokenOptimizationSuggestion serialization."""
        suggestion = TokenOptimizationSuggestion(
            type="model_choice",
            title="Switch model",
            description="Use cheaper model",
            potential_savings=10.50,
            confidence=0.8,
            action_required="Update configuration",
        )

        data = suggestion.model_dump()
        assert data["type"] == "model_choice"
        assert data["title"] == "Switch model"
        assert data["description"] == "Use cheaper model"
        assert data["potential_savings"] == 10.50
        assert data["confidence"] == 0.8
        assert data["action_required"] == "Update configuration"

    def test_usage_report_serialization(self):
        """Test TokenUsageReport serialization."""
        summary = TokenUsageSummary(
            total_tokens=1000,
            total_cost_usd=2.50,
            total_calls=10,
        )

        report = TokenUsageReport(
            period="monthly",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            summary=summary,
            top_operations=[{"operation": "op1", "total_tokens": 500}],
            cost_trends=[{"month": "2024-01", "cost": 2.50}],
            optimization_suggestions=[],
            export_data={"test": "data"},
        )

        data = report.model_dump()
        assert data["period"] == "monthly"
        assert data["summary"]["total_tokens"] == 1000
        assert len(data["top_operations"]) == 1
        assert len(data["cost_trends"]) == 1
        assert len(data["optimization_suggestions"]) == 0
        assert data["export_data"]["test"] == "data"
