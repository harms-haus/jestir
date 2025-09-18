"""Tests for template testing and preview functionality."""

import os
import tempfile
from pathlib import Path

from jestir.services.template_loader import TemplateLoader


class TestTemplateSyntaxValidation:
    """Test template syntax validation functionality."""

    def test_valid_template_syntax(self):
        """Test validation of valid template syntax."""
        loader = TemplateLoader()

        # Create a temporary template file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(
                "Hello {{name}}! This is a {{genre}} story for {{age_appropriate}} children.",
            )
            template_path = f.name

        try:
            result = loader.validate_template_syntax(template_path)

            assert result["valid"] is True
            assert len(result["syntax_errors"]) == 0
            assert result["variable_count"] == 3
            assert result["template_length"] > 0
            assert result["line_count"] == 1

            # Check variables
            variables = result["variables"]
            assert len(variables) == 3

            var_names = [var["name"] for var in variables]
            assert "name" in var_names
            assert "genre" in var_names
            assert "age_appropriate" in var_names

        finally:
            os.unlink(template_path)

    def test_invalid_template_syntax(self):
        """Test validation of invalid template syntax."""
        loader = TemplateLoader()

        # Create a temporary template file with syntax errors
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(
                "Hello {{name! This is a {{genre}} story for {{age_appropriate}} children.",
            )
            template_path = f.name

        try:
            result = loader.validate_template_syntax(template_path)

            assert result["valid"] is False
            assert len(result["syntax_errors"]) > 0
            assert "Mismatched braces" in str(result["syntax_errors"])

        finally:
            os.unlink(template_path)

    def test_template_with_documentation(self):
        """Test template with variable documentation."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(
                "Hello {{name # protagonist name}}! This is a {{genre # story genre}} story.",
            )
            template_path = f.name

        try:
            result = loader.validate_template_syntax(template_path)

            assert result["valid"] is True
            assert result["variable_count"] == 2

            variables = result["variables"]
            name_var = next(var for var in variables if var["name"] == "name")
            assert name_var["has_documentation"] is True
            assert name_var["documentation"] == "protagonist name"

            genre_var = next(var for var in variables if var["name"] == "genre")
            assert genre_var["has_documentation"] is True
            assert genre_var["documentation"] == "story genre"

        finally:
            os.unlink(template_path)

    def test_template_with_warnings(self):
        """Test template with warnings (spaces in variable names)."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello {{character name}}! This is a {{story genre}} story.")
            template_path = f.name

        try:
            result = loader.validate_template_syntax(template_path)

            assert result["valid"] is True
            assert len(result["warnings"]) > 0

            warning_text = " ".join(result["warnings"])
            assert "spaces" in warning_text.lower()

        finally:
            os.unlink(template_path)

    def test_nested_braces_error(self):
        """Test detection of nested braces (not supported)."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello {{name {{nested}} }}! This is a story.")
            template_path = f.name

        try:
            result = loader.validate_template_syntax(template_path)

            assert result["valid"] is False
            assert any("Nested braces" in error for error in result["syntax_errors"])

        finally:
            os.unlink(template_path)

    def test_empty_variable_name(self):
        """Test detection of empty variable names."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello {{}}! This is a story.")
            template_path = f.name

        try:
            result = loader.validate_template_syntax(template_path)

            assert result["valid"] is False
            assert any(
                "Empty variable name" in error for error in result["syntax_errors"]
            )

        finally:
            os.unlink(template_path)

    def test_unicode_and_special_characters(self):
        """Test template with Unicode and special characters."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8",
        ) as f:
            f.write(
                "Hello {{name}}! This is a {{genre}} story with émojis 🎭 and special chars: {{special_chars}}",
            )
            template_path = f.name

        try:
            result = loader.validate_template_syntax(template_path)

            assert result["valid"] is True
            assert result["variable_count"] == 3

            variables = result["variables"]
            var_names = [var["name"] for var in variables]
            assert "name" in var_names
            assert "genre" in var_names
            assert "special_chars" in var_names

        finally:
            os.unlink(template_path)

    def test_complex_nested_structures(self):
        """Test complex template with multiple levels of nesting."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("""
            Story: {{title}}
            Author: {{author.name}}
            Genre: {{metadata.genre}}
            Characters: {{characters[0].name}}, {{characters[1].name}}
            Settings: {{settings.location}}, {{settings.time_period}}
            """)
            template_path = f.name

        try:
            result = loader.validate_template_syntax(template_path)

            assert result["valid"] is True
            assert result["variable_count"] == 7  # Updated count

            variables = result["variables"]
            var_names = [var["name"] for var in variables]
            assert "title" in var_names
            assert "author.name" in var_names
            assert "metadata.genre" in var_names
            assert "characters[0].name" in var_names
            assert "characters[1].name" in var_names
            assert "settings.location" in var_names
            assert "settings.time_period" in var_names

        finally:
            os.unlink(template_path)

    def test_malformed_syntax_edge_cases(self):
        """Test various malformed syntax edge cases."""
        loader = TemplateLoader()

        test_cases = [
            ("Hello {{name! This is broken", "Unclosed brace"),
            ("Hello {{name}} and {{genre", "Unclosed brace"),
            ("Hello {{name}} and {{}} broken", "Empty variable"),
            ("Hello {{name}} and {{ }} broken", "Whitespace only variable"),
            ("Hello {{name}} and {{name}} and {{name", "Mixed valid/invalid"),
            ("Hello {{name}} and {{name}} and {{name}}", "Valid template"),
            ("Hello {{name}} and {{name}} and {{name}} and {{", "Trailing unclosed"),
            ("Hello {{name}} and {{name}} and {{name}} and {{}}", "Trailing empty"),
        ]

        for template_content, description in test_cases:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False,
            ) as f:
                f.write(template_content)
                template_path = f.name

            try:
                result = loader.validate_template_syntax(template_path)

                if "Valid template" in description:
                    assert result["valid"] is True, f"Should be valid: {description}"
                else:
                    assert result["valid"] is False, f"Should be invalid: {description}"
                    assert len(result["syntax_errors"]) > 0, (
                        f"Should have errors: {description}"
                    )

            finally:
                os.unlink(template_path)

    def test_variable_name_edge_cases(self):
        """Test variable names with edge cases."""
        loader = TemplateLoader()

        test_cases = [
            ("Hello {{name123}}! This is valid.", True, "Alphanumeric"),
            ("Hello {{name_123}}! This is valid.", True, "Underscore"),
            ("Hello {{name-123}}! This is valid.", True, "Hyphen"),
            ("Hello {{name.123}}! This is valid.", True, "Dot notation"),
            ("Hello {{name[0]}}! This is valid.", True, "Array notation"),
            ("Hello {{123name}}! This is valid.", True, "Starting with number"),
            (
                "Hello {{name with spaces}}! This has warnings.",
                True,
                "Spaces (warning)",
            ),
            ("Hello {{name@special}}! This is valid.", True, "Special chars"),
            ("Hello {{name#comment}}! This is valid.", True, "Comment syntax"),
        ]

        for template_content, should_be_valid, description in test_cases:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False,
            ) as f:
                f.write(template_content)
                template_path = f.name

            try:
                result = loader.validate_template_syntax(template_path)

                assert result["valid"] == should_be_valid, (
                    f"Validation failed for: {description}"
                )

                if "warning" in description.lower():
                    assert len(result["warnings"]) > 0, (
                        f"Should have warnings: {description}"
                    )

            finally:
                os.unlink(template_path)

    def test_large_template_performance(self):
        """Test syntax validation performance with large templates."""
        loader = TemplateLoader()

        # Create a large template with many variables
        large_template = "Hello {{name}}! " * 1000  # 1000 repetitions
        large_template += "This is a {{genre}} story. " * 500  # 500 more repetitions

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(large_template)
            template_path = f.name

        try:
            import time

            start_time = time.time()
            result = loader.validate_template_syntax(template_path)
            validation_time = time.time() - start_time

            assert result["valid"] is True
            assert validation_time < 1.0  # Should validate in under 1 second
            assert result["variable_count"] > 1000  # Should find many variables

        finally:
            os.unlink(template_path)

    def test_encoding_issues(self):
        """Test template with various encoding issues."""
        loader = TemplateLoader()

        # Test with different encodings
        test_content = (
            "Hello {{name}}! This is a {{genre}} story with émojis 🎭 and accents: café"
        )

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8",
        ) as f:
            f.write(test_content)
            template_path = f.name

        try:
            result = loader.validate_template_syntax(template_path)

            assert result["valid"] is True
            assert result["variable_count"] == 2

            variables = result["variables"]
            var_names = [var["name"] for var in variables]
            assert "name" in var_names
            assert "genre" in var_names

        finally:
            os.unlink(template_path)


class TestTemplateContextValidation:
    """Test template context validation functionality."""

    def test_valid_context_validation(self):
        """Test validation with complete context."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(
                "Hello {{name}}! This is a {{genre}} story for {{age_appropriate}} children.",
            )
            template_path = f.name

        try:
            context = {
                "name": "Alice",
                "genre": "adventure",
                "age_appropriate": "5-8 years",
            }

            result = loader.validate_template_with_context(template_path, context)

            assert result["valid"] is True
            assert result["overall_coverage"] == 1.0
            assert len(result["context_validation"]["missing_in_context"]) == 0
            assert len(result["context_validation"]["rendering_errors"]) == 0

        finally:
            os.unlink(template_path)

    def test_missing_context_variables(self):
        """Test validation with missing context variables."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(
                "Hello {{name}}! This is a {{genre}} story for {{age_appropriate}} children.",
            )
            template_path = f.name

        try:
            context = {
                "name": "Alice",
                # Missing genre and age_appropriate
            }

            result = loader.validate_template_with_context(template_path, context)

            assert result["valid"] is False
            assert result["overall_coverage"] < 1.0
            assert len(result["context_validation"]["missing_in_context"]) == 2
            assert "genre" in result["context_validation"]["missing_in_context"]
            assert (
                "age_appropriate" in result["context_validation"]["missing_in_context"]
            )

        finally:
            os.unlink(template_path)

    def test_extra_context_variables(self):
        """Test validation with extra context variables."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello {{name}}! This is a story.")
            template_path = f.name

        try:
            context = {
                "name": "Alice",
                "genre": "adventure",  # Extra variable not used in template
                "age_appropriate": "5-8 years",  # Extra variable not used in template
            }

            result = loader.validate_template_with_context(template_path, context)

            assert result["valid"] is True
            assert result["overall_coverage"] == 1.0
            assert len(result["context_validation"]["extra_in_context"]) == 2
            assert "genre" in result["context_validation"]["extra_in_context"]
            assert "age_appropriate" in result["context_validation"]["extra_in_context"]

        finally:
            os.unlink(template_path)

    def test_required_variables_validation(self):
        """Test validation with required variables list."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello {{name}}! This is a {{genre}} story.")
            template_path = f.name

        try:
            context = {
                "name": "Alice",
                "genre": "adventure",
            }
            required_vars = [
                "name",
                "genre",
                "age_appropriate",
            ]  # Missing age_appropriate

            result = loader.validate_template_with_context(
                template_path, context, required_vars,
            )

            assert result["valid"] is False
            assert "age_appropriate" in result["context_validation"]["missing_required"]

        finally:
            os.unlink(template_path)

    def test_rendering_errors(self):
        """Test detection of rendering errors."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello {{name}}! This is a {{genre}} story.")
            template_path = f.name

        try:
            context = {
                "name": "Alice",
                # Missing genre - should cause unresolved variables
            }

            result = loader.validate_template_with_context(template_path, context)

            assert result["valid"] is False
            assert len(result["context_validation"]["rendering_errors"]) > 0
            assert any(
                "Unresolved variables" in error
                for error in result["context_validation"]["rendering_errors"]
            )

        finally:
            os.unlink(template_path)

    def test_nested_template_structures(self):
        """Test validation with complex template structures (flat keys only)."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("""
            Story: {{title}}
            Author: {{author_name}}
            Genre: {{genre}}
            Character1: {{character1_name}}
            Character2: {{character2_name}}
            Location: {{location}}
            TimePeriod: {{time_period}}
            """)
            template_path = f.name

        try:
            # Test with complete flat context
            complete_context = {
                "title": "The Great Adventure",
                "author_name": "Jane Doe",
                "genre": "fantasy",
                "character1_name": "Alice",
                "character2_name": "Bob",
                "location": "Enchanted Forest",
                "time_period": "Medieval",
            }

            result = loader.validate_template_with_context(
                template_path, complete_context,
            )

            assert result["valid"] is True
            assert result["overall_coverage"] == 1.0
            assert len(result["context_validation"]["missing_in_context"]) == 0

        finally:
            os.unlink(template_path)

    def test_partial_nested_context_validation(self):
        """Test validation with partially missing nested context."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("""
            Story: {{title}}
            Author: {{author.name}}
            Genre: {{metadata.genre}}
            Characters: {{characters[0].name}}, {{characters[1].name}}
            Settings: {{settings.location}}, {{settings.time_period}}
            """)
            template_path = f.name

        try:
            # Test with incomplete nested context
            incomplete_context = {
                "title": "The Great Adventure",
                "author": {"name": "Jane Doe"},
                # Missing metadata.genre
                "characters": [
                    {"name": "Alice"},
                    # Missing characters[1].name
                ],
                "settings": {
                    "location": "Enchanted Forest",
                    # Missing settings.time_period
                },
            }

            result = loader.validate_template_with_context(
                template_path, incomplete_context,
            )

            assert result["valid"] is False
            assert result["overall_coverage"] < 1.0
            assert len(result["context_validation"]["missing_in_context"]) > 0

            missing_vars = result["context_validation"]["missing_in_context"]
            assert "metadata.genre" in missing_vars
            assert "characters[1].name" in missing_vars
            assert "settings.time_period" in missing_vars

        finally:
            os.unlink(template_path)

    def test_dynamic_key_generation_scenarios(self):
        """Test validation with dynamically generated keys (flat keys only)."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("""
            Character 1: {{character1_name}}
            Character 2: {{character2_name}}
            Character 3: {{character3_name}}
            Total characters: {{character_count}}
            """)
            template_path = f.name

        try:
            # Test with flat context
            context = {
                "character1_name": "Alice",
                "character2_name": "Bob",
                "character3_name": "Charlie",
                "character_count": 3,
            }

            result = loader.validate_template_with_context(template_path, context)

            assert result["valid"] is True
            assert result["overall_coverage"] == 1.0

        finally:
            os.unlink(template_path)

    def test_cross_template_key_dependencies(self):
        """Test validation with cross-template key dependencies."""
        loader = TemplateLoader()

        # Create multiple templates with dependencies
        template1_content = "Hello {{name}}! This is a {{genre}} story."
        template2_content = "The main character is {{name}} and the genre is {{genre}}."
        template3_content = "Story: {{title}} by {{author}} in {{genre}} genre."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(template1_content)
            template1_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(template2_content)
            template2_path = f.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(template3_content)
            template3_path = f.name

        try:
            # Test with context that satisfies some templates but not others
            context = {
                "name": "Alice",
                "genre": "adventure",
                # Missing title and author for template3
            }

            # Validate each template
            result1 = loader.validate_template_with_context(template1_path, context)
            result2 = loader.validate_template_with_context(template2_path, context)
            result3 = loader.validate_template_with_context(template3_path, context)

            assert result1["valid"] is True
            assert result2["valid"] is True
            assert result3["valid"] is False

            # Check that template3 has missing variables
            assert len(result3["context_validation"]["missing_in_context"]) == 2
            assert "title" in result3["context_validation"]["missing_in_context"]
            assert "author" in result3["context_validation"]["missing_in_context"]

        finally:
            os.unlink(template1_path)
            os.unlink(template2_path)
            os.unlink(template3_path)

    def test_optional_vs_required_key_handling(self):
        """Test validation with optional vs required key handling."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("""
            Required: {{name}} ({{age}} years old)
            Optional: {{nickname}} ({{description}})
            """)
            template_path = f.name

        try:
            # Test with only required keys - this should fail because all variables are required
            required_only_context = {
                "name": "Alice",
                "age": 25,
            }

            result = loader.validate_template_with_context(
                template_path, required_only_context,
            )

            # Should be invalid because missing optional keys are still required
            assert result["valid"] is False
            assert (
                result["overall_coverage"] < 1.0
            )  # Less than 100% due to missing keys

            # Test with all keys
            complete_context = {
                "name": "Alice",
                "age": 25,
                "nickname": "Ally",
                "description": "A brave adventurer",
            }

            result = loader.validate_template_with_context(
                template_path, complete_context,
            )

            assert result["valid"] is True
            assert result["overall_coverage"] == 1.0

        finally:
            os.unlink(template_path)

    def test_complex_validation_scenarios(self):
        """Test complex validation scenarios with multiple edge cases (flat keys only)."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("""
            Title: {{title}}
            Author: {{author_name}} ({{author_email}})
            Genre: {{genre}}
            Rating: {{rating}}
            Character1: {{character1_name}}
            Character2: {{character2_name}}
            Location: {{location}}
            TimePeriod: {{time_period}}
            Tag1: {{tag1}}
            Tag2: {{tag2}}
            Tag3: {{tag3}}
            """)
            template_path = f.name

        try:
            # Test with complex flat structure
            complex_context = {
                "title": "The Great Adventure",
                "author_name": "Jane Doe",
                "author_email": "jane@example.com",
                "genre": "fantasy",
                "rating": "PG-13",
                "character1_name": "Alice",
                "character2_name": "Bob",
                "location": "Enchanted Forest",
                "time_period": "Medieval",
                "tag1": "adventure",
                "tag2": "fantasy",
                "tag3": "magic",
            }

            result = loader.validate_template_with_context(
                template_path, complex_context,
            )

            assert result["valid"] is True
            assert result["overall_coverage"] == 1.0
            assert len(result["context_validation"]["missing_in_context"]) == 0
            assert len(result["context_validation"]["rendering_errors"]) == 0

        finally:
            os.unlink(template_path)

    def test_validation_performance_with_large_contexts(self):
        """Test validation performance with large context objects."""
        loader = TemplateLoader()

        # Create a template with many variables
        template_parts = []
        for i in range(100):
            template_parts.append(f"Variable {i}: {{var_{i}}}")

        template_content = "\n".join(template_parts)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(template_content)
            template_path = f.name

        try:
            # Create large context with all variables
            large_context = {f"var_{i}": f"value_{i}" for i in range(100)}

            import time

            start_time = time.time()
            result = loader.validate_template_with_context(template_path, large_context)
            validation_time = time.time() - start_time

            assert result["valid"] is True
            assert validation_time < 2.0  # Should validate in under 2 seconds
            assert result["overall_coverage"] == 1.0

        finally:
            os.unlink(template_path)


class TestTemplateRendering:
    """Test template rendering functionality."""

    def test_basic_rendering(self):
        """Test basic template rendering."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(
                "Hello {{name}}! This is a {{genre}} story for {{age_appropriate}} children.",
            )
            template_path = f.name

        try:
            context = {
                "name": "Alice",
                "genre": "adventure",
                "age_appropriate": "5-8 years",
            }

            result = loader.render_template(template_path, context)

            assert "Hello Alice!" in result
            assert "adventure story" in result
            assert "5-8 years children" in result
            assert "{{" not in result  # No unresolved variables

        finally:
            os.unlink(template_path)

    def test_rendering_with_documentation(self):
        """Test rendering with variable documentation."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(
                "Hello {{name # protagonist name}}! This is a {{genre # story genre}} story.",
            )
            template_path = f.name

        try:
            context = {
                "name": "Alice",
                "genre": "adventure",
            }

            result = loader.render_template(template_path, context)

            assert "Hello Alice!" in result
            assert "adventure story" in result
            assert "{{" not in result  # No unresolved variables

        finally:
            os.unlink(template_path)

    def test_rendering_with_missing_variables(self):
        """Test rendering with missing variables (should keep placeholders)."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(
                "Hello {{name}}! This is a {{genre}} story for {{age_appropriate}} children.",
            )
            template_path = f.name

        try:
            context = {
                "name": "Alice",
                # Missing genre and age_appropriate
            }

            result = loader.render_template(template_path, context)

            assert "Hello Alice!" in result
            assert "{{genre}}" in result  # Unresolved variable kept
            assert "{{age_appropriate}}" in result  # Unresolved variable kept

        finally:
            os.unlink(template_path)

    def test_rendering_with_none_values(self):
        """Test rendering with None values."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello {{name}}! This is a {{genre}} story.")
            template_path = f.name

        try:
            context = {
                "name": "Alice",
                "genre": None,
            }

            result = loader.render_template(template_path, context)

            assert "Hello Alice!" in result
            assert "This is a  story" in result  # None becomes empty string

        finally:
            os.unlink(template_path)

    def test_rendering_with_complex_values(self):
        """Test rendering with complex data types."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Characters: {{characters}}. Plot points: {{plot_points}}.")
            template_path = f.name

        try:
            context = {
                "characters": ["Alice", "Bob", "Charlie"],
                "plot_points": {
                    "beginning": "meeting",
                    "middle": "adventure",
                    "end": "resolution",
                },
            }

            result = loader.render_template(template_path, context)

            assert "['Alice', 'Bob', 'Charlie']" in result
            assert "{'beginning': 'meeting'" in result

        finally:
            os.unlink(template_path)


class TestTemplateEdgeCases:
    """Test template edge cases and error conditions."""

    def test_empty_template(self):
        """Test validation of empty template."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            template_path = f.name

        try:
            result = loader.validate_template_syntax(template_path)

            assert result["valid"] is True
            assert result["variable_count"] == 0
            assert result["template_length"] == 0

        finally:
            os.unlink(template_path)

    def test_template_with_no_variables(self):
        """Test template with no variables."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a static template with no variables.")
            template_path = f.name

        try:
            result = loader.validate_template_syntax(template_path)

            assert result["valid"] is True
            assert result["variable_count"] == 0

            # Test rendering
            rendered = loader.render_template(template_path, {})
            assert rendered == "This is a static template with no variables."

        finally:
            os.unlink(template_path)

    def test_template_with_only_whitespace(self):
        """Test template with only whitespace."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("   \n  \t  \n  ")
            template_path = f.name

        try:
            result = loader.validate_template_syntax(template_path)

            assert result["valid"] is True
            assert result["variable_count"] == 0

        finally:
            os.unlink(template_path)

    def test_template_file_not_found(self):
        """Test handling of non-existent template file."""
        loader = TemplateLoader()

        result = loader.validate_template_syntax("nonexistent.txt")

        assert result["valid"] is False
        assert "Failed to load template" in result["error"]

    def test_template_with_special_characters(self):
        """Test template with special characters in variables."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(
                "Hello {{name}}! This is a {{genre}} story with {{special-chars}} and {{under_score}}.",
            )
            template_path = f.name

        try:
            context = {
                "name": "Alice",
                "genre": "adventure",
                "special-chars": "test",
                "under_score": "test",
            }

            result = loader.render_template(template_path, context)

            assert "Hello Alice!" in result
            assert "special-chars" not in result  # Should be replaced
            assert "under_score" not in result  # Should be replaced

        finally:
            os.unlink(template_path)


class TestTemplatePerformance:
    """Test template performance and caching."""

    def test_template_caching(self):
        """Test that templates are cached for performance."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello {{name}}!")
            template_path = f.name

        try:
            # Load template multiple times
            content1 = loader.load_template(template_path)
            content2 = loader.load_template(template_path)

            assert content1 == content2

            # Verify cache is working (same object reference)
            assert loader._template_cache[str(Path(template_path))] is content1

        finally:
            os.unlink(template_path)

    def test_cache_clearing(self):
        """Test template cache clearing."""
        loader = TemplateLoader()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello {{name}}!")
            template_path = f.name

        try:
            # Load template to populate cache
            loader.load_template(template_path)
            assert len(loader._template_cache) > 0

            # Clear cache
            loader.clear_cache()
            assert len(loader._template_cache) == 0

        finally:
            os.unlink(template_path)

    def test_large_template_performance(self):
        """Test performance with large template."""
        loader = TemplateLoader()

        # Create a large template
        large_content = "Hello {{name}}! " * 1000  # 1000 repetitions

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(large_content)
            template_path = f.name

        try:
            # Test validation performance
            result = loader.validate_template_syntax(template_path)

            assert result["valid"] is True
            assert result["variable_count"] == 1000
            assert result["template_length"] > 10000

            # Test rendering performance
            context = {"name": "Alice"}
            rendered = loader.render_template(template_path, context)

            assert "Hello Alice!" in rendered
            assert len(rendered) > 10000

        finally:
            os.unlink(template_path)
