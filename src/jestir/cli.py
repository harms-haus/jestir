"""Command-line interface for Jestir."""

import click
import yaml
import os
import asyncio
import json
from pathlib import Path
from .services.context_generator import ContextGenerator
from .services.outline_generator import OutlineGenerator
from .services.story_writer import StoryWriter
from .services.lightrag_client import LightRAGClient
from .services.template_loader import TemplateLoader
from .models.api_config import LightRAGAPIConfig


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


@main.command()
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation results")
@click.option("--fix", is_flag=True, help="Attempt to fix common template issues")
def validate_templates(verbose, fix):
    """Validate all template files for syntax and completeness."""
    try:
        click.echo("Validating template files...")

        loader = TemplateLoader()
        templates = loader.get_available_templates()

        total_templates = 0
        valid_templates = 0
        issues_found = []

        # Define required variables for each template type
        required_vars = {
            "context_extraction": ["input_text"],
            "outline_generation": [
                "genre",
                "tone",
                "length",
                "age_appropriate",
                "morals",
                "characters",
                "locations",
                "items",
                "plot_points",
                "user_inputs",
            ],
            "story_generation": [
                "genre",
                "tone",
                "length",
                "target_word_count",
                "age_appropriate",
                "morals",
                "characters",
                "locations",
                "items",
                "plot_points",
                "user_inputs",
                "outline",
            ],
        }

        # Validate system prompts
        click.echo("\n📋 Validating system prompts...")
        for template_name in templates["system_prompts"]:
            total_templates += 1
            try:
                template_path = f"prompts/system_prompts/{template_name}.txt"
                content = loader.load_template(template_path)

                # System prompts are typically static, so just check they load successfully
                if content.strip():
                    valid_templates += 1
                    if verbose:
                        click.echo(f"  ✅ {template_name}.txt - OK")
                else:
                    issues_found.append(f"System prompt {template_name}.txt is empty")
                    if verbose:
                        click.echo(f"  ❌ {template_name}.txt - Empty file")

            except Exception as e:
                issues_found.append(f"System prompt {template_name}.txt - {str(e)}")
                if verbose:
                    click.echo(f"  ❌ {template_name}.txt - Error: {str(e)}")

        # Validate user prompts
        click.echo("\n📝 Validating user prompts...")
        for template_name in templates["user_prompts"]:
            total_templates += 1
            try:
                template_path = f"prompts/user_prompts/{template_name}.txt"
                content = loader.load_template(template_path)

                # Check for required variables
                if template_name in required_vars:
                    validation = loader.validate_template(
                        template_path, required_vars[template_name]
                    )
                    if validation["valid"]:
                        valid_templates += 1
                        if verbose:
                            click.echo(
                                f"  ✅ {template_name}.txt - All required variables present"
                            )
                    else:
                        missing = ", ".join(validation["missing_vars"])
                        issues_found.append(
                            f"User prompt {template_name}.txt missing variables: {missing}"
                        )
                        if verbose:
                            click.echo(f"  ❌ {template_name}.txt - Missing: {missing}")
                else:
                    # Just check basic syntax
                    if "{{" in content and "}}" in content:
                        valid_templates += 1
                        if verbose:
                            click.echo(f"  ✅ {template_name}.txt - OK")
                    else:
                        issues_found.append(
                            f"User prompt {template_name}.txt has no template variables"
                        )
                        if verbose:
                            click.echo(
                                f"  ⚠️  {template_name}.txt - No template variables"
                            )

            except Exception as e:
                issues_found.append(f"User prompt {template_name}.txt - {str(e)}")
                if verbose:
                    click.echo(f"  ❌ {template_name}.txt - Error: {str(e)}")

        # Validate include templates
        click.echo("\n🧩 Validating include templates...")
        for template_name in templates["includes"]:
            total_templates += 1
            try:
                template_path = f"prompts/includes/{template_name}.txt"
                content = loader.load_template(template_path)

                # Check for basic template syntax
                if "{{" in content and "}}" in content:
                    valid_templates += 1
                    if verbose:
                        click.echo(f"  ✅ {template_name}.txt - OK")
                else:
                    issues_found.append(
                        f"Include template {template_name}.txt has no template variables"
                    )
                    if verbose:
                        click.echo(f"  ⚠️  {template_name}.txt - No template variables")

            except Exception as e:
                issues_found.append(f"Include template {template_name}.txt - {str(e)}")
                if verbose:
                    click.echo(f"  ❌ {template_name}.txt - Error: {str(e)}")

        # Summary
        click.echo(f"\n📊 Validation Summary:")
        click.echo(f"  Total templates: {total_templates}")
        click.echo(f"  Valid templates: {valid_templates}")
        click.echo(f"  Issues found: {len(issues_found)}")

        if issues_found:
            click.echo(f"\n❌ Issues found:")
            for issue in issues_found:
                click.echo(f"  • {issue}")

            if fix:
                click.echo(f"\n🔧 Fix suggestions:")
                click.echo(f"  • Check template syntax ({{{{variable}}}})")
                click.echo(f"  • Ensure all required variables are present")
                click.echo(f"  • Verify file paths and permissions")
                click.echo(f"  • Check for typos in variable names")

            raise click.Abort()
        else:
            click.echo(f"\n✅ All templates are valid!")

    except Exception as e:
        click.echo(f"Error validating templates: {str(e)}", err=True)
        raise click.Abort()


@main.group()
def lightrag():
    """LightRAG API testing and validation commands."""
    pass


@lightrag.command()
@click.option("--base-url", default=None, help="LightRAG API base URL")
@click.option("--api-key", default=None, help="LightRAG API key")
@click.option("--timeout", default=30, help="Request timeout in seconds")
def test(base_url, api_key, timeout):
    """Test LightRAG API connectivity and configuration."""
    try:
        click.echo("Testing LightRAG API connectivity...")

        # Create configuration
        config = LightRAGAPIConfig(
            base_url=base_url
            or os.getenv("LIGHTRAG_BASE_URL", "http://localhost:8000"),
            api_key=api_key or os.getenv("LIGHTRAG_API_KEY"),
            timeout=timeout,
            mock_mode=os.getenv("LIGHTRAG_MOCK_MODE", "false").lower() == "true",
        )

        client = LightRAGClient(config)

        # Test basic connectivity
        click.echo(f"Configuration:")
        click.echo(f"  Base URL: {config.base_url}")
        click.echo(f"  API Key: {'***' if config.api_key else 'Not set'}")
        click.echo(f"  Timeout: {config.timeout}s")
        click.echo(f"  Mock Mode: {config.mock_mode}")

        # Test entity types
        click.echo("\nTesting entity types...")
        types = asyncio.run(client.get_available_entity_types())
        click.echo(f"Available entity types: {', '.join(types)}")

        # Test search functionality
        click.echo("\nTesting search functionality...")
        result = asyncio.run(client.search_entities("test", top_k=3))
        click.echo(f"Search test returned {len(result.entities)} entities")

        click.echo("\n✅ LightRAG API test completed successfully!")

    except Exception as e:
        click.echo(f"❌ LightRAG API test failed: {str(e)}", err=True)
        raise click.Abort()


@lightrag.command()
@click.argument("query")
@click.option(
    "--type", "entity_type", help="Filter by entity type (character, location, item)"
)
@click.option(
    "--mode",
    default="mix",
    help="Query mode (local, global, hybrid, naive, mix, bypass)",
)
@click.option("--limit", "top_k", default=10, help="Maximum number of results")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
def search(query, entity_type, mode, top_k, output_format):
    """Search for entities in LightRAG API."""
    try:
        click.echo(f"Searching LightRAG for: '{query}'")

        config = LightRAGAPIConfig(
            base_url=os.getenv("LIGHTRAG_BASE_URL", "http://localhost:8000"),
            api_key=os.getenv("LIGHTRAG_API_KEY"),
            timeout=int(os.getenv("LIGHTRAG_TIMEOUT", "30")),
            mock_mode=os.getenv("LIGHTRAG_MOCK_MODE", "false").lower() == "true",
        )

        client = LightRAGClient(config)
        result = asyncio.run(client.search_entities(query, entity_type, mode, top_k))

        if output_format == "json":
            output_data = {
                "query": result.query,
                "mode": result.mode,
                "total_count": result.total_count,
                "entities": [
                    {
                        "name": e.name,
                        "type": e.entity_type,
                        "description": e.description,
                        "properties": e.properties,
                    }
                    for e in result.entities
                ],
            }
            click.echo(json.dumps(output_data, indent=2))
        elif output_format == "yaml":
            output_data = {
                "query": result.query,
                "mode": result.mode,
                "total_count": result.total_count,
                "entities": [
                    {
                        "name": e.name,
                        "type": e.entity_type,
                        "description": e.description,
                        "properties": e.properties,
                    }
                    for e in result.entities
                ],
            }
            click.echo(yaml.dump(output_data, default_flow_style=False))
        else:  # table format
            if result.entities:
                click.echo(f"\nFound {result.total_count} entities:")
                click.echo("-" * 80)
                for i, entity in enumerate(result.entities, 1):
                    click.echo(f"{i}. {entity.name} ({entity.entity_type})")
                    if entity.description:
                        desc = (
                            entity.description[:100] + "..."
                            if len(entity.description) > 100
                            else entity.description
                        )
                        click.echo(f"   Description: {desc}")
                    if entity.properties:
                        props = ", ".join(
                            [f"{k}: {v}" for k, v in entity.properties.items()]
                        )
                        click.echo(f"   Properties: {props}")
                    click.echo()
            else:
                click.echo("No entities found.")

    except Exception as e:
        click.echo(f"Error searching LightRAG: {str(e)}", err=True)
        raise click.Abort()


@lightrag.command()
@click.argument("entity_name")
def show(entity_name):
    """Show detailed information about a specific entity."""
    try:
        click.echo(f"Getting details for entity: '{entity_name}'")

        config = LightRAGAPIConfig(
            base_url=os.getenv("LIGHTRAG_BASE_URL", "http://localhost:8000"),
            api_key=os.getenv("LIGHTRAG_API_KEY"),
            timeout=int(os.getenv("LIGHTRAG_TIMEOUT", "30")),
            mock_mode=os.getenv("LIGHTRAG_MOCK_MODE", "false").lower() == "true",
        )

        client = LightRAGClient(config)
        entity = asyncio.run(client.get_entity_details(entity_name))

        if entity:
            click.echo(f"\nEntity Details:")
            click.echo(f"Name: {entity.name}")
            click.echo(f"Type: {entity.entity_type}")
            if entity.description:
                click.echo(f"Description: {entity.description}")
            if entity.properties:
                click.echo(f"Properties:")
                for key, value in entity.properties.items():
                    click.echo(f"  {key}: {value}")
            if entity.relationships:
                click.echo(f"Relationships: {', '.join(entity.relationships)}")
        else:
            click.echo(f"Entity '{entity_name}' not found.")

    except Exception as e:
        click.echo(f"Error getting entity details: {str(e)}", err=True)
        raise click.Abort()


@lightrag.command()
@click.argument("name")
@click.option("--type", "entity_type", help="Filter by entity type")
def fuzzy(name, entity_type):
    """Perform fuzzy search for entities by name."""
    try:
        click.echo(f"Fuzzy searching for: '{name}'")

        config = LightRAGAPIConfig(
            base_url=os.getenv("LIGHTRAG_BASE_URL", "http://localhost:8000"),
            api_key=os.getenv("LIGHTRAG_API_KEY"),
            timeout=int(os.getenv("LIGHTRAG_TIMEOUT", "30")),
            mock_mode=os.getenv("LIGHTRAG_MOCK_MODE", "false").lower() == "true",
        )

        client = LightRAGClient(config)
        results = asyncio.run(client.fuzzy_search_entities(name, entity_type))

        if results:
            click.echo(f"\nFound {len(results)} fuzzy matches:")
            click.echo("-" * 60)
            for i, entity in enumerate(results, 1):
                click.echo(f"{i}. {entity.name} ({entity.entity_type})")
                if entity.description:
                    desc = (
                        entity.description[:80] + "..."
                        if len(entity.description) > 80
                        else entity.description
                    )
                    click.echo(f"   {desc}")
                click.echo()
        else:
            click.echo("No fuzzy matches found.")

    except Exception as e:
        click.echo(f"Error in fuzzy search: {str(e)}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
