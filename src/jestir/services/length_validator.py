"""Length validation service for story generation."""

import re
from typing import Any

from ..models.length_spec import LengthSpec


class LengthValidator:
    """Validates and provides suggestions for story length control."""

    def __init__(self):
        """Initialize the length validator."""

    def validate_outline_length(
        self,
        outline: str,
        length_spec: LengthSpec,
    ) -> dict[str, Any]:
        """Validate outline length and provide suggestions."""
        # Estimate word count from outline
        estimated_words = self._estimate_outline_word_count(outline)
        target_words = length_spec.get_target_word_count()

        # Calculate metrics
        deviation_percent = length_spec.get_deviation_percent(estimated_words)
        is_within_tolerance = length_spec.is_within_tolerance(estimated_words)

        # Generate suggestions
        suggestions = self._generate_outline_suggestions(
            outline,
            estimated_words,
            target_words,
            length_spec,
        )

        return {
            "estimated_word_count": estimated_words,
            "target_word_count": target_words,
            "deviation_percent": deviation_percent,
            "is_within_tolerance": is_within_tolerance,
            "suggestions": suggestions,
            "adjustment_needed": not is_within_tolerance,
        }

    def validate_story_length(
        self,
        story: str,
        length_spec: LengthSpec,
    ) -> dict[str, Any]:
        """Validate final story length and provide suggestions."""
        actual_words = self._count_words(story)
        target_words = length_spec.get_target_word_count()

        # Calculate metrics
        deviation_percent = length_spec.get_deviation_percent(actual_words)
        is_within_tolerance = length_spec.is_within_tolerance(actual_words)

        # Generate suggestions
        suggestions = self._generate_story_suggestions(
            story,
            actual_words,
            target_words,
            length_spec,
        )

        return {
            "actual_word_count": actual_words,
            "target_word_count": target_words,
            "deviation_percent": deviation_percent,
            "is_within_tolerance": is_within_tolerance,
            "suggestions": suggestions,
            "adjustment_needed": not is_within_tolerance,
            "reading_time_minutes": length_spec.get_target_reading_time(),
        }

    def _estimate_outline_word_count(self, outline: str) -> int:
        """Estimate word count from outline content."""
        # Remove markdown formatting
        clean_text = re.sub(r"[#*_`\[\]()]", "", outline)

        # Count words
        words = clean_text.split()
        base_count = len(words)

        # Estimate expansion factor (outline typically expands 3-5x in final story)
        # Use 4x as a reasonable estimate
        estimated_final_words = base_count * 4

        return estimated_final_words

    def _count_words(self, text: str) -> int:
        """Count words in text, removing markdown formatting."""
        # Remove markdown formatting but preserve punctuation
        clean_text = re.sub(r"[#*_`\[\]()]", "", text)

        # Split into words and count (preserve punctuation within words)
        words = clean_text.split()
        return len(words)

    def _generate_outline_suggestions(
        self,
        outline: str,
        estimated_words: int,
        target_words: int,
        length_spec: LengthSpec,
    ) -> list[str]:
        """Generate suggestions for adjusting outline length."""
        suggestions = []

        if estimated_words < length_spec.get_min_word_count():
            # Outline too short
            shortfall = target_words - estimated_words
            suggestions.append(
                f"Outline is too short. Add approximately {shortfall} words to reach target.",
            )
            suggestions.append(
                "Consider adding more scenes or expanding existing scene descriptions.",
            )
            suggestions.append("Add more character development or plot details.")
            suggestions.append("Include more dialogue or action sequences.")
        elif estimated_words > length_spec.get_max_word_count():
            # Outline too long
            excess = estimated_words - target_words
            suggestions.append(
                f"Outline is too long. Remove approximately {excess} words to reach target.",
            )
            suggestions.append("Consider combining or removing some scenes.")
            suggestions.append("Simplify scene descriptions to be more concise.")
            suggestions.append("Focus on the most essential plot points.")
        else:
            suggestions.append("Outline length is within acceptable range.")

        return suggestions

    def _generate_story_suggestions(
        self,
        story: str,
        actual_words: int,
        target_words: int,
        length_spec: LengthSpec,
    ) -> list[str]:
        """Generate suggestions for adjusting story length."""
        suggestions = []

        if actual_words < length_spec.get_min_word_count():
            # Story too short
            shortfall = target_words - actual_words
            suggestions.append(
                f"Story is too short. Add approximately {shortfall} words to reach target.",
            )
            suggestions.append("Expand dialogue between characters.")
            suggestions.append(
                "Add more descriptive details about settings and characters.",
            )
            suggestions.append("Include more character thoughts and emotions.")
            suggestions.append("Add transitional scenes between major events.")
        elif actual_words > length_spec.get_max_word_count():
            # Story too long
            excess = actual_words - target_words
            suggestions.append(
                f"Story is too long. Remove approximately {excess} words to reach target.",
            )
            suggestions.append("Remove redundant descriptions or dialogue.")
            suggestions.append("Combine or remove less essential scenes.")
            suggestions.append("Simplify complex sentences.")
            suggestions.append("Remove unnecessary subplots or characters.")
        else:
            suggestions.append("Story length is within acceptable range.")

        return suggestions

    def optimize_outline_for_length(self, outline: str, length_spec: LengthSpec) -> str:
        """Optimize outline to better match target length."""
        current_estimate = self._estimate_outline_word_count(outline)
        target_words = length_spec.get_target_word_count()

        if current_estimate < length_spec.get_min_word_count():
            # Expand outline
            return self._expand_outline(outline, target_words - current_estimate)
        if current_estimate > length_spec.get_max_word_count():
            # Compress outline
            return self._compress_outline(outline, current_estimate - target_words)
        # Already within tolerance
        return outline

    def _expand_outline(self, outline: str, words_to_add: int) -> str:
        """Expand outline by adding more detail."""
        # This is a simplified expansion - in practice, you might use AI
        # to intelligently expand the outline

        # Add expansion suggestions as comments
        expansion_suggestions = [
            "\n\n<!-- Consider adding more character development -->",
            "\n\n<!-- Consider adding more dialogue opportunities -->",
            "\n\n<!-- Consider adding more descriptive details -->",
            "\n\n<!-- Consider adding more conflict or tension -->",
        ]

        # Add suggestions based on how much expansion is needed
        if words_to_add > 200:
            outline += "".join(expansion_suggestions)
        elif words_to_add > 100:
            outline += "".join(expansion_suggestions[:2])
        else:
            outline += expansion_suggestions[0]

        return outline

    def _compress_outline(self, outline: str, words_to_remove: int) -> str:
        """Compress outline by removing less essential details."""
        # This is a simplified compression - in practice, you might use AI
        # to intelligently compress the outline

        # Remove some less essential elements
        lines = outline.split("\n")
        compressed_lines = []

        for line in lines:
            # Skip lines that are less essential
            if (
                line.strip().startswith("<!--")
                or line.strip().startswith("- [Brief description")
                or line.strip().startswith("- [Character development")
            ):
                continue
            compressed_lines.append(line)

        return "\n".join(compressed_lines)

    def get_length_metrics(self, text: str, length_spec: LengthSpec) -> dict[str, Any]:
        """Get comprehensive length metrics for text."""
        word_count = self._count_words(text)
        target_words = length_spec.get_target_word_count()

        return {
            "word_count": word_count,
            "target_word_count": target_words,
            "deviation_percent": length_spec.get_deviation_percent(word_count),
            "is_within_tolerance": length_spec.is_within_tolerance(word_count),
            "reading_time_minutes": length_spec.get_target_reading_time(),
            "estimated_reading_time_minutes": max(
                1,
                round(word_count / length_spec.reading_speed),
            ),
            "adjustment_suggestion": length_spec.get_adjustment_suggestion(word_count),
        }
