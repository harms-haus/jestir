"""Template processing monitoring and metrics collection service."""

import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TemplateMetrics:
    """Template processing metrics."""

    template_path: str
    processing_time_ms: float
    template_size_bytes: int
    variable_count: int
    success: bool
    error_type: str | None = None
    error_message: str | None = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class PerformanceThresholds:
    """Performance thresholds for monitoring."""

    max_processing_time_ms: float = 1000.0  # 1 second
    max_template_size_bytes: int = 100000  # 100KB
    max_variable_count: int = 100
    max_error_rate: float = 0.05  # 5%


class TemplateMonitor:
    """Monitor template processing performance and collect metrics."""

    def __init__(self, max_history: int = 1000):
        """Initialize the template monitor."""
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.error_counts: dict[str, int] = defaultdict(int)
        self.performance_stats: dict[str, Any] = {}
        self.thresholds = PerformanceThresholds()

        # Performance tracking
        self._processing_times: dict[str, list[float]] = defaultdict(list)
        self._template_sizes: dict[str, list[int]] = defaultdict(list)
        self._error_rates: dict[str, float] = defaultdict(float)

    def record_metrics(self, metrics: TemplateMetrics) -> None:
        """Record template processing metrics."""
        self.metrics_history.append(metrics)

        # Update error counts
        if not metrics.success and metrics.error_type:
            self.error_counts[metrics.error_type] += 1

        # Update performance tracking
        template_key = str(Path(metrics.template_path).name)
        self._processing_times[template_key].append(metrics.processing_time_ms)
        self._template_sizes[template_key].append(metrics.template_size_bytes)

        # Keep only recent data (last 100 entries per template)
        if len(self._processing_times[template_key]) > 100:
            self._processing_times[template_key] = self._processing_times[template_key][
                -100:
            ]
        if len(self._template_sizes[template_key]) > 100:
            self._template_sizes[template_key] = self._template_sizes[template_key][
                -100:
            ]

        # Update error rates
        recent_metrics = list(self.metrics_history)[-100:]  # Last 100 metrics
        if recent_metrics:
            error_count = sum(1 for m in recent_metrics if not m.success)
            self._error_rates[template_key] = error_count / len(recent_metrics)

        logger.debug(
            f"Recorded metrics for {metrics.template_path}: {metrics.processing_time_ms:.2f}ms",
        )

    def get_performance_summary(self) -> dict[str, Any]:
        """Get overall performance summary."""
        if not self.metrics_history:
            return {"status": "no_data", "message": "No metrics recorded yet"}

        recent_metrics = list(self.metrics_history)[-100:]  # Last 100 metrics

        # Calculate overall statistics
        total_metrics = len(recent_metrics)
        successful_metrics = [m for m in recent_metrics if m.success]
        failed_metrics = [m for m in recent_metrics if not m.success]

        success_rate = (
            len(successful_metrics) / total_metrics if total_metrics > 0 else 0
        )
        avg_processing_time = (
            sum(m.processing_time_ms for m in successful_metrics)
            / len(successful_metrics)
            if successful_metrics
            else 0
        )
        avg_template_size = (
            sum(m.template_size_bytes for m in recent_metrics) / total_metrics
        )
        avg_variable_count = (
            sum(m.variable_count for m in recent_metrics) / total_metrics
        )

        # Check for performance issues
        performance_issues = []
        if success_rate < (1 - self.thresholds.max_error_rate):
            performance_issues.append(f"High error rate: {success_rate:.1%}")
        if avg_processing_time > self.thresholds.max_processing_time_ms:
            performance_issues.append(
                f"Slow processing: {avg_processing_time:.1f}ms avg",
            )
        if avg_template_size > self.thresholds.max_template_size_bytes:
            performance_issues.append(
                f"Large templates: {avg_template_size:.0f} bytes avg",
            )
        if avg_variable_count > self.thresholds.max_variable_count:
            performance_issues.append(f"Many variables: {avg_variable_count:.1f} avg")

        return {
            "status": "healthy" if not performance_issues else "degraded",
            "total_metrics": total_metrics,
            "success_rate": success_rate,
            "average_processing_time_ms": avg_processing_time,
            "average_template_size_bytes": avg_template_size,
            "average_variable_count": avg_variable_count,
            "performance_issues": performance_issues,
            "error_counts": dict(self.error_counts),
            "thresholds": {
                "max_processing_time_ms": self.thresholds.max_processing_time_ms,
                "max_template_size_bytes": self.thresholds.max_template_size_bytes,
                "max_variable_count": self.thresholds.max_variable_count,
                "max_error_rate": self.thresholds.max_error_rate,
            },
        }

    def get_template_performance(self, template_path: str) -> dict[str, Any]:
        """Get performance metrics for a specific template."""
        template_key = str(Path(template_path).name)
        template_metrics = [
            m
            for m in self.metrics_history
            if str(Path(m.template_path).name) == template_key
        ]

        if not template_metrics:
            return {
                "status": "no_data",
                "message": f"No metrics for template: {template_path}",
            }

        recent_metrics = template_metrics[-50:]  # Last 50 metrics for this template
        successful_metrics = [m for m in recent_metrics if m.success]

        if not successful_metrics:
            return {
                "status": "error",
                "message": "No successful processing for this template",
                "error_rate": 1.0,
                "total_attempts": len(recent_metrics),
            }

        success_rate = len(successful_metrics) / len(recent_metrics)
        avg_processing_time = sum(
            m.processing_time_ms for m in successful_metrics
        ) / len(successful_metrics)
        avg_template_size = sum(m.template_size_bytes for m in recent_metrics) / len(
            recent_metrics,
        )
        avg_variable_count = sum(m.variable_count for m in recent_metrics) / len(
            recent_metrics,
        )

        # Performance trends
        processing_times = self._processing_times.get(template_key, [])
        if len(processing_times) >= 10:
            recent_avg = sum(processing_times[-10:]) / 10
            older_avg = (
                sum(processing_times[-20:-10]) / 10
                if len(processing_times) >= 20
                else recent_avg
            )
            trend = (
                "improving"
                if recent_avg < older_avg
                else "degrading"
                if recent_avg > older_avg
                else "stable"
            )
        else:
            trend = "insufficient_data"

        return {
            "status": "healthy"
            if success_rate > 0.95
            and avg_processing_time < self.thresholds.max_processing_time_ms
            else "degraded",
            "template_path": template_path,
            "total_metrics": len(recent_metrics),
            "success_rate": success_rate,
            "average_processing_time_ms": avg_processing_time,
            "average_template_size_bytes": avg_template_size,
            "average_variable_count": avg_variable_count,
            "performance_trend": trend,
            "error_rate": self._error_rates.get(template_key, 0.0),
        }

    def get_error_analysis(self) -> dict[str, Any]:
        """Get detailed error analysis."""
        if not self.metrics_history:
            return {"status": "no_data", "message": "No metrics recorded yet"}

        recent_metrics = list(self.metrics_history)[-100:]  # Last 100 metrics
        failed_metrics = [m for m in recent_metrics if not m.success]

        if not failed_metrics:
            return {
                "status": "healthy",
                "message": "No errors in recent processing",
                "total_metrics": len(recent_metrics),
                "error_rate": 0.0,
            }

        # Analyze error patterns
        error_types: dict[str, int] = defaultdict(int)
        error_templates: dict[str, int] = defaultdict(int)

        for metric in failed_metrics:
            if metric.error_type:
                error_types[metric.error_type] += 1
            error_templates[str(Path(metric.template_path).name)] += 1

        # Most common errors
        most_common_errors = sorted(
            error_types.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]
        most_problematic_templates = sorted(
            error_templates.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        return {
            "status": "issues_detected",
            "total_metrics": len(recent_metrics),
            "failed_metrics": len(failed_metrics),
            "error_rate": len(failed_metrics) / len(recent_metrics),
            "most_common_errors": most_common_errors,
            "most_problematic_templates": most_problematic_templates,
            "error_counts": dict(self.error_counts),
        }

    def get_memory_usage_analysis(self) -> dict[str, Any]:
        """Get memory usage analysis for large templates."""
        if not self.metrics_history:
            return {"status": "no_data", "message": "No metrics recorded yet"}

        recent_metrics = list(self.metrics_history)[-100:]  # Last 100 metrics

        # Analyze template sizes
        template_sizes = [m.template_size_bytes for m in recent_metrics]
        large_templates = [
            m
            for m in recent_metrics
            if m.template_size_bytes > self.thresholds.max_template_size_bytes
        ]

        if not template_sizes:
            return {"status": "no_data", "message": "No size data available"}

        max_size = max(template_sizes)
        avg_size = sum(template_sizes) / len(template_sizes)
        large_template_count = len(large_templates)

        # Memory usage trends
        size_trend = "stable"
        if len(template_sizes) >= 20:
            recent_avg = sum(template_sizes[-10:]) / 10
            older_avg = sum(template_sizes[-20:-10]) / 20
            if recent_avg > older_avg * 1.1:
                size_trend = "increasing"
            elif recent_avg < older_avg * 0.9:
                size_trend = "decreasing"

        return {
            "status": "healthy" if large_template_count == 0 else "attention_needed",
            "total_templates": len(recent_metrics),
            "large_templates": large_template_count,
            "max_template_size_bytes": max_size,
            "average_template_size_bytes": avg_size,
            "size_trend": size_trend,
            "large_template_threshold": self.thresholds.max_template_size_bytes,
            "large_templates_list": [
                {
                    "template": str(Path(m.template_path).name),
                    "size_bytes": m.template_size_bytes,
                    "variable_count": m.variable_count,
                }
                for m in large_templates[:10]  # Top 10 largest
            ],
        }

    def export_metrics(self, file_path: str) -> None:
        """Export metrics to JSON file."""
        metrics_data = {
            "export_timestamp": time.time(),
            "total_metrics": len(self.metrics_history),
            "performance_summary": self.get_performance_summary(),
            "error_analysis": self.get_error_analysis(),
            "memory_analysis": self.get_memory_usage_analysis(),
            "recent_metrics": [
                {
                    "template_path": m.template_path,
                    "processing_time_ms": m.processing_time_ms,
                    "template_size_bytes": m.template_size_bytes,
                    "variable_count": m.variable_count,
                    "success": m.success,
                    "error_type": m.error_type,
                    "timestamp": m.timestamp,
                }
                for m in list(self.metrics_history)[-50:]  # Last 50 metrics
            ],
        }

        with open(file_path, "w") as f:
            json.dump(metrics_data, f, indent=2)

        logger.info(f"Exported {len(self.metrics_history)} metrics to {file_path}")

    def clear_metrics(self) -> None:
        """Clear all stored metrics."""
        self.metrics_history.clear()
        self.error_counts.clear()
        self._processing_times.clear()
        self._template_sizes.clear()
        self._error_rates.clear()
        logger.info("Cleared all template processing metrics")

    def set_thresholds(self, thresholds: PerformanceThresholds) -> None:
        """Update performance thresholds."""
        self.thresholds = thresholds
        logger.info(f"Updated performance thresholds: {thresholds}")


class _GlobalMonitorManager:
    """Manages the global template monitor instance."""

    def __init__(self):
        self._monitor: TemplateMonitor | None = None

    def get_monitor(self) -> TemplateMonitor:
        """Get the global template monitor instance."""
        if self._monitor is None:
            self._monitor = TemplateMonitor()
        return self._monitor


# Global monitor manager instance
_monitor_manager = _GlobalMonitorManager()


def get_global_monitor() -> TemplateMonitor:
    """Get the global template monitor instance."""
    return _monitor_manager.get_monitor()


def record_template_metrics(
    template_path: str,
    processing_time_ms: float,
    template_size_bytes: int,
    variable_count: int,
    success: bool,
    error_type: str | None = None,
    error_message: str | None = None,
) -> None:
    """Record template processing metrics using the global monitor."""
    monitor = get_global_monitor()
    metrics = TemplateMetrics(
        template_path=template_path,
        processing_time_ms=processing_time_ms,
        template_size_bytes=template_size_bytes,
        variable_count=variable_count,
        success=success,
        error_type=error_type,
        error_message=error_message,
    )
    monitor.record_metrics(metrics)
