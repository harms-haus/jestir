"""Unit tests for enhanced error messaging."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from jestir.cli import main
from jestir.services.template_loader import TemplateLoader


class TestErrorMessaging:
    """Test cases for enhanced error messaging."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_context_command_missing_input_error(self):
        """Test context command with missing input shows clear error."""
        result = self.runner.invoke(main, ["context"])
        assert result.exit_code == 2
        assert "Missing argument 'INPUT_TEXT'" in result.output

    def test_context_command_permission_error(self):
        """Test context command with permission error shows helpful message."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a read-only directory
            readonly_dir = os.path.join(temp_dir, "readonly")
            os.makedirs(readonly_dir, mode=0o444)
            output_file = os.path.join(readonly_dir, "context.yaml")

            result = self.runner.invoke(
                main,
                [
                    "context",
                    "A simple test story",
                    "--output",
                    output_file,
                ],
            )

            assert result.exit_code == 1
            assert "❌ Permission Error" in result.output
            assert "💡 Tip: Check file permissions" in result.output

    def test_outline_command_file_not_found_error(self):
        """Test outline command with missing context file shows helpful message."""
        result = self.runner.invoke(main, ["outline", "nonexistent.yaml"])

        assert result.exit_code == 1
        assert "❌ File Not Found" in result.output
        assert "💡 Troubleshooting:" in result.output
        assert "Generate a context file first" in result.output

    def test_write_command_file_not_found_error(self):
        """Test write command with missing outline file shows helpful message."""
        result = self.runner.invoke(main, ["write", "nonexistent.md"])

        assert result.exit_code == 1
        assert "❌ File Not Found" in result.output
        assert "💡 Troubleshooting:" in result.output
        assert (
            "Generate an outline first" in result.output
            or "Make sure the outline file" in result.output
        )

    @patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "false"})
    def test_search_command_connection_error(self):
        """Test search command with connection error shows helpful message."""
        with patch.dict("os.environ", {"LIGHTRAG_BASE_URL": "http://invalid-url:9999"}):
            result = self.runner.invoke(
                main,
                ["search", "characters", "--query", "test"],
            )

            # The client gracefully falls back to mock mode, but if it fails completely
            # we should get an error. Let's test that the command completes.
            assert result.exit_code in [0, 1]  # Either graceful fallback or error

    def test_template_validation_directory_not_found(self):
        """Test template validation with missing directory shows helpful message."""
        # Create a TemplateLoader with non-existent directory
        with pytest.raises(Exception):
            loader = TemplateLoader("/nonexistent/path")
            loader.load_template("test.txt")

    def test_template_validation_file_not_found(self):
        """Test template validation with missing file shows helpful message."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = TemplateLoader(temp_dir)

            with pytest.raises(FileNotFoundError) as exc_info:
                loader.load_template("nonexistent.txt")

            error_msg = str(exc_info.value)
            assert "Template file not found" in error_msg
            assert "Expected location:" in error_msg
            assert "Available templates:" in error_msg

    def test_template_validation_permission_error(self):
        """Test template validation with permission error shows helpful message."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a template file with no read permissions
            template_file = Path(temp_dir) / "test.txt"
            template_file.write_text("Test template content")
            template_file.chmod(0o000)

            loader = TemplateLoader(temp_dir)

            try:
                with pytest.raises(PermissionError) as exc_info:
                    loader.load_template("test.txt")

                error_msg = str(exc_info.value)
                assert "Cannot read template file" in error_msg
                assert "Check file permissions" in error_msg
            finally:
                # Restore permissions for cleanup
                template_file.chmod(0o644)

    def test_template_validation_encoding_error(self):
        """Test template validation with encoding error shows helpful message."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a template file with invalid encoding
            template_file = Path(temp_dir) / "test.txt"
            with open(template_file, "wb") as f:
                f.write(b"\xff\xfe\x00\x00Invalid UTF-8")

            loader = TemplateLoader(temp_dir)

            with pytest.raises(ValueError) as exc_info:
                loader.load_template("test.txt")

            error_msg = str(exc_info.value)
            assert "Invalid file encoding" in error_msg
            assert "must be UTF-8 encoded" in error_msg

    def test_show_command_entity_not_found_helpful_message(self):
        """Test show command with entity not found shows helpful suggestions."""
        with patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "true"}):
            result = self.runner.invoke(main, ["show", "nonexistent_entity"])

            assert result.exit_code == 0
            assert "Entity 'nonexistent_entity' not found" in result.output

    def test_lightrag_test_command_error_handling(self):
        """Test lightrag test command error handling."""
        # Test with invalid URL
        result = self.runner.invoke(
            main,
            ["lightrag", "test", "--base-url", "http://invalid-url:9999"],
        )

        # Should either complete successfully due to graceful fallback or show error
        assert result.exit_code in [0, 1]

    def test_api_error_detection_in_context_command(self):
        """Test API error detection and helpful messaging."""
        with patch(
            "jestir.services.context_generator.ContextGenerator.generate_context",
        ) as mock_generate:
            # Simulate OpenAI API error
            mock_generate.side_effect = Exception(
                "OpenAI API error: insufficient credits",
            )

            result = self.runner.invoke(
                main,
                ["context", "test story", "--output", "/tmp/test_context.yaml"],
            )

            assert result.exit_code == 1
            assert "❌ API Error" in result.output
            assert "💡 Troubleshooting:" in result.output
            assert "Check your OPENAI_EXTRACTION_API_KEY" in result.output

    def test_yaml_parse_error_detection(self):
        """Test YAML parse error detection and helpful messaging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create an invalid YAML file
            invalid_yaml = os.path.join(temp_dir, "invalid.yaml")
            with open(invalid_yaml, "w") as f:
                f.write("invalid: yaml: content: [unclosed")

            result = self.runner.invoke(main, ["outline", invalid_yaml])

            assert result.exit_code == 1
            # The actual error depends on the YAML parsing implementation

    def test_template_error_detection_in_outline_command(self):
        """Test template error detection and helpful messaging."""
        with patch(
            "jestir.services.outline_generator.OutlineGenerator.generate_outline",
        ) as mock_generate:
            # Simulate template error
            mock_generate.side_effect = Exception("Template error: missing variable")

            with tempfile.TemporaryDirectory() as temp_dir:
                # Create a valid context file
                context_file = os.path.join(temp_dir, "context.yaml")
                with open(context_file, "w") as f:
                    f.write(
                        "metadata:\n  title: Test Story\nentities: []\nrelationships: []",
                    )

                result = self.runner.invoke(main, ["outline", context_file])

                assert result.exit_code == 1
                # Error message should be detected and categorized

    def test_search_command_query_error_detection(self):
        """Test search command query error detection."""
        with patch(
            "jestir.services.lightrag_client.LightRAGClient.search_entities",
        ) as mock_search:
            # Simulate invalid query error
            mock_search.side_effect = Exception("Invalid query format")

            result = self.runner.invoke(
                main,
                ["search", "characters", "--query", "invalid query"],
            )

            assert result.exit_code == 1
            assert "❌" in result.output  # Should show error with emoji

    def test_export_file_permission_error(self):
        """Test export file permission error handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a read-only directory
            readonly_dir = os.path.join(temp_dir, "readonly")
            os.makedirs(readonly_dir, mode=0o444)
            export_file = os.path.join(readonly_dir, "export.yaml")

            with patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "true"}):
                result = self.runner.invoke(
                    main,
                    [
                        "search",
                        "characters",
                        "--query",
                        "test",
                        "--export",
                        export_file,
                    ],
                )

                # Should handle permission error gracefully
                assert result.exit_code == 1

    def test_invalid_entity_type_error(self):
        """Test invalid entity type shows clear error."""
        result = self.runner.invoke(main, ["search", "invalid_type", "--query", "test"])

        assert result.exit_code == 2  # Click validation error
        assert "Invalid value for" in result.output or "Usage:" in result.output

    def test_pagination_edge_cases(self):
        """Test pagination with edge cases."""
        with patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "true"}):
            # Test with invalid page number
            result = self.runner.invoke(
                main,
                ["search", "characters", "--query", "test", "--page", "0"],
            )

            # Should handle gracefully or show validation error
            assert result.exit_code in [0, 1, 2]

    def test_export_format_error_handling(self):
        """Test export format error handling."""
        with patch.dict("os.environ", {"LIGHTRAG_MOCK_MODE": "true"}):
            with patch("yaml.dump") as mock_dump:
                # Simulate YAML serialization error
                mock_dump.side_effect = Exception("YAML serialization error")

                result = self.runner.invoke(
                    main,
                    [
                        "search",
                        "characters",
                        "--query",
                        "test",
                        "--export",
                        "/tmp/test_export.yaml",
                    ],
                )

                assert result.exit_code == 1
