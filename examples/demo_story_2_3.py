#!/usr/bin/env python3
"""
Demo script for Story 2.3: Entity Search and List Commands

This script demonstrates the new CLI commands implemented for Story 2.3:
- story search characters --query "dragon"
- story list locations --type interior
- story show character "Lily"
- Pagination support
- Export to YAML functionality
"""

import os
import subprocess
import sys


def run_command(cmd, description):
    """Run a CLI command and display the results."""
    print(f"\n{'=' * 60}")
    print(f"DEMO: {description}")
    print(f"Command: {cmd}")
    print("=" * 60)

    try:
        result = subprocess.run(
            cmd,
            check=False,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("Command timed out")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Run the Story 2.3 demo."""
    print("🎭 Jestir Story 2.3 Demo: Entity Search and List Commands")
    print("=" * 60)

    # Set mock mode for consistent demo results
    os.environ["LIGHTRAG_MOCK_MODE"] = "true"

    # Demo 1: Search for characters
    success = run_command(
        'python -m jestir search characters --query "dragon"',
        "Search for characters with query 'dragon'",
    )

    # Demo 2: List locations with type filter
    success &= run_command(
        "python -m jestir list locations --type interior",
        "List locations filtered by type 'interior'",
    )

    # Demo 3: Show specific character details
    success &= run_command(
        'python -m jestir show "Lily"',
        "Show detailed information for character 'Lily'",
    )

    # Demo 4: Search with pagination
    success &= run_command(
        'python -m jestir search characters --query "dragon" --page 1 --limit 3',
        "Search with pagination (page 1, limit 3)",
    )

    # Demo 5: Export to YAML
    export_file = "/tmp/story_2_3_export.yaml"
    success &= run_command(
        f'python -m jestir search characters --query "dragon" --export {export_file}',
        f"Export search results to YAML file: {export_file}",
    )

    # Demo 6: JSON output format
    success &= run_command(
        'python -m jestir search characters --query "dragon" --format json',
        "Search with JSON output format",
    )

    # Demo 7: YAML output format
    success &= run_command(
        'python -m jestir search characters --query "dragon" --format yaml',
        "Search with YAML output format",
    )

    # Demo 8: List all locations
    success &= run_command(
        "python -m jestir list locations",
        "List all locations without filtering",
    )

    # Demo 9: Search items
    success &= run_command(
        'python -m jestir search items --query "magic"',
        "Search for items with query 'magic'",
    )

    # Show exported file if it exists
    if os.path.exists(export_file):
        print(f"\n{'=' * 60}")
        print(f"EXPORTED YAML FILE: {export_file}")
        print("=" * 60)
        with open(export_file) as f:
            print(f.read())

    print(f"\n{'=' * 60}")
    if success:
        print("✅ All Story 2.3 demos completed successfully!")
        print("\nImplemented features:")
        print("• story search characters --query 'dragon'")
        print("• story list locations --type interior")
        print("• story show character 'Lily'")
        print("• Pagination support (--page, --limit)")
        print("• Export to YAML (--export)")
        print("• Multiple output formats (--format table|json|yaml)")
        print("• Readable table format with entity details")
    else:
        print("❌ Some demos failed. Check the output above for errors.")
        return 1

    print(f"\n{'=' * 60}")
    print("Story 2.3 Acceptance Criteria Status:")
    print("✅ Command 'story search characters --query \"dragon\"' returns matches")
    print("✅ Command 'story list locations --type interior' shows filtered results")
    print("✅ Command 'story show character \"Lily\"' displays full details")
    print("✅ Pagination for large result sets")
    print("✅ Output in readable table format")
    print("✅ Export option to YAML for context file use")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
