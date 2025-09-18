"""Integration tests for length control functionality."""

import tempfile
from pathlib import Path

import pytest

from src.jestir.models.length_spec import LengthSpec
from src.jestir.models.story_context import StoryContext
from src.jestir.services.length_validator import LengthValidator
from src.jestir.services.outline_generator import OutlineGenerator
from src.jestir.services.story_writer import StoryWriter


class TestLengthControlIntegration:
    """Integration tests for length control across the pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = LengthValidator()
        self.outline_generator = OutlineGenerator()
        self.story_writer = StoryWriter()

        # Create a test context
        self.context = StoryContext()
        self.context.add_user_input(
            "test_input", "A brave little mouse goes on an adventure",
        )
        self.context.add_plot_point("The mouse finds a magical cheese")
        self.context.add_plot_point("The mouse must overcome obstacles")
        self.context.add_plot_point("The mouse learns about friendship")

    def test_end_to_end_length_control(self):
        """Test length control through the entire pipeline."""
        # Set length specification
        length_spec = LengthSpec.from_word_count(300, tolerance_percent=15.0)
        self.context.set_length_spec(length_spec)

        # Generate outline
        outline = self.outline_generator.generate_outline(self.context)

        # Validate outline length
        outline_validation = self.validator.validate_outline_length(
            outline, length_spec,
        )
        assert "estimated_word_count" in outline_validation
        assert "target_word_count" in outline_validation

        # Generate story
        story = self.story_writer.generate_story(self.context, outline)

        # Validate story length
        story_validation = self.validator.validate_story_length(story, length_spec)
        assert "actual_word_count" in story_validation
        assert "target_word_count" in story_validation

        # Check that length specifications are being used
        assert story_validation["target_word_count"] == 300

    def test_length_spec_persistence(self):
        """Test that length specifications persist through context operations."""
        # Set initial length spec
        length_spec = LengthSpec.from_reading_time(3, reading_speed=200)
        self.context.set_length_spec(length_spec)

        # Verify it's set
        effective_spec = self.context.get_effective_length_spec()
        assert effective_spec.length_type == "reading_time"
        assert effective_spec.target_value == 3
        assert effective_spec.reading_speed == 200

        # Add more content
        self.context.add_plot_point("Additional plot point")

        # Verify length spec is still there
        effective_spec_after = self.context.get_effective_length_spec()
        assert effective_spec_after.length_type == "reading_time"
        assert effective_spec_after.target_value == 3

    def test_legacy_length_compatibility(self):
        """Test compatibility with legacy length settings."""
        # Set legacy length
        self.context.settings["length"] = "medium"

        # Get effective length spec
        effective_spec = self.context.get_effective_length_spec()

        # Should convert to word count
        assert effective_spec.length_type == "word_count"
        assert effective_spec.get_target_word_count() == 1000  # medium = 1000 words

        # Should update legacy setting when setting new spec
        new_spec = LengthSpec.from_word_count(500)
        self.context.set_length_spec(new_spec)

        assert self.context.settings["length"] == "short"  # 500 words = short

    def test_length_validation_accuracy(self):
        """Test accuracy of length validation."""
        # Create a story with known word count
        test_story = "word " * 100  # Exactly 100 words

        length_spec = LengthSpec.from_word_count(100, tolerance_percent=10.0)
        result = self.validator.validate_story_length(test_story, length_spec)

        assert result["actual_word_count"] == 100
        assert result["target_word_count"] == 100
        assert result["deviation_percent"] == 0.0
        assert result["is_within_tolerance"] is True

    def test_outline_story_length_consistency(self):
        """Test consistency between outline and story length targets."""
        # Set length specification
        length_spec = LengthSpec.from_word_count(400, tolerance_percent=20.0)
        self.context.set_length_spec(length_spec)

        # Generate outline
        outline = self.outline_generator.generate_outline(self.context)

        # Generate story
        story = self.story_writer.generate_story(self.context, outline)

        # Both should use the same length specification
        outline_validation = self.validator.validate_outline_length(
            outline, length_spec,
        )
        story_validation = self.validator.validate_story_length(story, length_spec)

        assert (
            outline_validation["target_word_count"]
            == story_validation["target_word_count"]
        )
        assert outline_validation["target_word_count"] == 400

    def test_length_override_functionality(self):
        """Test that length can be overridden at different stages."""
        # Set initial length
        initial_spec = LengthSpec.from_word_count(200)
        self.context.set_length_spec(initial_spec)

        # Override with new length
        override_spec = LengthSpec.from_word_count(600)
        self.context.set_length_spec(override_spec)

        # Should use the override
        effective_spec = self.context.get_effective_length_spec()
        assert effective_spec.get_target_word_count() == 600

    def test_reading_time_calculations(self):
        """Test reading time calculations across different speeds."""
        test_cases = [
            (150, 1050, 7),  # 7 minutes at 150 WPM = 1050 words
            (200, 1000, 5),  # 5 minutes at 200 WPM = 1000 words
            (250, 1000, 4),  # 4 minutes at 250 WPM = 1000 words
        ]

        for reading_speed, word_count, expected_minutes in test_cases:
            spec = LengthSpec.from_reading_time(
                expected_minutes, reading_speed=reading_speed,
            )
            assert spec.get_target_word_count() == word_count
            assert spec.get_target_reading_time() == expected_minutes

    def test_tolerance_boundaries(self):
        """Test tolerance boundary calculations."""
        spec = LengthSpec.from_word_count(1000, tolerance_percent=10.0)

        # Test exact boundaries
        assert spec.get_min_word_count() == 900
        assert spec.get_max_word_count() == 1100

        # Test boundary conditions
        assert spec.is_within_tolerance(900) is True
        assert spec.is_within_tolerance(1100) is True
        assert spec.is_within_tolerance(899) is False
        assert spec.is_within_tolerance(1101) is False

    def test_suggestion_quality(self):
        """Test quality of length adjustment suggestions."""
        # Test short story suggestions
        short_story = "This is a very short story."
        spec = LengthSpec.from_word_count(500, tolerance_percent=10.0)
        result = self.validator.validate_story_length(short_story, spec)

        suggestions = result["suggestions"]
        assert len(suggestions) > 0
        assert any("too short" in s.lower() for s in suggestions)
        assert any("add" in s.lower() for s in suggestions)

        # Test long story suggestions
        long_story = "word " * 1000  # 1000 words
        spec_short = LengthSpec.from_word_count(200, tolerance_percent=10.0)
        result_long = self.validator.validate_story_length(long_story, spec_short)

        suggestions_long = result_long["suggestions"]
        assert len(suggestions_long) > 0
        assert any("too long" in s.lower() for s in suggestions_long)
        assert any("remove" in s.lower() for s in suggestions_long)

    def test_file_operations_with_length(self):
        """Test file operations with length specifications."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create context with length spec
            length_spec = LengthSpec.from_word_count(250, tolerance_percent=15.0)
            self.context.set_length_spec(length_spec)

            # Save context to file
            context_file = temp_path / "test_context.yaml"
            import yaml

            with open(context_file, "w") as f:
                yaml.dump(self.context.model_dump(), f)

            # Load context from file
            with open(context_file) as f:
                loaded_data = yaml.safe_load(f)

            loaded_context = StoryContext(**loaded_data)

            # Verify length spec is preserved
            loaded_spec = loaded_context.get_effective_length_spec()
            assert loaded_spec.get_target_word_count() == 250
            assert loaded_spec.tolerance_percent == 15.0

    def test_error_handling(self):
        """Test error handling in length control."""
        # Test with invalid length specification
        with pytest.raises(ValueError):
            LengthSpec(length_type="word_count", target_value=10)  # Too few words

        # Test with invalid tolerance
        with pytest.raises(ValueError):
            LengthSpec(tolerance_percent=60.0)  # Too high tolerance

        # Test with empty text
        result = self.validator.validate_story_length(
            "", self.context.get_effective_length_spec(),
        )
        assert result["actual_word_count"] == 0
        assert result["adjustment_needed"] is True
