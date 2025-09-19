"""Tests for entity validation service."""

import pytest
from jestir.services.entity_validator import EntityValidator, EntityMatchResult
from jestir.services.lightrag_client import LightRAGEntity


class TestEntityValidator:
    """Test cases for EntityValidator class."""

    def test_initialization(self):
        """Test validator initialization with custom thresholds."""
        validator = EntityValidator(
            exact_match_threshold=0.9,
            high_confidence_threshold=0.7,
            low_confidence_threshold=0.4,
        )

        assert validator.exact_match_threshold == 0.9
        assert validator.high_confidence_threshold == 0.7
        assert validator.low_confidence_threshold == 0.4

    def test_exact_match_validation(self):
        """Test validation of exact matches."""
        validator = EntityValidator()

        entity = LightRAGEntity(
            name="Wendy Whisk",
            entity_type="character",
            description="A friendly cat",
        )

        result = validator.validate_entity_match("Wendy Whisk", entity, "character")

        assert result.is_exact_match is True
        assert result.similarity_score == 1.0
        assert result.confidence >= 0.95
        assert result.is_high_confidence is True

    def test_high_confidence_match(self):
        """Test validation of high confidence matches."""
        validator = EntityValidator()

        entity = LightRAGEntity(
            name="Wendy Whisk",
            entity_type="character",
            description="A friendly cat with whiskers",
        )

        result = validator.validate_entity_match("Wendy", entity, "character")

        assert result.is_exact_match is False
        assert result.similarity_score > 0.5
        assert result.confidence >= 0.8
        assert result.is_high_confidence is True

    def test_low_confidence_match(self):
        """Test validation of low confidence matches."""
        validator = EntityValidator()

        entity = LightRAGEntity(
            name="Wendy Whisk",
            entity_type="character",
            description="A friendly cat",
        )

        result = validator.validate_entity_match("whiskers", entity, "character")

        assert result.is_exact_match is False
        assert result.similarity_score < 0.8
        assert result.confidence < 0.8
        assert result.is_high_confidence is False

    def test_type_mismatch_penalty(self):
        """Test that type mismatches reduce confidence."""
        validator = EntityValidator()

        entity = LightRAGEntity(
            name="Wendy Whisk",
            entity_type="location",
            description="A place",
        )

        result = validator.validate_entity_match("Wendy Whisk", entity, "character")

        assert result.confidence < 1.0  # Should be penalized for type mismatch

    def test_type_match_bonus(self):
        """Test that type matches increase confidence."""
        validator = EntityValidator()

        entity = LightRAGEntity(
            name="Wendy Whisk",
            entity_type="character",
            description="A friendly cat",
        )

        result = validator.validate_entity_match("Wendy", entity, "character")

        # Should get bonus for type match
        assert result.confidence > result.similarity_score

    def test_description_quality_bonus(self):
        """Test that good descriptions increase confidence."""
        validator = EntityValidator()

        entity_with_desc = LightRAGEntity(
            name="Wendy Whisk",
            entity_type="character",
            description="A friendly cat with long whiskers and bright eyes",
        )

        entity_without_desc = LightRAGEntity(
            name="Wendy Whisk",
            entity_type="character",
            description=None,
        )

        result_with = validator.validate_entity_match("Wendy", entity_with_desc, "character")
        result_without = validator.validate_entity_match("Wendy", entity_without_desc, "character")

        assert result_with.confidence > result_without.confidence

    def test_properties_bonus(self):
        """Test that properties increase confidence."""
        validator = EntityValidator()

        entity_with_props = LightRAGEntity(
            name="Wendy Whisk",
            entity_type="character",
            description="A friendly cat",
            properties={"age": "3 years", "color": "orange"},
        )

        entity_without_props = LightRAGEntity(
            name="Wendy Whisk",
            entity_type="character",
            description="A friendly cat",
            properties=None,
        )

        result_with = validator.validate_entity_match("Wendy", entity_with_props, "character")
        result_without = validator.validate_entity_match("Wendy", entity_without_props, "character")

        assert result_with.confidence > result_without.confidence

    def test_similarity_calculation(self):
        """Test similarity score calculation."""
        validator = EntityValidator()

        # Test exact match
        similarity = validator._calculate_similarity("Wendy", "Wendy")
        assert similarity == 1.0

        # Test case insensitive match
        similarity = validator._calculate_similarity("wendy", "Wendy")
        assert similarity == 1.0

        # Test substring match
        similarity = validator._calculate_similarity("Wendy", "Wendy Whisk")
        assert similarity >= 0.7

        # Test no match
        similarity = validator._calculate_similarity("Alice", "Wendy")
        assert similarity < 0.5

    def test_filter_high_confidence_matches(self):
        """Test filtering high confidence matches."""
        validator = EntityValidator()

        high_conf = EntityMatchResult(
            entity=LightRAGEntity(name="High", entity_type="character"),
            confidence=0.9,
            similarity_score=0.9,
            is_exact_match=True,
            is_high_confidence=True,
            match_reason="High confidence",
        )

        low_conf = EntityMatchResult(
            entity=LightRAGEntity(name="Low", entity_type="character"),
            confidence=0.3,
            similarity_score=0.3,
            is_exact_match=False,
            is_high_confidence=False,
            match_reason="Low confidence",
        )

        matches = [high_conf, low_conf]
        filtered = validator.filter_high_confidence_matches(matches)

        assert len(filtered) == 1
        assert filtered[0].entity.name == "High"

    def test_get_best_match(self):
        """Test getting the best match from a list."""
        validator = EntityValidator()

        match1 = EntityMatchResult(
            entity=LightRAGEntity(name="Match1", entity_type="character"),
            confidence=0.6,
            similarity_score=0.6,
            is_exact_match=False,
            is_high_confidence=False,
            match_reason="Match 1",
        )

        match2 = EntityMatchResult(
            entity=LightRAGEntity(name="Match2", entity_type="character"),
            confidence=0.8,
            similarity_score=0.8,
            is_exact_match=False,
            is_high_confidence=True,
            match_reason="Match 2",
        )

        matches = [match1, match2]
        best = validator.get_best_match(matches)

        assert best.entity.name == "Match2"

    def test_should_require_confirmation(self):
        """Test confirmation requirement logic."""
        validator = EntityValidator()

        exact_match = EntityMatchResult(
            entity=LightRAGEntity(name="Exact", entity_type="character"),
            confidence=1.0,
            similarity_score=1.0,
            is_exact_match=True,
            is_high_confidence=True,
            match_reason="Exact match",
        )

        high_conf = EntityMatchResult(
            entity=LightRAGEntity(name="High", entity_type="character"),
            confidence=0.9,
            similarity_score=0.9,
            is_exact_match=False,
            is_high_confidence=True,
            match_reason="High confidence",
        )

        low_conf = EntityMatchResult(
            entity=LightRAGEntity(name="Low", entity_type="character"),
            confidence=0.3,
            similarity_score=0.3,
            is_exact_match=False,
            is_high_confidence=False,
            match_reason="Low confidence",
        )

        assert not validator.should_require_confirmation(exact_match)
        assert not validator.should_require_confirmation(high_conf)
        assert validator.should_require_confirmation(low_conf)

    def test_match_reason_generation(self):
        """Test match reason generation."""
        validator = EntityValidator()

        entity = LightRAGEntity(
            name="Wendy Whisk",
            entity_type="character",
            description="A friendly cat",
        )

        # Test exact match reason
        result = validator.validate_entity_match("Wendy Whisk", entity, "character")
        assert "Exact match" in result.match_reason

        # Test high confidence reason
        result = validator.validate_entity_match("Wendy", entity, "character")
        assert "High confidence" in result.match_reason or "Moderate confidence" in result.match_reason
