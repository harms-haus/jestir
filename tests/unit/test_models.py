"""Unit tests for data models."""

import pytest
from datetime import datetime
from jestir.models.entity import Entity
from jestir.models.relationship import Relationship
from jestir.models.story_context import StoryContext
from jestir.models.api_config import ExtractionAPIConfig, CreativeAPIConfig


class TestEntity:
    """Test cases for Entity model."""

    def test_entity_creation(self):
        """Test basic entity creation."""
        entity = Entity(
            id="char_001",
            type="character",
            subtype="protagonist",
            name="Arthur",
            description="A brave knight",
            existing=False,
        )

        assert entity.id == "char_001"
        assert entity.type == "character"
        assert entity.subtype == "protagonist"
        assert entity.name == "Arthur"
        assert entity.description == "A brave knight"
        assert entity.existing is False
        assert entity.rag_id is None
        assert entity.properties == {}

    def test_entity_with_optional_fields(self):
        """Test entity creation with optional fields."""
        entity = Entity(
            id="char_002",
            type="location",
            subtype="magical",
            name="Enchanted Forest",
            description="A magical forest",
            existing=True,
            rag_id="rag_123",
            properties={"magic_level": 5},
        )

        assert entity.existing is True
        assert entity.rag_id == "rag_123"
        assert entity.properties["magic_level"] == 5


class TestRelationship:
    """Test cases for Relationship model."""

    def test_relationship_creation(self):
        """Test basic relationship creation."""
        relationship = Relationship(type="visits", subject="char_001", object="loc_001")

        assert relationship.type == "visits"
        assert relationship.subject == "char_001"
        assert relationship.object == "loc_001"
        assert relationship.location is None
        assert relationship.mentioned_at == []
        assert relationship.metadata == {}

    def test_relationship_with_optional_fields(self):
        """Test relationship creation with optional fields."""
        relationship = Relationship(
            type="finds",
            subject="char_001",
            object="item_001",
            location="loc_001",
            mentioned_at=["Arthur finds the sword"],
            metadata={"importance": "high"},
        )

        assert relationship.location == "loc_001"
        assert "Arthur finds the sword" in relationship.mentioned_at
        assert relationship.metadata["importance"] == "high"

    def test_relationship_with_list_subject_object(self):
        """Test relationship with list subject and object."""
        relationship = Relationship(
            type="meets", subject=["char_001", "char_002"], object=["char_003"]
        )

        assert relationship.subject == ["char_001", "char_002"]
        assert relationship.object == ["char_003"]


class TestStoryContext:
    """Test cases for StoryContext model."""

    def test_story_context_creation(self):
        """Test basic story context creation."""
        context = StoryContext()

        assert "version" in context.metadata
        assert "created_at" in context.metadata
        assert "updated_at" in context.metadata
        assert context.settings["genre"] == "fantasy"
        assert context.entities == {}
        assert context.relationships == []
        assert context.user_inputs == {}
        assert context.plot_points == []
        assert context.outline is None
        assert context.story is None

    def test_add_entity(self):
        """Test adding entity to context."""
        context = StoryContext()
        entity = Entity(
            id="char_001",
            type="character",
            subtype="protagonist",
            name="Arthur",
            description="A brave knight",
            existing=False,
        )

        context.add_entity(entity)

        assert "char_001" in context.entities
        assert context.entities["char_001"] == entity
        assert context.metadata["updated_at"] != context.metadata["created_at"]

    def test_add_relationship(self):
        """Test adding relationship to context."""
        context = StoryContext()
        relationship = Relationship(type="visits", subject="char_001", object="loc_001")

        context.add_relationship(relationship)

        assert len(context.relationships) == 1
        assert context.relationships[0] == relationship

    def test_add_user_input(self):
        """Test adding user input to context."""
        context = StoryContext()

        context.add_user_input("request_1", "Arthur visits the forest")

        assert context.user_inputs["request_1"] == "Arthur visits the forest"

    def test_add_plot_point(self):
        """Test adding plot point to context."""
        context = StoryContext()

        context.add_plot_point("Arthur finds the sword")

        assert "Arthur finds the sword" in context.plot_points


class TestAPIConfig:
    """Test cases for API configuration models."""

    def test_extraction_api_config_defaults(self):
        """Test ExtractionAPIConfig with defaults."""
        config = ExtractionAPIConfig(api_key="test-key")

        assert config.api_key == "test-key"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.model == "gpt-4o-mini"
        assert config.max_tokens == 1000
        assert config.temperature == 0.1

    def test_creative_api_config_defaults(self):
        """Test CreativeAPIConfig with defaults."""
        config = CreativeAPIConfig(api_key="test-key")

        assert config.api_key == "test-key"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.model == "gpt-4o"
        assert config.max_tokens == 4000
        assert config.temperature == 0.8

    def test_api_config_custom_values(self):
        """Test API config with custom values."""
        config = ExtractionAPIConfig(
            api_key="custom-key",
            base_url="https://custom.api.com",
            model="gpt-4",
            max_tokens=2000,
            temperature=0.5,
        )

        assert config.api_key == "custom-key"
        assert config.base_url == "https://custom.api.com"
        assert config.model == "gpt-4"
        assert config.max_tokens == 2000
        assert config.temperature == 0.5
