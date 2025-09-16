# Database Schema

Since we're using LightRAG for read-only entity retrieval, we define the logical schema that LightRAG should adhere to on retrieval:

```python
# LightRAG Entity Retrieval Structure
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
