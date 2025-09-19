# New Context Generator Approach

## Overview

The context generator has been updated to use a more efficient and accurate approach for extracting entities from story input using LightRAG's knowledge graph.

## New Approach

### Step 1: Extract Entity Names
- Get available graph node labels from LightRAG using `/graph/label/list`
- Use OpenAI to analyze the story input and identify which graph node labels are mentioned
- Return a list of graph node labels that the AI is confident are included in the prompt

### Step 2: Iterative Entity Lookup
- Loop until the list of entity names is empty or a loop returns 0 results
- In each iteration:
  - Use LightRAG's `/query` endpoint to request information about ALL remaining entities
  - Try to find entity entries by comparing their names to the graph node labels
  - If any entry is found, extract the description and remove that entity from the list
  - Continue until no more entities can be found

### Step 3: Entity Matching
- Use multiple matching strategies:
  - Exact name matching
  - Partial name matching
  - Similarity matching with configurable threshold (default: 0.6)

## Benefits

1. **More Accurate**: Uses AI to identify which entities are actually mentioned in the story
2. **Efficient**: Only queries for entities that are likely to exist in the knowledge base
3. **Robust**: Handles various name variations and partial matches
4. **Iterative**: Continues searching until all possible entities are found

## Implementation Details

### New Methods

- `_extract_entity_names_with_labels()`: Extracts entity names using OpenAI with graph labels
- `_iterative_entity_lookup()`: Implements the iterative lookup process
- `_query_entities_data()`: Queries LightRAG for entity information
- `_find_matching_entity_name()`: Matches entity names using multiple strategies
- `_determine_subtype()`: Determines entity subtype based on type

### Configuration

The approach uses the existing LightRAG configuration and can be customized through:
- Similarity threshold for name matching
- Maximum number of graph labels to consider
- Query parameters for LightRAG API calls

## Usage

The new approach is automatically used when calling `generate_context()` on a `ContextGenerator` instance. No changes are needed to existing code.

## Fallback Behavior

If the new approach fails, the system falls back to the previous approach using similarity matching between candidate phrases and graph labels.

## Testing

A test script is provided at `test_new_context_generator.py` to verify the implementation works correctly.
