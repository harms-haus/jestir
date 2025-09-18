"""Unit tests for CLI functionality."""

import os
import tempfile
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
        assert (
            "Update existing context or create new one from natural language input"
            in result.output
        )

    def test_context_new_command_help(self):
        """Test context new command help."""
        result = self.runner.invoke(main, ["context-new", "--help"])
        assert result.exit_code == 0
        assert "Generate a new context from natural language input" in result.output

    def test_context_command_basic(self):
        """Test basic context command execution (creates new context when none exists)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory to avoid finding existing context.yaml
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            try:
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
            finally:
                os.chdir(original_cwd)

    def test_context_new_command_basic(self):
        """Test context new command execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_context.yaml")

            result = self.runner.invoke(
                main,
                [
                    "context-new",
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
            with open(output_file) as f:
                content = f.read()
                assert "metadata" in content
                assert "entities" in content
                assert "relationships" in content

    def test_context_command_updates_existing(self):
        """Test context command updates existing context file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create an initial context file
            initial_context_file = os.path.join(temp_dir, "context.yaml")
            result1 = self.runner.invoke(
                main,
                [
                    "context",
                    "Arthur visits the enchanted forest",
                    "--output",
                    initial_context_file,
                ],
            )
            assert result1.exit_code == 0
            assert "Context updated successfully" in result1.output

            # Update the context with new information
            result2 = self.runner.invoke(
                main,
                [
                    "context",
                    "Arthur finds a magical sword in the forest",
                    "--output",
                    initial_context_file,
                ],
            )
            assert result2.exit_code == 0
            assert "Context updated successfully" in result2.output

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

    def test_search_command_help(self):
        """Test search command help."""
        result = self.runner.invoke(main, ["search", "--help"])
        assert result.exit_code == 0
        assert "Search for entities in LightRAG API" in result.output

    def test_search_command_characters(self):
        """Test search command for characters."""
        with patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "true"}):
            result = self.runner.invoke(
                main,
                ["search", "characters", "--query", "dragon"],
            )
            assert result.exit_code == 0
            assert "Searching characters for: 'dragon'" in result.output
            assert "Purple Dragon" in result.output

    def test_search_command_locations(self):
        """Test search command for locations."""
        with patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "true"}):
            result = self.runner.invoke(
                main,
                ["search", "locations", "--query", "forest"],
            )
            assert result.exit_code == 0
            assert "Searching locations for: 'forest'" in result.output
            assert "Magic Forest" in result.output

    def test_search_command_with_pagination(self):
        """Test search command with pagination."""
        with patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "true"}):
            result = self.runner.invoke(
                main,
                [
                    "search",
                    "characters",
                    "--query",
                    "dragon",
                    "--page",
                    "1",
                    "--limit",
                    "5",
                ],
            )
            assert result.exit_code == 0
            assert "page 1 of" in result.output or "Found" in result.output

    def test_search_command_export_yaml(self):
        """Test search command with YAML export."""
        with tempfile.TemporaryDirectory() as temp_dir:
            export_file = os.path.join(temp_dir, "export.yaml")
            with patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "true"}):
                result = self.runner.invoke(
                    main,
                    [
                        "search",
                        "characters",
                        "--query",
                        "dragon",
                        "--export",
                        export_file,
                    ],
                )
                assert result.exit_code == 0
                assert os.path.exists(export_file)

                # Check that the exported file contains YAML content
                with open(export_file) as f:
                    content = f.read()
                    assert "entities:" in content
                    assert "Purple Dragon" in content

    def test_list_command_help(self):
        """Test list command help."""
        result = self.runner.invoke(main, ["list", "--help"])
        assert result.exit_code == 0
        assert "List entities from LightRAG API" in result.output

    def test_list_command_locations(self):
        """Test list command for locations."""
        with patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "true"}):
            result = self.runner.invoke(main, ["list", "locations"])
            assert result.exit_code == 0
            assert "Listing locations" in result.output
            assert "Magic Forest" in result.output

    def test_list_command_with_type_filter(self):
        """Test list command with type filtering."""
        with patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "true"}):
            result = self.runner.invoke(
                main,
                ["list", "locations", "--type", "interior"],
            )
            assert result.exit_code == 0
            assert "type 'interior'" in result.output

    def test_show_command_help(self):
        """Test show command help."""
        result = self.runner.invoke(main, ["show", "--help"])
        assert result.exit_code == 0
        assert "Show detailed information about a specific entity" in result.output

    def test_show_command_character(self):
        """Test show command for a character."""
        with patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "true"}):
            result = self.runner.invoke(main, ["show", "Lily"])
            assert result.exit_code == 0
            assert "Getting details for entity: 'Lily'" in result.output
            assert "Name: Lily" in result.output
            assert "character" in result.output

    def test_show_command_not_found(self):
        """Test show command for non-existent entity."""
        with patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "true"}):
            result = self.runner.invoke(main, ["show", "nonexistent"])
            assert result.exit_code == 0
            assert "Entity 'nonexistent' not found" in result.output

    def test_search_command_json_format(self):
        """Test search command with JSON output format."""
        with patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "true"}):
            result = self.runner.invoke(
                main,
                ["search", "characters", "--query", "dragon", "--format", "json"],
            )
            assert result.exit_code == 0
            # Should be valid JSON (skip the "Searching..." message)
            import json

            lines = result.output.strip().split("\n")
            json_start = next(
                i for i, line in enumerate(lines) if line.strip().startswith("{")
            )
            json_output = "\n".join(lines[json_start:])
            json.loads(json_output)

    def test_search_command_yaml_format(self):
        """Test search command with YAML output format."""
        with patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "true"}):
            result = self.runner.invoke(
                main,
                ["search", "characters", "--query", "dragon", "--format", "yaml"],
            )
            assert result.exit_code == 0
            # Should be valid YAML
            import yaml

            yaml.safe_load(result.output)
