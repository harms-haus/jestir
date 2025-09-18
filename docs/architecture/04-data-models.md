# Data Models

## OpenAI Configuration Models

### ExtractionAPIConfig Model

**Purpose:** Configuration for OpenAI API used for information extraction (entities and relationships)

**Key Attributes:**

- api_key: string - OpenAI API key for extraction endpoint (from `OPENAI_EXTRACTION_API_KEY`)
- base_url: string - Base URL for extraction API (from `OPENAI_EXTRACTION_BASE_URL`, default: https://api.openai.com/v1)
- model: string - Model to use for extraction (from `OPENAI_EXTRACTION_MODEL`, recommended: gpt-4o-mini, gpt-4o, gpt-oss:20b)
- max_tokens: int - Maximum tokens for extraction requests (from `OPENAI_EXTRACTION_MAX_TOKENS`)
- temperature: float - Temperature setting for extraction (from `OPENAI_EXTRACTION_TEMPERATURE`, lower for more consistent results)

### CreativeAPIConfig Model

**Purpose:** Configuration for OpenAI API used for creative generation (outlines and stories)

**Key Attributes:**

- api_key: string - OpenAI API key for creative endpoint (from `OPENAI_CREATIVE_API_KEY`)
- base_url: string - Base URL for creative API (from `OPENAI_CREATIVE_BASE_URL`, default: https://api.openai.com/v1)
- model: string - Model to use for creative generation (from `OPENAI_CREATIVE_MODEL`, recommended: gpt-4o, gpt-4, gpt-oss:120b)
- max_tokens: int - Maximum tokens for creative requests (from `OPENAI_CREATIVE_MAX_TOKENS`)
- temperature: float - Temperature setting for creative generation (from `OPENAI_CREATIVE_TEMPERATURE`, higher for more creativity)

## Context Entity Model

**Purpose:** Represents all entities (characters, locations, items) in the story world

**Key Attributes:**

- id: string - Unique identifier (e.g., "char_001")
- type: string - Entity type (character|location|item)
- subtype: string - Specific subtype (protagonist|interior|magical)
- name: string - Display name
- description: string - Full text description
- existing: boolean - Whether entity was found in LightRAG API (true) or is new to this story (false)
- rag_id: string - LightRAG API reference if existing
- properties: dict - Type-specific attributes

**Relationships:**

- Can be subject or object in relationships
- Can have properties specific to their type

## Relationship Model

**Purpose:** Captures interactions and connections between entities

**Key Attributes:**

- type: string - Relationship type (finds|visits|creates|owns)
- subject: string|list - Entity ID(s) performing action
- object: string|list - Entity ID(s) receiving action
- location: string - Optional location context
- mentioned_at: list - User input references
- metadata: dict - Additional relationship data

**Relationships:**

- Links entities together
- Provides narrative causality

## StoryContext Model

**Purpose:** Complete context for story generation including all settings and history

**Key Attributes:**

- metadata: dict - Version, timestamps, token usage
- settings: dict - Genre, tone, length, morals
- entities: dict - All entities keyed by ID
- relationships: list - All entity relationships
- user_inputs: dict - All user prompts and requests (preserves complete conversation history)
- plot_points: list - Key narrative points
- outline: string - Generated outline content
- story: string - Generated story content

**Relationships:**

- Contains all entities and relationships
- Updated at each pipeline stage

## Entity Validation Models

### LightRAGEntity Model

**Purpose:** Represents an entity from LightRAG API with validation metadata

**Key Attributes:**

- name: string - Entity name from LightRAG
- entity_type: string - Entity type (character|location|item)
- description: string - Entity description from LightRAG
- properties: dict - Additional entity properties
- relationships: list - Entity relationships
- confidence: float - Validation confidence score (0.0-1.0)
- similarity_score: float - String similarity score (0.0-1.0)

### EntityMatchResult Model

**Purpose:** Result of entity validation with confidence scoring

**Key Attributes:**

- entity: LightRAGEntity - The matched entity
- confidence: float - Overall confidence score (0.0-1.0)
- similarity_score: float - String similarity score (0.0-1.0)
- is_exact_match: boolean - Whether this is an exact string match
- is_high_confidence: boolean - Whether confidence meets high threshold
- match_reason: string - Human-readable reason for the match

**Validation Thresholds:**

- exact_match_threshold: 0.95 (exact string matches)
- high_confidence_threshold: 0.8 (high confidence matches)
- low_confidence_threshold: 0.5 (minimum usable matches)
