# Test Strategy and Standards

## Testing Philosophy

- **Approach:** Test-Driven Development (TDD)
- **Coverage Goals:** 80% minimum, 90% target
- **Test Pyramid:** 70% unit, 20% integration, 10% E2E

## Test Types and Organization

### Unit Tests

- **Framework:** pytest 7.4+
- **File Convention:** `test_[module_name].py`
- **Location:** `tests/unit/`
- **Mocking Library:** pytest-mock
- **Coverage Requirement:** 85%

**AI Agent Requirements:**

- Generate tests for all public methods
- Cover edge cases and error conditions
- Follow AAA pattern (Arrange, Act, Assert)
- Mock all external dependencies

### Integration Tests

- **Scope:** Pipeline stages, LightRAG integration
- **Location:** `tests/integration/`
- **Test Infrastructure:**
  - **LightRAG:** Mock with in-memory retrieval
  - **OpenAI:** Mock responses from fixtures
  - **File System:** Temp directories

### End-to-End Tests

- **Framework:** pytest with CLI runner
- **Scope:** Complete story generation pipeline
- **Environment:** Local with mocked externals
- **Test Data:** Fixture files in tests/fixtures/

## Test Data Management

- **Strategy:** Fixtures for predictable tests
- **Fixtures:** `tests/fixtures/`
- **Factories:** Entity and context factories
- **Cleanup:** Automatic via pytest fixtures

## Continuous Testing

- **CI Integration:** GitHub Actions on every push
- **Performance Tests:** Track token usage and generation time
- **Security Tests:** Validate no API keys in code
