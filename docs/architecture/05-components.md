# Components

## CLI Interface Component

**Responsibility:** Parse and route commands to appropriate handlers

**Key Interfaces:**

- `context` command → ContextGenerator
- `outline` command → OutlineGenerator  
- `write` command → StoryWriter
- Search/list commands → EntityRepository
- Manual data entry commands → EntityRepository

**Dependencies:** Click framework, all service components

**Technology Stack:** Click 8.1+, Python type hints

## ContextGenerator Component

**Responsibility:** Parse natural language input and create structured context

**Key Interfaces:**

- `generate(input_text: str, existing_context: Optional[StoryContext]) → StoryContext`
- `extract_entities(text: str) → List[Entity]`
- `extract_relationships(text: str, entities: List[Entity]) → List[Relationship]`

**Dependencies:** EntityRepository, TemplateManager, OpenAIClient

**Technology Stack:** Pydantic for validation, PyYAML for serialization

## OutlineGenerator Component

**Responsibility:** Create story outline from context using templates and AI

**Key Interfaces:**

- `generate(context: StoryContext) → str`
- `apply_length_constraints(outline: str, target_words: int) → str`

**Dependencies:** TemplateManager, OpenAIClient, TokenTracker

**Technology Stack:** OpenAI SDK, Markdown generation

## StoryWriter Component

**Responsibility:** Generate final story from outline and context

**Key Interfaces:**

- `generate(outline: str, context: StoryContext) → str`
- `estimate_reading_time(story: str) → float`
- `count_words(story: str) → int`

**Dependencies:** TemplateManager, OpenAIClient, TokenTracker

**Technology Stack:** OpenAI SDK, Markdown formatting

## EntityRepository Component  

**Responsibility:** Interface with LightRAG for entity retrieval

**Key Interfaces:**

- `search(query: str, entity_type: Optional[str]) → List[Entity]`
- `get(entity_id: str) → Optional[Entity]`
- `exists(name: str) → bool`
- `add_entity(entity: Entity) → str`  # Manual data entry after story reading

**Dependencies:** LightRAG

**Technology Stack:** LightRAG Python client, read-only operations

## TemplateManager Component

**Responsibility:** Load and process template files with variable substitution

**Key Interfaces:**

- `load_template(template_name: str) → str`
- `render(template: str, context: Dict[str, Any]) → str`
- `validate_template(template: str) → List[str]`  # Returns missing keys

**Dependencies:** File system access

**Technology Stack:** Custom regex-based substitution

## TokenTracker Component

**Responsibility:** Monitor and report OpenAI API token usage

**Key Interfaces:**

- `track_usage(prompt: str, response: str, model: str) → TokenUsage`
- `get_cost_estimate(usage: TokenUsage) → float`
- `generate_report(period: str) → UsageReport`

**Dependencies:** OpenAI tokenizer

**Technology Stack:** tiktoken library for counting
