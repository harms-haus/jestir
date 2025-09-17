# Coding Standards

## Core Standards

- **Languages & Runtimes:** Python 3.8+
- **Style & Linting:** Ruff formatter and linter
- **Test Organization:** tests/ mirrors src/ structure

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `ContextGenerator` |
| Functions | snake_case | `generate_outline` |
| Constants | UPPER_SNAKE | `MAX_TOKENS` |
| Files | snake_case | `story_writer.py` |

## Critical Rules

- **Type Hints Required:** All functions must have type hints
- **Docstrings Required:** All public functions need docstrings
- **No Direct File I/O:** Use FileHandler utility class
- **Mock External Services:** Never call real APIs in tests
- **Validate User Input:** All CLI inputs must be validated
