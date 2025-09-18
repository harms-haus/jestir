# Epic 2: Templates & LightRAG API Integration

**Epic Goal:** Integrate LightRAG API for read-only entity retrieval with validation, implement the template system for extensible prompt management, and ensure accurate entity matching through confidence scoring.

## Story 2.1: LightRAG API Integration

As a parent,
I want the system to reference existing characters and locations from previous stories,
so that we can maintain consistency across stories.

**Acceptance Criteria:**

1. LightRAG API client initialized for read-only entity retrieval
2. Entity search queries LightRAG API for existing characters/locations/items
3. Fuzzy matching for entity variations (e.g., "Purple Dragon" vs "Dragon")
4. Entity validation with confidence scoring to prevent incorrect matches
5. Integration tests verify API retrieval functionality
6. Mock mode for testing without LightRAG API

## Story 2.2: Template System Implementation

As a parent,
I want to modify story generation prompts without changing code,
so that I can customize how stories are created.

**Acceptance Criteria:**

1. Template files stored in templates/ directory
2. Templates for context, outline, and story generation
3. Template loading with {{key}} substitution from context
4. Character type templates (protagonist, antagonist, driving, supporting)
5. Location type templates (interior, exterior, region)
6. Tests verify template parsing and substitution
7. Error handling for missing templates or keys

## Story 2.3: Entity Search and List Commands

As a parent,
I want to search and browse existing entities from the LightRAG API,
so that I can reference them in new stories.

**Acceptance Criteria:**

1. Command `jestir search characters --query "dragon"` returns matches from LightRAG API
2. Command `jestir list locations --type interior` shows filtered results
3. Command `jestir show character "Lily"` displays full details
4. Pagination for large result sets
5. Output in readable table format
6. Export option to YAML for context file use

## Story 2.4: Entity Validation System

As a parent,
I want the system to validate entity matches from LightRAG queries with confidence scoring,
so that incorrect matches like "whiskers" → "Wendy Whisk" are prevented.

**Acceptance Criteria:**

1. Entity validation with confidence scoring (0.0-1.0) based on string similarity and type matching
2. Configurable confidence thresholds (default: 0.5 minimum, 0.8 high confidence)
3. User warnings for moderate confidence matches requiring verification
4. Low confidence matches (<0.5) are skipped by default
5. Command `jestir validate-entity "query" --type character` for testing entity matching
6. Detailed logging of match quality and confidence scores
7. Integration with context generation to validate all entity matches

## Story 2.5: Context Validation Command

As a parent,
I want to validate a context file before generation,
so that I can catch conflicts or missing references early.

**Acceptance Criteria:**

1. Command `jestir validate context.yaml` checks structure
2. Verify all entity references exist in LightRAG API
3. Check relationship consistency
4. Validate required settings are present
5. Warning for unusual patterns (e.g., no protagonists)
6. Clear error messages with fix suggestions
