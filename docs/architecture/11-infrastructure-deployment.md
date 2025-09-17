# Infrastructure and Deployment

## Infrastructure as Code

- **Tool:** Not applicable for CLI
- **Location:** N/A
- **Approach:** Local installation via pip/uv

## Virtual Environment Management

uv provides integrated virtual environment management that eliminates the need for separate venv or conda environments:

- **Automatic Environment Creation:** `uv sync` automatically creates and manages a virtual environment
- **Environment Activation:** `uv shell` activates the project's virtual environment
- **Command Execution:** `uv run <command>` executes commands within the virtual environment
- **Dependency Isolation:** Each project gets its own isolated environment automatically
- **No Manual Setup:** No need to manually create, activate, or manage virtual environments

**Key Commands:**
- `uv sync` - Install dependencies and create/update virtual environment
- `uv shell` - Activate the virtual environment
- `uv run <command>` - Run commands within the virtual environment
- `uv add <package>` - Add new dependencies
- `uv remove <package>` - Remove dependencies

## Deployment Strategy

- **Strategy:** Local installation
- **CI/CD Platform:** GitHub Actions for testing
- **Pipeline Configuration:** `.github/workflows/test.yml`

## Environments

- **Development:** Local development with .env file
- **Testing:** Pytest with mocked external services
- **Production:** User's local machine

## Environment Promotion Flow

```text
Development (local) -> Testing (CI) -> Release (PyPI/GitHub)
```

## Rollback Strategy

- **Primary Method:** Version pinning in pyproject.toml
- **Trigger Conditions:** Test failures in CI
- **Recovery Time Objective:** Immediate (local tool)
