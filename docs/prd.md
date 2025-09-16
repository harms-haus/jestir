
# Bedtime Story Generator Product Requirements Document (PRD)

## Goals and Background Context

### Goals

- Create a controlled, personalized bedtime story generation system that allows parent-child collaboration
- Maintain narrative consistency through a reusable world of characters and locations
- Provide human checkpoints to prevent AI hallucinations and ensure age-appropriate content
- Build a cost-effective solution that grows with the child's imagination
- Enable story customization for tone, length, morals, and complexity

### Background Context

Current AI story generation tools lack two critical features: consistent world-building across multiple stories and sufficient human control points to ensure appropriate content. This tool addresses these gaps through a 3-stage pipeline (context → outline → story) that allows intervention at each stage, combined with a knowledge base (LightRAG) that provides existing character and location information for reference. The system uses file-based templates for extensibility without code changes, making it adaptable as storytelling needs evolve.

**Data Entry Process:** LightRAG is populated manually after stories are read, not during generation. When generating a new story, the system queries LightRAG to find existing characters and locations, then creates new entities in the context file for any characters/locations not found. After the story is complete and read, parents can manually add new characters and locations to LightRAG for future stories.

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2024-01-15 | 1.0 | Initial PRD creation | PM |

## Requirements

### Functional

- FR1: The system shall process natural language input and identify existing characters, locations, and items from the LightRAG knowledge base
- FR2: The system shall generate stories through a 3-stage pipeline: context generation, outline creation, and story writing
- FR3: Each pipeline stage shall output an editable file that serves as input for the next stage
- FR4: The system shall support variable-strength control parameters (0-10 scale) for genre, tone, morals, and other story attributes
- FR5: The system shall track entity provenance, recording where each character/location/item was mentioned in user input
- FR6: The system shall support high-level natural language commands for story generation
- FR7: The system shall estimate story length using word count and reading time metrics
- FR8: The system shall use file-based templates with {{key}} substitution for prompts and content generation
- FR9: The system shall allow creation of new entities in the context file for the current story
- FR10: The context system shall maintain complete story memory including settings, entities, relationships, and generation history

### Non Functional

- NFR1: The CLI tool shall execute each pipeline stage independently to allow manual intervention
- NFR2: The system shall optimize token usage for cost-effectiveness with OpenAI API calls
- NFR3: All intermediate files shall be human-readable and editable (YAML for context, Markdown for outline/story)
- NFR4: The system shall support parallel story development through configurable input/output file names
- NFR5: Template files shall be stored externally and loaded at runtime for modification without code changes
- NFR6: The system shall integrate with LightRAG for vector-based retrieval and inference about existing story data
- NFR7: Response time for each generation stage shall be under 30 seconds for typical story complexity
- NFR8: The system shall support Python 3.8+ for broad compatibility

## User Interface Design Goals

### Overall UX Vision

Command-line interface optimized for quick story generation with clear feedback at each stage. Future web interface will provide visual workflow management.

### Key Interaction Paradigms

- Natural language input for story requests
- File-based pipeline for maximum control
- Clear progress indicators for each generation stage

### Core Screens and Views

- CLI command interface
- File outputs (context.yaml, outline.md, story.md)

### Accessibility: None

### Branding

Not applicable for personal tool

### Target Device and Platforms: CLI

MacOS, Linux, Windows (Python 3.8+)

## Technical Assumptions

### Repository Structure: Monorepo

### Service Architecture

Monolithic CLI application with modular components for each pipeline stage. Future web version will wrap CLI functionality.

### Testing Requirements

CRITICAL DECISION - Comprehensive testing including:

- Unit tests for each pipeline stage
- Integration tests for LightRAG connectivity
- Template parsing tests
- Entity extraction tests
- File I/O tests
- Mock tests for OpenAI API calls

### Additional Technical Assumptions and Requests

- Python 3.8+ with type hints throughout
- OpenAI API for LLM interactions
- LightRAG for vector-based entity retrieval
- YAML for context files
- Markdown for human-readable outputs
- External template files with {{key}} substitution pattern
- Poetry for dependency management
- pytest for testing framework
- Black for code formatting
- mypy for type checking

## Epic List

**Epic 1: Foundation & Core Pipeline** - Establish project setup, basic 3-stage pipeline, and file I/O

**Epic 2: Templates & LightRAG Integration** - Template system and LightRAG read-only integration

**Epic 3: Advanced Features & Optimization** - Token tracking, validation, search capabilities, and future web UI prep

## Epic 1: Foundation & Core Pipeline

**Epic Goal:** Establish project setup with Python CLI structure, implement the core 3-stage pipeline (context → outline → story), and create a working prototype that can generate a complete bedtime story from natural language input.

### Story 1.1: Project Initialization and Setup

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

### Story 1.2: Context Generation Pipeline

As a parent,
I want to input a natural language story request and generate a context file,
so that I have a structured representation of my story requirements.

**Acceptance Criteria:**

1. CLI command `story context "natural language input"` creates context.yaml
2. YAML schema implemented as designed (metadata, settings, entities, relationships, user_inputs, plot_points)
3. Default output to context.yaml with option to specify custom filename
4. Entity extraction identifies character names and marks them as new/existing based on LightRAG queries (mock LightRAG for now)
5. Relationship extraction identifies basic relationships (visits, finds, creates)
6. Unit tests cover YAML generation and structure validation
7. Error handling for malformed input

### Story 1.3: Outline Generation Pipeline

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

### Story 1.4: Story Writing Pipeline

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

### Story 1.5: End-to-End Pipeline Test

As a developer,
I want to test the complete pipeline from input to story,
so that I can verify the system works as designed.

**Acceptance Criteria:**

1. Integration test runs all three stages sequentially
2. Test covers entity extraction and relationship parsing
3. Mock OpenAI responses for consistent testing
4. Verify file outputs at each stage
5. Validate context.yaml maintains complete history
6. Test parallel story generation with different filenames

## Epic 2: Templates & LightRAG Integration

**Epic Goal:** Integrate LightRAG for read-only entity retrieval and implement the template system for extensible prompt management.

### Story 2.1: LightRAG Integration

As a parent,
I want the system to reference existing characters and locations from previous stories,
so that we can maintain consistency across stories.

**Acceptance Criteria:**

1. LightRAG initialized for read-only entity retrieval
2. Entity search queries LightRAG for existing characters/locations/items
3. Fuzzy matching for entity variations (e.g., "Purple Dragon" vs "Dragon")
4. Integration tests verify retrieval functionality
5. Mock mode for testing without LightRAG

### Story 2.2: Template System Implementation

As a parent,
I want to modify story generation prompts without changing code,
so that I can customize how stories are created.

**Acceptance Criteria:**

1. Template files stored in templates/ directory
2. Templates for context, outline, and story generation
3. Template loading with {{key}} substitution from context
4. Character type templates (protagonist, antagonist, supporting)
5. Location type templates (interior, exterior, region)
6. Tests verify template parsing and substitution
7. Error handling for missing templates or keys

### Story 2.3: Entity Search and List Commands

As a parent,
I want to search and browse existing entities from LightRAG,
so that I can reference them in new stories.

**Acceptance Criteria:**

1. Command `story search characters --query "dragon"` returns matches from LightRAG
2. Command `story list locations --type interior` shows filtered results
3. Command `story show character "Lily"` displays full details
4. Pagination for large result sets
5. Output in readable table format
6. Export option to YAML for context file use

### Story 2.4: Manual LightRAG Data Entry

As a parent,
I want to manually add new characters and locations to LightRAG after reading a story,
so that they can be referenced in future stories.

**Acceptance Criteria:**

1. Command `story add-to-lightrag character --name "X" --description "Y"` adds character to LightRAG
2. Command `story add-to-lightrag location --name "X" --type "interior" --description "Y"` adds location to LightRAG
3. Command `story add-to-lightrag item --name "X" --properties "magical,glowing"` adds item to LightRAG
4. Entity validation ensures required fields are present
5. Duplicate detection with confirmation prompt
6. Success confirmation with entity ID
7. Unit tests for each command type

### Story 2.5: Context Validation Command

As a parent,
I want to validate a context file before generation,
so that I can catch conflicts or missing references early.

**Acceptance Criteria:**

1. Command `story validate context.yaml` checks structure
2. Verify all entity references exist in LightRAG
3. Check relationship consistency
4. Validate required settings are present
5. Warning for unusual patterns (e.g., no protagonists)
6. Clear error messages with fix suggestions

## Epic 3: Advanced Features & Optimization

**Epic Goal:** Add token tracking for cost management, implement validation and testing tools, and prepare the foundation for future web UI development.

### Story 3.1: Token Usage Tracking

As a parent,
I want to track OpenAI API token usage per story,
so that I can optimize costs over time.

**Acceptance Criteria:**

1. Token counting for each OpenAI API call
2. Token usage stored in context.yaml per generation stage
3. Command `story stats` shows token usage summary
4. Cost estimation based on current OpenAI pricing
5. Weekly/monthly usage reports
6. Token optimization suggestions based on patterns

### Story 3.2: Template Testing and Preview

As a parent,
I want to test templates before using them in story generation,
so that I can verify they work correctly.

**Acceptance Criteria:**

1. Command `story template test protagonist.txt --name "Lily"`
2. Preview shows rendered template with substitutions
3. Validation catches missing required keys
4. Dry-run mode for generation without API calls
5. Template syntax validation
6. Unit tests for template edge cases

### Story 3.3: Story Length Control

As a parent,
I want to specify desired story length,
so that I can match stories to available reading time.

**Acceptance Criteria:**

1. Length specification in context settings (word count or reading time)
2. Outline generation respects length constraints
3. Story generation adheres to target length (±10%)
4. Command flag `--length 500` or `--time 5`
5. Length validation before generation
6. Automatic adjustment suggestions if outline too long/short

### Story 3.4: Web API Preparation

As a developer,
I want to expose CLI functionality through a Python API,
so that a future web interface can use it.

**Acceptance Criteria:**

1. Python module with public API for all CLI commands
2. Async support for long-running operations
3. Progress callbacks for generation stages
4. Error handling returns structured responses
5. Session management for parallel story generation
6. Comprehensive docstrings for API methods
7. Unit tests for API layer

### Story 3.5: Batch Operations Support

As a parent,
I want to process multiple story variations efficiently,
so that I can explore different story directions.

**Acceptance Criteria:**

1. Command `story batch --variations 3` generates multiple outlines
2. Parallel processing for independent operations
3. Variation parameters (tone, length, moral emphasis)
4. Results comparison in markdown table
5. Selection command to choose preferred variation
6. Token usage optimization for batches

## Checklist Results Report

**Overall PRD completeness:** 95%
**MVP scope appropriateness:** Just Right
**Readiness for architecture phase:** Ready
**Most critical gaps:** None blocking

## Next Steps

### UX Expert Prompt

For future web UI development: "Review the CLI workflow defined in this PRD and design a visual interface that maintains the 3-stage pipeline control while simplifying entity management. Focus on making the context editing stage visual and intuitive."

### Architect Prompt

"Create a Python CLI architecture that implements the 3-stage pipeline defined in this PRD. Focus on modular design where each stage can run independently, with a plugin system for templates and clear interfaces for future web API exposure. Ensure LightRAG integration is abstracted for testing."
