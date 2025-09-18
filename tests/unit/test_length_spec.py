"""Tests for length specification model."""

import pytest

from src.jestir.models.length_spec import LengthSpec


class TestLengthSpec:
    """Test cases for LengthSpec model."""

    def test_word_count_spec(self):
        """Test word count specification."""
        spec = LengthSpec.from_word_count(500, tolerance_percent=10.0)

        assert spec.length_type == "word_count"
        assert spec.target_value == 500
        assert spec.tolerance_percent == 10.0
        assert spec.get_target_word_count() == 500
        assert spec.get_target_reading_time() == 3  # 500 / 175 = 2.86, rounded to 3
        assert spec.get_min_word_count() == 450  # 500 * 0.9
        assert spec.get_max_word_count() == 550  # 500 * 1.1

    def test_reading_time_spec(self):
        """Test reading time specification."""
        spec = LengthSpec.from_reading_time(
            5, reading_speed=200, tolerance_percent=15.0,
        )

        assert spec.length_type == "reading_time"
        assert spec.target_value == 5
        assert spec.reading_speed == 200
        assert spec.tolerance_percent == 15.0
        assert spec.get_target_word_count() == 1000  # 5 * 200
        assert spec.get_target_reading_time() == 5
        assert spec.get_min_word_count() == 850  # 1000 * 0.85
        assert spec.get_max_word_count() == 1150  # 1000 * 1.15

    def test_legacy_length_conversion(self):
        """Test conversion from legacy length strings."""
        test_cases = [
            ("very_short", 200),
            ("short", 500),
            ("medium", 1000),
            ("long", 2000),
            ("very_long", 3000),
        ]

        for length_str, expected_words in test_cases:
            spec = LengthSpec.from_legacy_length(length_str)
            assert spec.get_target_word_count() == expected_words
            assert spec.length_type == "word_count"

    def test_tolerance_validation(self):
        """Test tolerance validation."""
        spec = LengthSpec.from_word_count(1000, tolerance_percent=10.0)

        # Within tolerance
        assert spec.is_within_tolerance(950) is True
        assert spec.is_within_tolerance(1050) is True
        assert spec.is_within_tolerance(1000) is True

        # Outside tolerance
        assert spec.is_within_tolerance(800) is False
        assert spec.is_within_tolerance(1200) is False

    def test_deviation_calculation(self):
        """Test deviation percentage calculation."""
        spec = LengthSpec.from_word_count(1000, tolerance_percent=10.0)

        assert spec.get_deviation_percent(1000) == 0.0
        assert spec.get_deviation_percent(1100) == 10.0
        assert spec.get_deviation_percent(900) == 10.0
        assert spec.get_deviation_percent(1200) == 20.0

    def test_adjustment_suggestions(self):
        """Test adjustment suggestions."""
        spec = LengthSpec.from_word_count(1000, tolerance_percent=10.0)

        # Too short
        suggestion = spec.get_adjustment_suggestion(800)
        assert "too short" in suggestion.lower()
        assert "200" in suggestion  # 1000 - 800 = 200

        # Too long
        suggestion = spec.get_adjustment_suggestion(1200)
        assert "too long" in suggestion.lower()
        assert "200" in suggestion  # 1200 - 1000 = 200

        # Within tolerance
        suggestion = spec.get_adjustment_suggestion(950)
        assert "within acceptable range" in suggestion.lower()

    def test_legacy_conversion_back(self):
        """Test conversion back to legacy length strings."""
        test_cases = [
            (200, "very_short"),
            (500, "short"),
            (1000, "medium"),
            (2000, "long"),
            (3000, "very_long"),
        ]

        for word_count, expected_legacy in test_cases:
            spec = LengthSpec.from_word_count(word_count)
            assert spec.to_legacy_length() == expected_legacy

    def test_validation_errors(self):
        """Test validation errors."""
        # Invalid word count
        with pytest.raises(ValueError, match="Word count must be at least 50 words"):
            LengthSpec(length_type="word_count", target_value=30)

        # Invalid reading time
        with pytest.raises(ValueError, match="Reading time must be at least 1 minute"):
            LengthSpec(length_type="reading_time", target_value=0)

        # Invalid tolerance
        with pytest.raises(ValueError):
            LengthSpec(tolerance_percent=60.0)  # > 50%

        with pytest.raises(ValueError):
            LengthSpec(tolerance_percent=-10.0)  # < 0%

    def test_reading_speed_validation(self):
        """Test reading speed validation."""
        # Valid reading speeds
        LengthSpec(reading_speed=100)
        LengthSpec(reading_speed=300)

        # Invalid reading speeds
        with pytest.raises(ValueError):
            LengthSpec(reading_speed=50)  # < 100

        with pytest.raises(ValueError):
            LengthSpec(reading_speed=400)  # > 300
