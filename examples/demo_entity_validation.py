#!/usr/bin/env python3
"""Demo script showing entity validation functionality."""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jestir.services.entity_validator import EntityValidator
from jestir.services.lightrag_client import LightRAGEntity


async def demo_entity_validation():
    """Demonstrate entity validation with various test cases."""
    print("🔍 Entity Validation Demo")
    print("=" * 50)

    validator = EntityValidator()

    # Test cases
    test_cases = [
        {
            "query": "Wendy Whisk",
            "entity": LightRAGEntity(
                name="Wendy Whisk",
                entity_type="character",
                description="A friendly orange cat with long whiskers",
                properties={"age": "3 years", "color": "orange"},
            ),
            "entity_type": "character",
            "description": "Exact match",
        },
        {
            "query": "Wendy",
            "entity": LightRAGEntity(
                name="Wendy Whisk",
                entity_type="character",
                description="A friendly orange cat with long whiskers",
                properties={"age": "3 years", "color": "orange"},
            ),
            "entity_type": "character",
            "description": "Partial match (high confidence)",
        },
        {
            "query": "whiskers",
            "entity": LightRAGEntity(
                name="Wendy Whisk",
                entity_type="character",
                description="A friendly orange cat with long whiskers",
                properties={"age": "3 years", "color": "orange"},
            ),
            "entity_type": "character",
            "description": "Low confidence match (your example)",
        },
        {
            "query": "Alice",
            "entity": LightRAGEntity(
                name="Wendy Whisk",
                entity_type="character",
                description="A friendly orange cat with long whiskers",
                properties={"age": "3 years", "color": "orange"},
            ),
            "entity_type": "character",
            "description": "No match",
        },
        {
            "query": "Wendy Whisk",
            "entity": LightRAGEntity(
                name="Wendy Whisk",
                entity_type="location",
                description="A magical forest clearing",
            ),
            "entity_type": "character",
            "description": "Exact name match but wrong type",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print("-" * 30)
        print(f"Query: '{test_case['query']}'")
        print(f"Entity: '{test_case['entity'].name}' ({test_case['entity'].entity_type})")

        result = validator.validate_entity_match(
            test_case["query"],
            test_case["entity"],
            test_case["entity_type"],
        )

        print(f"Similarity Score: {result.similarity_score:.3f}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Exact Match: {result.is_exact_match}")
        print(f"High Confidence: {result.is_high_confidence}")
        print(f"Requires Confirmation: {validator.should_require_confirmation(result)}")
        print(f"Match Reason: {result.match_reason}")

        # Show recommendation
        if result.confidence >= 0.8:
            print("✅ Recommendation: Use this match")
        elif result.confidence >= 0.5:
            print("⚠️  Recommendation: Verify this match")
        else:
            print("❌ Recommendation: This match may not be correct")

    print("\n" + "=" * 50)
    print("🎯 Key Benefits:")
    print("• Prevents incorrect entity matches like 'whiskers' → 'Wendy Whisk'")
    print("• Provides confidence scoring for all matches")
    print("• Warns users about low-confidence matches")
    print("• Considers entity type, description quality, and properties")
    print("• Configurable thresholds for different use cases")


if __name__ == "__main__":
    asyncio.run(demo_entity_validation())
