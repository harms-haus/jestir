# Database Schema

Since we're using LightRAG for read-only entity retrieval, we define the logical schema:

```python
# LightRAG Entity Retrieval Structure
{
    "entity_type": "character",
    "entity_id": "char_lily_main",
    "name": "Lily",
    "description": "Curious 5-year-old girl with braided hair",
    "properties": {
        "subtype": "protagonist",
        "created_date": "2024-01-01",
        "story_appearances": ["story_001", "story_002"],
        "relationships": ["friend_of:char_rascal"]
    },
    "embedding": [...],  # Vector for similarity search
}

# File-based Context (context.yaml)
# See Data Models section for structure
```
