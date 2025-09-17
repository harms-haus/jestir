# Technical Assumptions

## Repository Structure: Monorepo

## Service Architecture

Monolithic CLI application with modular components for each pipeline stage. Future web version will wrap CLI functionality.

## Testing Requirements

CRITICAL DECISION - Comprehensive testing including:

- Unit tests for each pipeline stage
- Integration tests for LightRAG API connectivity
- Template parsing tests
- Entity extraction tests
- File I/O tests
- Mock tests for OpenAI API calls

## Additional Technical Assumptions and Requests

- Python 3.8+ with type hints throughout
- OpenAI API for LLM interactions
- LightRAG API for vector-based entity retrieval
- YAML for context files
- Markdown for human-readable outputs
- External template files with {{key}} substitution pattern
- Poetry for dependency management
- pytest for testing framework
- Black for code formatting
- mypy for type checking
