# Jestir

AI-powered bedtime story generator with 3-stage pipeline.

## Overview

Jestir is a command-line tool that generates personalized bedtime stories through a three-stage pipeline:

1. **Context Generation**: Converts natural language input into structured context
2. **Outline Creation**: Generates a story outline from the context
3. **Story Writing**: Creates the final bedtime story from the outline

## Features

- Natural language story input processing
- Entity extraction and relationship mapping
- Template-based story generation
- Configurable story parameters (genre, tone, morals)
- **Advanced length control** with word count and reading time targets
- **Length validation** with tolerance checking and adjustment suggestions
- File-based workflow for manual review and editing
- Integration with LightRAG for character continuity

## Installation

### Prerequisites

- Python 3.10 or higher
- uv (for dependency management and virtual environments)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd jestir
   ```

2. Install dependencies and create virtual environment using uv:
   ```bash
   uv sync
   ```

3. Activate the virtual environment:
   ```bash
   uv shell
   ```

## Configuration

Jestir automatically reads environment variables from a `.env` file in your project directory. Create a `.env` file with your API keys and configuration:

**Quick Setup:**
1. Copy the example configuration: `cp .env.example .env`
2. Edit `.env` with your actual API keys

```bash
# OpenAI API Configuration
OPENAI_EXTRACTION_API_KEY=your_extraction_api_key_here
OPENAI_CREATIVE_API_KEY=your_creative_api_key_here

# Optional: Customize API endpoints and models
OPENAI_EXTRACTION_BASE_URL=https://api.openai.com/v1
OPENAI_CREATIVE_BASE_URL=https://api.openai.com/v1
OPENAI_EXTRACTION_MODEL=gpt-4o-mini
OPENAI_CREATIVE_MODEL=gpt-4o

# LightRAG Configuration (optional)
LIGHTRAG_BASE_URL=http://localhost:8000
LIGHTRAG_API_KEY=your_lightrag_api_key_here
LIGHTRAG_TIMEOUT=30
LIGHTRAG_MOCK_MODE=false

# Logging Configuration (optional)
JESTIR_LOG_TO_DISK=false  # Set to true to enable disk logging
```

**Note:** The `.env` file is automatically loaded when you run Jestir commands. You can also set these environment variables directly in your shell if you prefer.

## Usage

### Basic Commands

Create a new context from natural language input (overwrites existing):
```bash
jestir context new "A story about a brave little mouse who saves the forest"
```

Update existing context or create new one from natural language input:
```bash
jestir context "The antagonist should be a cat who wants to eat the mouse."
```

Generate story outline from context:
```bash
jestir outline context.yaml
```

Generate final story from outline:
```bash
jestir write outline.md
```

### Length Control

Jestir now supports precise length control for stories with word count and reading time targets:

**Set length when creating context:**
```bash
# Target word count
jestir context "A brave mouse adventure" --length 500

# Target reading time (3 minutes)
jestir context "A brave mouse adventure" --length 3m

# Custom tolerance (default is 10%)
jestir context "A brave mouse adventure" --length 500 --tolerance 15
```

**Override length for outline generation:**
```bash
jestir outline context.yaml --length 300
jestir outline context.yaml --length 2m --tolerance 20
```

**Override length for story generation:**
```bash
jestir write outline.md --length 400
jestir write outline.md --length 4m --tolerance 10
```

**Validate length of generated files:**
```bash
# Validate outline length
jestir validate-length outline.md --type outline --suggestions

# Validate story length
jestir validate-length story.md --type story --context context.yaml
```

**Length Control Features:**
- **Word count targets**: Specify exact word counts (e.g., `--length 500`)
- **Reading time targets**: Specify reading time in minutes (e.g., `--length 3m`)
- **Tolerance control**: Set acceptable deviation percentage (default: 10%)
- **Length validation**: Check if generated content meets length requirements
- **Adjustment suggestions**: Get specific recommendations for length adjustments
- **Backward compatibility**: Works with existing legacy length settings (short, medium, long)

### Command Options

All commands support custom output file names:
```bash
jestir context "story input" --output my-context.yaml
jestir context new "story input" --output my-context.yaml
jestir outline context.yaml --output my-outline.md
jestir write outline.md --output my-story.md
```

### Debug and Logging Options

**Verbose Mode (Console Debug Logging):**
```bash
# Enable verbose output for any command
jestir --verbose context "story input"
jestir --verbose outline context.yaml
jestir --verbose write outline.md
```

**Disk Logging (Environment Variable):**
```bash
# Enable logging to disk (off by default)
export JESTIR_LOG_TO_DISK=true
jestir context "story input"
```

**Combined Usage:**
```bash
# Both verbose console output and disk logging
export JESTIR_LOG_TO_DISK=true
jestir --verbose context "story input"
```

### Context Management

The `jestir context` command now intelligently manages your story context:

- **If no `context.yaml` exists**: Creates a new context file
- **If `context.yaml` exists**: Updates the existing context with your new input, merging entities and relationships intelligently
- **Use `jestir context new`**: Always creates a fresh context file, overwriting any existing one

This allows you to iteratively build and refine your story context through natural language prompts.

**All user prompts are preserved** in the context file, including:
- Initial story creation prompts
- Additional context-update prompts
- All subsequent refinements and modifications

The context maintains a complete history of all your natural language inputs, ensuring that every prompt you provide is captured and can be referenced during story generation.

## Documentation

- **[CLI Reference](docs/cli-reference.md)** - Complete command-line interface documentation
- **[Architecture](docs/architecture.md)** - System architecture and design patterns
- **[PRD](docs/prd.md)** - Product requirements and specifications

## Project Structure

```
jestir/
├── src/jestir/          # Main source code
├── tests/               # Test files
├── templates/           # Story templates
├── output/              # Generated files (gitignored)
├── docs/                # Documentation
└── pyproject.toml       # Project configuration
```

## Development

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run ruff format src/ tests/
```

### Type Checking

```bash
uv run mypy src/
```

### Pre-commit Hooks

Install pre-commit hooks:
```bash
uv run pre-commit install
```

## License

[Add your license here]

## Contributing

[Add contributing guidelines here]
