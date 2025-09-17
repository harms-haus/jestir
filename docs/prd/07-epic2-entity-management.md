# Epic 2: Templates & LightRAG API Integration

**Epic Goal:** Integrate LightRAG API for read-only entity retrieval and implement the template system for extensible prompt management.

## Story 2.1: LightRAG API Integration

As a parent,
I want the system to reference existing characters and locations from previous stories,
so that we can maintain consistency across stories.

**Acceptance Criteria:**

1. LightRAG API client initialized for read-only entity retrieval
2. Entity search queries LightRAG API for existing characters/locations/items
3. Fuzzy matching for entity variations (e.g., "Purple Dragon" vs "Dragon")
4. Integration tests verify API retrieval functionality
5. Mock mode for testing without LightRAG API

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

## Story 2.4: Context Validation Command

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
