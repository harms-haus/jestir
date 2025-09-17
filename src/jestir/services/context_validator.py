"""Context validation service for checking context file structure and consistency."""

import yaml
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from ..models.story_context import StoryContext
from ..models.entity import Entity
from ..models.relationship import Relationship
from .lightrag_client import LightRAGClient
from ..models.api_config import LightRAGAPIConfig
import os


@dataclass
class ValidationResult:
    """Result of context validation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    fixed_issues: Optional[List[str]] = None


class ContextValidator:
    """Validates context files for structure, consistency, and entity references."""

    def __init__(self, lightrag_config: Optional[LightRAGAPIConfig] = None):
        """Initialize the context validator."""
        self.lightrag_config = lightrag_config or self._load_lightrag_config()
        self.lightrag_client = LightRAGClient(self.lightrag_config)

    def _load_lightrag_config(self) -> LightRAGAPIConfig:
        """Load LightRAG configuration from environment variables."""
        return LightRAGAPIConfig(
            base_url=os.getenv("LIGHTRAG_BASE_URL", "http://localhost:8000"),
            api_key=os.getenv("LIGHTRAG_API_KEY"),
            timeout=int(os.getenv("LIGHTRAG_TIMEOUT", "30")),
            mock_mode=os.getenv("LIGHTRAG_MOCK_MODE", "false").lower() == "true",
        )

    def validate_context_file(
        self, context_file: str, verbose: bool = False, auto_fix: bool = False
    ) -> ValidationResult:
        """
        Validate a context file for structure and consistency.

        Args:
            context_file: Path to the context file to validate
            verbose: Whether to show detailed validation results
            auto_fix: Whether to attempt automatic fixes

        Returns:
            ValidationResult with validation status and issues
        """
        errors: List[str] = []
        warnings: List[str] = []
        suggestions: List[str] = []
        fixed_issues: List[str] = []

        try:
            # Load context file
            context = self._load_context_file(context_file)

            # Validate basic structure
            structure_errors, structure_warnings = self._validate_structure(context)
            errors.extend(structure_errors)
            warnings.extend(structure_warnings)

            # Validate required settings
            settings_errors, settings_warnings = self._validate_settings(context)
            errors.extend(settings_errors)
            warnings.extend(settings_warnings)

            # Validate entities
            entity_errors, entity_warnings = self._validate_entities(context)
            errors.extend(entity_errors)
            warnings.extend(entity_warnings)

            # Validate relationships
            relationship_errors, relationship_warnings = self._validate_relationships(
                context
            )
            errors.extend(relationship_errors)
            warnings.extend(relationship_warnings)

            # Check for unusual patterns
            pattern_warnings = self._check_unusual_patterns(context)
            warnings.extend(pattern_warnings)

            # Validate entity references in LightRAG
            if not self.lightrag_config.mock_mode:
                lightrag_errors, lightrag_warnings = asyncio.run(
                    self._validate_lightrag_references(context)
                )
                errors.extend(lightrag_errors)
                warnings.extend(lightrag_warnings)
            else:
                warnings.append("LightRAG validation skipped (mock mode enabled)")

            # Generate suggestions
            suggestions = self._generate_suggestions(errors, warnings)

            # Attempt auto-fix if requested
            if auto_fix and errors:
                fixed_issues = self._attempt_auto_fix(context, errors, context_file)

            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions,
                fixed_issues=fixed_issues,
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Failed to validate context file: {str(e)}"],
                warnings=[],
                suggestions=[
                    "Check that the file is valid YAML and follows the expected structure"
                ],
            )

    def _load_context_file(self, context_file: str) -> StoryContext:
        """Load context file and parse as StoryContext."""
        with open(context_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Convert to StoryContext object
        return StoryContext(**data)

    def _validate_structure(self, context: StoryContext) -> tuple[List[str], List[str]]:
        """Validate basic structure of the context."""
        errors: List[str] = []
        warnings: List[str] = []

        # Check required top-level fields
        required_fields = [
            "metadata",
            "settings",
            "entities",
            "relationships",
            "user_inputs",
            "plot_points",
        ]
        for field in required_fields:
            if not hasattr(context, field):
                errors.append(f"Missing required field: {field}")

        # Check metadata structure
        if hasattr(context, "metadata") and context.metadata:
            if "version" not in context.metadata:
                warnings.append("Missing version in metadata")
            if "created_at" not in context.metadata:
                warnings.append("Missing created_at timestamp in metadata")

        return errors, warnings

    def _validate_settings(self, context: StoryContext) -> tuple[List[str], List[str]]:
        """Validate required settings are present."""
        errors: List[str] = []
        warnings: List[str] = []

        if not hasattr(context, "settings") or not context.settings:
            errors.append("Settings section is missing or empty")
            return errors, warnings

        # Required settings
        required_settings = ["genre", "tone", "length", "age_appropriate"]
        for setting in required_settings:
            if setting not in context.settings:
                errors.append(f"Missing required setting: {setting}")

        # Validate setting values
        if "age_appropriate" in context.settings:
            if not isinstance(context.settings["age_appropriate"], bool):
                errors.append("age_appropriate must be a boolean value")

        if "genre" in context.settings:
            valid_genres = [
                "adventure",
                "fantasy",
                "mystery",
                "comedy",
                "drama",
                "horror",
            ]
            if context.settings["genre"] not in valid_genres:
                warnings.append(
                    f"Genre '{context.settings['genre']}' is not in common genres: {', '.join(valid_genres)}"
                )

        if "tone" in context.settings:
            valid_tones = [
                "gentle",
                "exciting",
                "mysterious",
                "funny",
                "serious",
                "whimsical",
            ]
            if context.settings["tone"] not in valid_tones:
                warnings.append(
                    f"Tone '{context.settings['tone']}' is not in common tones: {', '.join(valid_tones)}"
                )

        if "length" in context.settings:
            valid_lengths = ["short", "medium", "long"]
            if context.settings["length"] not in valid_lengths:
                warnings.append(
                    f"Length '{context.settings['length']}' is not in valid lengths: {', '.join(valid_lengths)}"
                )

        return errors, warnings

    def _validate_entities(self, context: StoryContext) -> tuple[List[str], List[str]]:
        """Validate entities in the context."""
        errors: List[str] = []
        warnings: List[str] = []

        if not hasattr(context, "entities") or not context.entities:
            warnings.append("No entities found in context")
            return errors, warnings

        # Check entity structure
        for entity_id, entity in context.entities.items():
            if not isinstance(entity, Entity):
                errors.append(f"Entity {entity_id} is not a valid Entity object")
                continue

            # Check required entity fields
            if not entity.id:
                errors.append(f"Entity {entity_id} missing ID")
            if not entity.name:
                errors.append(f"Entity {entity_id} missing name")
            if not entity.type:
                errors.append(f"Entity {entity_id} missing type")

            # Check entity type validity
            valid_types = ["character", "location", "item"]
            if entity.type not in valid_types:
                errors.append(
                    f"Entity {entity_id} has invalid type '{entity.type}'. Must be one of: {', '.join(valid_types)}"
                )

            # Check character subtypes
            if entity.type == "character" and hasattr(entity, "subtype"):
                valid_subtypes = ["protagonist", "antagonist", "supporting", "animal"]
                if entity.subtype not in valid_subtypes:
                    warnings.append(
                        f"Character {entity_id} has unusual subtype '{entity.subtype}'. Common subtypes: {', '.join(valid_subtypes)}"
                    )

        return errors, warnings

    def _validate_relationships(
        self, context: StoryContext
    ) -> tuple[List[str], List[str]]:
        """Validate relationships between entities."""
        errors: List[str] = []
        warnings: List[str] = []

        if not hasattr(context, "relationships") or not context.relationships:
            return errors, warnings

        # Get all entity IDs
        entity_ids: Set[str] = (
            set(context.entities.keys()) if context.entities else set()
        )

        for i, relationship in enumerate(context.relationships):
            if not isinstance(relationship, Relationship):
                errors.append(f"Relationship {i} is not a valid Relationship object")
                continue

            # Check that referenced entities exist
            subject_ids = (
                relationship.subject
                if isinstance(relationship.subject, list)
                else [relationship.subject]
            )
            object_ids = (
                relationship.object
                if isinstance(relationship.object, list)
                else [relationship.object]
            )

            for subject_id in subject_ids:
                if subject_id not in entity_ids:
                    errors.append(
                        f"Relationship {i} references non-existent subject entity: {subject_id}"
                    )

            for object_id in object_ids:
                if object_id not in entity_ids:
                    errors.append(
                        f"Relationship {i} references non-existent object entity: {object_id}"
                    )

            # Check for self-referential relationships
            all_subject_ids = set(subject_ids)
            all_object_ids = set(object_ids)
            if all_subject_ids & all_object_ids:  # Check for intersection
                warnings.append(
                    f"Relationship {i} is self-referential (entity relates to itself)"
                )

            # Check relationship type validity
            valid_types = [
                "finds",
                "visits",
                "creates",
                "owns",
                "friend",
                "enemy",
                "family",
                "colleague",
                "location_of",
                "uses",
                "interacts_with",
            ]
            if relationship.type not in valid_types:
                warnings.append(
                    f"Relationship {i} has unusual type '{relationship.type}'. Common types: {', '.join(valid_types)}"
                )

        return errors, warnings

    def _check_unusual_patterns(self, context: StoryContext) -> List[str]:
        """Check for unusual patterns in the context."""
        warnings: List[str] = []

        if not hasattr(context, "entities") or not context.entities:
            return warnings

        # Check for protagonists
        protagonists: List[Entity] = [
            e
            for e in context.entities.values()
            if e.type == "character"
            and hasattr(e, "subtype")
            and e.subtype == "protagonist"
        ]
        if not protagonists:
            warnings.append(
                "No protagonists found in story - consider adding a main character"
            )

        # Check for antagonists
        antagonists: List[Entity] = [
            e
            for e in context.entities.values()
            if e.type == "character"
            and hasattr(e, "subtype")
            and e.subtype == "antagonist"
        ]
        if (
            not antagonists
            and len([e for e in context.entities.values() if e.type == "character"]) > 1
        ):
            warnings.append(
                "No antagonists found - consider adding a character with conflict"
            )

        # Check for locations
        locations: List[Entity] = [
            e for e in context.entities.values() if e.type == "location"
        ]
        if not locations:
            warnings.append("No locations found - consider adding story settings")

        # Check for too many characters
        characters: List[Entity] = [
            e for e in context.entities.values() if e.type == "character"
        ]
        if len(characters) > 10:
            warnings.append(
                f"Many characters found ({len(characters)}) - consider simplifying for clarity"
            )

        # Check for plot points
        if not hasattr(context, "plot_points") or not context.plot_points:
            warnings.append("No plot points found - consider adding key story events")

        return warnings

    async def _validate_lightrag_references(
        self, context: StoryContext
    ) -> tuple[List[str], List[str]]:
        """Validate that entity references exist in LightRAG."""
        errors: List[str] = []
        warnings: List[str] = []

        if not hasattr(context, "entities") or not context.entities:
            return errors, warnings

        # Check each entity against LightRAG
        for entity_id, entity in context.entities.items():
            try:
                # Check if entity exists in LightRAG
                lightrag_entity = await self.lightrag_client.get_entity_details(
                    entity.name
                )
                if not lightrag_entity:
                    warnings.append(
                        f"Entity '{entity.name}' not found in LightRAG knowledge base"
                    )
                else:
                    # Check for type consistency
                    if lightrag_entity.entity_type != entity.type:
                        warnings.append(
                            f"Entity '{entity.name}' type mismatch: context has '{entity.type}', LightRAG has '{lightrag_entity.entity_type}'"
                        )
            except Exception as e:
                warnings.append(
                    f"Could not validate entity '{entity.name}' against LightRAG: {str(e)}"
                )

        return errors, warnings

    def _generate_suggestions(
        self, errors: List[str], warnings: List[str]
    ) -> List[str]:
        """Generate fix suggestions based on errors and warnings."""
        suggestions: List[str] = []

        for error in errors:
            if "Missing required field" in error:
                suggestions.append("Add the missing field to your context file")
            elif "Missing required setting" in error:
                suggestions.append("Add the missing setting with an appropriate value")
            elif "invalid type" in error:
                suggestions.append(
                    "Use a valid entity type: character, location, or item"
                )
            elif "not a valid Entity object" in error:
                suggestions.append(
                    "Ensure all entities follow the proper Entity structure"
                )

        for warning in warnings:
            if "not found in LightRAG" in warning:
                suggestions.append(
                    "Consider adding the entity to LightRAG or using an existing entity"
                )
            elif "No protagonists found" in warning:
                suggestions.append("Add a character with subtype 'protagonist'")
            elif "No antagonists found" in warning:
                suggestions.append(
                    "Add a character with subtype 'antagonist' for conflict"
                )
            elif "No locations found" in warning:
                suggestions.append("Add location entities to set the story scene")

        return suggestions

    def _attempt_auto_fix(
        self, context: StoryContext, errors: List[str], context_file: str
    ) -> List[str]:
        """Attempt to automatically fix common issues."""
        fixed_issues: List[str] = []

        # This is a placeholder for auto-fix functionality
        # In a real implementation, this would attempt to fix issues like:
        # - Adding missing required fields with defaults
        # - Fixing type mismatches
        # - Adding missing settings

        # For now, we'll just return the list of issues that could potentially be fixed
        for error in errors:
            if "Missing required field" in error:
                fixed_issues.append(f"Could potentially auto-fix: {error}")

        return fixed_issues
