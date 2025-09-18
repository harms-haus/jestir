# Jestir

**AI-powered bedtime story generator with intelligent world-building and human control**

Jestir is a command-line tool that creates personalized bedtime stories through a controlled 3-stage pipeline, maintaining narrative consistency across stories while providing human checkpoints to ensure age-appropriate content.

## ✨ Key Features

### 🎯 **Controlled Story Generation**
- **3-stage pipeline**: Context → Outline → Story with human intervention at each stage
- **Natural language input**: Describe your story in plain English
- **Intelligent context management**: Automatically updates existing stories or creates new ones
- **File-based workflow**: Edit intermediate files before proceeding to next stage

### 🌍 **Consistent World-Building**
- **Entity continuity**: Characters and locations persist across multiple stories
- **LightRAG integration**: Query existing characters, locations, and items from previous stories
- **Entity validation**: Confidence scoring prevents incorrect entity matches (e.g., "whiskers" → "Wendy Whisk")
- **Relationship tracking**: Maintains connections between story elements
- **Provenance tracking**: Records where each entity was first mentioned

### 🎨 **Customizable Storytelling**
- **Template system**: Modify story generation prompts without code changes
- **Length control**: Specify word count or reading time targets with tolerance settings
- **Story parameters**: Control genre, tone, morals, and complexity (0-10 scale)
- **Multiple variations**: Generate different story directions from the same context

### 💰 **Cost Management**
- **Token tracking**: Monitor OpenAI API usage and costs per story
- **Dual API configuration**: Use different models for extraction vs. creative generation
- **Optimization suggestions**: Get recommendations for reducing token usage
- **Usage reports**: Track weekly/monthly costs and patterns

### 🔧 **Developer-Friendly**
- **Comprehensive testing**: Unit, integration, and end-to-end test coverage
- **Type safety**: Full Python type hints throughout
- **Mock support**: Test without external API dependencies
- **Extensible architecture**: Plugin system for templates and future features

## 🚀 Quick Start

### Installation

**Prerequisites:**
- Python 3.8 or higher
- uv (for dependency management)

**Setup:**
```bash
# Clone the repository
git clone <repository-url>
cd jestir

# Install dependencies and create virtual environment
uv sync

# Activate virtual environment
uv shell
```

### Configuration

Create a `.env` file with your API keys:

```bash
# Copy example configuration
cp .env.example .env

# Edit with your actual API keys
nano .env
```

**Required Environment Variables:**
```bash
# OpenAI API Configuration (required)
OPENAI_EXTRACTION_API_KEY=your_extraction_api_key_here
OPENAI_CREATIVE_API_KEY=your_creative_api_key_here

# Optional: Customize models and endpoints
OPENAI_EXTRACTION_MODEL=gpt-4o-mini    # For entity extraction
OPENAI_CREATIVE_MODEL=gpt-4o           # For creative generation
OPENAI_EXTRACTION_TEMPERATURE=0.1      # Lower for consistent extraction
OPENAI_CREATIVE_TEMPERATURE=0.7        # Higher for creativity

# LightRAG Configuration (optional)
LIGHTRAG_BASE_URL=http://localhost:8000
LIGHTRAG_API_KEY=your_lightrag_api_key_here
LIGHTRAG_MOCK_MODE=false               # Set to true for testing

# Logging Configuration (optional)
JESTIR_LOG_TO_DISK=false              # Enable disk logging for debugging
```

### Basic Usage

**Complete story generation workflow:**
```bash
# 1. Create story context from natural language
jestir context "A brave little mouse named Pip saves the forest from a terrible drought"

# 2. Generate story outline (review and edit if needed)
jestir outline context.yaml

# 3. Generate final bedtime story
jestir write outline.md
```

**Iterative context building:**
```bash
# Initial story concept
jestir context "A brave little mouse saves the forest"

# Add more details
jestir context "The mouse has a magical acorn that can make plants grow"

# Add antagonist
jestir context "The antagonist is a greedy fox who wants to steal the acorn"

# Generate outline
jestir outline context.yaml
```

## 📖 Complete Command Reference

### Core Pipeline Commands

#### Context Generation
```bash
# Intelligent context management (creates new or updates existing)
jestir context "natural language input" [--output filename.yaml]

# Force new context (overwrites existing)
jestir context new "natural language input" [--output filename.yaml]
```

#### Outline Generation
```bash
# Generate story outline from context
jestir outline context.yaml [--output filename.md]
```

#### Story Writing
```bash
# Generate final story from outline
jestir write outline.md [--output filename.md] [--context context.yaml]
```

### Length Control

**Set length targets:**
```bash
# Word count targets
jestir context "story input" --length 500
jestir outline context.yaml --length 300
jestir write outline.md --length 400

# Reading time targets (in minutes)
jestir context "story input" --length 3m
jestir outline context.yaml --length 2m
jestir write outline.md --length 4m

# Custom tolerance (default: 10%)
jestir context "story input" --length 500 --tolerance 15
```

**Validate length:**
```bash
# Check if generated content meets length requirements
jestir validate-length outline.md --type outline --suggestions
jestir validate-length story.md --type story --context context.yaml
```

### Entity Management

**Search existing entities:**
```bash
# Search characters, locations, or items
jestir search characters --query "brave mouse"
jestir search locations --type interior --limit 20
jestir search items --format json --export results.yaml
```

**List entities:**
```bash
# List all entities with optional filtering
jestir list characters
jestir list locations --type exterior --format table
```

**Show entity details:**
```bash
# Get detailed information about specific entities
jestir show "Lily" --type character
jestir show "Magic Forest" --type location
```

**Test entity validation:**
```bash
# Test entity matching with confidence scoring
jestir validate-entity "whiskers" --type character
jestir validate-entity "Wendy" --threshold 0.8 --verbose
```

### Validation and Testing

**Validate templates:**
```bash
# Check template syntax and completeness
jestir validate-templates --verbose --fix
```

**Validate context:**
```bash
# Check context file structure and consistency
jestir validate context.yaml --verbose --fix
```

**Test LightRAG connectivity:**
```bash
# Test API connection and configuration
jestir lightrag test --base-url http://localhost:8000
```

### Debugging and Logging

**Verbose output:**
```bash
# Enable debug-level console logging
jestir --verbose context "story input"
jestir --verbose outline context.yaml
jestir --verbose write outline.md
```

**Disk logging:**
```bash
# Enable logging to disk files
export JESTIR_LOG_TO_DISK=true
jestir context "story input"
```

## 🏗️ Architecture

Jestir uses a **Pipeline Architecture** with file-based communication between stages:

```
Natural Language Input → Context (YAML) → Outline (Markdown) → Story (Markdown)
```

### Key Components

- **ContextGenerator**: Extracts entities and relationships using OpenAI AI
- **OutlineGenerator**: Creates story structure from context
- **StoryWriter**: Generates final bedtime story
- **EntityRepository**: Interfaces with LightRAG API for entity retrieval
- **TemplateManager**: Handles template loading and variable substitution
- **TokenTracker**: Monitors OpenAI API usage and costs

### Design Patterns

- **Pipeline Pattern**: Sequential processing with human intervention points
- **Repository Pattern**: Abstracted LightRAG API operations
- **Template Method Pattern**: External templates with variable substitution
- **Command Pattern**: CLI commands encapsulate operations
- **Strategy Pattern**: Intelligent context update vs. creation

## 🧪 Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/performance/

# Run with coverage
uv run pytest --cov=src/jestir
```

### Code Quality

```bash
# Format code
uv run ruff format src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/

# Install pre-commit hooks
uv run pre-commit install
```

### Project Structure

```
jestir/
├── src/jestir/              # Main source code
│   ├── cli.py               # CLI interface
│   ├── models/              # Data models
│   ├── services/            # Core services
│   ├── repositories/        # Data access layer
│   └── utils/               # Utilities
├── templates/               # Story templates
│   ├── prompts/            # AI prompts
│   └── story_template.txt  # Main story template
├── tests/                   # Test files
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── performance/        # Performance tests
├── docs/                    # Documentation
├── output/                  # Generated files (gitignored)
└── pyproject.toml          # Project configuration
```

## 📚 Documentation

- **[CLI Reference](docs/cli-reference.md)** - Complete command-line interface documentation
- **[Architecture](docs/architecture.md)** - System architecture and design patterns
- **[PRD](docs/prd.md)** - Product requirements and specifications
- **[Template Testing Guide](docs/template-testing-guide.md)** - Template development and testing
- **[Token Tracking](docs/token-tracking.md)** - Cost management and optimization

## 🎯 Use Cases

### For Parents
- **Bedtime stories**: Create personalized stories for children ages 3-10
- **Character continuity**: Build ongoing story worlds with recurring characters
- **Educational content**: Incorporate specific morals, lessons, or themes
- **Length control**: Match stories to available reading time

### For Educators
- **Storytelling workshops**: Generate story prompts and examples
- **Creative writing**: Use as a tool for teaching narrative structure
- **Character development**: Explore different character types and relationships

### For Developers
- **AI integration**: Learn patterns for LLM integration and prompt engineering
- **Template systems**: Study extensible template and plugin architectures
- **Cost optimization**: Implement token tracking and usage monitoring

## 🔒 Security & Privacy

- **No PII collection**: No personal information is stored or logged
- **Local processing**: All story generation happens locally
- **API key security**: Keys stored in environment variables only
- **Content safety**: Multi-stage human review prevents inappropriate content

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for:
- Code style and standards
- Testing requirements
- Pull request process
- Issue reporting

## 📄 License

[Add your license here]

## 🆘 Support

- **Documentation**: Check the [docs/](docs/) directory for detailed guides
- **Issues**: Report bugs and request features via GitHub issues
- **Discussions**: Join community discussions for questions and ideas

---

**Jestir** - Where imagination meets AI, one story at a time. 🌟
