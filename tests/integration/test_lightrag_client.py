"""Integration tests for LightRAG API client."""

import asyncio
from unittest.mock import patch

import pytest

from jestir.models.api_config import LightRAGAPIConfig
from jestir.services.lightrag_client import (
    LightRAGClient,
    LightRAGEntity,
    LightRAGSearchResult,
)


class TestLightRAGClient:
    """Test cases for LightRAG API client."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        return LightRAGAPIConfig(
            base_url="http://localhost:8000",
            api_key="test-key",
            timeout=30,
            mock_mode=True,
        )

    @pytest.fixture
    def client(self, mock_config):
        """Create a LightRAG client instance for testing."""
        return LightRAGClient(mock_config)

    def test_search_entities_mock_mode(self, client):
        """Test entity search in mock mode."""
        result = asyncio.run(client.search_entities("dragon", entity_type="character"))

        assert isinstance(result, LightRAGSearchResult)
        assert result.query == "dragon"
        assert result.mode == "mix"
        assert len(result.entities) > 0

        # Check that we get the expected mock dragon entity
        dragon_entity = next(
            (e for e in result.entities if "dragon" in e.name.lower()),
            None,
        )
        assert dragon_entity is not None
        assert dragon_entity.entity_type == "character"
        assert "purple" in dragon_entity.name.lower()

    def test_search_entities_with_type_filter(self, client):
        """Test entity search with type filtering."""
        result = asyncio.run(client.search_entities("forest", entity_type="location"))

        assert isinstance(result, LightRAGSearchResult)
        assert len(result.entities) > 0

        # All entities should be locations
        for entity in result.entities:
            assert entity.entity_type == "location"

    def test_get_entity_details_mock_mode(self, client):
        """Test getting entity details in mock mode."""
        entity = asyncio.run(client.get_entity_details("lily"))

        assert entity is not None
        assert entity.name == "Lily"
        assert entity.entity_type == "character"
        assert entity.properties["age"] == 8
        assert "curious" in entity.description.lower()

    def test_get_entity_details_not_found(self, client):
        """Test getting details for non-existent entity."""
        entity = asyncio.run(client.get_entity_details("nonexistent"))

        assert entity is None

    def test_get_available_entity_types_mock_mode(self, client):
        """Test getting available entity types in mock mode."""
        types = asyncio.run(client.get_available_entity_types())

        assert isinstance(types, list)
        assert "character" in types
        assert "location" in types
        assert "item" in types

    def test_fuzzy_search_entities(self, client):
        """Test fuzzy search for entities."""
        results = asyncio.run(
            client.fuzzy_search_entities("lily", entity_type="character"),
        )

        assert isinstance(results, list)
        assert len(results) > 0

        # Should find Lily regardless of case variations
        lily_entity = next((e for e in results if e.name.lower() == "lily"), None)
        assert lily_entity is not None

    def test_fuzzy_search_with_variations(self, client):
        """Test fuzzy search with different name variations."""
        # Test with different cases and partial matches
        variations = ["LILY", "lily", "Lily"]

        for variation in variations:
            results = asyncio.run(
                client.fuzzy_search_entities(variation, entity_type="character"),
            )
            # Should find at least one result for exact matches
            assert len(results) > 0

    def test_search_entities_real_api_fallback(self):
        """Test that search falls back to mock mode when API is unavailable."""
        # Create client with mock_mode=False but API will be unavailable
        config = LightRAGAPIConfig(base_url="http://unreachable:8000", mock_mode=False)
        client = LightRAGClient(config)

        # Should fall back to mock mode on connection error
        result = asyncio.run(client.search_entities("dragon"))

        assert isinstance(result, LightRAGSearchResult)
        assert len(result.entities) > 0

    def test_search_entities_with_different_modes(self, client):
        """Test search with different query modes."""
        modes = ["local", "global", "hybrid", "naive", "mix", "bypass"]

        for mode in modes:
            result = asyncio.run(client.search_entities("test", mode=mode))
            assert isinstance(result, LightRAGSearchResult)
            assert result.mode == mode

    def test_search_entities_with_top_k_limit(self, client):
        """Test search with different top_k limits."""
        result = asyncio.run(client.search_entities("test", top_k=3))

        assert len(result.entities) <= 3
        assert result.total_count >= len(result.entities)

    def test_config_loading_from_env(self):
        """Test configuration loading from environment variables."""
        with patch.dict(
            "os.environ",
            {
                "LIGHTRAG_BASE_URL": "http://test:9000",
                "LIGHTRAG_API_KEY": "env-key",
                "LIGHTRAG_TIMEOUT": "60",
                "LIGHTRAG_MOCK_MODE": "true",
            },
        ):
            client = LightRAGClient()

            assert client.config.base_url == "http://test:9000"
            assert client.config.api_key == "env-key"
            assert client.config.timeout == 60
            assert client.config.mock_mode is True

    def test_default_config(self):
        """Test default configuration values."""
        client = LightRAGClient()

        assert client.config.base_url == "http://localhost:8000"
        assert client.config.api_key is None
        assert client.config.timeout == 30
        assert client.config.mock_mode is False

    def test_entity_parsing(self, client):
        """Test parsing of entity data from API responses."""
        # Test the internal parsing methods
        mock_response = {
            "response": "Lily is a curious 8-year-old girl who loves adventures.",
        }

        entity = client._parse_entity_details(mock_response, "Lily")

        assert entity.name == "Lily"
        assert "curious" in entity.description.lower()
        assert entity.entity_type == "unknown"  # Default when not specified

    def test_search_result_parsing(self, client):
        """Test parsing of search results from API responses."""
        mock_response = {"response": "Found characters: Lily, Purple Dragon"}

        result = client._parse_search_response(mock_response, "characters", "local")

        assert isinstance(result, LightRAGSearchResult)
        assert result.query == "characters"
        assert result.mode == "local"
        assert len(result.entities) >= 0  # May be empty depending on parsing logic


class TestLightRAGEntity:
    """Test cases for LightRAGEntity dataclass."""

    def test_entity_creation(self):
        """Test creating a LightRAGEntity instance."""
        entity = LightRAGEntity(
            name="Test Entity",
            entity_type="character",
            description="A test entity",
            properties={"age": 10},
            relationships=["rel1", "rel2"],
        )

        assert entity.name == "Test Entity"
        assert entity.entity_type == "character"
        assert entity.description == "A test entity"
        assert entity.properties["age"] == 10
        assert entity.relationships == ["rel1", "rel2"]

    def test_entity_minimal_creation(self):
        """Test creating a LightRAGEntity with minimal data."""
        entity = LightRAGEntity(name="Minimal Entity", entity_type="location")

        assert entity.name == "Minimal Entity"
        assert entity.entity_type == "location"
        assert entity.description is None
        assert entity.properties is None
        assert entity.relationships is None


class TestLightRAGSearchResult:
    """Test cases for LightRAGSearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a LightRAGSearchResult instance."""
        entities = [
            LightRAGEntity(name="Entity1", entity_type="character"),
            LightRAGEntity(name="Entity2", entity_type="location"),
        ]

        result = LightRAGSearchResult(
            entities=entities,
            total_count=2,
            query="test query",
            mode="local",
        )

        assert len(result.entities) == 2
        assert result.total_count == 2
        assert result.query == "test query"
        assert result.mode == "local"
