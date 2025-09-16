"""Command-line interface for Jestir."""

import click


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
    click.echo(f"Generating context from: {input_text}")
    click.echo(f"Output file: {output}")
    # TODO: Implement context generation


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
