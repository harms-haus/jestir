#!/bin/bash
# Jestir Development Workflow Script
# Automatically runs checks after completing development tasks

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to run checks
run_checks() {
    local check_type="$1"

    print_status "Running $check_type checks..."

    case "$check_type" in
        "lint")
            uv run ruff check src/
            ;;
        "format")
            uv run ruff format src/
            ;;
        "type-check")
            uv run mypy src/ --ignore-missing-imports
            ;;
        "test")
            uv run pytest tests/ -v
            ;;
        "all")
            print_status "Running comprehensive checks..."
            uv run ruff check src/
            uv run ruff format src/
            uv run mypy src/ --ignore-missing-imports
            uv run pytest tests/ -v
            ;;
        *)
            print_error "Unknown check type: $check_type"
            echo "Available types: lint, format, type-check, test, all"
            exit 1
            ;;
    esac

    print_success "$check_type checks completed successfully!"
}

# Function to show help
show_help() {
    echo "Jestir Development Workflow Script"
    echo ""
    echo "Usage: $0 [OPTIONS] [CHECK_TYPE]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -v, --verbose  Enable verbose output"
    echo "  -f, --fix      Auto-fix issues where possible"
    echo ""
    echo "Check Types:"
    echo "  lint         Run ruff linting on src/ directory"
    echo "  format       Run ruff formatting on src/ directory"
    echo "  type-check   Run mypy type checking on src/ directory"
    echo "  test         Run all tests"
    echo "  all          Run all checks (default)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all checks"
    echo "  $0 lint              # Run only linting"
    echo "  $0 --fix all         # Run all checks with auto-fix"
    echo "  $0 --verbose test    # Run tests with verbose output"
}

# Parse command line arguments
VERBOSE=false
AUTO_FIX=false
CHECK_TYPE="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--fix)
            AUTO_FIX=true
            shift
            ;;
        lint|format|type-check|test|all)
            CHECK_TYPE="$1"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set verbose mode if requested
if [ "$VERBOSE" = true ]; then
    set -x
fi

# Change to project root directory
cd "$(dirname "$0")/.."

print_status "Starting Jestir development workflow..."
print_status "Working directory: $(pwd)"
print_status "Check type: $CHECK_TYPE"

# Run the requested checks
run_checks "$CHECK_TYPE"

print_success "Development workflow completed successfully!"
