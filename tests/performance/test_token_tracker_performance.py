"""Performance tests for token tracking functionality."""

import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jestir.services.token_tracker import TokenTracker


class TestTokenTrackerPerformance:
    """Performance tests for TokenTracker."""

    def test_large_usage_history_performance(self):
        """Test performance with large usage history."""
        tracker = TokenTracker()

        # Add 10,000 usage records
        start_time = time.time()

        for i in range(10000):
            tracker.track_usage(
                service=f"service_{i % 100}",
                operation=f"operation_{i % 50}",
                model="gpt-4o-mini",
                prompt_tokens=100 + (i % 1000),
                completion_tokens=50 + (i % 500),
                input_text=f"input text {i}",
                output_text=f"output text {i}",
            )

        add_time = time.time() - start_time

        # Should add 10,000 records quickly (within 2 seconds)
        assert add_time < 2.0
        assert len(tracker.usage_history) == 10000

        # Test summary generation performance
        start_time = time.time()
        summary = tracker.get_usage_summary()
        summary_time = time.time() - start_time

        # Should generate summary quickly (within 1 second)
        assert summary_time < 1.0
        assert summary.total_tokens > 0
        assert summary.total_calls == 10000

    def test_usage_summary_grouping_performance(self):
        """Test performance of usage summary grouping operations."""
        tracker = TokenTracker()

        # Add diverse usage data
        services = [f"service_{i}" for i in range(100)]
        operations = [f"operation_{i}" for i in range(50)]
        models = ["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo"]

        for i in range(5000):
            tracker.track_usage(
                service=services[i % len(services)],
                operation=operations[i % len(operations)],
                model=models[i % len(models)],
                prompt_tokens=100 + (i % 1000),
                completion_tokens=50 + (i % 500),
            )

        # Test summary generation with grouping
        start_time = time.time()
        summary = tracker.get_usage_summary()
        summary_time = time.time() - start_time

        # Should complete within reasonable time
        assert summary_time < 0.5
        assert len(summary.by_service) == 100
        assert len(summary.by_operation) == 50
        assert len(summary.by_model) == 4

    def test_date_filtering_performance(self):
        """Test performance of date filtering operations."""
        tracker = TokenTracker()

        # Add usage data over 365 days
        base_date = datetime(2023, 1, 1, tzinfo=timezone.utc)
        for i in range(365):
            usage = tracker.track_usage(
                service="test_service",
                operation="test_operation",
                model="gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
            )
            usage.timestamp = base_date + timedelta(days=i)

        # Test date filtering performance
        start_time = time.time()

        # Filter by year
        year_summary = tracker.get_usage_summary(
            start_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2023, 12, 31, tzinfo=timezone.utc),
        )

        # Filter by month
        month_summary = tracker.get_usage_summary(
            start_date=datetime(2023, 6, 1, tzinfo=timezone.utc),
            end_date=datetime(2023, 6, 30, tzinfo=timezone.utc),
        )

        # Filter by week
        week_summary = tracker.get_usage_summary(
            start_date=datetime(2023, 6, 1, tzinfo=timezone.utc),
            end_date=datetime(2023, 6, 7, tzinfo=timezone.utc),
        )

        filter_time = time.time() - start_time

        # Should complete filtering quickly (within 0.5 seconds)
        assert filter_time < 0.5
        assert year_summary.total_calls == 365
        assert month_summary.total_calls == 30
        assert week_summary.total_calls == 7

    def test_optimization_suggestions_performance(self):
        """Test performance of optimization suggestions generation."""
        tracker = TokenTracker()

        # Add high-cost usage to trigger suggestions
        for i in range(1000):
            tracker.track_usage(
                service="expensive_service",
                operation="expensive_operation",
                model="gpt-4o",
                prompt_tokens=2000,
                completion_tokens=1000,
            )

        summary = tracker.get_usage_summary()

        # Test optimization suggestions performance
        start_time = time.time()
        suggestions = tracker.generate_optimization_suggestions(summary)
        suggestions_time = time.time() - start_time

        # Should generate suggestions quickly (within 0.2 seconds)
        assert suggestions_time < 0.2
        assert len(suggestions) > 0

    def test_report_generation_performance(self):
        """Test performance of report generation."""
        tracker = TokenTracker()

        # Add diverse usage data
        for i in range(2000):
            tracker.track_usage(
                service=f"service_{i % 20}",
                operation=f"operation_{i % 10}",
                model="gpt-4o-mini",
                prompt_tokens=100 + (i % 500),
                completion_tokens=50 + (i % 250),
            )

        # Test report generation performance
        start_time = time.time()
        report = tracker.generate_report(period="monthly")
        report_time = time.time() - start_time

        # Should generate report quickly (within 0.5 seconds)
        assert report_time < 0.5
        assert report.summary.total_calls == 2000
        assert len(report.top_operations) > 0
        assert len(report.cost_trends) > 0

    def test_context_save_load_performance(self):
        """Test performance of context save/load operations."""
        tracker = TokenTracker()

        # Add usage data
        for i in range(1000):
            tracker.track_usage(
                service=f"service_{i % 10}",
                operation=f"operation_{i % 5}",
                model="gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
            )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            context_file = f.name

        try:
            # Test save performance
            start_time = time.time()
            tracker.save_usage_to_context(context_file)
            save_time = time.time() - start_time

            # Should save quickly (within 0.5 seconds)
            assert save_time < 0.5

            # Test load performance
            new_tracker = TokenTracker()
            start_time = time.time()
            new_tracker.load_usage_from_context(context_file)
            load_time = time.time() - start_time

            # Should load quickly (within 0.3 seconds)
            assert load_time < 0.3
            # Only last 50 records are saved to context file
            assert len(new_tracker.usage_history) == 50

        finally:
            Path(context_file).unlink(missing_ok=True)

    def test_export_performance(self):
        """Test performance of export operations."""
        tracker = TokenTracker()

        # Add usage data
        for i in range(1000):
            tracker.track_usage(
                service=f"service_{i % 10}",
                operation=f"operation_{i % 5}",
                model="gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
            )

        report = tracker.generate_report()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json_file = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml_file = f.name

        try:
            # Test JSON export performance
            start_time = time.time()
            tracker.export_report(report, json_file)
            json_export_time = time.time() - start_time

            # Should export JSON quickly (within 0.3 seconds)
            assert json_export_time < 0.3

            # Test YAML export performance
            start_time = time.time()
            tracker.export_report(report, yaml_file)
            yaml_export_time = time.time() - start_time

            # Should export YAML quickly (within 0.3 seconds)
            assert yaml_export_time < 0.3

        finally:
            Path(json_file).unlink(missing_ok=True)
            Path(yaml_file).unlink(missing_ok=True)

    def test_memory_usage_large_dataset(self):
        """Test memory usage with large dataset."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        tracker = TokenTracker()

        # Add 50,000 usage records
        for i in range(50000):
            tracker.track_usage(
                service=f"service_{i % 1000}",
                operation=f"operation_{i % 100}",
                model="gpt-4o-mini",
                prompt_tokens=100 + (i % 1000),
                completion_tokens=50 + (i % 500),
                input_text=f"input text {i}" * 10,  # Longer text
                output_text=f"output text {i}" * 10,
            )

        peak_memory = process.memory_info().rss
        memory_increase = peak_memory - initial_memory

        # Memory increase should be reasonable (less than 500MB)
        assert memory_increase < 500 * 1024 * 1024  # 500MB in bytes

        # Test that operations still work efficiently
        start_time = time.time()
        summary = tracker.get_usage_summary()
        summary_time = time.time() - start_time

        assert summary_time < 1.0
        assert summary.total_calls == 50000

    def test_concurrent_usage_tracking(self):
        """Test performance with concurrent usage tracking simulation."""
        import queue
        import threading

        tracker = TokenTracker()
        results = queue.Queue()

        def track_usage_batch(start_idx, count):
            """Track a batch of usage records."""
            for i in range(start_idx, start_idx + count):
                usage = tracker.track_usage(
                    service=f"service_{i % 100}",
                    operation=f"operation_{i % 50}",
                    model="gpt-4o-mini",
                    prompt_tokens=100 + (i % 1000),
                    completion_tokens=50 + (i % 500),
                )
                results.put(usage)

        # Create multiple threads to simulate concurrent usage
        threads = []
        batch_size = 1000
        num_threads = 5

        start_time = time.time()

        for i in range(num_threads):
            thread = threading.Thread(
                target=track_usage_batch,
                args=(i * batch_size, batch_size),
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Should complete within reasonable time (within 3 seconds)
        assert total_time < 3.0
        assert results.qsize() == num_threads * batch_size

        # Verify all usage records were tracked
        assert len(tracker.usage_history) == num_threads * batch_size

    def test_weekly_monthly_grouping_performance(self):
        """Test performance of weekly and monthly grouping operations."""
        tracker = TokenTracker()

        # Add usage data over 2 years
        base_date = datetime(2022, 1, 1, tzinfo=timezone.utc)
        for i in range(730):  # 2 years
            usage = tracker.track_usage(
                service="test_service",
                operation="test_operation",
                model="gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
            )
            usage.timestamp = base_date + timedelta(days=i)

        # Test weekly grouping performance
        start_time = time.time()
        summary = tracker.get_usage_summary()
        grouping_time = time.time() - start_time

        # Should complete grouping quickly (within 0.5 seconds)
        assert grouping_time < 0.5
        assert len(summary.weekly_usage) > 0
        assert len(summary.monthly_usage) > 0

        # Verify grouping accuracy
        total_weekly_calls = sum(
            data["total_calls"] for data in summary.weekly_usage.values()
        )
        total_monthly_calls = sum(
            data["total_calls"] for data in summary.monthly_usage.values()
        )

        assert total_weekly_calls == 730
        assert total_monthly_calls == 730

    def test_cost_calculation_performance(self):
        """Test performance of cost calculation operations."""
        tracker = TokenTracker()

        # Add usage data with different models
        models = ["gpt-4o-mini", "gpt-4o", "gpt-4", "gpt-3.5-turbo"]

        for i in range(10000):
            tracker.track_usage(
                service="test_service",
                operation="test_operation",
                model=models[i % len(models)],
                prompt_tokens=1000 + (i % 5000),
                completion_tokens=500 + (i % 2500),
            )

        # Test cost calculation performance
        start_time = time.time()
        summary = tracker.get_usage_summary()
        cost_time = time.time() - start_time

        # Should calculate costs quickly (within 0.3 seconds)
        assert cost_time < 0.3
        assert summary.total_cost_usd > 0

        # Verify cost calculation accuracy
        total_cost = sum(u.cost_usd for u in tracker.usage_history)
        assert abs(summary.total_cost_usd - total_cost) < 0.0001

    def test_usage_history_limit_performance(self):
        """Test performance with usage history limit in context saving."""
        tracker = TokenTracker()

        # Add more than 50 usage records (the limit for context saving)
        for i in range(1000):
            tracker.track_usage(
                service="test_service",
                operation="test_operation",
                model="gpt-4o-mini",
                prompt_tokens=100,
                completion_tokens=50,
            )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            context_file = f.name

        try:
            # Test save performance with history limit
            start_time = time.time()
            tracker.save_usage_to_context(context_file)
            save_time = time.time() - start_time

            # Should save quickly even with history limit (within 0.2 seconds)
            assert save_time < 0.2

        finally:
            Path(context_file).unlink(missing_ok=True)
