# Jestir Development Makefile
# Common development commands for the Jestir project

.PHONY: help install test lint type-check format check-all clean dev-setup

# Default target
help:
	@echo "Jestir Development Commands:"
	@echo "  install      - Install dependencies and setup virtual environment"
	@echo "  test         - Run all tests"
	@echo "  lint         - Run ruff linting on src/ directory"
	@echo "  format       - Run ruff formatting on src/ directory"
	@echo "  type-check   - Run mypy type checking on src/ directory"
	@echo "  check-all    - Run linting, formatting, type checking, and tests"
	@echo "  clean        - Clean up temporary files and caches"
	@echo "  dev-setup    - Complete development environment setup"
	@echo "  pre-commit   - Run pre-commit hooks on all files"
	@echo "  pre-commit-src - Run pre-commit hooks only on src/ directory"

# Install dependencies and setup virtual environment
install:
	uv sync

# Run all tests
test:
	uv run pytest tests/ -v

# Run ruff linting on src/ directory only
lint:
	uv run ruff check src/

# Run ruff formatting on src/ directory only
format:
	uv run ruff format src/

# Run mypy type checking on src/ directory only
type-check:
	uv run mypy src/ --ignore-missing-imports

# Run all checks (linting, formatting, type checking, and tests)
check-all: lint format type-check test
	@echo "✅ All checks passed!"

# Clean up temporary files and caches
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/ 2>/dev/null || true

# Complete development environment setup
dev-setup: install
	@echo "Setting up development environment..."
	uv run pre-commit install
	@echo "✅ Development environment ready!"

# Run pre-commit hooks on all files
pre-commit:
	uv run pre-commit run --all-files

# Run pre-commit hooks only on src/ directory
pre-commit-src:
	uv run pre-commit run --files src/

# Development workflow: run checks after making changes
dev-check: lint format type-check
	@echo "✅ Development checks completed!"

# Quick check for CI/CD
ci-check: lint type-check test
	@echo "✅ CI checks completed!"
