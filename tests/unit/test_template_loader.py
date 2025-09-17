"""Tests for the template loader service."""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from jestir.services.template_loader import TemplateLoader


class TestTemplateLoader:
    """Test cases for TemplateLoader."""

    def test_init_with_default_templates_dir(self):
        """Test initialization with default templates directory."""
        loader = TemplateLoader()
        assert loader.templates_dir is not None
        assert isinstance(loader.templates_dir, Path)

    def test_init_with_custom_templates_dir(self):
        """Test initialization with custom templates directory."""
        custom_dir = "/custom/templates"
        loader = TemplateLoader(custom_dir)
        assert str(loader.templates_dir) == custom_dir

    def test_load_template_success(self):
        """Test successful template loading."""
        loader = TemplateLoader()

        # Mock template content
        template_content = "Hello {{name}}, welcome to {{place}}!"

        with patch("builtins.open", mock_open(read_data=template_content)):
            with patch.object(Path, "exists", return_value=True):
                result = loader.load_template("test_template.txt")
                assert result == template_content

    def test_load_template_file_not_found(self):
        """Test template loading when file doesn't exist."""
        loader = TemplateLoader()

        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                loader.load_template("nonexistent.txt")

    def test_render_template_success(self):
        """Test successful template rendering with variable substitution."""
        loader = TemplateLoader()

        template_content = "Hello {{name}}, welcome to {{place}}!"
        context = {"name": "Alice", "place": "Wonderland"}
        expected = "Hello Alice, welcome to Wonderland!"

        with patch.object(loader, "load_template", return_value=template_content):
            result = loader.render_template("test.txt", context)
            assert result == expected

    def test_render_template_missing_variable(self):
        """Test template rendering with missing variables."""
        loader = TemplateLoader()

        template_content = "Hello {{name}}, welcome to {{place}}!"
        context = {"name": "Alice"}  # Missing 'place'
        expected = "Hello Alice, welcome to {{place}}!"  # Placeholder preserved

        with patch.object(loader, "load_template", return_value=template_content):
            result = loader.render_template("test.txt", context)
            assert result == expected

    def test_render_template_none_value(self):
        """Test template rendering with None values."""
        loader = TemplateLoader()

        template_content = "Hello {{name}}, welcome to {{place}}!"
        context = {"name": "Alice", "place": None}
        expected = "Hello Alice, welcome to !"  # None becomes empty string

        with patch.object(loader, "load_template", return_value=template_content):
            result = loader.render_template("test.txt", context)
            assert result == expected

    def test_load_character_template(self):
        """Test loading character-specific templates."""
        loader = TemplateLoader()

        with patch.object(loader, "load_template") as mock_load:
            loader.load_character_template("protagonist")
            mock_load.assert_called_once_with(
                "prompts/includes/character_protagonist.txt",
            )

    def test_load_location_template(self):
        """Test loading location-specific templates."""
        loader = TemplateLoader()

        with patch.object(loader, "load_template") as mock_load:
            loader.load_location_template("interior")
            mock_load.assert_called_once_with("prompts/includes/location_interior.txt")

    def test_load_system_prompt(self):
        """Test loading system prompt templates."""
        loader = TemplateLoader()

        with patch.object(loader, "load_template") as mock_load:
            loader.load_system_prompt("context_extraction")
            mock_load.assert_called_once_with(
                "prompts/system_prompts/context_extraction.txt",
            )

    def test_load_user_prompt(self):
        """Test loading user prompt templates."""
        loader = TemplateLoader()

        with patch.object(loader, "load_template") as mock_load:
            loader.load_user_prompt("story_generation")
            mock_load.assert_called_once_with(
                "prompts/user_prompts/story_generation.txt",
            )

    def test_clear_cache(self):
        """Test clearing the template cache."""
        loader = TemplateLoader()

        # Add something to cache
        loader._template_cache["test"] = "cached content"
        assert "test" in loader._template_cache

        # Clear cache
        loader.clear_cache()
        assert len(loader._template_cache) == 0

    def test_get_available_templates(self):
        """Test getting available templates by category."""
        loader = TemplateLoader()

        # Test that the method returns the expected structure
        result = loader.get_available_templates()

        # Check that all expected categories are present
        assert "system_prompts" in result
        assert "user_prompts" in result
        assert "includes" in result

        # Check that each category is a list
        assert isinstance(result["system_prompts"], list)
        assert isinstance(result["user_prompts"], list)
        assert isinstance(result["includes"], list)

    def test_validate_template_success(self):
        """Test template validation with all required variables present."""
        loader = TemplateLoader()

        template_content = (
            "Hello {{name}}, you are {{age}} years old and live in {{place}}."
        )
        required_vars = ["name", "age", "place"]

        with patch.object(loader, "load_template", return_value=template_content):
            result = loader.validate_template("test.txt", required_vars)

            assert result["valid"] is True
            assert len(result["missing_vars"]) == 0
            assert "name" in result["found_vars"]
            assert "age" in result["found_vars"]
            assert "place" in result["found_vars"]

    def test_validate_template_missing_variables(self):
        """Test template validation with missing required variables."""
        loader = TemplateLoader()

        template_content = "Hello {{name}}, you are {{age}} years old."
        required_vars = ["name", "age", "place", "country"]

        with patch.object(loader, "load_template", return_value=template_content):
            result = loader.validate_template("test.txt", required_vars)

            assert result["valid"] is False
            assert "place" in result["missing_vars"]
            assert "country" in result["missing_vars"]
            assert "name" in result["found_vars"]
            assert "age" in result["found_vars"]

    def test_validate_template_extra_variables(self):
        """Test template validation with extra variables not in required list."""
        loader = TemplateLoader()

        template_content = (
            "Hello {{name}}, you are {{age}} years old and live in {{place}}."
        )
        required_vars = ["name", "age"]

        with patch.object(loader, "load_template", return_value=template_content):
            result = loader.validate_template("test.txt", required_vars)

            assert result["valid"] is True  # No missing required vars
            assert "place" in result["extra_vars"]
            assert len(result["missing_vars"]) == 0

    def test_template_caching(self):
        """Test that templates are cached after first load."""
        loader = TemplateLoader()

        template_content = "Hello {{name}}!"

        with patch("builtins.open", mock_open(read_data=template_content)):
            with patch.object(Path, "exists", return_value=True):
                # First load
                result1 = loader.load_template("test.txt")

                # Second load should use cache
                result2 = loader.load_template("test.txt")

                assert result1 == result2
                # Check that the full path is in the cache, not just the filename
                cache_key = str(loader.templates_dir / "test.txt")
                assert cache_key in loader._template_cache
