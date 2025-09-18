"""Entity validation service for LightRAG query results."""

import logging
from dataclasses import dataclass
from difflib import SequenceMatcher

from .lightrag_client import LightRAGEntity

logger = logging.getLogger(__name__)


@dataclass
class EntityMatchResult:
    """Result of entity matching with confidence scoring."""

    entity: LightRAGEntity
    confidence: float
    similarity_score: float
    is_exact_match: bool
    is_high_confidence: bool
    match_reason: str


class EntityValidator:
    """Validates and scores entity matches from LightRAG queries."""

    def __init__(
        self,
        exact_match_threshold: float = 0.95,
        high_confidence_threshold: float = 0.8,
        low_confidence_threshold: float = 0.5,
    ):
        """
        Initialize entity validator with configurable thresholds.

        Args:
            exact_match_threshold: Threshold for considering an exact match (0.0-1.0)
            high_confidence_threshold: Threshold for high confidence matches (0.0-1.0)
            low_confidence_threshold: Threshold for low confidence matches (0.0-1.0)
        """
        self.exact_match_threshold = exact_match_threshold
        self.high_confidence_threshold = high_confidence_threshold
        self.low_confidence_threshold = low_confidence_threshold

    def validate_entity_match(
        self,
        search_query: str,
        lightrag_entity: LightRAGEntity,
        entity_type: str | None = None,
    ) -> EntityMatchResult:
        """
        Validate and score a LightRAG entity match against the search query.

        Args:
            search_query: Original search query
            lightrag_entity: Entity found by LightRAG
            entity_type: Expected entity type (optional)

        Returns:
            EntityMatchResult with confidence scoring and validation
        """
        # Calculate similarity score
        similarity_score = self._calculate_similarity(
            search_query,
            lightrag_entity.name,
        )

        # Check for exact match
        is_exact_match = similarity_score >= self.exact_match_threshold

        # Calculate confidence based on multiple factors
        confidence = self._calculate_confidence(
            search_query,
            lightrag_entity,
            similarity_score,
            entity_type,
        )

        # Determine if high confidence
        is_high_confidence = confidence >= self.high_confidence_threshold

        # Generate match reason
        match_reason = self._generate_match_reason(
            search_query,
            lightrag_entity,
            similarity_score,
            confidence,
            is_exact_match,
        )

        return EntityMatchResult(
            entity=lightrag_entity,
            confidence=confidence,
            similarity_score=similarity_score,
            is_exact_match=is_exact_match,
            is_high_confidence=is_high_confidence,
            match_reason=match_reason,
        )

    def _calculate_similarity(self, query: str, entity_name: str) -> float:
        """Calculate string similarity between query and entity name."""
        # Normalize strings for comparison
        query_norm = query.lower().strip()
        entity_norm = entity_name.lower().strip()

        # Use SequenceMatcher for similarity
        similarity = SequenceMatcher(None, query_norm, entity_norm).ratio()

        # Boost score for exact matches (case-insensitive)
        if query_norm == entity_norm:
            return 1.0

        # Boost score for substring matches
        if query_norm in entity_norm or entity_norm in query_norm:
            similarity = max(similarity, 0.7)

        return similarity

    def _calculate_confidence(
        self,
        search_query: str,
        lightrag_entity: LightRAGEntity,
        similarity_score: float,
        entity_type: str | None,
    ) -> float:
        """Calculate overall confidence score for the match."""
        confidence = similarity_score

        # Type matching bonus
        if entity_type and lightrag_entity.entity_type == entity_type:
            confidence += 0.1
        elif entity_type and lightrag_entity.entity_type != entity_type:
            confidence -= 0.2

        # Description quality bonus
        if lightrag_entity.description and len(lightrag_entity.description) > 20:
            confidence += 0.05

        # Properties bonus
        if lightrag_entity.properties and len(lightrag_entity.properties) > 0:
            confidence += 0.05

        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))

    def _generate_match_reason(
        self,
        search_query: str,
        lightrag_entity: LightRAGEntity,
        similarity_score: float,
        confidence: float,
        is_exact_match: bool,
    ) -> str:
        """Generate human-readable reason for the match."""
        if is_exact_match:
            return f"Exact match for '{search_query}'"

        if confidence >= self.high_confidence_threshold:
            return f"High confidence match: '{lightrag_entity.name}' (similarity: {similarity_score:.2f})"

        if confidence >= self.low_confidence_threshold:
            return f"Moderate confidence match: '{lightrag_entity.name}' (similarity: {similarity_score:.2f})"

        return f"Low confidence match: '{lightrag_entity.name}' (similarity: {similarity_score:.2f})"

    def filter_high_confidence_matches(
        self,
        matches: list[EntityMatchResult],
    ) -> list[EntityMatchResult]:
        """Filter to only high confidence matches."""
        return [match for match in matches if match.is_high_confidence]

    def get_best_match(
        self,
        matches: list[EntityMatchResult],
    ) -> EntityMatchResult | None:
        """Get the best match from a list of matches."""
        if not matches:
            return None

        # Sort by confidence, then by similarity score
        return max(matches, key=lambda m: (m.confidence, m.similarity_score))

    def should_require_confirmation(
        self,
        match: EntityMatchResult,
    ) -> bool:
        """Determine if user confirmation should be required for this match."""
        return (
            not match.is_exact_match
            and match.confidence < self.high_confidence_threshold
        )
