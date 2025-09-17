"""Tests for token tracking functionality."""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import yaml

from jestir.models.token_usage import (
    TokenPricing,
    TokenUsageSummary,
)
from jestir.services.token_tracker import TokenTracker


class TestTokenTracker:
    """Test cases for TokenTracker."""

    def test_track_usage(self):
        """Test basic token usage tracking."""
        tracker = TokenTracker()

        # Track a usage
        usage = tracker.track_usage(
            service="test_service",
            operation="test_operation",
            model="gpt-4o-mini",
            prompt_tokens=100,
            completion_tokens=50,
            input_text="test input",
            output_text="test output",
        )

        assert usage.service == "test_service"
        assert usage.operation == "test_operation"
        assert usage.model == "gpt-4o-mini"
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.input_text_length == 10
        assert usage.output_text_length == 11
        assert usage.cost_usd > 0  # Should have some cost

        # Check it's in history
        assert len(tracker.usage_history) == 1
        assert tracker.usage_history[0] == usage

    def test_cost_calculation(self):
        """Test cost calculation for different models."""
        tracker = TokenTracker()

        # Test gpt-4o-mini (cheaper)
        usage_mini = tracker.track_usage(
            service="test",
            operation="test",
            model="gpt-4o-mini",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        # Test gpt-4o (more expensive)
        usage_o = tracker.track_usage(
            service="test",
            operation="test",
            model="gpt-4o",
            prompt_tokens=1000,
            completion_tokens=500,
        )

        # gpt-4o should be more expensive
        assert usage_o.cost_usd > usage_mini.cost_usd

    def test_usage_summary(self):
        """Test usage summary generation."""
        tracker = TokenTracker()

        # Add some usage data
        tracker.track_usage("service1", "op1", "gpt-4o-mini", 100, 50)
        tracker.track_usage("service1", "op2", "gpt-4o-mini", 200, 100)
        tracker.track_usage("service2", "op1", "gpt-4o", 150, 75)

        summary = tracker.get_usage_summary()

        assert summary.total_tokens == 675  # 150 + 300 + 225
        assert summary.total_calls == 3
        assert summary.total_cost_usd > 0

        # Check service breakdown
        assert "service1" in summary.by_service
        assert "service2" in summary.by_service
        assert summary.by_service["service1"]["total_tokens"] == 450
        assert summary.by_service["service2"]["total_tokens"] == 225

        # Check operation breakdown
        assert "op1" in summary.by_operation
        assert "op2" in summary.by_operation
        assert summary.by_operation["op1"]["total_tokens"] == 375
        assert summary.by_operation["op2"]["total_tokens"] == 300

        # Check model breakdown
        assert "gpt-4o-mini" in summary.by_model
        assert "gpt-4o" in summary.by_model

    def test_date_filtering(self):
        """Test usage summary with date filtering."""
        tracker = TokenTracker()

        # Add usage with specific timestamps
        now = datetime.now()
        yesterday = now - timedelta(days=1)

        # Mock timestamps
        usage1 = tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)
        usage1.timestamp = yesterday

        usage2 = tracker.track_usage("test", "test", "gpt-4o-mini", 200, 100)
        usage2.timestamp = now

        # Test filtering
        summary_all = tracker.get_usage_summary()
        summary_today = tracker.get_usage_summary(
            start_date=now.replace(hour=0, minute=0, second=0),
        )

        assert summary_all.total_tokens == 450
        assert summary_today.total_tokens == 300

    def test_optimization_suggestions(self):
        """Test optimization suggestion generation."""
        tracker = TokenTracker()

        # Add high-cost usage to trigger suggestions (need > $5 total cost)
        for _ in range(200):  # Many calls to reach cost threshold
            tracker.track_usage(
                "expensive_service",
                "expensive_op",
                "gpt-4o",
                2000,
                1000,
            )

        summary = tracker.get_usage_summary()
        suggestions = tracker.generate_optimization_suggestions(summary)

        # Should have suggestions for high-cost usage
        assert len(suggestions) > 0
        assert any("GPT-4o-mini" in s.description for s in suggestions)

    def test_report_generation(self):
        """Test comprehensive report generation."""
        tracker = TokenTracker()

        # Add some usage data
        tracker.track_usage("service1", "op1", "gpt-4o-mini", 100, 50)
        tracker.track_usage("service2", "op2", "gpt-4o", 200, 100)

        report = tracker.generate_report(period="monthly")

        assert report.period == "monthly"
        assert report.summary.total_tokens == 450
        assert len(report.top_operations) > 0
        assert len(report.cost_trends) > 0

    def test_context_save_load(self):
        """Test saving and loading usage from context."""
        tracker = TokenTracker()

        # Add some usage
        tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)

        # Save to context
        context_file = "test_context.yaml"
        tracker.save_usage_to_context(context_file)

        # Create new tracker and load
        new_tracker = TokenTracker()
        new_tracker.load_usage_from_context(context_file)

        # Should have loaded the usage
        assert len(new_tracker.usage_history) == 1
        assert new_tracker.usage_history[0].total_tokens == 150

    def test_pricing_configuration(self):
        """Test custom pricing configuration."""
        custom_pricing = {
            "custom-model": TokenPricing(
                model="custom-model",
                input_price_per_1k=0.001,
                output_price_per_1k=0.002,
                description="Custom model",
            ),
            "gpt-4o-mini": TokenPricing(
                model="gpt-4o-mini",
                input_price_per_1k=0.00015,
                output_price_per_1k=0.0006,
                description="GPT-4 Omni Mini - Fast and efficient",
            ),
        }

        tracker = TokenTracker(pricing_config=custom_pricing)

        usage = tracker.track_usage("test", "test", "custom-model", 1000, 500)

        # Should use custom pricing
        expected_cost = (1000 / 1000) * 0.001 + (500 / 1000) * 0.002
        assert abs(usage.cost_usd - expected_cost) < 0.0001

    def test_unknown_model_fallback(self):
        """Test fallback to default pricing for unknown models."""
        tracker = TokenTracker()

        usage = tracker.track_usage("test", "test", "unknown-model", 1000, 500)

        # Should use gpt-4o-mini pricing as fallback
        expected_cost = (1000 / 1000) * 0.00015 + (500 / 1000) * 0.0006
        assert abs(usage.cost_usd - expected_cost) < 0.0001

    def test_empty_usage_history(self):
        """Test behavior with empty usage history."""
        tracker = TokenTracker()

        summary = tracker.get_usage_summary()
        assert summary.total_tokens == 0
        assert summary.total_cost_usd == 0.0
        assert summary.total_calls == 0
        assert summary.by_service == {}
        assert summary.by_operation == {}
        assert summary.by_model == {}

    def test_usage_summary_edge_cases(self):
        """Test usage summary with edge cases."""
        tracker = TokenTracker()

        # Test with single usage
        tracker.track_usage("service1", "op1", "gpt-4o-mini", 100, 50)
        summary = tracker.get_usage_summary()

        assert summary.total_tokens == 150
        assert summary.total_calls == 1
        assert summary.by_service["service1"]["total_tokens"] == 150
        assert summary.by_operation["op1"]["total_tokens"] == 150
        assert summary.by_model["gpt-4o-mini"]["total_tokens"] == 150

    def test_date_filtering_edge_cases(self):
        """Test date filtering with edge cases."""
        tracker = TokenTracker()

        # Add usage with specific timestamps
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        usage1 = tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)
        usage1.timestamp = yesterday

        usage2 = tracker.track_usage("test", "test", "gpt-4o-mini", 200, 100)
        usage2.timestamp = now

        usage3 = tracker.track_usage("test", "test", "gpt-4o-mini", 300, 150)
        usage3.timestamp = tomorrow

        # Test filtering with exact dates
        summary_today = tracker.get_usage_summary(start_date=now, end_date=now)
        assert summary_today.total_tokens == 300

        # Test filtering with no results
        future_date = now + timedelta(days=2)
        summary_future = tracker.get_usage_summary(start_date=future_date)
        assert summary_future.total_tokens == 0

    def test_optimization_suggestions_edge_cases(self):
        """Test optimization suggestions with edge cases."""
        tracker = TokenTracker()

        # Test with no usage
        summary = TokenUsageSummary()
        suggestions = tracker.generate_optimization_suggestions(summary)
        assert len(suggestions) == 0

        # Test with low-cost usage
        tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)
        summary = tracker.get_usage_summary()
        suggestions = tracker.generate_optimization_suggestions(summary)
        assert len(suggestions) == 0

    def test_optimization_suggestions_high_cost(self):
        """Test optimization suggestions for high-cost usage."""
        tracker = TokenTracker()

        # Add high-cost usage (need > $5 total cost)
        for _ in range(200):
            tracker.track_usage("expensive", "expensive", "gpt-4o", 2000, 1000)

        summary = tracker.get_usage_summary()
        suggestions = tracker.generate_optimization_suggestions(summary)

        # Should have suggestions for high-cost usage
        assert len(suggestions) > 0
        assert any("GPT-4o-mini" in s.description for s in suggestions)

    def test_optimization_suggestions_inefficient_operations(self):
        """Test optimization suggestions for inefficient operations."""
        tracker = TokenTracker()

        # Add many inefficient operations
        for _ in range(15):
            tracker.track_usage("service", "inefficient", "gpt-4o-mini", 3000, 1500)

        summary = tracker.get_usage_summary()
        suggestions = tracker.generate_optimization_suggestions(summary)

        # Should have suggestions for inefficient operations
        assert len(suggestions) > 0
        assert any("inefficient" in s.description for s in suggestions)

    def test_optimization_suggestions_cost_trends(self):
        """Test optimization suggestions for cost trends."""
        tracker = TokenTracker()

        # Add usage over multiple days to trigger trend analysis (need > $2/day average)
        base_date = datetime.now() - timedelta(days=10)
        for i in range(10):
            usage = tracker.track_usage(
                "trend",
                "trend",
                "gpt-4o",
                200000,
                100000,
            )  # Much higher cost per call
            usage.timestamp = base_date + timedelta(days=i)

        summary = tracker.get_usage_summary()
        suggestions = tracker.generate_optimization_suggestions(summary)

        # Should have suggestions for high daily usage
        assert len(suggestions) > 0
        assert any("High daily usage" in s.title for s in suggestions)

    def test_report_generation_daily(self):
        """Test daily report generation."""
        tracker = TokenTracker()

        # Add some usage
        tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)

        report = tracker.generate_report(period="daily")

        assert report.period == "daily"
        assert report.summary.total_tokens == 150
        assert len(report.cost_trends) > 0

    def test_report_generation_weekly(self):
        """Test weekly report generation."""
        tracker = TokenTracker()

        # Add some usage
        tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)

        report = tracker.generate_report(period="weekly")

        assert report.period == "weekly"
        assert report.summary.total_tokens == 150
        assert len(report.cost_trends) > 0

    def test_report_generation_monthly(self):
        """Test monthly report generation."""
        tracker = TokenTracker()

        # Add some usage
        tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)

        report = tracker.generate_report(period="monthly")

        assert report.period == "monthly"
        assert report.summary.total_tokens == 150
        assert len(report.cost_trends) > 0

    def test_report_generation_custom_dates(self):
        """Test report generation with custom dates."""
        tracker = TokenTracker()

        # Add usage with specific timestamp
        usage = tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)
        usage.timestamp = datetime(2024, 1, 15, tzinfo=timezone.utc)

        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)

        report = tracker.generate_report(
            period="monthly",
            start_date=start_date,
            end_date=end_date,
        )

        assert report.start_date == start_date
        assert report.end_date == end_date
        assert report.summary.total_tokens == 150

    def test_report_top_operations(self):
        """Test report top operations sorting."""
        tracker = TokenTracker()

        # Add multiple operations with different token usage
        tracker.track_usage("service1", "op1", "gpt-4o-mini", 100, 50)
        tracker.track_usage("service2", "op2", "gpt-4o-mini", 200, 100)
        tracker.track_usage("service3", "op3", "gpt-4o-mini", 300, 150)

        report = tracker.generate_report()

        # Should be sorted by total tokens descending
        assert len(report.top_operations) == 3
        assert report.top_operations[0]["operation"] == "op3"
        assert report.top_operations[0]["total_tokens"] == 450
        assert report.top_operations[1]["operation"] == "op2"
        assert report.top_operations[1]["total_tokens"] == 300
        assert report.top_operations[2]["operation"] == "op1"
        assert report.top_operations[2]["total_tokens"] == 150

    def test_save_usage_to_context_new_file(self):
        """Test saving usage to a new context file."""
        tracker = TokenTracker()

        # Add some usage
        tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            context_file = f.name

        try:
            tracker.save_usage_to_context(context_file)

            # Verify file was created and contains usage data
            with open(context_file) as f:
                data = yaml.safe_load(f)

            assert data is not None
            assert "metadata" in data
            assert "token_usage" in data["metadata"]
            assert data["metadata"]["token_usage"]["total_tokens"] == 150
            assert data["metadata"]["token_usage"]["total_calls"] == 1

        finally:
            Path(context_file).unlink(missing_ok=True)

    def test_save_usage_to_context_existing_file(self):
        """Test saving usage to an existing context file."""
        tracker = TokenTracker()

        # Add some usage
        tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            context_file = f.name
            # Write existing context data
            yaml.dump({"existing": "data"}, f)

        try:
            tracker.save_usage_to_context(context_file)

            # Verify file contains both existing data and usage data
            with open(context_file) as f:
                data = yaml.safe_load(f)

            assert "existing" in data
            assert "metadata" in data
            assert "token_usage" in data["metadata"]

        finally:
            Path(context_file).unlink(missing_ok=True)

    def test_save_usage_to_context_error_handling(self):
        """Test error handling in save_usage_to_context."""
        tracker = TokenTracker()

        # Add some usage
        tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)

        # Test with invalid file path (should not raise exception)
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            tracker.save_usage_to_context("/invalid/path/context.yaml")
            # Should not raise exception, just log error

    def test_load_usage_from_context_existing_file(self):
        """Test loading usage from an existing context file."""
        tracker = TokenTracker()

        # Create a context file with usage data
        usage_data = {
            "metadata": {
                "token_usage": {
                    "total_tokens": 150,
                    "total_cost_usd": 0.0003,
                    "total_calls": 1,
                    "last_updated": "2024-01-01T00:00:00",
                    "usage_history": [
                        {
                            "timestamp": "2024-01-01T00:00:00",
                            "service": "test",
                            "operation": "test",
                            "model": "gpt-4o-mini",
                            "prompt_tokens": 100,
                            "completion_tokens": 50,
                            "total_tokens": 150,
                            "cost_usd": 0.0003,
                            "input_text_length": 0,
                            "output_text_length": 0,
                        },
                    ],
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            context_file = f.name
            yaml.dump(usage_data, f)

        try:
            tracker.load_usage_from_context(context_file)

            assert len(tracker.usage_history) == 1
            assert tracker.usage_history[0].total_tokens == 150
            assert tracker.usage_history[0].service == "test"

        finally:
            Path(context_file).unlink(missing_ok=True)

    def test_load_usage_from_context_missing_file(self):
        """Test loading usage from a missing context file."""
        tracker = TokenTracker()

        # Should not raise exception for missing file
        tracker.load_usage_from_context("/nonexistent/file.yaml")
        assert len(tracker.usage_history) == 0

    def test_load_usage_from_context_invalid_data(self):
        """Test loading usage from context file with invalid data."""
        tracker = TokenTracker()

        # Create a context file with invalid usage data
        invalid_data = {
            "metadata": {
                "token_usage": {
                    "usage_history": [
                        {
                            "invalid": "data",
                        },
                    ],
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            context_file = f.name
            yaml.dump(invalid_data, f)

        try:
            # Should not raise exception, just log error
            tracker.load_usage_from_context(context_file)
            assert len(tracker.usage_history) == 0

        finally:
            Path(context_file).unlink(missing_ok=True)

    def test_export_report_json(self):
        """Test exporting report to JSON file."""
        tracker = TokenTracker()

        # Add some usage
        tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)

        report = tracker.generate_report()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            output_file = f.name

        try:
            tracker.export_report(report, output_file)

            # Verify file was created and contains valid JSON
            with open(output_file) as f:
                data = json.load(f)

            assert data["period"] == "monthly"
            assert data["summary"]["total_tokens"] == 150

        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_export_report_yaml(self):
        """Test exporting report to YAML file."""
        tracker = TokenTracker()

        # Add some usage
        tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)

        report = tracker.generate_report()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            output_file = f.name

        try:
            tracker.export_report(report, output_file)

            # Verify file was created and contains valid YAML
            with open(output_file) as f:
                data = yaml.safe_load(f)

            assert data["period"] == "monthly"
            assert data["summary"]["total_tokens"] == 150

        finally:
            Path(output_file).unlink(missing_ok=True)

    def test_export_report_error_handling(self):
        """Test error handling in export_report."""
        tracker = TokenTracker()

        # Add some usage
        tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)

        report = tracker.generate_report()

        # Test with invalid file path (should not raise exception)
        with patch("builtins.open", side_effect=PermissionError("Permission denied")):
            tracker.export_report(report, "/invalid/path/report.json")
            # Should not raise exception, just log error

    def test_weekly_usage_grouping(self):
        """Test weekly usage grouping logic."""
        tracker = TokenTracker()

        # Add usage on different days of the same week
        base_date = datetime(2024, 1, 15, tzinfo=timezone.utc)  # Monday
        for i in range(7):  # Monday to Sunday
            usage = tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)
            usage.timestamp = base_date + timedelta(days=i)

        summary = tracker.get_usage_summary()

        # Should group all days into one week
        assert len(summary.weekly_usage) == 1
        week_key = next(iter(summary.weekly_usage.keys()))
        assert "2024-W02" in week_key  # Week 2 of 2024 (Jan 15 is in week 2)

    def test_monthly_usage_grouping(self):
        """Test monthly usage grouping logic."""
        tracker = TokenTracker()

        # Add usage on different days of the same month
        base_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        for i in range(10):
            usage = tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)
            usage.timestamp = base_date + timedelta(days=i)

        summary = tracker.get_usage_summary()

        # Should group all days into one month
        assert len(summary.monthly_usage) == 1
        month_key = next(iter(summary.monthly_usage.keys()))
        assert month_key == "2024-01"

    def test_daily_usage_grouping(self):
        """Test daily usage grouping logic."""
        tracker = TokenTracker()

        # Add usage on different days
        base_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
        for i in range(3):
            usage = tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)
            usage.timestamp = base_date + timedelta(days=i)

        summary = tracker.get_usage_summary()

        # Should group into 3 different days
        assert len(summary.daily_usage) == 3
        assert "2024-01-15" in summary.daily_usage
        assert "2024-01-16" in summary.daily_usage
        assert "2024-01-17" in summary.daily_usage

    def test_model_average_calculation(self):
        """Test average tokens per call calculation for models."""
        tracker = TokenTracker()

        # Add multiple calls for the same model
        for i in range(5):
            tracker.track_usage("test", "test", "gpt-4o-mini", 100 + i * 10, 50 + i * 5)

        summary = tracker.get_usage_summary()

        # Check average calculation
        model_data = summary.by_model["gpt-4o-mini"]
        assert model_data["total_calls"] == 5
        assert model_data["avg_tokens_per_call"] > 0
        assert (
            model_data["avg_tokens_per_call"]
            == model_data["total_tokens"] / model_data["total_calls"]
        )

    def test_operation_service_breakdown(self):
        """Test operation breakdown includes service details."""
        tracker = TokenTracker()

        # Add usage with different services for the same operation
        tracker.track_usage("service1", "operation", "gpt-4o-mini", 100, 50)
        tracker.track_usage("service2", "operation", "gpt-4o-mini", 200, 100)

        summary = tracker.get_usage_summary()

        # Check operation breakdown includes services
        op_data = summary.by_operation["operation"]
        assert "services" in op_data
        assert "service1" in op_data["services"]
        assert "service2" in op_data["services"]
        assert op_data["services"]["service1"]["total_tokens"] == 150
        assert op_data["services"]["service2"]["total_tokens"] == 300

    def test_service_operation_breakdown(self):
        """Test service breakdown includes operation details."""
        tracker = TokenTracker()

        # Add usage with different operations for the same service
        tracker.track_usage("service", "operation1", "gpt-4o-mini", 100, 50)
        tracker.track_usage("service", "operation2", "gpt-4o-mini", 200, 100)

        summary = tracker.get_usage_summary()

        # Check service breakdown includes operations
        service_data = summary.by_service["service"]
        assert "operations" in service_data
        assert "operation1" in service_data["operations"]
        assert "operation2" in service_data["operations"]
        assert service_data["operations"]["operation1"]["total_tokens"] == 150
        assert service_data["operations"]["operation2"]["total_tokens"] == 300

    def test_cost_trends_daily(self):
        """Test cost trends for daily reports."""
        tracker = TokenTracker()

        # Add usage over multiple days
        base_date = datetime.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        ) - timedelta(days=2)
        for i in range(3):
            usage = tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)
            usage.timestamp = base_date + timedelta(days=i)

        # Generate report with custom date range to include all our data
        start_date = base_date
        end_date = base_date + timedelta(days=3)
        report = tracker.generate_report(
            period="daily",
            start_date=start_date,
            end_date=end_date,
        )

        # Check cost trends
        assert len(report.cost_trends) == 3
        assert all("date" in trend for trend in report.cost_trends)
        assert all("cost" in trend for trend in report.cost_trends)

    def test_cost_trends_weekly(self):
        """Test cost trends for weekly reports."""
        tracker = TokenTracker()

        # Add usage over multiple weeks
        base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        # Get Monday of current week
        monday = base_date - timedelta(days=base_date.weekday())
        for i in range(3):
            usage = tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)
            usage.timestamp = monday + timedelta(weeks=i)

        # Generate report with custom date range to include all our data
        start_date = monday
        end_date = monday + timedelta(weeks=3)
        report = tracker.generate_report(
            period="weekly",
            start_date=start_date,
            end_date=end_date,
        )

        # Check cost trends
        assert len(report.cost_trends) == 3
        assert all("week" in trend for trend in report.cost_trends)
        assert all("cost" in trend for trend in report.cost_trends)

    def test_cost_trends_monthly(self):
        """Test cost trends for monthly reports."""
        tracker = TokenTracker()

        # Add usage over multiple months
        base_date = datetime.now().replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        for i in range(3):
            usage = tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)
            usage.timestamp = base_date + timedelta(days=i * 30)

        # Generate report with custom date range to include all our data
        start_date = base_date
        end_date = base_date + timedelta(days=90)
        report = tracker.generate_report(
            period="monthly",
            start_date=start_date,
            end_date=end_date,
        )

        # Check cost trends (should have at least 2 months due to date grouping)
        assert len(report.cost_trends) >= 2
        assert all("month" in trend for trend in report.cost_trends)
        assert all("cost" in trend for trend in report.cost_trends)

    def test_export_data_structure(self):
        """Test export data structure in reports."""
        tracker = TokenTracker()

        # Add some usage
        tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)

        report = tracker.generate_report()

        # Check export data structure
        assert "usage_history" in report.export_data
        assert "pricing_config" in report.export_data
        assert len(report.export_data["usage_history"]) == 1
        assert "gpt-4o-mini" in report.export_data["pricing_config"]

    def test_usage_history_limit_in_context(self):
        """Test that only last 50 usage records are saved to context."""
        tracker = TokenTracker()

        # Add more than 50 usage records
        for i in range(60):
            tracker.track_usage("test", "test", "gpt-4o-mini", 100, 50)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            context_file = f.name

        try:
            tracker.save_usage_to_context(context_file)

            # Verify only last 50 records are saved
            with open(context_file) as f:
                data = yaml.safe_load(f)

            assert data is not None
            assert "metadata" in data
            assert "token_usage" in data["metadata"]
            usage_history = data["metadata"]["token_usage"]["usage_history"]
            assert len(usage_history) == 50

        finally:
            Path(context_file).unlink(missing_ok=True)

    def test_timestamp_parsing_in_load(self):
        """Test timestamp parsing when loading from context."""
        tracker = TokenTracker()

        # Create context with string timestamp
        usage_data = {
            "metadata": {
                "token_usage": {
                    "usage_history": [
                        {
                            "timestamp": "2024-01-01T12:00:00",
                            "service": "test",
                            "operation": "test",
                            "model": "gpt-4o-mini",
                            "prompt_tokens": 100,
                            "completion_tokens": 50,
                            "total_tokens": 150,
                            "cost_usd": 0.0003,
                            "input_text_length": 0,
                            "output_text_length": 0,
                        },
                    ],
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            context_file = f.name
            yaml.dump(usage_data, f)

        try:
            tracker.load_usage_from_context(context_file)

            # Verify timestamp was parsed correctly
            assert len(tracker.usage_history) == 1
            assert isinstance(tracker.usage_history[0].timestamp, datetime)
            assert tracker.usage_history[0].timestamp.year == 2024

        finally:
            Path(context_file).unlink(missing_ok=True)
