"""Entity model for story characters, locations, and items."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, Optional, Callable


class Entity(BaseModel):
    """Represents all entities (characters, locations, items) in the story world."""

    id: str = Field(..., description="Unique identifier (e.g., 'char_001')")
    type: str = Field(..., description="Entity type (character|location|item)")
    subtype: str = Field(
        ..., description="Specific subtype (protagonist|interior|magical)"
    )
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Full text description")
    existing: bool = Field(
        default=False,
        description="Whether entity was found in LightRAG (true) or is new to this story (false)",
    )
    rag_id: Optional[str] = Field(
        default=None, description="LightRAG reference if existing"
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Type-specific attributes"
    )

    model_config = ConfigDict(
        json_encoders={
            # Add any custom encoders if needed
        }
    )
