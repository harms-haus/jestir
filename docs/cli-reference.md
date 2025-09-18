# Jestir CLI Reference

This document provides a comprehensive reference for the Jestir command-line interface.

## Overview

Jestir is a command-line tool for generating AI-powered bedtime stories through a three-stage pipeline. The CLI provides commands for context generation, outline creation, and story writing, along with debugging and validation tools.

## Global Options

### Verbose Mode
```bash
jestir --verbose <command> [options]
```

Enables debug-level console logging for any command. This provides detailed information about:
- API calls and responses
- Entity extraction and processing
- Template rendering
- File operations
- Error details

**Example:**
```bash
jestir --verbose context "A brave little mouse saves the forest"
```

## Environment Variables

### Logging Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `JESTIR_LOG_TO_DISK` | `false` | Enable logging to disk files |

**Example:**
```bash
export JESTIR_LOG_TO_DISK=true
jestir context "story input"
```

## Commands

### Context Generation

#### `context` - Intelligent Context Management
```bash
jestir context "natural language input" [options]
```

Creates or updates story context from natural language input. This command intelligently:
- Creates new context if `context.yaml` doesn't exist
- Updates existing context if `context.yaml` exists
- Merges entities and relationships intelligently
- Preserves all user prompts in the context history

**Options:**
- `--output, -o` - Output file name (default: `context.yaml`)

**Examples:**
```bash
# Create new context
jestir context "A brave little mouse saves the forest"

# Update existing context
jestir context "The antagonist should be a cat who wants to eat the mouse"

# Custom output file
jestir context "story input" --output my-story.yaml
```

#### `context new` - Force New Context
```bash
jestir context new "natural language input" [options]
```

Always creates a new context file, overwriting any existing one.

**Options:**
- `--output, -o` - Output file name (default: `context.yaml`)

**Example:**
```bash
jestir context new "A completely different story about a dragon"
```

### Outline Generation

#### `outline` - Generate Story Outline
```bash
jestir outline <context_file> [options]
```

Generates a story outline from a context file.

**Options:**
- `--output, -o` - Output file name (default: `outline.md`)

**Example:**
```bash
jestir outline context.yaml
jestir outline context.yaml --output my-outline.md
```

### Story Writing

#### `write` - Generate Final Story
```bash
jestir write <outline_file> [options]
```

Generates the final bedtime story from an outline file.

**Options:**
- `--output, -o` - Output file name (default: `story.md`)
- `--context, -c` - Context file to load and update (default: `context.yaml`)

**Example:**
```bash
jestir write outline.md
jestir write outline.md --output my-story.md --context my-context.yaml
```

### Validation Commands

#### `validate-templates` - Validate Template Files
```bash
jestir validate-templates [options]
```

Validates all template files for syntax and completeness.

**Options:**
- `--verbose, -v` - Show detailed validation results
- `--fix` - Attempt to fix common template issues

**Example:**
```bash
jestir validate-templates --verbose
```

#### `validate` - Validate Context File
```bash
jestir validate <context_file> [options]
```

Validates a context file for structure and consistency.

**Options:**
- `--verbose, -v` - Show detailed validation results
- `--fix` - Attempt to fix common issues automatically

**Example:**
```bash
jestir validate context.yaml --verbose
```

### Entity Management

#### `search` - Search Entities
```bash
jestir search <entity_type> [options]
```

Search for entities in the LightRAG API.

**Arguments:**
- `entity_type` - Type of entities to search (characters, locations, items)

**Options:**
- `--query, -q` - Search query to filter results
- `--type` - Filter by specific type (e.g., 'interior' for locations)
- `--limit, -l` - Maximum number of results to show (default: 10)
- `--page, -p` - Page number for pagination (default: 1)
- `--format` - Output format (table, json, yaml) (default: table)
- `--export, -e` - Export results to YAML file

**Examples:**
```bash
jestir search characters --query "brave mouse"
jestir search locations --type interior --limit 20
jestir search items --format json --export results.yaml
```

#### `list` - List Entities
```bash
jestir list <entity_type> [options]
```

List entities from LightRAG API with optional filtering.

**Arguments:**
- `entity_type` - Type of entities to list (characters, locations, items)

**Options:**
- `--type` - Filter by specific type (e.g., 'interior' for locations)
- `--limit, -l` - Maximum number of results to show (default: 20)
- `--page, -p` - Page number for pagination (default: 1)
- `--format` - Output format (table, json, yaml) (default: table)
- `--export, -e` - Export results to YAML file

**Examples:**
```bash
jestir list characters
jestir list locations --type exterior --format json
```

#### `show` - Show Entity Details
```bash
jestir show <entity_name> [options]
```

Show detailed information about a specific entity.

**Arguments:**
- `entity_name` - Name of the entity to show

**Options:**
- `--type` - Entity type (character, location, item)

**Example:**
```bash
jestir show "Lily" --type character
```

#### `validate-entity` - Test Entity Validation
```bash
jestir validate-entity <entity_name> [options]
```

Test entity validation and matching with confidence scoring. This command helps verify that LightRAG queries are finding the correct entities and shows detailed match quality information.

**Arguments:**
- `entity_name` - Name of the entity to search for

**Options:**
- `--type` - Entity type (character, location, item)
- `--threshold, -t` - Confidence threshold (0.0-1.0, default: 0.5)
- `--verbose, -v` - Show detailed validation results

**Examples:**
```bash
# Test basic entity validation
jestir validate-entity "Wendy Whisk"

# Test with specific type and threshold
jestir validate-entity "whiskers" --type character --threshold 0.8

# Test with verbose output
jestir validate-entity "Wendy" --type character --verbose
```

**Output:**
The command shows all potential matches with confidence scores, similarity scores, and recommendations:
- ✅ High Confidence: Use this match
- ⚠️ Moderate Confidence: Verify this match
- ❌ Low Confidence: This match may not be correct

### LightRAG API Commands

#### `lightrag test` - Test API Connectivity
```bash
jestir lightrag test [options]
```

Test LightRAG API connectivity and configuration.

**Options:**
- `--base-url` - LightRAG API base URL
- `--api-key` - LightRAG API key
- `--timeout` - Request timeout in seconds (default: 30)

**Example:**
```bash
jestir lightrag test --base-url http://localhost:8000
```

#### `lightrag fuzzy` - Fuzzy Search
```bash
jestir lightrag fuzzy <name> [options]
```

Perform fuzzy search for entities by name.

**Arguments:**
- `name` - Name to search for

**Options:**
- `--type` - Filter by entity type

**Example:**
```bash
jestir lightrag fuzzy "Lily" --type character
```

## Usage Examples

### Complete Story Generation Workflow

```bash
# 1. Create initial context
jestir context "A brave little mouse named Pip saves the forest from a terrible drought"

# 2. Generate outline
jestir outline context.yaml

# 3. Generate final story
jestir write outline.md

# 4. View the generated files
ls -la *.yaml *.md
```

### Debugging Workflow

```bash
# Enable verbose output and disk logging
export JESTIR_LOG_TO_DISK=true
jestir --verbose context "A story about a magical garden"

# Check logs
ls -la jestir-*.log
```

### Context Iteration

```bash
# Initial context
jestir context "A brave little mouse saves the forest"

# Add more details
jestir context "The mouse has a magical acorn that can make plants grow"

# Add antagonist
jestir context "The antagonist is a greedy fox who wants to steal the acorn"

# Generate outline
jestir outline context.yaml
```

## Error Handling

The CLI provides detailed error messages with troubleshooting tips:

- **API Errors**: Check API keys and network connectivity
- **File Errors**: Verify file permissions and paths
- **Template Errors**: Run `jestir validate-templates` to check templates
- **Validation Errors**: Use `--fix` option to attempt automatic fixes

## Configuration

All configuration is done through environment variables. See the main README.md for a complete list of available configuration options.

## Logging

- **Console Logging**: Use `--verbose` flag for debug output
- **Disk Logging**: Set `JESTIR_LOG_TO_DISK=true` to enable file logging
- **Log Format**: `%(timestamp)s - %(name)s - %(level)s - %(message)s`
- **Log Levels**: DEBUG (verbose), INFO (standard), WARNING (issues), ERROR (failures)
