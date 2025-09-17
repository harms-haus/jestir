# External APIs

## LightRAG API (Knowledge Graph & RAG Hybrid)

- **Purpose:** Knowledge graph and RAG hybrid system for entity retrieval and natural language querying
- **Documentation:** OpenAPI specification available in `docs/LightRAG-openapi.json`
- **Base URL:** Configurable via `LIGHTRAG_BASE_URL` environment variable
- **Authentication:** API key via `LIGHTRAG_API_KEY` environment variable (optional)
- **Architecture:** Hybrid system combining knowledge graphs with retrieval-augmented generation (RAG)
- **Query Interface:** Natural language queries that return structured information
- **Response Format:** Natural language by default, with optional structured formats (JSON, etc.)
- **Entity System:** Entities do not have traditional "ID"s - they are identified by natural language names and relationships

**Key Capabilities:**

- Natural language query processing
- Knowledge graph traversal and entity relationship discovery
- Hybrid retrieval combining vector search with graph-based reasoning
- Support for multiple query modes (local, global, hybrid, naive, mix, bypass)
- Entity existence checking and relationship management

**Key Endpoints Used:**

- `POST /query` - Process natural language queries and return information in natural language
- `GET /graph/label/list` - Retrieve all available graph labels/entity types
- `GET /graphs` - Get knowledge graph subgraphs for specific entities
- `GET /graph/entity/exists` - Check if an entity exists in the knowledge graph

**Query Modes:**

- **local**: Focus on specific entities and their immediate relationships
- **global**: Emphasize broader graph structure and long-range relationships
- **hybrid**: Balance between local and global perspectives
- **naive**: Simple vector-based retrieval without graph reasoning
- **mix**: Intelligent combination of multiple approaches
- **bypass**: Direct LLM processing without retrieval

**Integration Notes:**

- Queries are processed in natural language and return natural language responses by default
- Can request structured data formats (JSON) via response_type parameter
- Supports conversation history for context-aware responses
- Token management for controlling response length and context size

## LightRAG API Endpoint Details

### POST /query

**Purpose:** Process natural language queries and return information about entities and relationships

**Request Body:**

```json
{
  "query": "What is the relationship between character X and location Y?",
  "mode": "hybrid",
  "response_type": "Multiple Paragraphs",
  "top_k": 10,
  "chunk_top_k": 5,
  "conversation_history": [
    {"role": "user", "content": "Previous question"},
    {"role": "assistant", "content": "Previous response"}
  ]
}
```

**Response:**

```json
{
  "response": "Character X has a strong connection to location Y through their backstory..."
}
```

**Key Parameters:**

- `query` (required): Natural language query string
- `mode`: Query mode (local, global, hybrid, naive, mix, bypass)
- `response_type`: Format for response (Multiple Paragraphs, Single Paragraph, Bullet Points, JSON, etc.)
- `top_k`: Number of top entities/relationships to retrieve
- `chunk_top_k`: Number of text chunks to retrieve and rerank
- `conversation_history`: Previous conversation context

### GET /graph/label/list

**Purpose:** Retrieve all available graph labels/entity types in the knowledge graph

**Response:**

```json
["character", "location", "item", "event", "organization"]
```

**Usage:** Used to understand what types of entities are available in the knowledge graph for querying.

### GET /graphs

**Purpose:** Get knowledge graph subgraphs for specific entities

**Query Parameters:**

- `label` (required): Label/type of the starting node
- `max_depth` (optional): Maximum depth of the subgraph (default: 3)
- `max_nodes` (optional): Maximum nodes to return (default: 1000)

**Example Request:**

```http
GET /graphs?label=character&max_depth=2&max_nodes=50
```

**Response:**

```json
{
  "character_1": ["location_A", "character_2", "item_X"],
  "character_2": ["character_1", "event_Y"],
  "location_A": ["character_1"]
}
```

**Usage:** Used to explore entity relationships and build context for story generation.

### GET /graph/entity/exists

**Purpose:** Check if an entity with a given name exists in the knowledge graph

**Query Parameters:**

- `name` (required): Name of the entity to check

**Example Request:**

```http
GET /graph/entity/exists?name=Gandalf
```

**Response:**

```json
{
  "exists": true
}
```

**Usage:** Used to verify entity existence before querying or to check if entities mentioned in user input are present in the knowledge base.

## OpenAI API (Information Extraction)

- **Purpose:** Extract entities and relationships from natural language input
- **Documentation:** <https://platform.openai.com/docs>
- **Base URL(s):** <https://api.openai.com/v1> (configurable via `OPENAI_EXTRACTION_BASE_URL` environment variable)
- **Authentication:** API key via `OPENAI_EXTRACTION_API_KEY` environment variable
- **Model:** Configurable via `OPENAI_EXTRACTION_MODEL` environment variable (default: gpt-4o-mini)
- **Max Tokens:** Configurable via `OPENAI_EXTRACTION_MAX_TOKENS` environment variable
- **Temperature:** Configurable via `OPENAI_EXTRACTION_TEMPERATURE` environment variable (default: 0.1)
- **Rate Limits:** 90,000 TPM for GPT-4, monitoring via TokenTracker
- **Recommended Models:** GPT-4o-mini, GPT-4o, gpt-oss:20b (for accuracy in structured data extraction)

**Key Endpoints Used:**

- `POST /chat/completions` - Entity and relationship extraction

## OpenAI API (Creative Generation)

- **Purpose:** Generate story outlines and creative content
- **Documentation:** <https://platform.openai.com/docs>
- **Base URL(s):** <https://api.openai.com/v1> (configurable via `OPENAI_CREATIVE_BASE_URL` environment variable)
- **Authentication:** API key via `OPENAI_CREATIVE_API_KEY` environment variable
- **Model:** Configurable via `OPENAI_CREATIVE_MODEL` environment variable (default: gpt-4o)
- **Max Tokens:** Configurable via `OPENAI_CREATIVE_MAX_TOKENS` environment variable
- **Temperature:** Configurable via `OPENAI_CREATIVE_TEMPERATURE` environment variable (default: 0.7)
- **Rate Limits:** 90,000 TPM for GPT-4, monitoring via TokenTracker
- **Recommended Models:** GPT-4o, GPT-4, gpt-oss:120b (for creative quality and narrative coherence)

**Key Endpoints Used:**

- `POST /chat/completions` - Outline and story generation

**Integration Notes:** Retry logic with exponential backoff, timeout handling, streaming responses for long content

## Environment Variables Summary

**Note:** All environment variables are automatically loaded from a `.env` file if present in the project directory. This is handled by python-dotenv at application startup.

### LightRAG API Endpoint

- `LIGHTRAG_API_KEY` - API key for LightRAG authentication (optional)
- `LIGHTRAG_BASE_URL` - Base URL for LightRAG API (e.g., <http://localhost:8000>)

### Information Extraction Endpoint

- `OPENAI_EXTRACTION_API_KEY` - API key for extraction endpoint
- `OPENAI_EXTRACTION_BASE_URL` - Base URL for extraction API (default: <https://api.openai.com/v1>)
- `OPENAI_EXTRACTION_MODEL` - Model for extraction (default: gpt-4o-mini)
- `OPENAI_EXTRACTION_MAX_TOKENS` - Maximum tokens for extraction requests
- `OPENAI_EXTRACTION_TEMPERATURE` - Temperature for extraction (default: 0.1)

### Creative Generation Endpoint

- `OPENAI_CREATIVE_API_KEY` - API key for creative endpoint
- `OPENAI_CREATIVE_BASE_URL` - Base URL for creative API (default: <https://api.openai.com/v1>)
- `OPENAI_CREATIVE_MODEL` - Model for creative generation (default: gpt-4o)
- `OPENAI_CREATIVE_MAX_TOKENS` - Maximum tokens for creative requests
- `OPENAI_CREATIVE_TEMPERATURE` - Temperature for creative generation (default: 0.7)

### Example Configuration

```bash
# LightRAG API configuration
export LIGHTRAG_BASE_URL="http://localhost:8000"
export LIGHTRAG_API_KEY="your-api-key-here"  # Optional

# Use different models for different tasks
export OPENAI_EXTRACTION_MODEL="gpt-oss:20b"
export OPENAI_CREATIVE_MODEL="gpt-oss:120b"

# Use different endpoints if needed
export OPENAI_EXTRACTION_BASE_URL="https://your-extraction-endpoint.com/v1"
export OPENAI_CREATIVE_BASE_URL="https://your-creative-endpoint.com/v1"

# Fine-tune parameters
export OPENAI_EXTRACTION_TEMPERATURE="0.1"  # Lower for consistent extraction
export OPENAI_CREATIVE_TEMPERATURE="0.8"    # Higher for more creativity
```
