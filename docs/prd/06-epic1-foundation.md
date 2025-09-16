# Epic 1: Foundation & Core Pipeline

**Epic Goal:** Establish project setup with Python CLI structure, implement the core 3-stage pipeline (context → outline → story), and create a working prototype that can generate a complete bedtime story from natural language input using OpenAI AI parsing.

## Story 1.1: Project Initialization and Setup

As a developer,
I want to initialize the Python project with proper structure and dependencies,
so that I have a maintainable codebase with all required tools.

**Acceptance Criteria:**

1. Python project initialized with Poetry for dependency management
2. Project structure created with src/, tests/, templates/, and output/ directories
3. Core dependencies installed (PyYAML, OpenAI, pytest, black, mypy)
4. Basic CLI structure using Click or argparse
5. Git repository initialized with .gitignore for Python
6. README.md with basic project description and setup instructions
7. Pre-commit hooks configured for black and mypy

## Story 1.2: Context Generation Pipeline

As a parent,
I want to input a natural language story request and generate a context file using OpenAI AI parsing,
so that I have a structured representation of my story requirements.

**Acceptance Criteria:**

1. CLI command `story context "natural language input"` creates context.yaml
2. YAML schema implemented as designed (metadata, settings, entities, relationships, user_inputs, plot_points)
3. Default output to context.yaml with option to specify custom filename
4. Entity extraction identifies character names and marks them as new/existing based on LightRAG queries (mock LightRAG for now)
5. Relationship extraction identifies basic relationships (visits, finds, creates)
6. Unit tests cover YAML generation and structure validation
7. Error handling for malformed input

## Story 1.3: Outline Generation Pipeline

As a parent,
I want to generate a story outline from a context file,
so that I can review and edit the story structure before final generation.

**Acceptance Criteria:**

1. CLI command `story outline context.yaml` creates outline.md
2. OpenAI API integration for outline generation
3. Template system reads outline_template.txt with {{key}} substitutions
4. Outline in markdown format with clear sections/scenes
5. Context file updated with generated outline content
6. Unit tests mock OpenAI API calls
7. Configurable input/output file names

## Story 1.4: Story Writing Pipeline

As a parent,
I want to generate the final story from an approved outline,
so that I have a complete bedtime story ready to read.

**Acceptance Criteria:**

1. CLI command `story write outline.md` creates story.md
2. OpenAI API call uses outline and context for story generation
3. Template system reads story_template.txt with {{key}} substitutions
4. Plain markdown output with proper paragraph formatting
5. Context file updated with generated story content
6. Reading time estimation displayed after generation
7. Word count displayed after generation

## Story 1.5: End-to-End Pipeline Test

As a developer,
I want to test the complete pipeline from input to story,
so that I can verify the system works as designed.

**Acceptance Criteria:**

1. Integration test runs all three stages sequentially
2. Test covers entity extraction and relationship parsing using OpenAI AI
3. Mock OpenAI responses for consistent testing
4. Verify file outputs at each stage
5. Validate context.yaml maintains complete history
6. Test parallel story generation with different filenames
