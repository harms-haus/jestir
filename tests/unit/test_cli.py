"""Unit tests for CLI functionality."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner
from jestir.cli import main


class TestCLI:
    """Test cases for CLI commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_main_group(self):
        """Test main CLI group."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Jestir: AI-powered bedtime story generator" in result.output

    def test_context_command_help(self):
        """Test context command help."""
        result = self.runner.invoke(main, ["context", "--help"])
        assert result.exit_code == 0
        assert "Generate context from natural language input" in result.output

    def test_context_command_basic(self):
        """Test basic context command execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_context.yaml")

            result = self.runner.invoke(
                main,
                [
                    "context",
                    "Arthur visits the enchanted forest",
                    "--output",
                    output_file,
                ],
            )

            # Should succeed even without OpenAI key (uses fallback)
            assert result.exit_code == 0
            assert "Context generated successfully" in result.output
            assert os.path.exists(output_file)

    def test_context_command_with_custom_output(self):
        """Test context command with custom output file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "custom_context.yaml")

            result = self.runner.invoke(
                main,
                [
                    "context",
                    "A brave knight named Arthur goes to find a magical sword",
                    "--output",
                    output_file,
                ],
            )

            assert result.exit_code == 0
            assert os.path.exists(output_file)

            # Check that the file contains YAML content
            with open(output_file, "r") as f:
                content = f.read()
                assert "metadata" in content
                assert "entities" in content
                assert "relationships" in content

    def test_outline_command_help(self):
        """Test outline command help."""
        result = self.runner.invoke(main, ["outline", "--help"])
        assert result.exit_code == 0
        assert "Generate story outline from context file" in result.output

    def test_write_command_help(self):
        """Test write command help."""
        result = self.runner.invoke(main, ["write", "--help"])
        assert result.exit_code == 0
        assert "Generate final story from outline file" in result.output

    def test_context_command_missing_input(self):
        """Test context command with missing input."""
        result = self.runner.invoke(main, ["context"])
        assert result.exit_code != 0  # Should fail due to missing required argument

    @patch.dict("os.environ", {"OPENAI_EXTRACTION_API_KEY": "test-key"})
    def test_context_command_with_api_key(self):
        """Test context command with API key set."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_context.yaml")

            result = self.runner.invoke(
                main,
                [
                    "context",
                    "Arthur visits the enchanted forest",
                    "--output",
                    output_file,
                ],
            )

            assert result.exit_code == 0
            assert "Warning" not in result.output  # No warning about missing API key
