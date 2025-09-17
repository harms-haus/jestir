# Requirements

## Functional

- FR1: The system shall process natural language input using OpenAI AI to identify existing characters, locations, and items from the LightRAG API knowledge base
- FR2: The system shall generate stories through a 3-stage pipeline: context generation, outline creation, and story writing
- FR3: Each pipeline stage shall output an editable file that serves as input for the next stage
- FR4: The system shall support variable-strength control parameters (0-10 scale) for genre, tone, morals, and other story attributes
- FR5: The system shall track entity provenance, recording where each character/location/item was mentioned in user input
- FR6: The system shall support high-level natural language commands for story generation using OpenAI AI parsing
- FR7: The system shall estimate story length using word count and reading time metrics
- FR8: The system shall use file-based templates with {{key}} substitution for prompts and content generation
- FR9: The system shall allow creation of new entities in the context file for the current story
- FR10: The context system shall maintain complete story memory including settings, entities, relationships, and generation history

## Non Functional

- NFR1: The CLI tool shall execute each pipeline stage independently to allow manual intervention
- NFR2: The system shall optimize token usage for cost-effectiveness with separate OpenAI API calls for extraction and creative generation
- NFR3: All intermediate files shall be human-readable and editable (YAML for context, Markdown for outline/story)
- NFR4: The system shall support parallel story development through configurable input/output file names
- NFR5: Template files shall be stored externally and loaded at runtime for modification without code changes
- NFR6: The system shall integrate with the LightRAG API for vector-based retrieval and inference about existing story data
- NFR7: Response time for each generation stage shall be under 30 seconds for typical story complexity
- NFR8: The system shall support Python 3.8+ for broad compatibility
- NFR9: The system shall support separate OpenAI API configurations for extraction and creative generation, allowing different models and endpoints
