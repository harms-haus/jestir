"""Relationship model for entity interactions."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Relationship(BaseModel):
    """Captures interactions and connections between entities."""

    type: str = Field(..., description="Relationship type (finds|visits|creates|owns)")
    subject: str | list[str] = Field(
        ...,
        description="Entity ID(s) performing action",
    )
    object: str | list[str] = Field(
        ...,
        description="Entity ID(s) receiving action",
    )
    location: str | None = Field(
        default=None,
        description="Optional location context",
    )
    mentioned_at: list[str] = Field(
        default_factory=list,
        description="User input references",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional relationship data",
    )

    model_config = ConfigDict(
        json_encoders={
            # Add any custom encoders if needed
        },
    )
