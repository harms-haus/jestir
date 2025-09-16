"""Relationship model for entity interactions."""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Union, Optional, Callable


class Relationship(BaseModel):
    """Captures interactions and connections between entities."""

    type: str = Field(..., description="Relationship type (finds|visits|creates|owns)")
    subject: Union[str, List[str]] = Field(
        ..., description="Entity ID(s) performing action"
    )
    object: Union[str, List[str]] = Field(
        ..., description="Entity ID(s) receiving action"
    )
    location: Optional[str] = Field(
        default=None, description="Optional location context"
    )
    mentioned_at: List[str] = Field(
        default_factory=list, description="User input references"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional relationship data"
    )

    model_config = ConfigDict(
        json_encoders={
            # Add any custom encoders if needed
        }
    )
