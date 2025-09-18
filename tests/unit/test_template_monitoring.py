"""Tests for template monitoring and metrics collection."""

import os
import tempfile

from jestir.services.template_loader import TemplateLoader
from jestir.services.template_monitor import (
    PerformanceThresholds,
    TemplateMetrics,
    TemplateMonitor,
)


class TestTemplateMonitor:
    """Test template monitoring functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.monitor = TemplateMonitor(max_history=100)
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_record_metrics(self):
        """Test recording template processing metrics."""
        metrics = TemplateMetrics(
            template_path="test_template.txt",
            processing_time_ms=150.5,
            template_size_bytes=1024,
            variable_count=5,
            success=True,
        )

        self.monitor.record_metrics(metrics)

        assert len(self.monitor.metrics_history) == 1
        assert self.monitor.metrics_history[0].template_path == "test_template.txt"
        assert self.monitor.metrics_history[0].processing_time_ms == 150.5
        assert self.monitor.metrics_history[0].success is True

    def test_record_failed_metrics(self):
        """Test recording failed template processing metrics."""
        metrics = TemplateMetrics(
            template_path="broken_template.txt",
            processing_time_ms=50.0,
            template_size_bytes=512,
            variable_count=3,
            success=False,
            error_type="FileNotFoundError",
            error_message="Template file not found",
        )

        self.monitor.record_metrics(metrics)

        assert len(self.monitor.metrics_history) == 1
        assert self.monitor.metrics_history[0].success is False
        assert self.monitor.error_counts["FileNotFoundError"] == 1

    def test_performance_summary_no_data(self):
        """Test performance summary with no data."""
        summary = self.monitor.get_performance_summary()

        assert summary["status"] == "no_data"
        assert "No metrics recorded yet" in summary["message"]

    def test_performance_summary_with_data(self):
        """Test performance summary with metrics data."""
        # Record some successful metrics
        for i in range(10):
            metrics = TemplateMetrics(
                template_path=f"template_{i}.txt",
                processing_time_ms=100.0 + i * 10,
                template_size_bytes=1000 + i * 100,
                variable_count=5 + i,
                success=True,
            )
            self.monitor.record_metrics(metrics)

        summary = self.monitor.get_performance_summary()

        assert summary["status"] == "healthy"
        assert summary["total_metrics"] == 10
        assert summary["success_rate"] == 1.0
        assert summary["average_processing_time_ms"] > 0
        assert summary["average_template_size_bytes"] > 0
        assert summary["average_variable_count"] > 0

    def test_performance_summary_with_issues(self):
        """Test performance summary with performance issues."""
        # Record metrics that exceed thresholds
        for i in range(5):
            metrics = TemplateMetrics(
                template_path=f"large_template_{i}.txt",
                processing_time_ms=2000.0,  # Exceeds 1000ms threshold
                template_size_bytes=150000,  # Exceeds 100KB threshold
                variable_count=150,  # Exceeds 100 variable threshold
                success=True,
            )
            self.monitor.record_metrics(metrics)

        summary = self.monitor.get_performance_summary()

        assert summary["status"] == "degraded"
        assert len(summary["performance_issues"]) > 0
        assert any(
            "Slow processing" in issue for issue in summary["performance_issues"]
        )
        assert any(
            "Large templates" in issue for issue in summary["performance_issues"]
        )
        assert any("Many variables" in issue for issue in summary["performance_issues"])

    def test_template_performance_specific_template(self):
        """Test getting performance metrics for a specific template."""
        # Record metrics for a specific template
        for i in range(5):
            metrics = TemplateMetrics(
                template_path="test_template.txt",
                processing_time_ms=100.0 + i * 10,
                template_size_bytes=1000 + i * 100,
                variable_count=5 + i,
                success=True,
            )
            self.monitor.record_metrics(metrics)

        # Record metrics for different template
        for i in range(3):
            metrics = TemplateMetrics(
                template_path="other_template.txt",
                processing_time_ms=200.0,
                template_size_bytes=2000,
                variable_count=10,
                success=True,
            )
            self.monitor.record_metrics(metrics)

        template_metrics = self.monitor.get_template_performance("test_template.txt")

        assert template_metrics["status"] == "healthy"
        assert template_metrics["total_metrics"] == 5
        assert template_metrics["success_rate"] == 1.0
        assert template_metrics["template_path"] == "test_template.txt"

    def test_template_performance_no_data(self):
        """Test getting performance metrics for non-existent template."""
        template_metrics = self.monitor.get_template_performance("nonexistent.txt")

        assert template_metrics["status"] == "no_data"
        assert "No metrics for template" in template_metrics["message"]

    def test_error_analysis_no_errors(self):
        """Test error analysis with no errors."""
        # Record only successful metrics
        for i in range(10):
            metrics = TemplateMetrics(
                template_path=f"template_{i}.txt",
                processing_time_ms=100.0,
                template_size_bytes=1000,
                variable_count=5,
                success=True,
            )
            self.monitor.record_metrics(metrics)

        error_analysis = self.monitor.get_error_analysis()

        assert error_analysis["status"] == "healthy"
        assert error_analysis["error_rate"] == 0.0
        assert "No errors in recent processing" in error_analysis["message"]

    def test_error_analysis_with_errors(self):
        """Test error analysis with errors."""
        # Record mix of successful and failed metrics
        for i in range(8):
            metrics = TemplateMetrics(
                template_path=f"template_{i}.txt",
                processing_time_ms=100.0,
                template_size_bytes=1000,
                variable_count=5,
                success=True,
            )
            self.monitor.record_metrics(metrics)

        # Record some failed metrics
        for i in range(2):
            metrics = TemplateMetrics(
                template_path=f"broken_template_{i}.txt",
                processing_time_ms=50.0,
                template_size_bytes=500,
                variable_count=3,
                success=False,
                error_type="FileNotFoundError",
                error_message="Template not found",
            )
            self.monitor.record_metrics(metrics)

        error_analysis = self.monitor.get_error_analysis()

        assert error_analysis["status"] == "issues_detected"
        assert error_analysis["error_rate"] == 0.2  # 2 out of 10
        assert error_analysis["failed_metrics"] == 2
        assert "FileNotFoundError" in error_analysis["most_common_errors"][0][0]

    def test_memory_usage_analysis(self):
        """Test memory usage analysis."""
        # Record metrics with various template sizes
        sizes = [1000, 5000, 50000, 150000, 200000]  # Including some large ones

        for i, size in enumerate(sizes):
            metrics = TemplateMetrics(
                template_path=f"template_{i}.txt",
                processing_time_ms=100.0,
                template_size_bytes=size,
                variable_count=5,
                success=True,
            )
            self.monitor.record_metrics(metrics)

        memory_analysis = self.monitor.get_memory_usage_analysis()

        assert memory_analysis["status"] == "attention_needed"  # Due to large templates
        assert memory_analysis["total_templates"] == 5
        assert memory_analysis["large_templates"] == 2  # 150000 and 200000 bytes
        assert memory_analysis["max_template_size_bytes"] == 200000
        assert memory_analysis["average_template_size_bytes"] == 81200

    def test_export_metrics(self):
        """Test exporting metrics to JSON file."""
        # Record some metrics
        for i in range(5):
            metrics = TemplateMetrics(
                template_path=f"template_{i}.txt",
                processing_time_ms=100.0 + i * 10,
                template_size_bytes=1000 + i * 100,
                variable_count=5 + i,
                success=True,
            )
            self.monitor.record_metrics(metrics)

        export_file = os.path.join(self.temp_dir, "metrics.json")
        self.monitor.export_metrics(export_file)

        assert os.path.exists(export_file)

        # Verify file contents
        import json

        with open(export_file) as f:
            data = json.load(f)

        assert "export_timestamp" in data
        assert data["total_metrics"] == 5
        assert "performance_summary" in data
        assert "error_analysis" in data
        assert "memory_analysis" in data
        assert len(data["recent_metrics"]) == 5

    def test_clear_metrics(self):
        """Test clearing all metrics."""
        # Record some metrics
        for i in range(5):
            metrics = TemplateMetrics(
                template_path=f"template_{i}.txt",
                processing_time_ms=100.0,
                template_size_bytes=1000,
                variable_count=5,
                success=True,
            )
            self.monitor.record_metrics(metrics)

        assert len(self.monitor.metrics_history) == 5

        self.monitor.clear_metrics()

        assert len(self.monitor.metrics_history) == 0
        assert len(self.monitor.error_counts) == 0
        assert len(self.monitor._processing_times) == 0
        assert len(self.monitor._template_sizes) == 0

    def test_set_thresholds(self):
        """Test setting performance thresholds."""
        new_thresholds = PerformanceThresholds(
            max_processing_time_ms=500.0,
            max_template_size_bytes=50000,
            max_variable_count=50,
            max_error_rate=0.1,
        )

        self.monitor.set_thresholds(new_thresholds)

        assert self.monitor.thresholds.max_processing_time_ms == 500.0
        assert self.monitor.thresholds.max_template_size_bytes == 50000
        assert self.monitor.thresholds.max_variable_count == 50
        assert self.monitor.thresholds.max_error_rate == 0.1

    def test_max_history_limit(self):
        """Test that metrics history respects max_history limit."""
        # Create monitor with small history limit
        small_monitor = TemplateMonitor(max_history=3)

        # Record more metrics than the limit
        for i in range(5):
            metrics = TemplateMetrics(
                template_path=f"template_{i}.txt",
                processing_time_ms=100.0,
                template_size_bytes=1000,
                variable_count=5,
                success=True,
            )
            small_monitor.record_metrics(metrics)

        # Should only keep the last 3 metrics
        assert len(small_monitor.metrics_history) == 3
        assert small_monitor.metrics_history[0].template_path == "template_2.txt"
        assert small_monitor.metrics_history[-1].template_path == "template_4.txt"

    def test_performance_trends(self):
        """Test performance trend calculation."""
        # Record metrics with improving performance (need at least 20 for trend calculation)
        processing_times = [
            200.0,
            190.0,
            180.0,
            170.0,
            160.0,
            150.0,
            140.0,
            130.0,
            120.0,
            110.0,
            100.0,
            90.0,
            80.0,
            70.0,
            60.0,
            50.0,
            40.0,
            30.0,
            20.0,
            10.0,
        ]

        for i, time_ms in enumerate(processing_times):
            metrics = TemplateMetrics(
                template_path="test_template.txt",
                processing_time_ms=time_ms,
                template_size_bytes=1000,
                variable_count=5,
                success=True,
            )
            self.monitor.record_metrics(metrics)

        template_metrics = self.monitor.get_template_performance("test_template.txt")

        assert template_metrics["performance_trend"] == "improving"

    def test_integration_with_template_loader(self):
        """Test integration with template loader monitoring."""
        # Create a test template
        template_content = "Hello {{name}}! This is a {{genre}} story."
        template_path = os.path.join(self.temp_dir, "test_template.txt")

        with open(template_path, "w") as f:
            f.write(template_content)

        # Create template loader with monitoring
        loader = TemplateLoader()

        # Render template (should record metrics)
        context = {"name": "Alice", "genre": "adventure"}
        result = loader.render_template(template_path, context)

        # Verify rendering worked
        assert "Hello Alice!" in result
        assert "adventure story" in result

        # Check that metrics were recorded
        from jestir.services.template_monitor import get_global_monitor

        monitor = get_global_monitor()

        # Should have at least one metric recorded
        assert len(monitor.metrics_history) >= 1

        # Check the recorded metric
        latest_metric = monitor.metrics_history[-1]
        assert latest_metric.template_path == template_path
        assert latest_metric.success is True
        assert latest_metric.variable_count == 2
        assert latest_metric.template_size_bytes > 0
