# Infrastructure and Deployment

## Infrastructure as Code

- **Tool:** Not applicable for CLI
- **Location:** N/A
- **Approach:** Local installation via pip/poetry

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
