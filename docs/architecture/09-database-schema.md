# Database Schema

Since we're using the LightRAG API for read-only entity retrieval, we define the logical schema that the LightRAG API should return for entity queries:

```python
# LightRAG API Entity Retrieval Structure
{
    "entity_type": "character",
    "name": "Lily",
    "description": "Curious 5-year-old girl with braided hair",
    "properties": {
        "subtype": "protagonist",
        "relationships": ["friend_of:char_rascal"]
    },
    "embedding": [...],  # Vector for similarity search
}

# File-based Context (context.yaml)
# See Data Models section for structure
```
