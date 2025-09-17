"""Tests for context validation service."""

import os
import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest
import yaml

from jestir.models.entity import Entity
from jestir.models.relationship import Relationship
from jestir.models.story_context import StoryContext
from jestir.services.context_validator import ContextValidator


class TestContextValidator:
    """Test cases for ContextValidator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ContextValidator()

        # Create a valid context for testing
        self.valid_context = StoryContext(
            metadata={
                "version": "1.0.0",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "token_usage": {},
            },
            settings={
                "genre": "adventure",
                "tone": "gentle",
                "length": "short",
                "age_appropriate": True,
                "morals": [],
            },
            entities={
                "char_001": Entity(
                    id="char_001",
                    name="Lily",
                    type="character",
                    subtype="protagonist",
                    description="A brave girl",
                    existing=True,
                    rag_id="rag_char_001",
                    properties={"age": 8},
                ),
                "loc_001": Entity(
                    id="loc_001",
                    name="Magic Forest",
                    type="location",
                    subtype="exterior",
                    description="A magical forest",
                    existing=True,
                    rag_id="rag_loc_001",
                    properties={"type": "magical"},
                ),
            },
            relationships=[
                Relationship(
                    type="visits",
                    subject="char_001",
                    object="loc_001",
                    location="Magic Forest",
                    mentioned_at=["initial_request"],
                ),
            ],
            user_inputs={"initial_request": "Lily goes to the magic forest"},
            plot_points=["Lily discovers the magic forest"],
        )

    def test_validate_valid_context(self):
        """Test validation of a valid context file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(self.valid_context.model_dump(), f)
            temp_file = f.name

        try:
            result = self.validator.validate_context_file(temp_file)
            assert result.is_valid
            assert len(result.errors) == 0
        finally:
            os.unlink(temp_file)

    def test_validate_missing_file(self):
        """Test validation of a non-existent file."""
        result = self.validator.validate_context_file("nonexistent.yaml")
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "Failed to validate context file" in result.errors[0]

    def test_validate_invalid_yaml(self):
        """Test validation of invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_file = f.name

        try:
            result = self.validator.validate_context_file(temp_file)
            assert not result.is_valid
            assert len(result.errors) > 0
        finally:
            os.unlink(temp_file)

    def test_validate_structure_missing_fields(self):
        """Test validation with missing required fields."""
        # Create context with missing fields
        invalid_context = StoryContext(
            metadata={},
            settings={},
            entities={},
            relationships=[],
            user_inputs={},
            plot_points=[],
        )

        errors, warnings = self.validator._validate_structure(invalid_context)
        assert len(errors) == 0  # All required fields are present in StoryContext
        assert len(warnings) == 0

    def test_validate_settings_missing_required(self):
        """Test validation with missing required settings."""
        context = StoryContext(
            metadata={"version": "1.0.0"},
            settings={},  # Empty settings
            entities={},
            relationships=[],
            user_inputs={},
            plot_points=[],
        )

        errors, warnings = self.validator._validate_settings(context)
        assert len(errors) > 0
        assert any("Settings section is missing or empty" in error for error in errors)

    def test_validate_settings_invalid_values(self):
        """Test validation with invalid setting values."""
        context = StoryContext(
            metadata={"version": "1.0.0"},
            settings={
                "genre": "adventure",
                "tone": "gentle",
                "length": "short",
                "age_appropriate": "not_a_boolean",  # Invalid type
            },
            entities={},
            relationships=[],
            user_inputs={},
            plot_points=[],
        )

        errors, warnings = self.validator._validate_settings(context)
        assert len(errors) > 0
        assert any("age_appropriate must be a boolean" in error for error in errors)

    def test_validate_entities_missing_fields(self):
        """Test validation with entities missing required fields."""
        context = StoryContext(
            metadata={"version": "1.0.0"},
            settings={
                "genre": "adventure",
                "tone": "gentle",
                "length": "short",
                "age_appropriate": True,
            },
            entities={
                "char_001": Entity(
                    id="",  # Missing ID
                    name="Lily",
                    type="character",
                    subtype="protagonist",
                    description="A brave girl",
                ),
            },
            relationships=[],
            user_inputs={},
            plot_points=[],
        )

        errors, warnings = self.validator._validate_entities(context)
        assert len(errors) > 0
        assert any("missing ID" in error for error in errors)

    def test_validate_entities_invalid_type(self):
        """Test validation with invalid entity types."""
        context = StoryContext(
            metadata={"version": "1.0.0"},
            settings={
                "genre": "adventure",
                "tone": "gentle",
                "length": "short",
                "age_appropriate": True,
            },
            entities={
                "char_001": Entity(
                    id="char_001",
                    name="Lily",
                    type="invalid_type",  # Invalid type
                    subtype="protagonist",
                    description="A brave girl",
                ),
            },
            relationships=[],
            user_inputs={},
            plot_points=[],
        )

        errors, warnings = self.validator._validate_entities(context)
        assert len(errors) > 0
        assert any("invalid type" in error for error in errors)

    def test_validate_relationships_invalid_references(self):
        """Test validation with relationships referencing non-existent entities."""
        context = StoryContext(
            metadata={"version": "1.0.0"},
            settings={
                "genre": "adventure",
                "tone": "gentle",
                "length": "short",
                "age_appropriate": True,
            },
            entities={
                "char_001": Entity(
                    id="char_001",
                    name="Lily",
                    type="character",
                    subtype="protagonist",
                    description="A brave girl",
                ),
            },
            relationships=[
                Relationship(
                    type="visits",
                    subject="char_001",
                    object="nonexistent_entity",  # Non-existent entity
                    location="somewhere",
                ),
            ],
            user_inputs={},
            plot_points=[],
        )

        errors, warnings = self.validator._validate_relationships(context)
        assert len(errors) > 0
        assert any("non-existent object entity" in error for error in errors)

    def test_check_unusual_patterns_no_protagonist(self):
        """Test detection of unusual patterns - no protagonist."""
        context = StoryContext(
            metadata={"version": "1.0.0"},
            settings={
                "genre": "adventure",
                "tone": "gentle",
                "length": "short",
                "age_appropriate": True,
            },
            entities={
                "char_001": Entity(
                    id="char_001",
                    name="Lily",
                    type="character",
                    subtype="supporting",  # Not protagonist
                    description="A brave girl",
                ),
            },
            relationships=[],
            user_inputs={},
            plot_points=[],
        )

        warnings = self.validator._check_unusual_patterns(context)
        assert len(warnings) > 0
        assert any("No protagonists found" in warning for warning in warnings)

    def test_check_unusual_patterns_no_locations(self):
        """Test detection of unusual patterns - no locations."""
        context = StoryContext(
            metadata={"version": "1.0.0"},
            settings={
                "genre": "adventure",
                "tone": "gentle",
                "length": "short",
                "age_appropriate": True,
            },
            entities={
                "char_001": Entity(
                    id="char_001",
                    name="Lily",
                    type="character",
                    subtype="protagonist",
                    description="A brave girl",
                ),
            },
            relationships=[],
            user_inputs={},
            plot_points=[],
        )

        warnings = self.validator._check_unusual_patterns(context)
        assert len(warnings) > 0
        assert any("No locations found" in warning for warning in warnings)

    def test_check_unusual_patterns_too_many_characters(self):
        """Test detection of unusual patterns - too many characters."""
        context = StoryContext(
            metadata={"version": "1.0.0"},
            settings={
                "genre": "adventure",
                "tone": "gentle",
                "length": "short",
                "age_appropriate": True,
            },
            entities={
                f"char_{i:03d}": Entity(
                    id=f"char_{i:03d}",
                    name=f"Character {i}",
                    type="character",
                    subtype="supporting",
                    description=f"Character {i}",
                )
                for i in range(15)  # More than 10 characters
            },
            relationships=[],
            user_inputs={},
            plot_points=[],
        )

        warnings = self.validator._check_unusual_patterns(context)
        assert len(warnings) > 0
        assert any("Many characters found" in warning for warning in warnings)

    @pytest.mark.asyncio
    async def test_validate_lightrag_references_mock_mode(self):
        """Test LightRAG validation in mock mode."""
        # Mock the LightRAG client
        mock_client = Mock()
        mock_client.get_entity_details = AsyncMock(return_value=None)

        with patch.object(self.validator, "lightrag_client", mock_client):
            errors, warnings = await self.validator._validate_lightrag_references(
                self.valid_context,
            )
            assert len(errors) == 0
            assert len(warnings) > 0  # Should warn about entities not found in LightRAG

    @pytest.mark.asyncio
    async def test_validate_lightrag_references_entity_found(self):
        """Test LightRAG validation when entity is found."""

        # Mock the LightRAG client to return appropriate entities
        def mock_get_entity_details(entity_name):
            if entity_name == "Lily":
                mock_entity = Mock()
                mock_entity.entity_type = "character"
                mock_entity.name = "Lily"
                return mock_entity
            if entity_name == "Magic Forest":
                mock_entity = Mock()
                mock_entity.entity_type = "location"
                mock_entity.name = "Magic Forest"
                return mock_entity
            return None

        mock_client = Mock()
        mock_client.get_entity_details = AsyncMock(side_effect=mock_get_entity_details)

        with patch.object(self.validator, "lightrag_client", mock_client):
            errors, warnings = await self.validator._validate_lightrag_references(
                self.valid_context,
            )
            assert len(errors) == 0
            assert (
                len(warnings) == 0
            )  # No warnings when entity is found and type matches

    @pytest.mark.asyncio
    async def test_validate_lightrag_references_type_mismatch(self):
        """Test LightRAG validation with type mismatch."""
        # Mock the LightRAG client to return an entity with different type
        mock_entity = Mock()
        mock_entity.entity_type = "location"  # Different from context entity type
        mock_entity.name = "Lily"

        mock_client = Mock()
        mock_client.get_entity_details = AsyncMock(return_value=mock_entity)

        with patch.object(self.validator, "lightrag_client", mock_client):
            errors, warnings = await self.validator._validate_lightrag_references(
                self.valid_context,
            )
            assert len(errors) == 0
            assert len(warnings) > 0
            assert any("type mismatch" in warning for warning in warnings)

    def test_generate_suggestions(self):
        """Test generation of fix suggestions."""
        errors = [
            "Missing required setting: genre",
            "Entity char_001 has invalid type 'invalid_type'",
        ]
        warnings = [
            "No protagonists found in story",
            "Entity 'Lily' not found in LightRAG knowledge base",
        ]

        suggestions = self.validator._generate_suggestions(errors, warnings)
        assert len(suggestions) > 0
        assert any(
            "Add the missing setting" in suggestion for suggestion in suggestions
        )
        assert any(
            "Add a character with subtype 'protagonist'" in suggestion
            for suggestion in suggestions
        )

    def test_attempt_auto_fix(self):
        """Test auto-fix functionality."""
        errors = ["Missing required field: metadata", "Missing required setting: genre"]

        fixed_issues = self.validator._attempt_auto_fix(
            self.valid_context,
            errors,
            "test.yaml",
        )
        assert len(fixed_issues) > 0
        assert any("Could potentially auto-fix" in issue for issue in fixed_issues)

    def test_validate_context_file_with_auto_fix(self):
        """Test full validation with auto-fix enabled."""
        # Create a context with some issues
        context_with_issues = StoryContext(
            metadata={"version": "1.0.0"},
            settings={
                "genre": "adventure",
                "tone": "gentle",
                "length": "short",
                "age_appropriate": True,
            },
            entities={},  # No entities
            relationships=[],
            user_inputs={},
            plot_points=[],
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(context_with_issues.model_dump(), f)
            temp_file = f.name

        try:
            result = self.validator.validate_context_file(temp_file, auto_fix=True)
            # Should have warnings but no errors (since it's a valid structure)
            assert result.is_valid
            assert (
                len(result.warnings) > 0
            )  # Should warn about no entities, no protagonists, etc.
        finally:
            os.unlink(temp_file)
