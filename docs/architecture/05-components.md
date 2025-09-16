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

**Responsibility:** Parse natural language input using OpenAI AI to extract entities and relationships, creating structured context

**Key Interfaces:**

- `generate(input_text: str, existing_context: Optional[StoryContext]) → StoryContext`
- `extract_entities(text: str) → List[Entity]` - Uses OpenAI AI to parse natural language and identify entities
- `extract_relationships(text: str, entities: List[Entity]) → List[Relationship]` - Uses OpenAI AI to parse natural language and extract relationships

**Dependencies:** EntityRepository, TemplateManager, OpenAIClient (Extraction)

**Technology Stack:** Pydantic for validation, PyYAML for serialization, OpenAI SDK for information extraction

## OutlineGenerator Component

**Responsibility:** Create story outline from context using templates and AI

**Key Interfaces:**

- `generate(context: StoryContext) → str`
- `apply_length_constraints(outline: str, target_words: int) → str`

**Dependencies:** TemplateManager, OpenAIClient (Creative), TokenTracker

**Technology Stack:** OpenAI SDK for creative generation, Markdown generation

## StoryWriter Component

**Responsibility:** Generate final story from outline and context

**Key Interfaces:**

- `generate(outline: str, context: StoryContext) → str`
- `estimate_reading_time(story: str) → float`
- `count_words(story: str) → int`

**Dependencies:** TemplateManager, OpenAIClient (Creative), TokenTracker

**Technology Stack:** OpenAI SDK for creative generation, Markdown formatting

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

### Prompt Templating

The creative AI prompts (outline and story) are driven by external templates that use `{{key}}` substitution. Templates live under `templates/` (e.g., `templates/story_template.txt` and `templates/prompts/`). They accept the same template values exposed by the `StoryContext` model and used in services:

- `{{genre}}`, `{{tone}}`, `{{length}}`, `{{age_appropriate}}`, `{{morals}}`
- `{{characters}}`, `{{locations}}`, `{{items}}`
- `{{plot_points}}`, `{{user_inputs}}`, `{{outline}}`
- Derived helpers like `{{target_word_count}}` may be provided by the generator when rendering

See the dedicated documentation in `docs/architecture/templating.md` for full details and examples.

## TokenTracker Component

**Responsibility:** Monitor and report OpenAI API token usage

**Key Interfaces:**

- `track_usage(prompt: str, response: str, model: str) → TokenUsage`
- `get_cost_estimate(usage: TokenUsage) → float`
- `generate_report(period: str) → UsageReport`

**Dependencies:** OpenAI tokenizer

**Technology Stack:** tiktoken library for counting
