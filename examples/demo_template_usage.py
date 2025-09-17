#!/usr/bin/env python3
"""
Demo script showing how to use the template system programmatically.

This script demonstrates:
1. Loading templates with the TemplateLoader
2. Rendering templates with context data
3. Validating templates
4. Using different template types
"""

import sys
from pathlib import Path

# Add the src directory to the path so we can import jestir modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jestir.services.template_loader import TemplateLoader


def demo_basic_template_usage():
    """Demonstrate basic template loading and rendering."""
    print("=== Basic Template Usage Demo ===\n")

    # Initialize the template loader
    loader = TemplateLoader()

    # Example context data
    context = {
        "name": "Thumper",
        "description": "A brave little rabbit with soft brown fur",
        "personality": "curious and determined",
        "species": "rabbit",
        "role": "protagonist",
    }

    print("1. Loading a character template...")
    try:
        # Load a character template
        template_content = loader.load_character_template("protagonist")
        print(f"✅ Loaded protagonist template")
        print(f"Template content preview: {template_content[:100]}...")

        # Render the template with context
        rendered = loader.render_template(
            "prompts/includes/character_protagonist.txt", context
        )
        print(f"\n✅ Rendered template with context:")
        print(rendered)

    except Exception as e:
        print(f"❌ Error: {e}")


def demo_user_prompt_rendering():
    """Demonstrate rendering user prompts with story context."""
    print("\n=== User Prompt Rendering Demo ===\n")

    loader = TemplateLoader()

    # Example story context
    story_context = {
        "genre": "adventure",
        "tone": "gentle",
        "length": "short",
        "age_appropriate": True,
        "morals": "courage, friendship, perseverance",
        "characters": "- Thumper: A brave little rabbit (protagonist)\n- Wise Old Owl: A mysterious forest guide (supporting)",
        "locations": "- Whispering Woods: A magical forest (exterior)\n- Crystal Cave: A hidden cave with glowing crystals (magical)",
        "items": "- Golden Carrot: A magical carrot that brings rain (magical)",
        "plot_points": "- Thumper decides to find the magical carrot\n- Thumper meets the Wise Old Owl\n- Thumper solves the cave riddle",
        "user_inputs": "A brave little rabbit named Thumper goes on an adventure to find the magical carrot",
    }

    print("2. Rendering outline generation prompt...")
    try:
        rendered_prompt = loader.render_template(
            "prompts/user_prompts/outline_generation.txt", story_context
        )
        print(f"✅ Rendered outline generation prompt")
        print(f"Prompt preview: {rendered_prompt[:200]}...")

    except Exception as e:
        print(f"❌ Error: {e}")


def demo_template_validation():
    """Demonstrate template validation."""
    print("\n=== Template Validation Demo ===\n")

    loader = TemplateLoader()

    print("3. Validating templates...")

    # Get available templates
    templates = loader.get_available_templates()
    print(f"Found {sum(len(t) for t in templates.values())} templates:")
    for category, template_list in templates.items():
        print(f"  {category}: {len(template_list)} templates")

    # Validate a specific template
    print(f"\n4. Validating character_protagonist template...")
    try:
        validation = loader.validate_template(
            "prompts/includes/character_protagonist.txt",
            ["name", "description", "personality"],
        )

        if validation["valid"]:
            print("✅ Template is valid")
        else:
            print(f"❌ Template validation failed:")
            print(f"  Missing variables: {validation['missing_vars']}")
            print(f"  Extra variables: {validation['extra_vars']}")

    except Exception as e:
        print(f"❌ Error validating template: {e}")


def demo_template_caching():
    """Demonstrate template caching functionality."""
    print("\n=== Template Caching Demo ===\n")

    loader = TemplateLoader()

    print("5. Testing template caching...")

    # Load the same template twice
    template1 = loader.load_template("prompts/includes/character_protagonist.txt")
    template2 = loader.load_template("prompts/includes/character_protagonist.txt")

    # Check if they're the same (should be from cache)
    if template1 == template2:
        print("✅ Template caching is working (same content returned)")
    else:
        print("❌ Template caching may not be working")

    # Check cache size
    cache_size = len(loader._template_cache)
    print(f"Cache contains {cache_size} templates")

    # Clear cache
    loader.clear_cache()
    print("✅ Cache cleared")
    print(f"Cache now contains {len(loader._template_cache)} templates")


def main():
    """Run all demos."""
    print("🎭 Jestir Template System Demo")
    print("=" * 50)

    try:
        demo_basic_template_usage()
        demo_user_prompt_rendering()
        demo_template_validation()
        demo_template_caching()

        print("\n" + "=" * 50)
        print("✅ All demos completed successfully!")
        print("\nTo run the CLI template validation:")
        print("  python -m jestir validate-templates --verbose")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
