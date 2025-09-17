#!/usr/bin/env python3
"""Demo script showing token usage tracking functionality."""

import sys
from pathlib import Path

# Add the src directory to the path so we can import jestir modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from jestir.services.token_tracker import TokenTracker


def demo_token_tracking():
    """Demonstrate token tracking functionality."""
    print("🔍 Token Usage Tracking Demo")
    print("=" * 50)

    # Create a token tracker
    tracker = TokenTracker()

    print("\n1. Tracking some API calls...")

    # Simulate some API calls
    tracker.track_usage(
        service="context_generator",
        operation="extract_entities_and_relationships",
        model="gpt-4o-mini",
        prompt_tokens=150,
        completion_tokens=75,
        input_text="A brave little girl named Lily goes on an adventure in a magic forest",
        output_text="Extracted entities: Lily (character), magic forest (location)...",
    )

    tracker.track_usage(
        service="outline_generator",
        operation="generate_outline",
        model="gpt-4o-mini",
        prompt_tokens=300,
        completion_tokens=200,
        input_text="Story context with characters and plot",
        output_text="# Story Outline: Lily's Adventure\n\n## Act I: Beginning...",
    )

    tracker.track_usage(
        service="story_writer",
        operation="generate_story",
        model="gpt-4o",
        prompt_tokens=500,
        completion_tokens=800,
        input_text="Story context and outline",
        output_text="# Lily's Adventure\n\nOnce upon a time, there was a brave little girl named Lily...",
    )

    print("✅ Tracked 3 API calls")

    print("\n2. Generating usage summary...")
    summary = tracker.get_usage_summary()

    print("📊 Summary:")
    print(f"   Total Tokens: {summary.total_tokens:,}")
    print(f"   Total Cost: ${summary.total_cost_usd:.4f}")
    print(f"   Total Calls: {summary.total_calls}")

    if summary.total_calls > 0:
        avg_tokens = summary.total_tokens / summary.total_calls
        avg_cost = summary.total_cost_usd / summary.total_calls
        print(f"   Average Tokens per Call: {avg_tokens:.1f}")
        print(f"   Average Cost per Call: ${avg_cost:.4f}")

    print("\n3. Usage by Service:")
    for service, data in summary.by_service.items():
        print(f"   {service}:")
        print(f"     Tokens: {data['total_tokens']:,}")
        print(f"     Cost: ${data['total_cost']:.4f}")
        print(f"     Calls: {data['total_calls']}")

    print("\n4. Usage by Model:")
    for model, data in summary.by_model.items():
        print(f"   {model}:")
        print(f"     Tokens: {data['total_tokens']:,}")
        print(f"     Cost: ${data['total_cost']:.4f}")
        print(f"     Calls: {data['total_calls']}")
        print(f"     Avg Tokens/Call: {data['avg_tokens_per_call']:.1f}")

    print("\n5. Generating optimization suggestions...")
    suggestions = tracker.generate_optimization_suggestions(summary)

    if suggestions:
        print("💡 Optimization Suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion.title}")
            print(f"      {suggestion.description}")
            if suggestion.potential_savings > 0:
                print(f"      Potential Savings: ${suggestion.potential_savings:.2f}")
            print(f"      Action: {suggestion.action_required}")
            print()
    else:
        print("   No optimization suggestions at this time.")

    print("\n6. Generating comprehensive report...")
    report = tracker.generate_report(period="monthly")

    print("📈 Monthly Report:")
    print(f"   Period: {report.period}")
    print(f"   Start Date: {report.start_date.strftime('%Y-%m-%d')}")
    print(f"   End Date: {report.end_date.strftime('%Y-%m-%d')}")
    print(f"   Total Tokens: {report.summary.total_tokens:,}")
    print(f"   Total Cost: ${report.summary.total_cost_usd:.4f}")

    print("\n7. Top Operations:")
    for i, op in enumerate(report.top_operations[:3], 1):
        print(f"   {i}. {op['operation']}")
        print(f"      Tokens: {op['total_tokens']:,}")
        print(f"      Cost: ${op['total_cost']:.4f}")
        print(f"      Calls: {op['total_calls']}")

    print("\n8. Saving usage to context file...")
    context_file = "demo_context.yaml"
    tracker.save_usage_to_context(context_file)
    print(f"✅ Saved usage data to {context_file}")

    print("\n9. Testing context file loading...")
    new_tracker = TokenTracker()
    new_tracker.load_usage_from_context(context_file)
    print(f"✅ Loaded {len(new_tracker.usage_history)} usage records from context file")

    print("\n10. Exporting report...")
    report_file = "demo_token_report.json"
    tracker.export_report(report, report_file)
    print(f"✅ Exported report to {report_file}")

    print("\n🎉 Token tracking demo completed!")
    print("\nTo use this in your own projects:")
    print("1. Import TokenTracker from jestir.services.token_tracker")
    print("2. Create a tracker instance: tracker = TokenTracker()")
    print("3. Track usage after API calls: tracker.track_usage(...)")
    print("4. Generate reports: report = tracker.generate_report()")
    print("5. Save to context: tracker.save_usage_to_context('context.yaml')")

    # Clean up demo files
    for file in [context_file, report_file]:
        file_path = Path(file)
        if file_path.exists():
            file_path.unlink()
            print(f"🧹 Cleaned up {file}")


if __name__ == "__main__":
    demo_token_tracking()
