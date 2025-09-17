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

    except FileNotFoundError as e:
        click.echo(f"❌ File Error: Cannot access file - {str(e)}", err=True)
        click.echo(
            "💡 Tip: Make sure you have write permissions to the output directory",
            err=True,
        )
        raise click.Abort()
    except PermissionError as e:
        click.echo(
            f"❌ Permission Error: Cannot write to output file - {str(e)}", err=True
        )
        click.echo(
            "💡 Tip: Check file permissions or try a different output directory",
            err=True,
        )
        raise click.Abort()
    except Exception as e:
        error_msg = str(e).lower()
        if "api" in error_msg or "openai" in error_msg:
            click.echo(f"❌ API Error: {str(e)}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your OPENAI_EXTRACTION_API_KEY environment variable",
                err=True,
            )
            click.echo(
                "   • Verify your OpenAI account has sufficient credits", err=True
            )
            click.echo("   • Check your internet connection", err=True)
        elif "template" in error_msg:
            click.echo(f"❌ Template Error: {str(e)}", err=True)
            click.echo(
                "💡 Tip: Run 'jestir validate-templates' to check template files",
                err=True,
            )
        else:
            click.echo(f"❌ Unexpected Error: {str(e)}", err=True)
            click.echo(
                "💡 Tip: Try running with a simpler input text or check the logs",
                err=True,
            )
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
        click.echo(f"❌ File Not Found: {str(e)}", err=True)
        click.echo("💡 Troubleshooting:", err=True)
        click.echo(f"   • Make sure the context file '{context_file}' exists", err=True)
        click.echo(
            f"   • Generate a context file first: 'jestir context \"your story idea\"'",
            err=True,
        )
        click.echo(f"   • Check the file path is correct", err=True)
        raise click.Abort()
    except PermissionError as e:
        click.echo(
            f"❌ Permission Error: Cannot write to output file - {str(e)}", err=True
        )
        click.echo(
            "💡 Tip: Check file permissions or try a different output directory",
            err=True,
        )
        raise click.Abort()
    except Exception as e:
        error_msg = str(e).lower()
        if "api" in error_msg or "openai" in error_msg:
            click.echo(f"❌ API Error: {str(e)}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your OPENAI_CREATIVE_API_KEY environment variable", err=True
            )
            click.echo(
                "   • Verify your OpenAI account has sufficient credits", err=True
            )
            click.echo("   • Check your internet connection", err=True)
        elif "yaml" in error_msg or "parse" in error_msg:
            click.echo(
                f"❌ Context File Error: Invalid YAML format - {str(e)}", err=True
            )
            click.echo(
                f"💡 Tip: Check that '{context_file}' is a valid YAML file", err=True
            )
        else:
            click.echo(f"❌ Unexpected Error: {str(e)}", err=True)
            click.echo(
                "💡 Tip: Check that your context file is valid and complete", err=True
            )
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
        error_str = str(e)
        click.echo(f"❌ File Not Found: {error_str}", err=True)
        click.echo("💡 Troubleshooting:", err=True)
        if outline_file in error_str:
            click.echo(
                f"   • Generate an outline first: 'jestir outline {context}'", err=True
            )
            click.echo(
                f"   • Make sure the outline file '{outline_file}' exists", err=True
            )
        elif context in error_str:
            click.echo(
                f"   • Generate a context file first: 'jestir context \"your story idea\"'",
                err=True,
            )
            click.echo(f"   • Make sure the context file '{context}' exists", err=True)
        click.echo(f"   • Check the file paths are correct", err=True)
        raise click.Abort()
    except PermissionError as e:
        click.echo(
            f"❌ Permission Error: Cannot write to output file - {str(e)}", err=True
        )
        click.echo(
            "💡 Tip: Check file permissions or try a different output directory",
            err=True,
        )
        raise click.Abort()
    except Exception as e:
        error_msg = str(e).lower()
        if "api" in error_msg or "openai" in error_msg:
            click.echo(f"❌ API Error: {str(e)}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your OPENAI_CREATIVE_API_KEY environment variable", err=True
            )
            click.echo(
                "   • Verify your OpenAI account has sufficient credits", err=True
            )
            click.echo("   • Check your internet connection", err=True)
        elif "yaml" in error_msg or "parse" in error_msg:
            click.echo(
                f"❌ File Format Error: Invalid YAML format - {str(e)}", err=True
            )
            click.echo(f"💡 Tip: Check that your files are valid YAML format", err=True)
        else:
            click.echo(f"❌ Unexpected Error: {str(e)}", err=True)
            click.echo(
                "💡 Tip: Check that your outline and context files are valid and complete",
                err=True,
            )
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

    except FileNotFoundError as e:
        click.echo(f"❌ Template Directory Not Found: {str(e)}", err=True)
        click.echo("💡 Troubleshooting:", err=True)
        click.echo(
            "   • Make sure you're running from the project root directory", err=True
        )
        click.echo("   • Verify the templates/ directory exists", err=True)
        click.echo("   • Check that template files are properly installed", err=True)
        raise click.Abort()
    except PermissionError as e:
        click.echo(
            f"❌ Permission Error: Cannot read template files - {str(e)}", err=True
        )
        click.echo(
            "💡 Tip: Check file permissions in the templates/ directory", err=True
        )
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Template Validation Error: {str(e)}", err=True)
        click.echo("💡 Troubleshooting:", err=True)
        click.echo(
            "   • Check that all template files are properly formatted", err=True
        )
        click.echo("   • Verify template syntax uses {{variable}} format", err=True)
        click.echo("   • Make sure templates/ directory structure is correct", err=True)
        raise click.Abort()


@main.command()
@click.argument("context_file")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation results")
@click.option("--fix", is_flag=True, help="Attempt to fix common issues automatically")
def validate(context_file, verbose, fix):
    """Validate a context file for structure and consistency."""
    try:
        click.echo(f"Validating context file: {context_file}")

        # Import the validation service
        from .services.context_validator import ContextValidator

        # Create validator instance
        validator = ContextValidator()

        # Load and validate context
        validation_result = validator.validate_context_file(
            context_file, verbose=verbose, auto_fix=fix
        )

        # Display results
        if validation_result.is_valid:
            click.echo("✅ Context file is valid!")
            if validation_result.warnings:
                click.echo(f"\n⚠️  {len(validation_result.warnings)} warnings found:")
                for warning in validation_result.warnings:
                    click.echo(f"  • {warning}")
        else:
            click.echo("❌ Context file has validation errors:")
            for error in validation_result.errors:
                click.echo(f"  • {error}")

            if validation_result.suggestions:
                click.echo("\n💡 Fix suggestions:")
                for suggestion in validation_result.suggestions:
                    click.echo(f"  • {suggestion}")

            raise click.Abort()

    except FileNotFoundError as e:
        click.echo(f"❌ File Not Found: {str(e)}", err=True)
        click.echo("💡 Troubleshooting:", err=True)
        click.echo(f"   • Make sure the context file '{context_file}' exists", err=True)
        click.echo(
            f"   • Generate a context file first: 'jestir context \"your story idea\"'",
            err=True,
        )
        click.echo(f"   • Check the file path is correct", err=True)
        raise click.Abort()
    except PermissionError as e:
        click.echo(f"❌ Permission Error: Cannot read file - {str(e)}", err=True)
        click.echo("💡 Tip: Check file permissions", err=True)
        raise click.Abort()
    except Exception as e:
        error_msg = str(e).lower()
        if "yaml" in error_msg or "parse" in error_msg:
            click.echo(
                f"❌ File Format Error: Invalid YAML format - {str(e)}", err=True
            )
            click.echo(
                "💡 Tip: Check that the context file is valid YAML format", err=True
            )
        else:
            click.echo(f"❌ Validation Error: {str(e)}", err=True)
            click.echo(
                "💡 Tip: Check that your context file is properly formatted", err=True
            )
        raise click.Abort()


@main.command()
@click.argument("entity_type", type=click.Choice(["characters", "locations", "items"]))
@click.option("--query", "-q", help="Search query to filter results")
@click.option(
    "--type",
    "filter_type",
    help="Filter by specific type (e.g., 'interior' for locations)",
)
@click.option("--limit", "-l", default=10, help="Maximum number of results to show")
@click.option("--page", "-p", default=1, help="Page number for pagination")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.option("--export", "-e", help="Export results to YAML file for context use")
def search(entity_type, query, filter_type, limit, page, output_format, export):
    """Search for entities in LightRAG API."""
    try:
        # Map entity_type to LightRAG entity type
        entity_type_map = {
            "characters": "character",
            "locations": "location",
            "items": "item",
        }
        lightrag_type = entity_type_map[entity_type]

        # Build search query
        search_query = query or f"all {entity_type}"
        if filter_type:
            search_query = f"{filter_type} {entity_type}: {search_query}"

        click.echo(f"Searching {entity_type} for: '{search_query}'")

        config = LightRAGAPIConfig(
            base_url=os.getenv("LIGHTRAG_BASE_URL", "http://localhost:8000"),
            api_key=os.getenv("LIGHTRAG_API_KEY"),
            timeout=int(os.getenv("LIGHTRAG_TIMEOUT", "30")),
            mock_mode=os.getenv("LIGHTRAG_MOCK_MODE", "false").lower() == "true",
        )

        client = LightRAGClient(config)

        # Calculate pagination
        offset = (page - 1) * limit
        total_limit = offset + limit

        result = asyncio.run(
            client.search_entities(search_query, lightrag_type, "mix", total_limit)
        )

        # Apply pagination to results
        paginated_entities = result.entities[offset : offset + limit]
        total_pages = (result.total_count + limit - 1) // limit

        # Prepare output data
        output_data = {
            "query": result.query,
            "entity_type": entity_type,
            "total_count": result.total_count,
            "page": page,
            "total_pages": total_pages,
            "limit": limit,
            "entities": [
                {
                    "name": e.name,
                    "type": e.entity_type,
                    "description": e.description,
                    "properties": e.properties,
                }
                for e in paginated_entities
            ],
        }

        if output_format == "json":
            click.echo(json.dumps(output_data, indent=2))
        elif output_format == "yaml":
            click.echo(yaml.dump(output_data, default_flow_style=False))
        else:  # table format
            if paginated_entities:
                page_info = (
                    f" (page {page} of {total_pages})" if total_pages > 1 else ""
                )
                click.echo(f"\nFound {result.total_count} {entity_type}{page_info}:")
                click.echo("-" * 80)
                for i, entity in enumerate(paginated_entities, offset + 1):
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

                # Show pagination info
                if total_pages > 1:
                    click.echo(
                        f"Showing {len(paginated_entities)} of {result.total_count} results"
                    )
                    if page < total_pages:
                        click.echo(f"Use --page {page + 1} to see more results")
            else:
                click.echo(f"No {entity_type} found.")

        # Export to YAML if requested
        if export:
            with open(export, "w", encoding="utf-8") as f:
                yaml.dump(output_data, f, default_flow_style=False, allow_unicode=True)
            click.echo(f"Results exported to: {export}")

    except Exception as e:
        error_msg = str(e).lower()
        if (
            "connection" in error_msg
            or "timeout" in error_msg
            or "refused" in error_msg
        ):
            click.echo(
                f"❌ Connection Error: Cannot reach LightRAG API - {str(e)}", err=True
            )
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(f"   • Check LIGHTRAG_BASE_URL: {config.base_url}", err=True)
            click.echo("   • Verify LightRAG service is running", err=True)
            click.echo("   • Check your network connection", err=True)
            click.echo("   • Try using mock mode: LIGHTRAG_MOCK_MODE=true", err=True)
        elif "unauthorized" in error_msg or "forbidden" in error_msg:
            click.echo(f"❌ Authentication Error: {str(e)}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your LIGHTRAG_API_KEY environment variable", err=True
            )
            click.echo("   • Verify the API key is valid and not expired", err=True)
        elif "invalid" in error_msg and "query" in error_msg:
            click.echo(f"❌ Query Error: {str(e)}", err=True)
            click.echo("💡 Tips:", err=True)
            click.echo(f"   • Try a simpler search query", err=True)
            click.echo(f"   • Check spelling and try different keywords", err=True)
            click.echo(
                f"   • Use 'jestir list {entity_type}' to see all available entities",
                err=True,
            )
        else:
            click.echo(f"❌ Search Error: {str(e)}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(f"   • Try using mock mode: LIGHTRAG_MOCK_MODE=true", err=True)
            click.echo(f"   • Check LightRAG service status", err=True)
            click.echo(
                f"   • Use 'jestir lightrag test' to verify configuration", err=True
            )
        raise click.Abort()


@main.command(name="list")
@click.argument("entity_type", type=click.Choice(["characters", "locations", "items"]))
@click.option(
    "--type",
    "filter_type",
    help="Filter by specific type (e.g., 'interior' for locations)",
)
@click.option("--limit", "-l", default=20, help="Maximum number of results to show")
@click.option("--page", "-p", default=1, help="Page number for pagination")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.option("--export", "-e", help="Export results to YAML file for context use")
def list_entities(entity_type, filter_type, limit, page, output_format, export):
    """List entities from LightRAG API with optional filtering."""
    try:
        # Map entity_type to LightRAG entity type
        entity_type_map = {
            "characters": "character",
            "locations": "location",
            "items": "item",
        }
        lightrag_type = entity_type_map[entity_type]

        # Build search query
        search_query = f"all {entity_type}"
        if filter_type:
            search_query = f"{filter_type} {entity_type}"

        click.echo(
            f"Listing {entity_type}"
            + (f" of type '{filter_type}'" if filter_type else "")
        )

        config = LightRAGAPIConfig(
            base_url=os.getenv("LIGHTRAG_BASE_URL", "http://localhost:8000"),
            api_key=os.getenv("LIGHTRAG_API_KEY"),
            timeout=int(os.getenv("LIGHTRAG_TIMEOUT", "30")),
            mock_mode=os.getenv("LIGHTRAG_MOCK_MODE", "false").lower() == "true",
        )

        client = LightRAGClient(config)

        # Calculate pagination
        offset = (page - 1) * limit
        total_limit = offset + limit

        result = asyncio.run(
            client.search_entities(search_query, lightrag_type, "mix", total_limit)
        )

        # Apply pagination to results
        paginated_entities = result.entities[offset : offset + limit]
        total_pages = (result.total_count + limit - 1) // limit

        # Prepare output data
        output_data = {
            "entity_type": entity_type,
            "filter_type": filter_type,
            "total_count": result.total_count,
            "page": page,
            "total_pages": total_pages,
            "limit": limit,
            "entities": [
                {
                    "name": e.name,
                    "type": e.entity_type,
                    "description": e.description,
                    "properties": e.properties,
                }
                for e in paginated_entities
            ],
        }

        if output_format == "json":
            click.echo(json.dumps(output_data, indent=2))
        elif output_format == "yaml":
            click.echo(yaml.dump(output_data, default_flow_style=False))
        else:  # table format
            if paginated_entities:
                filter_text = f" (type: {filter_type})" if filter_type else ""
                page_info = (
                    f" (page {page} of {total_pages})" if total_pages > 1 else ""
                )
                click.echo(
                    f"\nFound {result.total_count} {entity_type}{filter_text}{page_info}:"
                )
                click.echo("-" * 80)
                for i, entity in enumerate(paginated_entities, offset + 1):
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

                # Show pagination info
                if total_pages > 1:
                    click.echo(
                        f"Showing {len(paginated_entities)} of {result.total_count} results"
                    )
                    if page < total_pages:
                        click.echo(f"Use --page {page + 1} to see more results")
            else:
                filter_text = f" of type '{filter_type}'" if filter_type else ""
                click.echo(f"No {entity_type}{filter_text} found.")

        # Export to YAML if requested
        if export:
            with open(export, "w", encoding="utf-8") as f:
                yaml.dump(output_data, f, default_flow_style=False, allow_unicode=True)
            click.echo(f"Results exported to: {export}")

    except Exception as e:
        error_msg = str(e).lower()
        if (
            "connection" in error_msg
            or "timeout" in error_msg
            or "refused" in error_msg
        ):
            click.echo(
                f"❌ Connection Error: Cannot reach LightRAG API - {str(e)}", err=True
            )
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(f"   • Check LIGHTRAG_BASE_URL: {config.base_url}", err=True)
            click.echo("   • Verify LightRAG service is running", err=True)
            click.echo("   • Check your network connection", err=True)
            click.echo("   • Try using mock mode: LIGHTRAG_MOCK_MODE=true", err=True)
        elif "unauthorized" in error_msg or "forbidden" in error_msg:
            click.echo(f"❌ Authentication Error: {str(e)}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your LIGHTRAG_API_KEY environment variable", err=True
            )
            click.echo("   • Verify the API key is valid and not expired", err=True)
        else:
            click.echo(f"❌ List Error: {str(e)}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(f"   • Try using mock mode: LIGHTRAG_MOCK_MODE=true", err=True)
            click.echo(
                f"   • Use 'jestir lightrag test' to verify configuration", err=True
            )
        raise click.Abort()


@main.command()
@click.argument("entity_name")
@click.option("--type", "entity_type", help="Entity type (character, location, item)")
def show(entity_name, entity_type):
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
        error_msg = str(e).lower()
        if (
            "connection" in error_msg
            or "timeout" in error_msg
            or "refused" in error_msg
        ):
            click.echo(
                f"❌ Connection Error: Cannot reach LightRAG API - {str(e)}", err=True
            )
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(f"   • Check LIGHTRAG_BASE_URL: {config.base_url}", err=True)
            click.echo("   • Verify LightRAG service is running", err=True)
            click.echo("   • Check your network connection", err=True)
            click.echo("   • Try using mock mode: LIGHTRAG_MOCK_MODE=true", err=True)
        elif "unauthorized" in error_msg or "forbidden" in error_msg:
            click.echo(f"❌ Authentication Error: {str(e)}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your LIGHTRAG_API_KEY environment variable", err=True
            )
            click.echo("   • Verify the API key is valid and not expired", err=True)
        else:
            click.echo(f"❌ Entity Details Error: {str(e)}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(f"   • Check that entity '{entity_name}' exists", err=True)
            click.echo(
                f"   • Try searching first: 'jestir search characters --query \"{entity_name}\"'",
                err=True,
            )
            click.echo(f"   • Try using mock mode: LIGHTRAG_MOCK_MODE=true", err=True)
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
        error_msg = str(e).lower()
        if (
            "connection" in error_msg
            or "timeout" in error_msg
            or "refused" in error_msg
        ):
            click.echo(f"❌ Connection Failed: Cannot reach LightRAG API", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(f"   • Check LIGHTRAG_BASE_URL: {config.base_url}", err=True)
            click.echo("   • Verify LightRAG service is running", err=True)
            click.echo("   • Check your network connection", err=True)
            click.echo("   • Try: docker ps | grep lightrag", err=True)
        elif (
            "unauthorized" in error_msg
            or "forbidden" in error_msg
            or "401" in error_msg
        ):
            click.echo(f"❌ Authentication Failed: Invalid API credentials", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your LIGHTRAG_API_KEY environment variable", err=True
            )
            click.echo("   • Verify the API key is valid and not expired", err=True)
            click.echo("   • Contact your LightRAG administrator", err=True)
        elif "404" in error_msg or "not found" in error_msg:
            click.echo(
                f"❌ Service Not Found: LightRAG API endpoints not available", err=True
            )
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                f"   • Verify LIGHTRAG_BASE_URL is correct: {config.base_url}", err=True
            )
            click.echo("   • Check LightRAG service version compatibility", err=True)
            click.echo("   • Ensure all required API endpoints are available", err=True)
        else:
            click.echo(f"❌ LightRAG API test failed: {str(e)}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo("   • Check LightRAG service logs", err=True)
            click.echo("   • Verify service configuration", err=True)
            click.echo("   • Try using mock mode: LIGHTRAG_MOCK_MODE=true", err=True)
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
