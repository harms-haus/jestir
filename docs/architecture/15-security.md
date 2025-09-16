# Security

## Input Validation

- **Validation Library:** Pydantic
- **Validation Location:** CLI layer before processing
- **Required Rules:**
  - All external inputs MUST be validated
  - File paths must be sanitized
  - Template keys must be alphanumeric

## Authentication & Authorization

- **Auth Method:** API key for OpenAI only
- **Session Management:** Not applicable for CLI
- **Required Patterns:**
  - API keys only via environment variables (`OPENAI_API_KEY`)
  - Base URLs configurable via environment variables (`OPENAI_BASE_URL`)
  - Never log API keys or sensitive configuration

## Secrets Management

- **Development:** .env file (gitignored)
- **Production:** Environment variables
- **Code Requirements:**
  - NEVER hardcode secrets
  - Access via settings module only
  - No secrets in logs or error messages

## API Security

- **Rate Limiting:** Respect OpenAI rate limits
- **CORS Policy:** Not applicable for CLI
- **Security Headers:** Not applicable for CLI
- **HTTPS Enforcement:** OpenAI SDK handles TLS

## Data Protection

- **Encryption at Rest:** Not required (local files)
- **Encryption in Transit:** TLS for API calls
- **PII Handling:** No PII collected
- **Logging Restrictions:** No story content in logs

## Dependency Security

- **Scanning Tool:** pip-audit
- **Update Policy:** Monthly security updates
- **Approval Process:** Review changelogs before updating

## Security Testing

- **SAST Tool:** bandit for Python
- **DAST Tool:** Not applicable for CLI
- **Penetration Testing:** Not required for local tool
