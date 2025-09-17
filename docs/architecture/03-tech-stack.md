# Tech Stack

## Cloud Infrastructure

- **Provider:** Local development initially
- **Key Services:** File system for storage, potential future cloud deployment
- **Deployment Regions:** N/A for CLI tool

## Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **Language** | Python | 3.8+ | Primary development language | Type hints, broad compatibility, rich ecosystem |
| **Package Manager** | Poetry | 1.7+ | Dependency management | Lock file support, virtual env management |
| **CLI Framework** | Click | 8.1+ | Command-line interface | Declarative commands, automatic help, testing support |
| **LLM Integration** | OpenAI Python SDK | 1.0+ | AI content generation | Official SDK, async support, token counting, dual client support |
| **Knowledge Graph & RAG** | LightRAG API | Latest | Hybrid entity retrieval | Knowledge-graph and RAG hybrid system with natural language queries, no traditional IDs, returns natural language responses by default |
| **Data Format** | PyYAML | 6.0 | Context file handling | Human-readable, preserves structure |
| **Template Engine** | Custom | N/A | Simple {{key}} substitution | Minimal complexity, easy to understand |
| **Testing** | pytest | 7.4+ | Unit and integration tests | Fixtures, mocking, good assertion messages |
| **Mocking** | pytest-mock | 3.12+ | Mock external services | Clean mock management |
| **Code Formatting** | Black | 23.0+ | Code style enforcement | No debates, consistent style |
| **Type Checking** | mypy | 1.5+ | Static type checking | Catch errors early, improve IDE support |
| **HTTP Client** | httpx | 0.25+ | Async HTTP for OpenAI | Better than requests for async operations |
| **Validation** | Pydantic | 2.0+ | Data validation | Type-safe YAML parsing, automatic validation |
