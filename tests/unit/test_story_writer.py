"""Unit tests for the StoryWriter service."""

import pytest
from unittest.mock import Mock, patch, mock_open
import yaml
from pathlib import Path

from jestir.services.story_writer import StoryWriter
from jestir.models.story_context import StoryContext
from jestir.models.entity import Entity
from jestir.models.api_config import CreativeAPIConfig


class TestStoryWriter:
    """Test cases for StoryWriter service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = CreativeAPIConfig(
            api_key="test-key",
            base_url="https://api.test.com/v1",
            model="gpt-4o-mini",
            max_tokens=4000,
            temperature=0.8,
        )
        self.writer = StoryWriter(self.config)

        # Create test context
        self.test_context = StoryContext(
            settings={
                "genre": "adventure",
                "tone": "gentle",
                "length": "short",
                "age_appropriate": True,
                "morals": ["courage", "friendship"],
            },
            entities={
                "char_001": Entity(
                    id="char_001",
                    type="character",
                    subtype="protagonist",
                    name="Whiskers",
                    description="A brave little mouse",
                )
            },
            user_inputs={
                "initial_request": "A brave little mouse named Whiskers who saves the enchanted forest"
            },
            plot_points=["goes on an adventure", "saves the forest"],
        )

        self.test_outline = """# Story Outline: Whiskers's Adventure

## Act I: Beginning
### Scene 1: The Setup
- Whiskers is introduced
- The adventure begins when they goes on an adventure

## Act II: Middle
### Scene 2: The Challenge
- Whiskers faces obstacles
- They learn important lessons

## Act III: End
### Scene 3: The Resolution
- Whiskers achieves their goal
- They return home wiser

## Moral Lesson
Even when things seem difficult, with courage and determination, you can overcome any challenge.
"""

    def test_init_with_config(self):
        """Test initialization with provided config."""
        writer = StoryWriter(self.config)
        assert writer.config == self.config
        assert writer.client is not None

    def test_init_without_config(self):
        """Test initialization without config loads from environment."""
        with patch.dict(
            "os.environ",
            {
                "OPENAI_CREATIVE_API_KEY": "env-key",
                "OPENAI_CREATIVE_BASE_URL": "https://api.env.com/v1",
                "OPENAI_CREATIVE_MODEL": "gpt-4",
                "OPENAI_CREATIVE_MAX_TOKENS": "5000",
                "OPENAI_CREATIVE_TEMPERATURE": "0.9",
            },
        ):
            writer = StoryWriter()
            assert writer.config.api_key == "env-key"
            assert writer.config.base_url == "https://api.env.com/v1"
            assert writer.config.model == "gpt-4"
            assert writer.config.max_tokens == 5000
            assert writer.config.temperature == 0.9

    @patch("jestir.services.story_writer.OpenAI")
    def test_generate_story_success(self, mock_openai_class):
        """Test successful story generation."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = (
            "# Whiskers's Adventure\n\nOnce upon a time..."
        )

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        writer = StoryWriter(self.config)
        result = writer.generate_story(self.test_context, self.test_outline)

        assert result.startswith("# Whiskers's Adventure")
        mock_client.chat.completions.create.assert_called_once()

    @patch("jestir.services.story_writer.OpenAI")
    def test_generate_story_fallback(self, mock_openai_class):
        """Test fallback story generation when OpenAI fails."""
        # Mock OpenAI to raise exception
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai_class.return_value = mock_client

        writer = StoryWriter(self.config)
        result = writer.generate_story(self.test_context, self.test_outline)

        assert "Whiskers's Adventure" in result
        assert "Once upon a time" in result
        assert "The End" in result

    def test_build_story_prompt(self):
        """Test story prompt building."""
        prompt = self.writer._build_story_prompt(self.test_context, self.test_outline)

        assert "Genre: adventure" in prompt
        assert "Tone: gentle" in prompt
        assert "Length: short" in prompt
        assert "Whiskers: A brave little mouse" in prompt
        assert "goes on an adventure" in prompt
        assert "saves the forest" in prompt
        assert self.test_outline in prompt

    def test_get_target_word_count(self):
        """Test target word count calculation."""
        assert self.writer._get_target_word_count("very_short") == 200
        assert self.writer._get_target_word_count("short") == 500
        assert self.writer._get_target_word_count("medium") == 1000
        assert self.writer._get_target_word_count("long") == 2000
        assert self.writer._get_target_word_count("very_long") == 3000
        assert self.writer._get_target_word_count("unknown") == 500

    def test_format_story(self):
        """Test story formatting."""
        raw_content = "  # Test Story  \n\n  Once upon a time...  \n\n  The end.  "
        formatted = self.writer._format_story(raw_content)

        assert formatted.startswith("# Test Story")
        assert "Once upon a time..." in formatted
        assert "The end." in formatted
        assert "  " not in formatted  # No leading/trailing spaces

    def test_fallback_story(self):
        """Test fallback story generation."""
        result = self.writer._fallback_story(self.test_context, self.test_outline)

        assert "Whiskers's Adventure" in result
        assert "Once upon a time" in result
        assert "goes on an adventure" in result
        assert "The End" in result

    def test_load_outline_from_file(self):
        """Test loading outline from file."""
        test_content = "# Test Outline\n\nSome content here."

        with patch("builtins.open", mock_open(read_data=test_content)):
            with patch("pathlib.Path.exists", return_value=True):
                result = self.writer.load_outline_from_file("test_outline.md")
                assert result == test_content

    def test_load_outline_from_file_not_found(self):
        """Test loading outline from non-existent file."""
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                self.writer.load_outline_from_file("nonexistent.md")

    def test_load_context_from_file(self):
        """Test loading context from YAML file."""
        test_data = {
            "settings": {"genre": "adventure"},
            "entities": {},
            "relationships": [],
            "user_inputs": {},
            "plot_points": [],
        }

        with patch("builtins.open", mock_open(read_data=yaml.dump(test_data))):
            with patch("pathlib.Path.exists", return_value=True):
                result = self.writer.load_context_from_file("test_context.yaml")
                assert isinstance(result, StoryContext)
                assert result.settings["genre"] == "adventure"

    def test_save_story_to_file(self):
        """Test saving story to file."""
        test_story = "# Test Story\n\nContent here."

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("pathlib.Path.parent") as mock_parent:
                mock_parent.mkdir = Mock()
                self.writer.save_story_to_file(test_story, "test_story.md")
                # Check that open was called with a Path object and the correct arguments
                mock_file.assert_called_once()
                call_args = mock_file.call_args
                assert str(call_args[0][0]).endswith("test_story.md")
                assert call_args[0][1] == "w"
                assert call_args[1]["encoding"] == "utf-8"
                mock_file().write.assert_called_once_with(test_story)

    def test_update_context_with_story(self):
        """Test updating context with story."""
        test_story = "# Test Story\n\nContent here."

        self.writer.update_context_with_story(self.test_context, test_story)

        assert self.test_context.story == test_story
        assert self.test_context.metadata["updated_at"] is not None

    def test_calculate_word_count(self):
        """Test word count calculation."""
        text = "# Title\n\nThis is a test story with ten words total here."
        count = self.writer.calculate_word_count(text)
        assert (
            count == 11
        )  # "This is a test story with ten words total here" = 11 words

    def test_calculate_reading_time(self):
        """Test reading time calculation."""
        # Test with 175 words (1 minute)
        assert self.writer.calculate_reading_time(175) == "1 minute"

        # Test with 350 words (2 minutes)
        assert self.writer.calculate_reading_time(350) == "2 minutes"

        # Test with 0 words (minimum 1 minute)
        assert self.writer.calculate_reading_time(0) == "1 minute"
