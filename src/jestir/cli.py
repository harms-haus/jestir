"""Command-line interface for Jestir."""

import click
import yaml
import os
from pathlib import Path
from .services.context_generator import ContextGenerator
from .services.outline_generator import OutlineGenerator
from .services.story_writer import StoryWriter


@click.group()
@click.version_option()
def main():
    """Jestir: AI-powered bedtime story generator with 3-stage pipeline."""
    pass


@main.command()
@click.argument("input_text")
@click.option("--output", "-o", default="context.yaml", help="Output context file")
def context(input_text, output):
    """Generate context from natural language input."""
    try:
        click.echo(f"Generating context from: {input_text}")

        # Check for OpenAI API key
        if not os.getenv("OPENAI_EXTRACTION_API_KEY"):
            click.echo(
                "Warning: OPENAI_EXTRACTION_API_KEY not set. Using fallback extraction.",
                err=True,
            )

        # Generate context
        generator = ContextGenerator()
        context = generator.generate_context(input_text)

        # Convert to dict for YAML serialization
        context_dict = context.model_dump()

        # Write to file
        output_path = Path(output)
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(
                context_dict,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        click.echo(f"Context generated successfully: {output}")
        click.echo(
            f"Found {len(context.entities)} entities and {len(context.relationships)} relationships"
        )
        click.echo(f"Plot points: {len(context.plot_points)}")

    except Exception as e:
        click.echo(f"Error generating context: {str(e)}", err=True)
        raise click.Abort()


@main.command()
@click.argument("context_file")
@click.option("--output", "-o", default="outline.md", help="Output outline file")
def outline(context_file, output):
    """Generate story outline from context file."""
    try:
        click.echo(f"Generating outline from: {context_file}")

        # Check for OpenAI API key
        if not os.getenv("OPENAI_CREATIVE_API_KEY"):
            click.echo(
                "Warning: OPENAI_CREATIVE_API_KEY not set. Using fallback outline generation.",
                err=True,
            )

        # Load context from file
        generator = OutlineGenerator()
        context = generator.load_context_from_file(context_file)

        # Generate outline
        outline_content = generator.generate_outline(context)

        # Save outline to file
        generator.save_outline_to_file(outline_content, output)

        # Update context with outline and save back
        generator.update_context_with_outline(context, outline_content)

        # Save updated context back to file
        context_dict = context.model_dump()
        with open(context_file, "w", encoding="utf-8") as f:
            yaml.dump(
                context_dict,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        click.echo(f"Outline generated successfully: {output}")
        click.echo(f"Context file updated: {context_file}")

    except FileNotFoundError as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error generating outline: {str(e)}", err=True)
        raise click.Abort()


@main.command()
@click.argument("outline_file")
@click.option("--output", "-o", default="story.md", help="Output story file")
@click.option(
    "--context", "-c", default="context.yaml", help="Context file to load and update"
)
def write(outline_file, output, context):
    """Generate final story from outline file."""
    try:
        click.echo(f"Generating story from: {outline_file}")

        # Check for OpenAI API key
        if not os.getenv("OPENAI_CREATIVE_API_KEY"):
            click.echo(
                "Warning: OPENAI_CREATIVE_API_KEY not set. Using fallback story generation.",
                err=True,
            )

        # Load outline and context
        writer = StoryWriter()
        outline_content = writer.load_outline_from_file(outline_file)
        story_context = writer.load_context_from_file(context)

        # Generate story
        story_content = writer.generate_story(story_context, outline_content)

        # Save story to file
        writer.save_story_to_file(story_content, output)

        # Update context with story and save back
        writer.update_context_with_story(story_context, story_content)

        # Save updated context back to file
        context_dict = story_context.model_dump()
        with open(context, "w", encoding="utf-8") as f:
            yaml.dump(
                context_dict,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        # Calculate and display metrics
        word_count = writer.calculate_word_count(story_content)
        reading_time = writer.calculate_reading_time(word_count)

        click.echo(f"Story generated successfully: {output}")
        click.echo(f"Context file updated: {context}")
        click.echo(f"Word count: {word_count}")
        click.echo(f"Estimated reading time: {reading_time}")

    except FileNotFoundError as e:
        click.echo(f"Error: {str(e)}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error generating story: {str(e)}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
