"""Story context model for complete story generation state."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from .entity import Entity
from .relationship import Relationship


class StoryContext(BaseModel):
    """Complete context for story generation including all settings and history."""

    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "token_usage": {},
        },
        description="Version, timestamps, token usage",
    )
    settings: Dict[str, Any] = Field(
        default_factory=lambda: {
            "genre": "adventure",
            "tone": "gentle",
            "length": "short",
            "morals": [],
            "age_appropriate": True,
        },
        description="Genre, tone, length, morals",
    )
    entities: Dict[str, Entity] = Field(
        default_factory=dict, description="All entities keyed by ID"
    )
    relationships: List[Relationship] = Field(
        default_factory=list, description="All entity relationships"
    )
    user_inputs: Dict[str, str] = Field(
        default_factory=dict, description="Original user requests"
    )
    plot_points: List[str] = Field(
        default_factory=list, description="Key narrative points"
    )
    outline: Optional[str] = Field(
        default=None, description="Generated outline content"
    )
    story: Optional[str] = Field(default=None, description="Generated story content")

    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the context."""
        self.entities[entity.id] = entity
        self._update_timestamp()

    def add_relationship(self, relationship: Relationship) -> None:
        """Add a relationship to the context."""
        self.relationships.append(relationship)
        self._update_timestamp()

    def add_user_input(self, input_id: str, input_text: str) -> None:
        """Add a user input to the context."""
        self.user_inputs[input_id] = input_text
        self._update_timestamp()

    def add_plot_point(self, plot_point: str) -> None:
        """Add a plot point to the context."""
        self.plot_points.append(plot_point)
        self._update_timestamp()

    def _update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.metadata["updated_at"] = datetime.now().isoformat()

    model_config = ConfigDict(
        json_encoders={
            # Add any custom encoders if needed
        }
    )
