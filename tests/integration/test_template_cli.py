"""Integration tests for template CLI command."""

import os
import tempfile
from pathlib import Path

import yaml
from click.testing import CliRunner

from jestir.cli import main


class TestTemplateCLI:
    """Test template CLI command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()

        # Create a test template
        self.template_content = "Hello {{name}}! This is a {{genre}} story for {{age_appropriate}} children."
        self.template_path = os.path.join(self.temp_dir, "test_template.txt")
        with open(self.template_path, "w") as f:
            f.write(self.template_content)

        # Create a test context file
        self.context_data = {
            "name": "Alice",
            "genre": "adventure",
            "age_appropriate": "5-8 years",
            "morals": "friendship and courage",
        }
        self.context_path = os.path.join(self.temp_dir, "test_context.yaml")
        with open(self.context_path, "w") as f:
            yaml.dump(self.context_data, f)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_template_command_basic(self):
        """Test basic template command functionality."""
        result = self.runner.invoke(
            main,
            [
                "template",
                self.template_path,
                "--name",
                "Alice",
            ],
        )

        assert result.exit_code == 0
        assert "Testing template:" in result.output
        assert "Template Preview:" in result.output
        assert "Hello Alice!" in result.output
        assert "adventure story" in result.output
        assert "5-8 years children" in result.output

    def test_template_command_with_context(self):
        """Test template command with context file."""
        result = self.runner.invoke(
            main,
            [
                "template",
                self.template_path,
                "--context",
                self.context_path,
            ],
        )

        assert result.exit_code == 0
        assert "Loading context from:" in result.output
        assert "Template Preview:" in result.output
        assert "Hello Alice!" in result.output
        assert "adventure story" in result.output

    def test_template_command_validation(self):
        """Test template command with validation."""
        result = self.runner.invoke(
            main,
            [
                "template",
                self.template_path,
                "--validate",
            ],
        )

        assert result.exit_code == 0
        assert "Validating template syntax" in result.output
        assert "Template syntax is valid" in result.output
        assert "Found 3 template variables:" in result.output
        assert "name" in result.output
        assert "genre" in result.output
        assert "age_appropriate" in result.output

    def test_template_command_debug(self):
        """Test template command with debug mode."""
        result = self.runner.invoke(
            main,
            [
                "template",
                self.template_path,
                "--name",
                "Alice",
                "--debug",
            ],
        )

        assert result.exit_code == 0
        assert "Variable Substitutions:" in result.output
        assert "name: Alice" in result.output
        assert "protagonist: Alice" in result.output

    def test_template_command_dry_run(self):
        """Test template command with dry run mode."""
        result = self.runner.invoke(
            main,
            [
                "template",
                self.template_path,
                "--name",
                "Alice",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "Dry run mode - no API calls made" in result.output
        assert "Template is ready for use in story generation" in result.output

    def test_template_command_missing_file(self):
        """Test template command with missing template file."""
        result = self.runner.invoke(
            main,
            [
                "template",
                "nonexistent.txt",
            ],
        )

        assert result.exit_code != 0
        assert "Template Not Found" in result.output
        assert "Check that template file 'nonexistent.txt' exists" in result.output

    def test_template_command_invalid_syntax(self):
        """Test template command with invalid syntax."""
        # Create template with syntax errors
        invalid_template = os.path.join(self.temp_dir, "invalid_template.txt")
        with open(invalid_template, "w") as f:
            f.write("Hello {{name! This is invalid syntax.")

        result = self.runner.invoke(
            main,
            [
                "template",
                invalid_template,
                "--validate",
            ],
        )

        assert result.exit_code != 0
        assert "Template syntax errors found" in result.output
        assert "Mismatched braces" in result.output

    def test_template_command_missing_context_file(self):
        """Test template command with missing context file."""
        result = self.runner.invoke(
            main,
            [
                "template",
                self.template_path,
                "--context",
                "nonexistent.yaml",
            ],
        )

        assert result.exit_code == 0  # Should not fail, just warn
        assert "Warning: Could not load context file" in result.output
        assert "Template context validation passed" in result.output

    def test_template_command_unresolved_variables(self):
        """Test template command with unresolved variables."""
        # Create template with variables not in context
        template_with_missing = os.path.join(self.temp_dir, "missing_vars.txt")
        with open(template_with_missing, "w") as f:
            f.write("Hello {{name}}! This is a {{missing_var}} story.")

        result = self.runner.invoke(
            main,
            [
                "template",
                template_with_missing,
                "--name",
                "Alice",
            ],
        )

        assert result.exit_code == 0
        assert "Warning: 1 unresolved variables:" in result.output
        assert "missing_var" in result.output

    def test_template_command_context_validation(self):
        """Test template command with context validation."""
        result = self.runner.invoke(
            main,
            [
                "template",
                self.template_path,
                "--context",
                self.context_path,
                "--validate",
            ],
        )

        assert result.exit_code == 0
        assert "Template context validation passed" in result.output
        assert "Context coverage:" in result.output

    def test_template_command_context_validation_issues(self):
        """Test template command with context validation issues."""
        # Create context with missing variables
        incomplete_context = {
            "name": "Alice",
            # Missing genre and age_appropriate
        }
        incomplete_context_path = os.path.join(self.temp_dir, "incomplete_context.yaml")
        with open(incomplete_context_path, "w") as f:
            yaml.dump(incomplete_context, f)

        result = self.runner.invoke(
            main,
            [
                "template",
                self.template_path,
                "--context",
                incomplete_context_path,
                "--validate",
            ],
        )

        assert result.exit_code == 0
        assert "Template context validation passed" in result.output
        assert "Context coverage:" in result.output

    def test_template_command_all_options(self):
        """Test template command with all options."""
        result = self.runner.invoke(
            main,
            [
                "template",
                self.template_path,
                "--name",
                "Alice",
                "--context",
                self.context_path,
                "--validate",
                "--debug",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "Validating template syntax" in result.output
        assert "Template syntax is valid" in result.output
        assert "Template context validation passed" in result.output
        assert "Variable Substitutions:" in result.output
        assert "Dry run mode - no API calls made" in result.output

    def test_template_command_with_documentation(self):
        """Test template command with variable documentation."""
        # Create template with documentation
        doc_template = os.path.join(self.temp_dir, "doc_template.txt")
        with open(doc_template, "w") as f:
            f.write(
                "Hello {{name # protagonist name}}! This is a {{genre # story genre}} story.",
            )

        result = self.runner.invoke(
            main,
            [
                "template",
                doc_template,
                "--validate",
            ],
        )

        assert result.exit_code == 0
        assert "Template syntax is valid" in result.output
        assert "protagonist name" in result.output
        assert "story genre" in result.output

    def test_template_command_performance(self):
        """Test template command with large template."""
        # Create large template
        large_content = "Hello {{name}}! " * 100  # 100 repetitions
        large_template = os.path.join(self.temp_dir, "large_template.txt")
        with open(large_template, "w") as f:
            f.write(large_content)

        result = self.runner.invoke(
            main,
            [
                "template",
                large_template,
                "--name",
                "Alice",
                "--validate",
            ],
        )

        assert result.exit_code == 0
        assert "Template syntax is valid" in result.output
        assert "Found 100 template variables:" in result.output
        assert "Hello Alice!" in result.output

    def test_template_command_error_handling(self):
        """Test template command error handling."""
        # Create template with permission issues (read-only)
        readonly_template = os.path.join(self.temp_dir, "readonly_template.txt")
        with open(readonly_template, "w") as f:
            f.write("Hello {{name}}!")

        # Make file read-only
        Path(readonly_template).chmod(0o444)

        try:
            result = self.runner.invoke(
                main,
                [
                    "template",
                    readonly_template,
                    "--name",
                    "Alice",
                ],
            )

            # Should still work for reading
            assert result.exit_code == 0
            assert "Hello Alice!" in result.output

        finally:
            # Restore permissions for cleanup
            Path(readonly_template).chmod(0o644)

    def test_template_command_help(self):
        """Test template command help."""
        result = self.runner.invoke(
            main,
            [
                "template",
                "--help",
            ],
        )

        assert result.exit_code == 0
        assert "Test and preview templates with variable substitution" in result.output
        assert "--name" in result.output
        assert "--context" in result.output
        assert "--dry-run" in result.output
        assert "--validate" in result.output
        assert "--debug" in result.output
