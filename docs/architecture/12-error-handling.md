# Error Handling Strategy

## General Approach

- **Error Model:** Custom exceptions for each component
- **Exception Hierarchy:** BaseStoryException → specific exceptions
- **Error Propagation:** Bubble up with context, handle at CLI level

## Logging Standards

- **Library:** Python logging module
- **Format:** `%(timestamp)s - %(name)s - %(level)s - %(message)s`
- **Levels:** DEBUG (verbose), INFO (standard), WARNING (issues), ERROR (failures)
- **Console Logging:** Controlled by `--verbose` CLI flag (debug level output)
- **Disk Logging:** Controlled by `JESTIR_LOG_TO_DISK` environment variable (off by default)
- **Required Context:**
  - Correlation ID: Story generation session ID
  - Service Context: Component name
  - User Context: No PII logged

## Error Handling Patterns

### External API Errors

- **Retry Policy:** 3 retries with exponential backoff
- **Circuit Breaker:** Not needed for CLI tool
- **Timeout Configuration:** 30 seconds for OpenAI calls
- **Error Translation:** User-friendly messages for common errors

### Business Logic Errors

- **Custom Exceptions:** `EntityNotFound`, `TemplateError`, `ValidationError`
- **User-Facing Errors:** Clear messages with fix suggestions
- **Error Codes:** STORY-001 format for tracking

### Data Consistency

- **Transaction Strategy:** File writes are atomic
- **Compensation Logic:** Previous file versions preserved
- **Idempotency:** Repeated commands produce same result
