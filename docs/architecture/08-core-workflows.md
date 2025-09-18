# Core Workflows

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant ContextGen
    participant LightRAG[LightRAG API]
    participant OpenAI_EXT[OpenAI (Extraction)]
    participant OpenAI_CREAT[OpenAI (Creative)]
    participant FileSystem

    User->>CLI: jestir context "purple dragon story"
    CLI->>ContextGen: check for existing context.yaml
    alt Context exists
        CLI->>ContextGen: update_context(input, existing_context)
    else No context
        CLI->>ContextGen: generate_context(input)
    end
    ContextGen->>LightRAG: POST /query (search existing entities)
    LightRAG-->>ContextGen: return matches
    ContextGen->>ContextGen: validate entity matches (confidence scoring)
    alt High confidence match
        ContextGen->>ContextGen: use entity data
    else Low confidence match
        ContextGen->>ContextGen: skip or warn user
    end
    ContextGen->>OpenAI_EXT: parse natural language to extract entities and relationships
    OpenAI_EXT-->>ContextGen: parsed content
    ContextGen->>FileSystem: write/update context.yaml
    FileSystem-->>User: context.yaml created/updated

    User->>CLI: jestir outline context.yaml
    CLI->>FileSystem: read context.yaml
    CLI->>OpenAI_CREAT: generate outline
    OpenAI_CREAT-->>CLI: outline content
    CLI->>FileSystem: write outline.md
    FileSystem-->>User: outline.md created

    User->>User: Edit outline.md

    User->>CLI: jestir write outline.md
    CLI->>FileSystem: read outline.md, context.yaml
    CLI->>OpenAI_CREAT: generate story
    OpenAI_CREAT-->>CLI: story content
    CLI->>FileSystem: write story.md
    FileSystem-->>User: story.md created

    Note over User,FileSystem: Context preserves all user prompts<br/>for iterative story building
```
