#!/usr/bin/env python3
"""Demonstration of story length control functionality."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jestir.models.length_spec import LengthSpec
from jestir.models.story_context import StoryContext
from jestir.services.length_validator import LengthValidator


def demo_length_specifications():
    """Demonstrate different length specification types."""
    print("🔧 Length Specification Demo")
    print("=" * 50)

    # Word count specification
    word_spec = LengthSpec.from_word_count(500, tolerance_percent=10.0)
    print(f"Word Count Spec: {word_spec.get_target_word_count()} words")
    print(f"Reading Time: {word_spec.get_target_reading_time()} minutes")
    print(f"Tolerance: ±{word_spec.tolerance_percent}%")
    print(
        f"Range: {word_spec.get_min_word_count()}-{word_spec.get_max_word_count()} words",
    )
    print()

    # Reading time specification
    time_spec = LengthSpec.from_reading_time(
        3, reading_speed=200, tolerance_percent=15.0,
    )
    print(f"Reading Time Spec: {time_spec.get_target_reading_time()} minutes")
    print(f"Word Count: {time_spec.get_target_word_count()} words")
    print(f"Reading Speed: {time_spec.reading_speed} WPM")
    print(f"Tolerance: ±{time_spec.tolerance_percent}%")
    print()

    # Legacy length conversion
    legacy_spec = LengthSpec.from_legacy_length("medium")
    print(f"Legacy 'medium': {legacy_spec.get_target_word_count()} words")
    print(f"Legacy conversion back: {legacy_spec.to_legacy_length()}")
    print()


def demo_length_validation():
    """Demonstrate length validation functionality."""
    print("📏 Length Validation Demo")
    print("=" * 50)

    validator = LengthValidator()
    length_spec = LengthSpec.from_word_count(300, tolerance_percent=10.0)

    # Test different story lengths
    test_cases = [
        ("This is a very short story.", "Short story"),
        ("word " * 150, "Medium story (150 words)"),
        ("word " * 300, "Target length story (300 words)"),
        ("word " * 400, "Long story (400 words)"),
    ]

    for story, description in test_cases:
        result = validator.validate_story_length(story, length_spec)
        print(f"{description}:")
        print(f"  Words: {result['actual_word_count']}")
        print(f"  Target: {result['target_word_count']}")
        print(f"  Deviation: {result['deviation_percent']:.1f}%")
        print(f"  Within Tolerance: {'✅' if result['is_within_tolerance'] else '❌'}")
        print(f"  Suggestion: {result['suggestions'][0]}")
        print()


def demo_outline_length_control():
    """Demonstrate outline length control."""
    print("📋 Outline Length Control Demo")
    print("=" * 50)

    # Create a test context
    context = StoryContext()
    context.add_user_input("test_input", "A brave little mouse goes on an adventure")
    context.add_plot_point("The mouse finds a magical cheese")
    context.add_plot_point("The mouse must overcome obstacles")
    context.add_plot_point("The mouse learns about friendship")

    # Set different length specifications
    length_specs = [
        LengthSpec.from_word_count(200, tolerance_percent=15.0),
        LengthSpec.from_word_count(500, tolerance_percent=10.0),
        LengthSpec.from_reading_time(2, reading_speed=200, tolerance_percent=20.0),
    ]

    validator = LengthValidator()

    for i, length_spec in enumerate(length_specs, 1):
        print(f"Test {i}: {length_spec.get_target_word_count()} words target")
        context.set_length_spec(length_spec)

        # Generate outline (this would normally use OpenAI)
        # For demo, we'll create a mock outline
        mock_outline = """
        # Story Outline: The Brave Mouse's Adventure

        ## Act I: Beginning
        ### Scene 1: Introduction
        - The brave little mouse is introduced
        - The magical cheese is discovered

        ### Scene 2: The Call to Adventure
        - The mouse decides to go on an adventure
        - The first obstacle is encountered

        ## Act II: Middle
        ### Scene 3: The Journey
        - The mouse faces various challenges
        - Friends are made along the way

        ### Scene 4: The Climax
        - The biggest obstacle is faced
        - The mouse must use all learned skills

        ## Act III: End
        ### Scene 5: Resolution
        - The adventure is completed successfully
        - The mouse returns home wiser
        """

        # Validate outline length
        result = validator.validate_outline_length(mock_outline, length_spec)
        print(f"  Estimated words: {result['estimated_word_count']}")
        print(f"  Target words: {result['target_word_count']}")
        print(f"  Deviation: {result['deviation_percent']:.1f}%")
        print(f"  Within tolerance: {'✅' if result['is_within_tolerance'] else '❌'}")
        print()


def demo_length_metrics():
    """Demonstrate comprehensive length metrics."""
    print("📊 Length Metrics Demo")
    print("=" * 50)

    validator = LengthValidator()

    # Test with different length specifications
    test_story = "This is a test story with exactly twenty words in total."

    length_specs = [
        LengthSpec.from_word_count(100, tolerance_percent=10.0),
        LengthSpec.from_word_count(50, tolerance_percent=10.0),
        LengthSpec.from_reading_time(1, reading_speed=150, tolerance_percent=15.0),
    ]

    for i, length_spec in enumerate(length_specs, 1):
        print(f"Test {i}: {length_spec.length_type} = {length_spec.target_value}")
        metrics = validator.get_length_metrics(test_story, length_spec)

        print(f"  Word count: {metrics['word_count']}")
        print(f"  Target words: {metrics['target_word_count']}")
        print(f"  Deviation: {metrics['deviation_percent']:.1f}%")
        print(f"  Within tolerance: {'✅' if metrics['is_within_tolerance'] else '❌'}")
        print(f"  Reading time: {metrics['reading_time_minutes']} min")
        print(
            f"  Estimated reading time: {metrics['estimated_reading_time_minutes']} min",
        )
        print(f"  Adjustment: {metrics['adjustment_suggestion']}")
        print()


def demo_cli_usage():
    """Demonstrate CLI usage for length control."""
    print("💻 CLI Usage Demo")
    print("=" * 50)

    print("Create context with length specification:")
    print("  jestir context 'A brave mouse adventure' --length 500")
    print("  jestir context 'A brave mouse adventure' --length 3m --tolerance 15")
    print()

    print("Generate outline with length override:")
    print("  jestir outline context.yaml --length 300")
    print("  jestir outline context.yaml --length 2m --tolerance 20")
    print()

    print("Generate story with length override:")
    print("  jestir write outline.md --length 400")
    print("  jestir write outline.md --length 4m --tolerance 10")
    print()

    print("Validate length of files:")
    print("  jestir validate-length outline.md --type outline --suggestions")
    print("  jestir validate-length story.md --type story --context context.yaml")
    print()


def main():
    """Run all demonstrations."""
    print("🎭 Jestir Length Control Demonstration")
    print("=" * 60)
    print()

    try:
        demo_length_specifications()
        demo_length_validation()
        demo_outline_length_control()
        demo_length_metrics()
        demo_cli_usage()

        print("✅ All demonstrations completed successfully!")
        print()
        print("Key Features Demonstrated:")
        print("• Word count and reading time specifications")
        print("• Length validation with tolerance checking")
        print("• Outline length estimation and optimization")
        print("• Comprehensive length metrics")
        print("• CLI integration for length control")
        print("• Backward compatibility with legacy length settings")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
