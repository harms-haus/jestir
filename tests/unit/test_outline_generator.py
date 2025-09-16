"""Tests for the outline generator service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import yaml

from jestir.services.outline_generator import OutlineGenerator
from jestir.models.story_context import StoryContext
from jestir.models.entity import Entity
from jestir.models.api_config import CreativeAPIConfig


class TestOutlineGenerator:
    """Test cases for OutlineGenerator."""

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = CreativeAPIConfig(
            api_key="test-key",
            base_url="https://test.api.com",
            model="gpt-4",
            max_tokens=1000,
            temperature=0.5,
        )
        generator = OutlineGenerator(config)
        assert generator.config == config

    def test_init_with_env_config(self):
        """Test initialization with environment config."""
        with patch.dict(
            "os.environ",
            {
                "OPENAI_CREATIVE_API_KEY": "env-key",
                "OPENAI_CREATIVE_BASE_URL": "https://env.api.com",
                "OPENAI_CREATIVE_MODEL": "gpt-3.5-turbo",
                "OPENAI_CREATIVE_MAX_TOKENS": "1500",
                "OPENAI_CREATIVE_TEMPERATURE": "0.8",
            },
        ):
            generator = OutlineGenerator()
            assert generator.config.api_key == "env-key"
            assert generator.config.base_url == "https://env.api.com"
            assert generator.config.model == "gpt-3.5-turbo"
            assert generator.config.max_tokens == 1500
            assert generator.config.temperature == 0.8

    def test_generate_outline_success(self):
        """Test successful outline generation."""
        # Create a mock context
        context = StoryContext()
        context.add_entity(
            Entity(
                id="char_001",
                type="character",
                subtype="protagonist",
                name="Arthur",
                description="A brave knight",
            )
        )
        context.add_plot_point("find a magical sword")
        context.add_user_input(
            "initial_request",
            "A brave knight named Arthur goes to find a magical sword",
        )

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[
            0
        ].message.content = """# Story Outline: Arthur's Quest

## Act I: Beginning
### Scene 1: The Call to Adventure
- Arthur learns about the magical sword
- He decides to embark on the quest

## Act II: Middle
### Scene 2: The Journey
- Arthur travels through the enchanted forest
- He faces various challenges

## Act III: End
### Scene 3: The Resolution
- Arthur finds the magical sword
- He returns home victorious

## Key Themes
- Courage and determination
- The power of perseverance

## Moral Lesson
With courage and determination, you can achieve your goals."""

        generator = OutlineGenerator()
        with patch.object(
            generator.client.chat.completions, "create", return_value=mock_response
        ):
            outline = generator.generate_outline(context)

            assert "# Story Outline: Arthur's Quest" in outline
            assert "Act I: Beginning" in outline
            assert "Act II: Middle" in outline
            assert "Act III: End" in outline
            assert "Moral Lesson" in outline

    def test_generate_outline_fallback(self):
        """Test fallback outline generation when OpenAI fails."""
        context = StoryContext()
        context.add_entity(
            Entity(
                id="char_001",
                type="character",
                subtype="protagonist",
                name="Arthur",
                description="A brave knight",
            )
        )
        context.add_plot_point("find a magical sword")

        generator = OutlineGenerator()
        with patch.object(
            generator.client.chat.completions,
            "create",
            side_effect=Exception("API Error"),
        ):
            outline = generator.generate_outline(context)

            assert "# Story Outline: Arthur's Adventure" in outline
            assert "Act I: Beginning" in outline
            assert "Act II: Middle" in outline
            assert "Act III: End" in outline

    def test_generate_outline_empty_response(self):
        """Test outline generation with empty OpenAI response."""
        context = StoryContext()
        context.add_entity(
            Entity(
                id="char_001",
                type="character",
                subtype="protagonist",
                name="Arthur",
                description="A brave knight",
            )
        )

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = None

        generator = OutlineGenerator()
        with patch.object(
            generator.client.chat.completions, "create", return_value=mock_response
        ):
            outline = generator.generate_outline(context)

            assert "# Story Outline: Arthur's Adventure" in outline
            assert "Act I: Beginning" in outline

    def test_build_outline_prompt(self):
        """Test outline prompt building."""
        context = StoryContext()
        context.settings["genre"] = "adventure"
        context.settings["tone"] = "gentle"
        context.settings["length"] = "short"

        context.add_entity(
            Entity(
                id="char_001",
                type="character",
                subtype="protagonist",
                name="Arthur",
                description="A brave knight",
            )
        )
        context.add_entity(
            Entity(
                id="loc_001",
                type="location",
                subtype="magical",
                name="Enchanted Forest",
                description="A mysterious forest",
            )
        )
        context.add_plot_point("find a magical sword")
        context.add_user_input(
            "initial_request",
            "A brave knight named Arthur goes to find a magical sword",
        )

        generator = OutlineGenerator()
        prompt = generator._build_outline_prompt(context)

        assert "adventure" in prompt
        assert "gentle" in prompt
        assert "Arthur" in prompt
        assert "Enchanted Forest" in prompt
        assert "find a magical sword" in prompt
        assert "3-act structure" in prompt
        assert "markdown formatting" in prompt

    def test_format_outline(self):
        """Test outline formatting."""
        generator = OutlineGenerator()

        # Test with proper heading
        content = "# Story Outline: Test\n\nSome content"
        formatted = generator._format_outline(content)
        assert formatted.startswith("# Story Outline: Test")

        # Test without heading
        content = "Some content without heading"
        formatted = generator._format_outline(content)
        assert formatted.startswith("# Story Outline")

    def test_fallback_outline(self):
        """Test fallback outline generation."""
        context = StoryContext()
        context.add_entity(
            Entity(
                id="char_001",
                type="character",
                subtype="protagonist",
                name="Arthur",
                description="A brave knight",
            )
        )
        context.add_plot_point("find a magical sword")

        generator = OutlineGenerator()
        outline = generator._fallback_outline(context)

        assert "# Story Outline: Arthur's Adventure" in outline
        assert "Act I: Beginning" in outline
        assert "Act II: Middle" in outline
        assert "Act III: End" in outline
        assert "find a magical sword" in outline

    def test_load_context_from_file(self):
        """Test loading context from YAML file."""
        # Create a temporary context file
        context_data = {
            "metadata": {
                "version": "1.0.0",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "token_usage": {},
            },
            "settings": {
                "genre": "adventure",
                "tone": "gentle",
                "length": "short",
                "morals": [],
                "age_appropriate": True,
            },
            "entities": {
                "char_001": {
                    "id": "char_001",
                    "type": "character",
                    "subtype": "protagonist",
                    "name": "Arthur",
                    "description": "A brave knight",
                    "existing": False,
                    "rag_id": None,
                    "properties": {},
                }
            },
            "relationships": [],
            "user_inputs": {
                "initial_request": "A brave knight named Arthur goes to find a magical sword"
            },
            "plot_points": ["find a magical sword"],
            "outline": None,
            "story": None,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(context_data, f)
            temp_file = f.name

        try:
            generator = OutlineGenerator()
            context = generator.load_context_from_file(temp_file)

            assert context.entities["char_001"].name == "Arthur"
            assert context.plot_points == ["find a magical sword"]
            assert (
                context.user_inputs["initial_request"]
                == "A brave knight named Arthur goes to find a magical sword"
            )
        finally:
            Path(temp_file).unlink()

    def test_load_context_from_file_not_found(self):
        """Test loading context from non-existent file."""
        generator = OutlineGenerator()

        with pytest.raises(FileNotFoundError):
            generator.load_context_from_file("nonexistent.yaml")

    def test_save_outline_to_file(self):
        """Test saving outline to file."""
        outline_content = "# Test Outline\n\nSome content"

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test_outline.md"

            generator = OutlineGenerator()
            generator.save_outline_to_file(outline_content, str(output_file))

            assert output_file.exists()
            with open(output_file, "r") as f:
                content = f.read()
                assert content == outline_content

    def test_update_context_with_outline(self):
        """Test updating context with outline."""
        context = StoryContext()
        outline_content = "# Test Outline\n\nSome content"

        generator = OutlineGenerator()
        generator.update_context_with_outline(context, outline_content)

        assert context.outline == outline_content
        assert context.metadata["updated_at"] is not None
