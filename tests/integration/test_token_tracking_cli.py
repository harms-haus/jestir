"""Integration tests for token tracking CLI functionality."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from jestir.cli import main


class TestTokenTrackingCLI:
    """Integration tests for token tracking CLI commands."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.context_file = Path(self.temp_dir) / "test_context.yaml"

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_stats_command_no_context(self):
        """Test stats command with no context file."""
        result = self.runner.invoke(main, ["stats"])

        # Should not fail, but show empty stats
        assert result.exit_code == 0
        assert "📊 Token Usage Statistics" in result.output
        assert "Total Tokens: 0" in result.output

    def test_stats_command_with_context(self):
        """Test stats command with context file containing usage data."""
        # Create context file with token usage data
        context_data = {
            "metadata": {
                "token_usage": {
                    "total_tokens": 1500,
                    "total_cost_usd": 3.75,
                    "total_calls": 10,
                    "last_updated": "2025-09-17T12:00:00",
                    "usage_history": [
                        {
                            "timestamp": "2025-09-17T12:00:00",
                            "service": "context_generator",
                            "operation": "extract_entities",
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

        with open(self.context_file, "w") as f:
            yaml.dump(context_data, f)

        result = self.runner.invoke(
            main,
            ["stats", "--context", str(self.context_file)],
        )

        assert result.exit_code == 0
        assert "📊 Token Usage Statistics" in result.output
        assert "Total Tokens: 150" in result.output
        assert "Total Cost: $0.0003" in result.output
        assert "Total API Calls: 1" in result.output

    def test_stats_command_with_suggestions(self):
        """Test stats command with optimization suggestions."""
        # Create context with high-cost usage to trigger suggestions
        context_data = {
            "metadata": {
                "token_usage": {
                    "total_tokens": 10000,
                    "total_cost_usd": 25.0,
                    "total_calls": 5,
                    "last_updated": "2025-09-17T12:00:00",
                    "usage_history": [
                        {
                            "timestamp": "2025-09-17T12:00:00",
                            "service": "story_writer",
                            "operation": "generate_story",
                            "model": "gpt-4o",
                            "prompt_tokens": 2000,
                            "completion_tokens": 1000,
                            "total_tokens": 3000,
                            "cost_usd": 6.0,  # Above $5.0 threshold for gpt-4o suggestion
                            "input_text_length": 0,
                            "output_text_length": 0,
                        },
                    ],
                },
            },
        }

        with open(self.context_file, "w") as f:
            yaml.dump(context_data, f)

        result = self.runner.invoke(
            main,
            ["stats", "--context", str(self.context_file), "--suggestions"],
        )

        assert result.exit_code == 0
        assert "📊 Token Usage Statistics" in result.output
        assert "💡 Optimization Suggestions" in result.output
        assert "gpt-4o-mini" in result.output  # Should suggest cheaper model

    def test_stats_command_weekly_period(self):
        """Test stats command with weekly period."""
        # Create context with usage data
        context_data = {
            "metadata": {
                "token_usage": {
                    "total_tokens": 1000,
                    "total_cost_usd": 2.5,
                    "total_calls": 5,
                    "last_updated": "2025-09-17T12:00:00",
                    "usage_history": [
                        {
                            "timestamp": "2025-09-17T12:00:00",
                            "service": "story_writer",
                            "operation": "generate_story",
                            "model": "gpt-4o",
                            "prompt_tokens": 500,
                            "completion_tokens": 500,
                            "total_tokens": 1000,
                            "cost_usd": 2.5,
                            "input_text_length": 0,
                            "output_text_length": 0,
                        },
                    ],
                },
            },
        }

        with open(self.context_file, "w") as f:
            yaml.dump(context_data, f)

        result = self.runner.invoke(
            main,
            ["stats", "--context", str(self.context_file), "--period", "weekly"],
        )

        assert result.exit_code == 0
        assert "📊 Token Usage Statistics" in result.output
        assert "📈 Cost Trends" in result.output

    def test_stats_command_monthly_period(self):
        """Test stats command with monthly period."""
        # Create context with usage data
        context_data = {
            "metadata": {
                "token_usage": {
                    "total_tokens": 1000,
                    "total_cost_usd": 2.5,
                    "total_calls": 5,
                    "last_updated": "2025-09-17T12:00:00",
                    "usage_history": [
                        {
                            "timestamp": "2025-09-17T12:00:00",
                            "service": "story_writer",
                            "operation": "generate_story",
                            "model": "gpt-4o",
                            "prompt_tokens": 500,
                            "completion_tokens": 500,
                            "total_tokens": 1000,
                            "cost_usd": 2.5,
                            "input_text_length": 0,
                            "output_text_length": 0,
                        },
                    ],
                },
            },
        }

        with open(self.context_file, "w") as f:
            yaml.dump(context_data, f)

        result = self.runner.invoke(
            main,
            ["stats", "--context", str(self.context_file), "--period", "monthly"],
        )

        assert result.exit_code == 0
        assert "📊 Token Usage Statistics" in result.output
        assert "📈 Cost Trends" in result.output

    def test_stats_command_json_format(self):
        """Test stats command with JSON output format."""
        # Create context with usage data
        context_data = {
            "metadata": {
                "token_usage": {
                    "total_tokens": 1000,
                    "total_cost_usd": 2.5,
                    "total_calls": 5,
                    "last_updated": "2025-09-17T12:00:00",
                    "usage_history": [
                        {
                            "timestamp": "2025-09-17T12:00:00",
                            "service": "story_writer",
                            "operation": "generate_story",
                            "model": "gpt-4o",
                            "prompt_tokens": 500,
                            "completion_tokens": 500,
                            "total_tokens": 1000,
                            "cost_usd": 2.5,
                            "input_text_length": 0,
                            "output_text_length": 0,
                        },
                    ],
                },
            },
        }

        with open(self.context_file, "w") as f:
            yaml.dump(context_data, f)

        result = self.runner.invoke(
            main,
            ["stats", "--context", str(self.context_file), "--format", "json"],
        )

        assert result.exit_code == 0

        # Parse JSON output (skip the first line which is not JSON)
        output_lines = result.output.strip().split("\n")
        json_start = 0
        for i, line in enumerate(output_lines):
            if line.strip().startswith("{"):
                json_start = i
                break

        json_output = "\n".join(output_lines[json_start:])
        try:
            data = json.loads(json_output)
            assert "period" in data
            assert "summary" in data
            assert data["summary"]["total_tokens"] == 1000
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_stats_command_yaml_format(self):
        """Test stats command with YAML output format."""
        # Create context with usage data
        context_data = {
            "metadata": {
                "token_usage": {
                    "total_tokens": 1000,
                    "total_cost_usd": 2.5,
                    "total_calls": 5,
                    "last_updated": "2025-09-17T12:00:00",
                    "usage_history": [
                        {
                            "timestamp": "2025-09-17T12:00:00",
                            "service": "story_writer",
                            "operation": "generate_story",
                            "model": "gpt-4o",
                            "prompt_tokens": 500,
                            "completion_tokens": 500,
                            "total_tokens": 1000,
                            "cost_usd": 2.5,
                            "input_text_length": 0,
                            "output_text_length": 0,
                        },
                    ],
                },
            },
        }

        with open(self.context_file, "w") as f:
            yaml.dump(context_data, f)

        result = self.runner.invoke(
            main,
            ["stats", "--context", str(self.context_file), "--format", "yaml"],
        )

        assert result.exit_code == 0

        # Parse YAML output (skip the first line which is not YAML)
        output_lines = result.output.strip().split("\n")
        yaml_start = 0
        for i, line in enumerate(output_lines):
            if line.strip().startswith("period:") or line.strip().startswith("{"):
                yaml_start = i
                break

        yaml_output = "\n".join(output_lines[yaml_start:])
        try:
            data = yaml.safe_load(yaml_output)
            assert "period" in data
            assert "summary" in data
            assert data["summary"]["total_tokens"] == 1000
        except yaml.YAMLError:
            pytest.fail("Output is not valid YAML")

    def test_stats_command_export(self):
        """Test stats command with export functionality."""
        # Create context with usage data
        context_data = {
            "metadata": {
                "token_usage": {
                    "total_tokens": 1000,
                    "total_cost_usd": 2.5,
                    "total_calls": 5,
                    "last_updated": "2025-09-17T12:00:00",
                    "usage_history": [
                        {
                            "timestamp": "2025-09-17T12:00:00",
                            "service": "story_writer",
                            "operation": "generate_story",
                            "model": "gpt-4o",
                            "prompt_tokens": 500,
                            "completion_tokens": 500,
                            "total_tokens": 1000,
                            "cost_usd": 2.5,
                            "input_text_length": 0,
                            "output_text_length": 0,
                        },
                    ],
                },
            },
        }

        with open(self.context_file, "w") as f:
            yaml.dump(context_data, f)

        export_file = Path(self.temp_dir) / "export.json"

        result = self.runner.invoke(
            main,
            [
                "stats",
                "--context",
                str(self.context_file),
                "--export",
                str(export_file),
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0
        assert export_file.exists()

        # Verify exported file content
        with open(export_file) as f:
            data = json.load(f)

        assert "period" in data
        assert "summary" in data
        assert data["summary"]["total_tokens"] == 1000

    def test_stats_command_invalid_context_file(self):
        """Test stats command with invalid context file."""
        result = self.runner.invoke(
            main,
            ["stats", "--context", "/nonexistent/file.yaml"],
        )

        # Should not fail, but show empty stats
        assert result.exit_code == 0
        assert "📊 Token Usage Statistics" in result.output
        assert "Total Tokens: 0" in result.output

    def test_stats_command_malformed_context_file(self):
        """Test stats command with malformed context file."""
        # Create malformed YAML file
        with open(self.context_file, "w") as f:
            f.write("invalid: yaml: content: [")

        result = self.runner.invoke(
            main,
            ["stats", "--context", str(self.context_file)],
        )

        # Should not fail, but show empty stats
        assert result.exit_code == 0
        assert "📊 Token Usage Statistics" in result.output
        assert "Total Tokens: 0" in result.output

    def test_stats_command_context_without_usage_data(self):
        """Test stats command with context file that has no usage data."""
        # Create context file without token usage data
        context_data = {
            "metadata": {
                "other_data": "value",
            },
        }

        with open(self.context_file, "w") as f:
            yaml.dump(context_data, f)

        result = self.runner.invoke(
            main,
            ["stats", "--context", str(self.context_file)],
        )

        assert result.exit_code == 0
        assert "📊 Token Usage Statistics" in result.output
        assert "Total Tokens: 0" in result.output

    def test_stats_command_verbose_output(self):
        """Test stats command with verbose output."""
        # Create context with usage data
        context_data = {
            "metadata": {
                "token_usage": {
                    "total_tokens": 1000,
                    "total_cost_usd": 2.5,
                    "total_calls": 5,
                    "last_updated": "2025-09-17T12:00:00",
                    "usage_history": [
                        {
                            "timestamp": "2025-09-17T12:00:00",
                            "service": "context_generator",
                            "operation": "extract_entities",
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

        with open(self.context_file, "w") as f:
            yaml.dump(context_data, f)

        result = self.runner.invoke(
            main,
            ["--verbose", "stats", "--context", str(self.context_file)],
        )

        assert result.exit_code == 0
        assert "📊 Token Usage Statistics" in result.output
        assert "Total Tokens: 150" in result.output

    def test_stats_command_all_options(self):
        """Test stats command with all options."""
        # Create context with usage data
        context_data = {
            "metadata": {
                "token_usage": {
                    "total_tokens": 1000,
                    "total_cost_usd": 2.5,
                    "total_calls": 5,
                    "last_updated": "2025-09-17T12:00:00",
                    "usage_history": [],
                },
            },
        }

        with open(self.context_file, "w") as f:
            yaml.dump(context_data, f)

        export_file = Path(self.temp_dir) / "export.json"

        result = self.runner.invoke(
            main,
            [
                "stats",
                "--context",
                str(self.context_file),
                "--period",
                "weekly",
                "--format",
                "json",
                "--export",
                str(export_file),
                "--suggestions",
            ],
        )

        assert result.exit_code == 0
        assert export_file.exists()

        # Verify exported file content
        with open(export_file) as f:
            data = json.load(f)

        assert data["period"] == "weekly"
        assert "summary" in data
        assert "optimization_suggestions" in data

    def test_stats_command_help(self):
        """Test stats command help."""
        result = self.runner.invoke(main, ["stats", "--help"])

        assert result.exit_code == 0
        assert "Show token usage statistics" in result.output
        assert "--context" in result.output
        assert "--period" in result.output
        assert "--format" in result.output
        assert "--export" in result.output
        assert "--suggestions" in result.output

    def test_stats_command_invalid_period(self):
        """Test stats command with invalid period."""
        result = self.runner.invoke(main, ["stats", "--period", "invalid"])

        # Click exits with 2 for invalid choices
        assert result.exit_code == 2

    def test_stats_command_invalid_format(self):
        """Test stats command with invalid format."""
        result = self.runner.invoke(main, ["stats", "--format", "invalid"])

        # Click exits with 2 for invalid choices
        assert result.exit_code == 2

    def test_stats_command_export_directory_creation(self):
        """Test stats command creates export directory if it doesn't exist."""
        # Create context with usage data
        context_data = {
            "metadata": {
                "token_usage": {
                    "total_tokens": 1000,
                    "total_cost_usd": 2.5,
                    "total_calls": 5,
                    "last_updated": "2025-09-17T12:00:00",
                    "usage_history": [],
                },
            },
        }

        with open(self.context_file, "w") as f:
            yaml.dump(context_data, f)

        # Export to a path that requires directory creation
        export_file = Path(self.temp_dir) / "subdir" / "export.json"

        result = self.runner.invoke(
            main,
            [
                "stats",
                "--context",
                str(self.context_file),
                "--export",
                str(export_file),
            ],
        )

        assert result.exit_code == 0
        assert export_file.exists()
        assert export_file.parent.exists()

    def test_stats_command_large_dataset(self):
        """Test stats command with large dataset."""
        # Create context with many usage records
        usage_history = []
        for i in range(100):
            usage_history.append(
                {
                    "timestamp": f"2025-09-{(i % 30) + 1:02d}T12:00:00",
                    "service": f"service_{i % 5}",
                    "operation": f"operation_{i % 3}",
                    "model": "gpt-4o-mini",
                    "prompt_tokens": 100 + i,
                    "completion_tokens": 50 + i,
                    "total_tokens": 150 + i * 2,
                    "cost_usd": 0.0003 + i * 0.0001,
                    "input_text_length": 0,
                    "output_text_length": 0,
                },
            )

        context_data = {
            "metadata": {
                "token_usage": {
                    "total_tokens": sum(150 + i * 2 for i in range(100)),
                    "total_cost_usd": sum(0.0003 + i * 0.0001 for i in range(100)),
                    "total_calls": 100,
                    "last_updated": "2025-09-17T12:00:00",
                    "usage_history": usage_history,
                },
            },
        }

        with open(self.context_file, "w") as f:
            yaml.dump(context_data, f)

        result = self.runner.invoke(
            main,
            ["stats", "--context", str(self.context_file)],
        )

        assert result.exit_code == 0
        assert "📊 Token Usage Statistics" in result.output
        assert (
            "Total API Calls: 61" in result.output
        )  # Actual count after date filtering

    def test_stats_command_performance(self):
        """Test stats command performance with large dataset."""
        # Create context with many usage records
        usage_history = []
        for i in range(1000):
            usage_history.append(
                {
                    "timestamp": f"2025-09-{(i % 30) + 1:02d}T12:00:00",
                    "service": f"service_{i % 10}",
                    "operation": f"operation_{i % 5}",
                    "model": "gpt-4o-mini",
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                    "cost_usd": 0.0003,
                    "input_text_length": 0,
                    "output_text_length": 0,
                },
            )

        context_data = {
            "metadata": {
                "token_usage": {
                    "total_tokens": 150000,
                    "total_cost_usd": 0.3,
                    "total_calls": 1000,
                    "last_updated": "2025-09-17T12:00:00",
                    "usage_history": usage_history,
                },
            },
        }

        with open(self.context_file, "w") as f:
            yaml.dump(context_data, f)

        import time

        start_time = time.time()

        result = self.runner.invoke(
            main,
            ["stats", "--context", str(self.context_file)],
        )

        end_time = time.time()
        execution_time = end_time - start_time

        assert result.exit_code == 0
        assert "📊 Token Usage Statistics" in result.output
        assert (
            "Total API Calls: 571" in result.output
        )  # Actual count after date filtering
        # Should complete within reasonable time (5 seconds)
        assert execution_time < 5.0
