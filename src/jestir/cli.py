"""Command-line interface for Jestir."""

import asyncio
import json
import os
from pathlib import Path

import click
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()
from .models.api_config import LightRAGAPIConfig
from .services.context_generator import ContextGenerator
from .services.lightrag_client import LightRAGClient
from .services.outline_generator import OutlineGenerator
from .services.story_writer import StoryWriter
from .services.template_loader import TemplateLoader
from .services.token_tracker import TokenTracker
from .utils.logging_config import (
    get_logger,
    log_command_end,
    log_command_start,
    setup_logging,
)


@click.group()
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose debug logging to console",
)
@click.version_option()
@click.pass_context
def main(ctx, verbose):
    """Jestir: AI-powered bedtime story generator with 3-stage pipeline."""
    # Set up logging configuration
    setup_logging(verbose=verbose)

    # Store verbose flag in context for use by subcommands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@main.command()
@click.argument("input_text")
@click.option("--output", "-o", default="context.yaml", help="Output context file")
@click.pass_context
def context(ctx, input_text, output):
    """Update existing context or create new one from natural language input."""
    logger = get_logger("cli.context")
    log_command_start("context", {"input_text": input_text, "output": output}, logger)

    try:
        # Check if default context file exists
        default_context_file = "context.yaml"
        existing_context = None

        if os.path.exists(default_context_file):
            logger.debug(f"Found existing context file: {default_context_file}")
            click.echo(f"Found existing context file: {default_context_file}")
            try:
                # Load existing context
                generator = ContextGenerator()
                existing_context = generator.load_context_from_file(
                    default_context_file,
                )
                logger.debug("Successfully loaded existing context")
                click.echo("Loading existing context for updates...")
            except Exception as e:
                logger.warning(f"Could not load existing context: {e}")
                click.echo(f"Warning: Could not load existing context: {e}")
                click.echo("Creating new context instead...")
                existing_context = None
        else:
            logger.debug("No existing context file found")
            click.echo("No existing context found, creating new one...")

        # Generate or update context
        token_tracker = TokenTracker()
        generator = ContextGenerator(token_tracker=token_tracker)
        if existing_context:
            logger.debug(f"Updating context with input: {input_text}")
            click.echo(f"Updating context with: {input_text}")
            updated_context = generator.update_context(input_text, existing_context)
        else:
            logger.debug(f"Generating new context from input: {input_text}")
            click.echo(f"Generating new context from: {input_text}")
            updated_context = generator.generate_context(input_text)

        # Save token usage to context
        token_tracker.save_usage_to_context(output)

        # Convert to dict for YAML serialization
        context_dict = updated_context.model_dump()
        logger.debug(
            f"Context serialized to dict with {len(context_dict)} top-level keys",
        )

        # Write to file
        output_path = Path(output)
        logger.debug(f"Writing context to file: {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(
                context_dict,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        action = "Updated" if existing_context else "Generated"
        logger.info(f"Context {action.lower()} successfully: {output}")
        click.echo(f"Context {action.lower()} successfully: {output}")
        click.echo(
            f"Found {len(updated_context.entities)} entities and {len(updated_context.relationships)} relationships",
        )
        click.echo(f"Plot points: {len(updated_context.plot_points)}")

        log_command_end("context", success=True, logger=logger)

    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        click.echo(f"❌ File Error: Cannot access file - {e!s}", err=True)
        click.echo(
            "💡 Tip: Make sure you have write permissions to the output directory",
            err=True,
        )
        log_command_end("context", success=False, logger=logger)
        raise click.Abort()
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        click.echo(
            f"❌ Permission Error: Cannot write to output file - {e!s}",
            err=True,
        )
        click.echo(
            "💡 Tip: Check file permissions or try a different output directory",
            err=True,
        )
        log_command_end("context", success=False, logger=logger)
        raise click.Abort()
    except Exception as e:
        logger.exception("Unexpected error in context command")
        error_msg = str(e).lower()
        if "api" in error_msg or "openai" in error_msg:
            click.echo(f"❌ API Error: {e!s}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your OPENAI_EXTRACTION_API_KEY environment variable",
                err=True,
            )
            click.echo(
                "   • Verify your OpenAI account has sufficient credits",
                err=True,
            )
            click.echo("   • Check your internet connection", err=True)
        elif "template" in error_msg:
            click.echo(f"❌ Template Error: {e!s}", err=True)
            click.echo(
                "💡 Tip: Run 'jestir validate-templates' to check template files",
                err=True,
            )
        else:
            click.echo(f"❌ Unexpected Error: {e!s}", err=True)
            click.echo(
                "💡 Tip: Try running with a simpler input text or check the logs",
                err=True,
            )
        log_command_end("context", success=False, logger=logger)
        raise click.Abort()


@main.command()
@click.argument("input_text")
@click.option("--output", "-o", default="context.yaml", help="Output context file")
@click.pass_context
def context_new(ctx, input_text, output):
    """Generate a new context from natural language input."""
    logger = get_logger("cli.context_new")
    log_command_start(
        "context_new",
        {"input_text": input_text, "output": output},
        logger,
    )

    try:
        logger.debug(f"Generating new context from: {input_text}")
        click.echo(f"Generating context from: {input_text}")

        # Check for OpenAI API key
        if not os.getenv("OPENAI_EXTRACTION_API_KEY"):
            logger.warning(
                "OPENAI_EXTRACTION_API_KEY not set, using fallback extraction",
            )
            click.echo(
                "Warning: OPENAI_EXTRACTION_API_KEY not set. Using fallback extraction.",
                err=True,
            )

        # Generate context
        token_tracker = TokenTracker()
        generator = ContextGenerator(token_tracker=token_tracker)
        logger.debug("Starting context generation")
        context = generator.generate_context(input_text)
        logger.debug("Context generation completed")

        # Save token usage to context
        token_tracker.save_usage_to_context(output)

        # Convert to dict for YAML serialization
        context_dict = context.model_dump()
        logger.debug(
            f"Context serialized to dict with {len(context_dict)} top-level keys",
        )

        # Write to file
        output_path = Path(output)
        logger.debug(f"Writing context to file: {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(
                context_dict,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        logger.info(f"Context generated successfully: {output}")
        click.echo(f"Context generated successfully: {output}")
        click.echo(
            f"Found {len(context.entities)} entities and {len(context.relationships)} relationships",
        )
        click.echo(f"Plot points: {len(context.plot_points)}")

        log_command_end("context_new", success=True, logger=logger)

    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        click.echo(f"❌ File Error: Cannot access file - {e!s}", err=True)
        click.echo(
            "💡 Tip: Make sure you have write permissions to the output directory",
            err=True,
        )
        log_command_end("context_new", success=False, logger=logger)
        raise click.Abort()
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        click.echo(
            f"❌ Permission Error: Cannot write to output file - {e!s}",
            err=True,
        )
        click.echo(
            "💡 Tip: Check file permissions or try a different output directory",
            err=True,
        )
        log_command_end("context_new", success=False, logger=logger)
        raise click.Abort()
    except Exception as e:
        logger.exception("Unexpected error in context_new command")
        error_msg = str(e).lower()
        if "api" in error_msg or "openai" in error_msg:
            click.echo(f"❌ API Error: {e!s}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your OPENAI_EXTRACTION_API_KEY environment variable",
                err=True,
            )
            click.echo(
                "   • Verify your OpenAI account has sufficient credits",
                err=True,
            )
            click.echo("   • Check your internet connection", err=True)
        elif "template" in error_msg:
            click.echo(f"❌ Template Error: {e!s}", err=True)
            click.echo(
                "💡 Tip: Run 'jestir validate-templates' to check template files",
                err=True,
            )
        else:
            click.echo(f"❌ Unexpected Error: {e!s}", err=True)
            click.echo(
                "💡 Tip: Try running with a simpler input text or check the logs",
                err=True,
            )
        log_command_end("context_new", success=False, logger=logger)
        raise click.Abort()


@main.command()
@click.argument("context_file")
@click.option("--output", "-o", default="outline.md", help="Output outline file")
@click.pass_context
def outline(ctx, context_file, output):
    """Generate story outline from context file."""
    logger = get_logger("cli.outline")
    log_command_start(
        "outline",
        {"context_file": context_file, "output": output},
        logger,
    )

    try:
        logger.debug(f"Generating outline from: {context_file}")
        click.echo(f"Generating outline from: {context_file}")

        # Check for OpenAI API key
        if not os.getenv("OPENAI_CREATIVE_API_KEY"):
            logger.warning(
                "OPENAI_CREATIVE_API_KEY not set, using fallback outline generation",
            )
            click.echo(
                "Warning: OPENAI_CREATIVE_API_KEY not set. Using fallback outline generation.",
                err=True,
            )

        # Load context from file
        token_tracker = TokenTracker()
        token_tracker.load_usage_from_context(context_file)
        generator = OutlineGenerator(token_tracker=token_tracker)
        logger.debug(f"Loading context from file: {context_file}")
        context = generator.load_context_from_file(context_file)
        logger.debug("Context loaded successfully")

        # Generate outline
        logger.debug("Starting outline generation")
        outline_content = generator.generate_outline(context)
        logger.debug("Outline generation completed")

        # Save token usage to context
        token_tracker.save_usage_to_context(context_file)

        # Save outline to file
        logger.debug(f"Saving outline to file: {output}")
        generator.save_outline_to_file(outline_content, output)

        # Update context with outline and save back
        logger.debug("Updating context with outline")
        generator.update_context_with_outline(context, outline_content)

        # Save updated context back to file
        context_dict = context.model_dump()
        logger.debug(f"Saving updated context to file: {context_file}")
        with open(context_file, "w", encoding="utf-8") as f:
            yaml.dump(
                context_dict,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        logger.info(f"Outline generated successfully: {output}")
        click.echo(f"Outline generated successfully: {output}")
        click.echo(f"Context file updated: {context_file}")

        log_command_end("outline", success=True, logger=logger)

    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        click.echo(f"❌ File Not Found: {e!s}", err=True)
        click.echo("💡 Troubleshooting:", err=True)
        click.echo(f"   • Make sure the context file '{context_file}' exists", err=True)
        click.echo(
            "   • Generate a context file first: 'jestir context \"your story idea\"'",
            err=True,
        )
        click.echo("   • Check the file path is correct", err=True)
        log_command_end("outline", success=False, logger=logger)
        raise click.Abort()
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        click.echo(
            f"❌ Permission Error: Cannot write to output file - {e!s}",
            err=True,
        )
        click.echo(
            "💡 Tip: Check file permissions or try a different output directory",
            err=True,
        )
        log_command_end("outline", success=False, logger=logger)
        raise click.Abort()
    except Exception as e:
        logger.exception("Unexpected error in outline command")
        error_msg = str(e).lower()
        if "api" in error_msg or "openai" in error_msg:
            click.echo(f"❌ API Error: {e!s}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your OPENAI_CREATIVE_API_KEY environment variable",
                err=True,
            )
            click.echo(
                "   • Verify your OpenAI account has sufficient credits",
                err=True,
            )
            click.echo("   • Check your internet connection", err=True)
        elif "yaml" in error_msg or "parse" in error_msg:
            click.echo(
                f"❌ Context File Error: Invalid YAML format - {e!s}",
                err=True,
            )
            click.echo(
                f"💡 Tip: Check that '{context_file}' is a valid YAML file",
                err=True,
            )
        else:
            click.echo(f"❌ Unexpected Error: {e!s}", err=True)
            click.echo(
                "💡 Tip: Check that your context file is valid and complete",
                err=True,
            )
        log_command_end("outline", success=False, logger=logger)
        raise click.Abort()


@main.command()
@click.argument("outline_file")
@click.option("--output", "-o", default="story.md", help="Output story file")
@click.option(
    "--context",
    "-c",
    default="context.yaml",
    help="Context file to load and update",
)
@click.pass_context
def write(ctx, outline_file, output, context):
    """Generate final story from outline file."""
    logger = get_logger("cli.write")
    log_command_start(
        "write",
        {"outline_file": outline_file, "output": output, "context": context},
        logger,
    )

    try:
        logger.debug(f"Generating story from: {outline_file}")
        click.echo(f"Generating story from: {outline_file}")

        # Check for OpenAI API key
        if not os.getenv("OPENAI_CREATIVE_API_KEY"):
            logger.warning(
                "OPENAI_CREATIVE_API_KEY not set, using fallback story generation",
            )
            click.echo(
                "Warning: OPENAI_CREATIVE_API_KEY not set. Using fallback story generation.",
                err=True,
            )

        # Load outline and context
        token_tracker = TokenTracker()
        token_tracker.load_usage_from_context(context)
        writer = StoryWriter(token_tracker=token_tracker)
        logger.debug(f"Loading outline from file: {outline_file}")
        outline_content = writer.load_outline_from_file(outline_file)
        logger.debug(f"Loading context from file: {context}")
        story_context = writer.load_context_from_file(context)
        logger.debug("Outline and context loaded successfully")

        # Generate story
        logger.debug("Starting story generation")
        story_content = writer.generate_story(story_context, outline_content)
        logger.debug("Story generation completed")

        # Save token usage to context
        token_tracker.save_usage_to_context(context)

        # Save story to file
        logger.debug(f"Saving story to file: {output}")
        writer.save_story_to_file(story_content, output)

        # Update context with story and save back
        logger.debug("Updating context with story")
        writer.update_context_with_story(story_context, story_content)

        # Save updated context back to file
        context_dict = story_context.model_dump()
        logger.debug(f"Saving updated context to file: {context}")
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
        logger.debug(
            f"Story metrics - Word count: {word_count}, Reading time: {reading_time}",
        )

        logger.info(f"Story generated successfully: {output}")
        click.echo(f"Story generated successfully: {output}")
        click.echo(f"Context file updated: {context}")
        click.echo(f"Word count: {word_count}")
        click.echo(f"Estimated reading time: {reading_time}")

        log_command_end("write", success=True, logger=logger)

    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        error_str = str(e)
        click.echo(f"❌ File Not Found: {error_str}", err=True)
        click.echo("💡 Troubleshooting:", err=True)
        if outline_file in error_str:
            click.echo(
                f"   • Generate an outline first: 'jestir outline {context}'",
                err=True,
            )
            click.echo(
                f"   • Make sure the outline file '{outline_file}' exists",
                err=True,
            )
        elif context in error_str:
            click.echo(
                "   • Generate a context file first: 'jestir context \"your story idea\"'",
                err=True,
            )
            click.echo(f"   • Make sure the context file '{context}' exists", err=True)
        click.echo("   • Check the file paths are correct", err=True)
        log_command_end("write", success=False, logger=logger)
        raise click.Abort()
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        click.echo(
            f"❌ Permission Error: Cannot write to output file - {e!s}",
            err=True,
        )
        click.echo(
            "💡 Tip: Check file permissions or try a different output directory",
            err=True,
        )
        log_command_end("write", success=False, logger=logger)
        raise click.Abort()
    except Exception as e:
        logger.exception("Unexpected error in write command")
        error_msg = str(e).lower()
        if "api" in error_msg or "openai" in error_msg:
            click.echo(f"❌ API Error: {e!s}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your OPENAI_CREATIVE_API_KEY environment variable",
                err=True,
            )
            click.echo(
                "   • Verify your OpenAI account has sufficient credits",
                err=True,
            )
            click.echo("   • Check your internet connection", err=True)
        elif "yaml" in error_msg or "parse" in error_msg:
            click.echo(
                f"❌ File Format Error: Invalid YAML format - {e!s}",
                err=True,
            )
            click.echo("💡 Tip: Check that your files are valid YAML format", err=True)
        else:
            click.echo(f"❌ Unexpected Error: {e!s}", err=True)
            click.echo(
                "💡 Tip: Check that your outline and context files are valid and complete",
                err=True,
            )
        log_command_end("write", success=False, logger=logger)
        raise click.Abort()


@main.command()
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation results")
@click.option("--fix", is_flag=True, help="Attempt to fix common template issues")
@click.pass_context
def validate_templates(ctx, verbose, fix):
    """Validate all template files for syntax and completeness."""
    logger = get_logger("cli.validate_templates")
    log_command_start("validate_templates", {"verbose": verbose, "fix": fix}, logger)

    try:
        logger.debug("Starting template validation")
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
                issues_found.append(f"System prompt {template_name}.txt - {e!s}")
                if verbose:
                    click.echo(f"  ❌ {template_name}.txt - Error: {e!s}")

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
                        template_path,
                        required_vars[template_name],
                    )
                    if validation["valid"]:
                        valid_templates += 1
                        if verbose:
                            click.echo(
                                f"  ✅ {template_name}.txt - All required variables present",
                            )
                    else:
                        missing = ", ".join(validation["missing_vars"])
                        issues_found.append(
                            f"User prompt {template_name}.txt missing variables: {missing}",
                        )
                        if verbose:
                            click.echo(f"  ❌ {template_name}.txt - Missing: {missing}")
                # Just check basic syntax
                elif "{{" in content and "}}" in content:
                    valid_templates += 1
                    if verbose:
                        click.echo(f"  ✅ {template_name}.txt - OK")
                else:
                    issues_found.append(
                        f"User prompt {template_name}.txt has no template variables",
                    )
                    if verbose:
                        click.echo(
                            f"  ⚠️  {template_name}.txt - No template variables",
                        )

            except Exception as e:
                issues_found.append(f"User prompt {template_name}.txt - {e!s}")
                if verbose:
                    click.echo(f"  ❌ {template_name}.txt - Error: {e!s}")

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
                        f"Include template {template_name}.txt has no template variables",
                    )
                    if verbose:
                        click.echo(f"  ⚠️  {template_name}.txt - No template variables")

            except Exception as e:
                issues_found.append(f"Include template {template_name}.txt - {e!s}")
                if verbose:
                    click.echo(f"  ❌ {template_name}.txt - Error: {e!s}")

        # Summary
        click.echo("\n📊 Validation Summary:")
        click.echo(f"  Total templates: {total_templates}")
        click.echo(f"  Valid templates: {valid_templates}")
        click.echo(f"  Issues found: {len(issues_found)}")

        if issues_found:
            click.echo("\n❌ Issues found:")
            for issue in issues_found:
                click.echo(f"  • {issue}")

            if fix:
                click.echo("\n🔧 Fix suggestions:")
                click.echo("  • Check template syntax ({{variable}})")
                click.echo("  • Ensure all required variables are present")
                click.echo("  • Verify file paths and permissions")
                click.echo("  • Check for typos in variable names")

            raise click.Abort()
        logger.info("All templates are valid")
        click.echo("\n✅ All templates are valid!")

        log_command_end("validate_templates", success=True, logger=logger)

    except FileNotFoundError as e:
        logger.error(f"Template directory not found: {e}")
        click.echo(f"❌ Template Directory Not Found: {e!s}", err=True)
        click.echo("💡 Troubleshooting:", err=True)
        click.echo(
            "   • Make sure you're running from the project root directory",
            err=True,
        )
        click.echo("   • Verify the templates/ directory exists", err=True)
        click.echo("   • Check that template files are properly installed", err=True)
        log_command_end("validate_templates", success=False, logger=logger)
        raise click.Abort()
    except PermissionError as e:
        logger.error(f"Permission error reading template files: {e}")
        click.echo(
            f"❌ Permission Error: Cannot read template files - {e!s}",
            err=True,
        )
        click.echo(
            "💡 Tip: Check file permissions in the templates/ directory",
            err=True,
        )
        log_command_end("validate_templates", success=False, logger=logger)
        raise click.Abort()
    except Exception as e:
        logger.exception("Template validation error")
        click.echo(f"❌ Template Validation Error: {e!s}", err=True)
        click.echo("💡 Troubleshooting:", err=True)
        click.echo(
            "   • Check that all template files are properly formatted",
            err=True,
        )
        click.echo("   • Verify template syntax uses {{variable}} format", err=True)
        click.echo("   • Make sure templates/ directory structure is correct", err=True)
        log_command_end("validate_templates", success=False, logger=logger)
        raise click.Abort()


@main.command()
@click.argument("context_file")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed validation results")
@click.option("--fix", is_flag=True, help="Attempt to fix common issues automatically")
@click.pass_context
def validate(ctx, context_file, verbose, fix):
    """Validate a context file for structure and consistency."""
    logger = get_logger("cli.validate")
    log_command_start(
        "validate",
        {"context_file": context_file, "verbose": verbose, "fix": fix},
        logger,
    )

    try:
        logger.debug(f"Validating context file: {context_file}")
        click.echo(f"Validating context file: {context_file}")

        # Import the validation service
        from .services.context_validator import ContextValidator

        # Create validator instance
        validator = ContextValidator()

        # Load and validate context
        validation_result = validator.validate_context_file(
            context_file,
            verbose=verbose,
            auto_fix=fix,
        )

        # Display results
        if validation_result.is_valid:
            logger.info("Context file is valid")
            click.echo("✅ Context file is valid!")
            if validation_result.warnings:
                logger.warning(f"Found {len(validation_result.warnings)} warnings")
                click.echo(f"\n⚠️  {len(validation_result.warnings)} warnings found:")
                for warning in validation_result.warnings:
                    click.echo(f"  • {warning}")
            log_command_end("validate", success=True, logger=logger)
        else:
            logger.error(
                f"Context file has {len(validation_result.errors)} validation errors",
            )
            click.echo("❌ Context file has validation errors:")
            for error in validation_result.errors:
                click.echo(f"  • {error}")

            if validation_result.suggestions:
                click.echo("\n💡 Fix suggestions:")
                for suggestion in validation_result.suggestions:
                    click.echo(f"  • {suggestion}")

            log_command_end("validate", success=False, logger=logger)
            raise click.Abort()

    except FileNotFoundError as e:
        logger.error(f"File not found error: {e}")
        click.echo(f"❌ File Not Found: {e!s}", err=True)
        click.echo("💡 Troubleshooting:", err=True)
        click.echo(f"   • Make sure the context file '{context_file}' exists", err=True)
        click.echo(
            "   • Generate a context file first: 'jestir context \"your story idea\"'",
            err=True,
        )
        click.echo("   • Check the file path is correct", err=True)
        log_command_end("validate", success=False, logger=logger)
        raise click.Abort()
    except PermissionError as e:
        logger.error(f"Permission error: {e}")
        click.echo(f"❌ Permission Error: Cannot read file - {e!s}", err=True)
        click.echo("💡 Tip: Check file permissions", err=True)
        log_command_end("validate", success=False, logger=logger)
        raise click.Abort()
    except Exception as e:
        logger.exception("Validation error")
        error_msg = str(e).lower()
        if "yaml" in error_msg or "parse" in error_msg:
            click.echo(
                f"❌ File Format Error: Invalid YAML format - {e!s}",
                err=True,
            )
            click.echo(
                "💡 Tip: Check that the context file is valid YAML format",
                err=True,
            )
        else:
            click.echo(f"❌ Validation Error: {e!s}", err=True)
            click.echo(
                "💡 Tip: Check that your context file is properly formatted",
                err=True,
            )
        log_command_end("validate", success=False, logger=logger)
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
            client.search_entities(search_query, lightrag_type, "mix", total_limit),
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
        elif paginated_entities:
            page_info = f" (page {page} of {total_pages})" if total_pages > 1 else ""
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
                        [f"{k}: {v}" for k, v in entity.properties.items()],
                    )
                    click.echo(f"   Properties: {props}")
                click.echo()

            # Show pagination info
            if total_pages > 1:
                click.echo(
                    f"Showing {len(paginated_entities)} of {result.total_count} results",
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
                f"❌ Connection Error: Cannot reach LightRAG API - {e!s}",
                err=True,
            )
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(f"   • Check LIGHTRAG_BASE_URL: {config.base_url}", err=True)
            click.echo("   • Verify LightRAG service is running", err=True)
            click.echo("   • Check your network connection", err=True)
            click.echo("   • Try using mock mode: LIGHTRAG_MOCK_MODE=true", err=True)
        elif "unauthorized" in error_msg or "forbidden" in error_msg:
            click.echo(f"❌ Authentication Error: {e!s}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your LIGHTRAG_API_KEY environment variable",
                err=True,
            )
            click.echo("   • Verify the API key is valid and not expired", err=True)
        elif "invalid" in error_msg and "query" in error_msg:
            click.echo(f"❌ Query Error: {e!s}", err=True)
            click.echo("💡 Tips:", err=True)
            click.echo("   • Try a simpler search query", err=True)
            click.echo("   • Check spelling and try different keywords", err=True)
            click.echo(
                f"   • Use 'jestir list {entity_type}' to see all available entities",
                err=True,
            )
        else:
            click.echo(f"❌ Search Error: {e!s}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo("   • Try using mock mode: LIGHTRAG_MOCK_MODE=true", err=True)
            click.echo("   • Check LightRAG service status", err=True)
            click.echo(
                "   • Use 'jestir lightrag test' to verify configuration",
                err=True,
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
            + (f" of type '{filter_type}'" if filter_type else ""),
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
            client.search_entities(search_query, lightrag_type, "mix", total_limit),
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
        elif paginated_entities:
            filter_text = f" (type: {filter_type})" if filter_type else ""
            page_info = f" (page {page} of {total_pages})" if total_pages > 1 else ""
            click.echo(
                f"\nFound {result.total_count} {entity_type}{filter_text}{page_info}:",
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
                        [f"{k}: {v}" for k, v in entity.properties.items()],
                    )
                    click.echo(f"   Properties: {props}")
                click.echo()

            # Show pagination info
            if total_pages > 1:
                click.echo(
                    f"Showing {len(paginated_entities)} of {result.total_count} results",
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
                f"❌ Connection Error: Cannot reach LightRAG API - {e!s}",
                err=True,
            )
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(f"   • Check LIGHTRAG_BASE_URL: {config.base_url}", err=True)
            click.echo("   • Verify LightRAG service is running", err=True)
            click.echo("   • Check your network connection", err=True)
            click.echo("   • Try using mock mode: LIGHTRAG_MOCK_MODE=true", err=True)
        elif "unauthorized" in error_msg or "forbidden" in error_msg:
            click.echo(f"❌ Authentication Error: {e!s}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your LIGHTRAG_API_KEY environment variable",
                err=True,
            )
            click.echo("   • Verify the API key is valid and not expired", err=True)
        else:
            click.echo(f"❌ List Error: {e!s}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo("   • Try using mock mode: LIGHTRAG_MOCK_MODE=true", err=True)
            click.echo(
                "   • Use 'jestir lightrag test' to verify configuration",
                err=True,
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
            click.echo("\nEntity Details:")
            click.echo(f"Name: {entity.name}")
            click.echo(f"Type: {entity.entity_type}")
            if entity.description:
                click.echo(f"Description: {entity.description}")
            if entity.properties:
                click.echo("Properties:")
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
                f"❌ Connection Error: Cannot reach LightRAG API - {e!s}",
                err=True,
            )
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(f"   • Check LIGHTRAG_BASE_URL: {config.base_url}", err=True)
            click.echo("   • Verify LightRAG service is running", err=True)
            click.echo("   • Check your network connection", err=True)
            click.echo("   • Try using mock mode: LIGHTRAG_MOCK_MODE=true", err=True)
        elif "unauthorized" in error_msg or "forbidden" in error_msg:
            click.echo(f"❌ Authentication Error: {e!s}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your LIGHTRAG_API_KEY environment variable",
                err=True,
            )
            click.echo("   • Verify the API key is valid and not expired", err=True)
        else:
            click.echo(f"❌ Entity Details Error: {e!s}", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(f"   • Check that entity '{entity_name}' exists", err=True)
            click.echo(
                f"   • Try searching first: 'jestir search characters --query \"{entity_name}\"'",
                err=True,
            )
            click.echo("   • Try using mock mode: LIGHTRAG_MOCK_MODE=true", err=True)
        raise click.Abort()


@main.group()
def lightrag():
    """LightRAG API testing and validation commands."""


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
        click.echo("Configuration:")
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
            click.echo("❌ Connection Failed: Cannot reach LightRAG API", err=True)
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
            click.echo("❌ Authentication Failed: Invalid API credentials", err=True)
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                "   • Check your LIGHTRAG_API_KEY environment variable",
                err=True,
            )
            click.echo("   • Verify the API key is valid and not expired", err=True)
            click.echo("   • Contact your LightRAG administrator", err=True)
        elif "404" in error_msg or "not found" in error_msg:
            click.echo(
                "❌ Service Not Found: LightRAG API endpoints not available",
                err=True,
            )
            click.echo("💡 Troubleshooting:", err=True)
            click.echo(
                f"   • Verify LIGHTRAG_BASE_URL is correct: {config.base_url}",
                err=True,
            )
            click.echo("   • Check LightRAG service version compatibility", err=True)
            click.echo("   • Ensure all required API endpoints are available", err=True)
        else:
            click.echo(f"❌ LightRAG API test failed: {e!s}", err=True)
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
        click.echo(f"Error in fuzzy search: {e!s}", err=True)
        raise click.Abort()


@main.command()
@click.option("--context", "-c", default="context.yaml", help="Context file to analyze")
@click.option(
    "--period",
    "-p",
    type=click.Choice(["daily", "weekly", "monthly"]),
    default="monthly",
    help="Report period",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.option("--export", "-e", help="Export report to file")
@click.option("--suggestions", "-s", is_flag=True, help="Show optimization suggestions")
@click.pass_context
def stats(ctx, context, period, output_format, export, suggestions):
    """Show token usage statistics and cost analysis."""
    logger = get_logger("cli.stats")
    log_command_start(
        "stats",
        {"context": context, "period": period, "format": output_format},
        logger,
    )

    try:
        logger.debug(f"Generating stats for context: {context}")
        click.echo("Generating token usage statistics...")

        # Load token tracker and usage from context
        token_tracker = TokenTracker()
        token_tracker.load_usage_from_context(context)

        # Generate report
        report = token_tracker.generate_report(period=period)

        if output_format == "json":
            click.echo(json.dumps(report.model_dump(), indent=2, default=str))
        elif output_format == "yaml":
            click.echo(
                yaml.dump(
                    report.model_dump(),
                    default_flow_style=False,
                    allow_unicode=True,
                ),
            )
        else:
            # Table format
            click.echo(f"\n📊 Token Usage Statistics ({period.title()})")
            click.echo("=" * 50)

            # Summary
            summary = report.summary
            click.echo(f"Total Tokens: {summary.total_tokens:,}")
            click.echo(f"Total Cost: ${summary.total_cost_usd:.4f}")
            click.echo(f"Total API Calls: {summary.total_calls}")

            if summary.total_calls > 0:
                avg_tokens = summary.total_tokens / summary.total_calls
                avg_cost = summary.total_cost_usd / summary.total_calls
                click.echo(f"Average Tokens per Call: {avg_tokens:.1f}")
                click.echo(f"Average Cost per Call: ${avg_cost:.4f}")

            # By service
            if summary.by_service:
                click.echo("\n📈 Usage by Service:")
                click.echo("-" * 30)
                for service, data in summary.by_service.items():
                    click.echo(f"{service}:")
                    click.echo(f"  Tokens: {data['total_tokens']:,}")
                    click.echo(f"  Cost: ${data['total_cost']:.4f}")
                    click.echo(f"  Calls: {data['total_calls']}")

            # By operation
            if summary.by_operation:
                click.echo("\n🔧 Usage by Operation:")
                click.echo("-" * 30)
                for operation, data in summary.by_operation.items():
                    click.echo(f"{operation}:")
                    click.echo(f"  Tokens: {data['total_tokens']:,}")
                    click.echo(f"  Cost: ${data['total_cost']:.4f}")
                    click.echo(f"  Calls: {data['total_calls']}")

            # By model
            if summary.by_model:
                click.echo("\n🤖 Usage by Model:")
                click.echo("-" * 30)
                for model, data in summary.by_model.items():
                    click.echo(f"{model}:")
                    click.echo(f"  Tokens: {data['total_tokens']:,}")
                    click.echo(f"  Cost: ${data['total_cost']:.4f}")
                    click.echo(f"  Calls: {data['total_calls']}")
                    click.echo(f"  Avg Tokens/Call: {data['avg_tokens_per_call']:.1f}")

            # Top operations
            if report.top_operations:
                click.echo("\n🏆 Top Operations by Token Usage:")
                click.echo("-" * 40)
                for i, op in enumerate(report.top_operations[:5], 1):
                    click.echo(f"{i}. {op['operation']}")
                    click.echo(f"   Tokens: {op['total_tokens']:,}")
                    click.echo(f"   Cost: ${op['total_cost']:.4f}")
                    click.echo(f"   Calls: {op['total_calls']}")

            # Cost trends
            if report.cost_trends:
                click.echo("\n📈 Cost Trends:")
                click.echo("-" * 20)
                for trend in report.cost_trends[-7:]:  # Show last 7 entries
                    date_key = (
                        trend.get("date") or trend.get("week") or trend.get("month")
                    )
                    click.echo(
                        f"{date_key}: ${trend['cost']:.4f} ({trend['tokens']:,} tokens)",
                    )

            # Optimization suggestions
            if suggestions and report.optimization_suggestions:
                click.echo("\n💡 Optimization Suggestions:")
                click.echo("-" * 30)
                for i, suggestion in enumerate(report.optimization_suggestions, 1):
                    click.echo(f"{i}. {suggestion.title}")
                    click.echo(f"   {suggestion.description}")
                    if suggestion.potential_savings > 0:
                        click.echo(
                            f"   Potential Savings: ${suggestion.potential_savings:.2f}",
                        )
                    click.echo(f"   Action: {suggestion.action_required}")
                    click.echo()

        # Export if requested
        if export:
            token_tracker.export_report(report, export)
            click.echo(f"Report exported to: {export}")

        log_command_end("stats", success=True, logger=logger)

    except FileNotFoundError as e:
        logger.error(f"Context file not found: {e}")
        click.echo(f"❌ Context file not found: {e!s}", err=True)
        click.echo(
            "💡 Tip: Generate a context file first: 'jestir context \"your story idea\"'",
            err=True,
        )
        log_command_end("stats", success=False, logger=logger)
        raise click.Abort()
    except Exception as e:
        logger.exception("Unexpected error in stats command")
        click.echo(f"❌ Stats Error: {e!s}", err=True)
        click.echo(
            "💡 Tip: Check that your context file is valid and contains token usage data",
            err=True,
        )
        log_command_end("stats", success=False, logger=logger)
        raise click.Abort()


if __name__ == "__main__":
    main()
