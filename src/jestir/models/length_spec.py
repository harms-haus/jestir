"""Length specification model for story generation."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LengthSpec(BaseModel):
    """Specification for story length with word count or reading time targets."""

    # Length type: either word count or reading time
    length_type: Literal["word_count", "reading_time"] = Field(
        default="word_count",
        description="Type of length specification",
    )

    # Target value
    target_value: int = Field(
        default=500,
        description="Target word count or reading time in minutes",
    )

    # Tolerance percentage (±10% by default)
    tolerance_percent: float = Field(
        default=10.0,
        ge=0.0,
        le=50.0,
        description="Acceptable deviation percentage from target",
    )

    # Reading speed for time-based calculations (words per minute)
    reading_speed: int = Field(
        default=175,
        ge=100,
        le=300,
        description="Words per minute for reading time calculations",
    )

    @field_validator("target_value")
    @classmethod
    def validate_target_value(cls, v, info):
        """Validate target value based on length type."""
        if info.data and "length_type" in info.data:
            if info.data["length_type"] == "word_count" and v < 50:
                raise ValueError("Word count must be at least 50 words")
            if info.data["length_type"] == "reading_time" and v < 1:
                raise ValueError("Reading time must be at least 1 minute")
        return v

    def get_target_word_count(self) -> int:
        """Get target word count regardless of length type."""
        if self.length_type == "word_count":
            return self.target_value
        return self.target_value * self.reading_speed

    def get_target_reading_time(self) -> int:
        """Get target reading time in minutes regardless of length type."""
        if self.length_type == "reading_time":
            return self.target_value
        return max(1, round(self.target_value / self.reading_speed))

    def get_min_word_count(self) -> int:
        """Get minimum acceptable word count."""
        target = self.get_target_word_count()
        return int(target * (1 - self.tolerance_percent / 100))

    def get_max_word_count(self) -> int:
        """Get maximum acceptable word count."""
        target = self.get_target_word_count()
        return int(target * (1 + self.tolerance_percent / 100))

    def is_within_tolerance(self, word_count: int) -> bool:
        """Check if word count is within acceptable tolerance."""
        min_words = self.get_min_word_count()
        max_words = self.get_max_word_count()
        return min_words <= word_count <= max_words

    def get_deviation_percent(self, word_count: int) -> float:
        """Get deviation percentage from target."""
        target = self.get_target_word_count()
        return abs(word_count - target) / target * 100

    def get_adjustment_suggestion(self, word_count: int) -> str:
        """Get suggestion for adjusting length."""
        target = self.get_target_word_count()
        deviation = self.get_deviation_percent(word_count)

        if word_count < self.get_min_word_count():
            shortfall = target - word_count
            return f"Story is {deviation:.1f}% too short. Add approximately {shortfall} words to reach target."
        if word_count > self.get_max_word_count():
            excess = word_count - target
            return f"Story is {deviation:.1f}% too long. Remove approximately {excess} words to reach target."
        return f"Story length is within acceptable range ({deviation:.1f}% deviation)."

    @classmethod
    def from_word_count(
        cls,
        word_count: int,
        tolerance_percent: float = 10.0,
    ) -> "LengthSpec":
        """Create LengthSpec from word count."""
        return cls(
            length_type="word_count",
            target_value=word_count,
            tolerance_percent=tolerance_percent,
        )

    @classmethod
    def from_reading_time(
        cls,
        minutes: int,
        reading_speed: int = 175,
        tolerance_percent: float = 10.0,
    ) -> "LengthSpec":
        """Create LengthSpec from reading time."""
        return cls(
            length_type="reading_time",
            target_value=minutes,
            reading_speed=reading_speed,
            tolerance_percent=tolerance_percent,
        )

    @classmethod
    def from_legacy_length(cls, length_str: str) -> "LengthSpec":
        """Create LengthSpec from legacy length string (short, medium, long, etc.)."""
        length_mapping = {
            "very_short": 200,
            "short": 500,
            "medium": 1000,
            "long": 2000,
            "very_long": 3000,
        }

        word_count = length_mapping.get(length_str, 500)
        return cls.from_word_count(word_count)

    def to_legacy_length(self) -> str:
        """Convert to legacy length string for backward compatibility."""
        word_count = self.get_target_word_count()

        if word_count <= 300:
            return "very_short"
        if word_count <= 750:
            return "short"
        if word_count <= 1500:
            return "medium"
        if word_count <= 2500:
            return "long"
        return "very_long"
