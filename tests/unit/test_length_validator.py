"""Tests for length validator service."""

from jestir.models.length_spec import LengthSpec
from jestir.services.length_validator import LengthValidator


class TestLengthValidator:
    """Test cases for LengthValidator service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = LengthValidator()
        self.length_spec = LengthSpec.from_word_count(500, tolerance_percent=10.0)

    def test_word_counting(self):
        """Test word counting functionality."""
        text = "This is a test sentence with exactly ten words."
        assert self.validator._count_words(text) == 9

        # Test with markdown
        markdown_text = "# Title\n\nThis is **bold** text with *italics*."
        assert self.validator._count_words(markdown_text) == 7  # Excludes markdown

        # Test with empty text
        assert self.validator._count_words("") == 0

        # Test with whitespace
        assert self.validator._count_words("   \n\n   ") == 0

    def test_outline_word_estimation(self):
        """Test outline word count estimation."""
        outline = """
        # Story Outline

        ## Act I: Beginning
        ### Scene 1: Introduction
        - Character is introduced
        - Setting is established

        ### Scene 2: Conflict
        - Problem arises
        - Character must act
        """

        estimated = self.validator._estimate_outline_word_count(outline)
        # Should be reasonable estimate (outline words * 4)
        assert estimated > 0
        assert estimated < 1000  # Shouldn't be too high

    def test_outline_validation(self):
        """Test outline length validation."""
        # Short outline
        short_outline = "# Short Outline\n\n## Act I\n- Brief scene"
        result = self.validator.validate_outline_length(short_outline, self.length_spec)

        assert "estimated_word_count" in result
        assert "target_word_count" in result
        assert "deviation_percent" in result
        assert "is_within_tolerance" in result
        assert "suggestions" in result
        assert "adjustment_needed" in result

        # Should suggest adding more content
        assert result["adjustment_needed"] is True
        assert len(result["suggestions"]) > 0

    def test_story_validation(self):
        """Test story length validation."""
        # Short story
        short_story = "This is a very short story with only a few words."
        result = self.validator.validate_story_length(short_story, self.length_spec)

        assert "actual_word_count" in result
        assert "target_word_count" in result
        assert "deviation_percent" in result
        assert "is_within_tolerance" in result
        assert "suggestions" in result
        assert "adjustment_needed" in result
        assert "reading_time_minutes" in result

        # Should suggest adding more content
        assert result["adjustment_needed"] is True
        assert len(result["suggestions"]) > 0

    def test_within_tolerance_validation(self):
        """Test validation when within tolerance."""
        # Create a story that's within tolerance
        target_words = self.length_spec.get_target_word_count()
        words_per_sentence = 10
        sentences_needed = target_words // words_per_sentence

        story = "This is a test sentence with exactly ten words. " * sentences_needed
        result = self.validator.validate_story_length(story, self.length_spec)

        assert result["is_within_tolerance"] is True
        assert result["adjustment_needed"] is False
        assert "within acceptable range" in result["suggestions"][0].lower()

    def test_outline_suggestions(self):
        """Test outline adjustment suggestions."""
        # Very short outline
        short_outline = "# Outline\n\n## Act I\n- Scene"
        result = self.validator.validate_outline_length(short_outline, self.length_spec)

        suggestions = result["suggestions"]
        assert any("too short" in s.lower() for s in suggestions)
        assert any("add" in s.lower() for s in suggestions)
        assert any("scenes" in s.lower() for s in suggestions)

    def test_story_suggestions(self):
        """Test story adjustment suggestions."""
        # Very short story
        short_story = "This is a very short story."
        result = self.validator.validate_story_length(short_story, self.length_spec)

        suggestions = result["suggestions"]
        assert any("too short" in s.lower() for s in suggestions)
        assert any("add" in s.lower() for s in suggestions)
        assert any("dialogue" in s.lower() for s in suggestions)

    def test_outline_optimization(self):
        """Test outline optimization."""
        # Short outline that needs expansion
        short_outline = "# Outline\n\n## Act I\n- Brief scene"
        optimized = self.validator.optimize_outline_for_length(
            short_outline, self.length_spec,
        )

        # Should be longer than original
        assert len(optimized) > len(short_outline)
        assert "<!--" in optimized  # Should have expansion suggestions

    def test_outline_compression(self):
        """Test outline compression."""
        # Create a long outline
        long_outline = """
        # Story Outline

        ## Act I: Beginning
        ### Scene 1: Introduction
        - Character is introduced with detailed background
        - Setting is established with extensive description
        - [Brief description of what happens]
        - [Character development/conflict introduction]

        ### Scene 2: Conflict
        - Problem arises with complex details
        - Character must act decisively
        - [Brief description of what happens]
        - [Plot development]
        """

        # Use a very small target to force compression
        small_spec = LengthSpec.from_word_count(50, tolerance_percent=10.0)
        compressed = self.validator.optimize_outline_for_length(
            long_outline, small_spec,
        )

        # Should be shorter than original
        assert len(compressed) < len(long_outline)

    def test_length_metrics(self):
        """Test comprehensive length metrics."""
        text = "This is a test story with exactly ten words."
        metrics = self.validator.get_length_metrics(text, self.length_spec)

        assert "word_count" in metrics
        assert "target_word_count" in metrics
        assert "deviation_percent" in metrics
        assert "is_within_tolerance" in metrics
        assert "reading_time_minutes" in metrics
        assert "estimated_reading_time_minutes" in metrics
        assert "adjustment_suggestion" in metrics

        assert metrics["word_count"] == 9
        assert metrics["target_word_count"] == 500
        assert metrics["deviation_percent"] > 0
        assert metrics["is_within_tolerance"] is False

    def test_reading_time_calculation(self):
        """Test reading time calculation."""
        # Test with different reading speeds
        spec_150 = LengthSpec.from_reading_time(5, reading_speed=150)
        spec_200 = LengthSpec.from_reading_time(5, reading_speed=200)

        text = "word " * 1000  # 1000 words

        metrics_150 = self.validator.get_length_metrics(text, spec_150)
        metrics_200 = self.validator.get_length_metrics(text, spec_200)

        # Should have different estimated reading times
        assert (
            metrics_150["estimated_reading_time_minutes"]
            != metrics_200["estimated_reading_time_minutes"]
        )

        # 1000 words at 150 WPM = ~6.7 minutes
        # 1000 words at 200 WPM = 5 minutes
        assert (
            metrics_150["estimated_reading_time_minutes"]
            > metrics_200["estimated_reading_time_minutes"]
        )

    def test_edge_cases(self):
        """Test edge cases."""
        # Empty text
        result = self.validator.validate_story_length("", self.length_spec)
        assert result["actual_word_count"] == 0
        assert result["adjustment_needed"] is True

        # Very long text
        long_text = "word " * 10000  # 10,000 words
        result = self.validator.validate_story_length(long_text, self.length_spec)
        assert result["actual_word_count"] == 10000
        assert result["adjustment_needed"] is True
        assert any("too long" in s.lower() for s in result["suggestions"])

    def test_markdown_handling(self):
        """Test handling of markdown formatting."""
        markdown_text = """
        # Title

        This is **bold** text and *italic* text.

        - List item 1
        - List item 2

        [Link text](http://example.com)
        """

        word_count = self.validator._count_words(markdown_text)
        # Should count only actual words, not markdown syntax
        assert word_count > 0
        assert word_count < 20  # Should be reasonable count
