"""Command-line interface for Jestir."""

import click
import yaml
import os
from pathlib import Path
from .services.context_generator import ContextGenerator


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
    click.echo(f"Generating outline from: {context_file}")
    click.echo(f"Output file: {output}")
    # TODO: Implement outline generation


@main.command()
@click.argument("outline_file")
@click.option("--output", "-o", default="story.md", help="Output story file")
def write(outline_file, output):
    """Generate final story from outline file."""
    click.echo(f"Generating story from: {outline_file}")
    click.echo(f"Output file: {output}")
    # TODO: Implement story generation


if __name__ == "__main__":
    main()
