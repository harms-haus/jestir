# Epic 3: Advanced Features & Optimization

**Epic Goal:** Add token tracking for cost management, implement validation and testing tools, and prepare the foundation for future web UI development.

## Story 3.1: Token Usage Tracking

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

## Story 3.2: Template Testing and Preview

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

## Story 3.3: Story Length Control

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

## Story 3.4: Web API Preparation

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

## Story 3.5: Batch Operations Support

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
