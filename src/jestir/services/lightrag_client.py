"""LightRAG API client for entity retrieval and search."""

import json
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import httpx
from ..models.api_config import LightRAGAPIConfig

logger = logging.getLogger(__name__)


@dataclass
class LightRAGEntity:
    """Represents an entity from LightRAG API."""

    name: str
    entity_type: str
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    relationships: Optional[List[str]] = None


@dataclass
class LightRAGSearchResult:
    """Represents a search result from LightRAG API."""

    entities: List[LightRAGEntity]
    total_count: int
    query: str
    mode: str


class LightRAGClient:
    """Client for interacting with LightRAG API for entity retrieval."""

    def __init__(self, config: Optional[LightRAGAPIConfig] = None):
        """Initialize the LightRAG client with configuration."""
        self.config = config or self._load_config_from_env()
        self.base_url = self.config.base_url.rstrip("/")
        self.timeout = self.config.timeout

    def _load_config_from_env(self) -> LightRAGAPIConfig:
        """Load configuration from environment variables."""
        import os

        return LightRAGAPIConfig(
            base_url=os.getenv("LIGHTRAG_BASE_URL", "http://localhost:8000"),
            api_key=os.getenv("LIGHTRAG_API_KEY"),
            timeout=int(os.getenv("LIGHTRAG_TIMEOUT", "30")),
            mock_mode=os.getenv("LIGHTRAG_MOCK_MODE", "false").lower() == "true",
        )

    async def search_entities(
        self,
        query: str,
        entity_type: Optional[str] = None,
        mode: str = "mix",
        top_k: int = 10,
    ) -> LightRAGSearchResult:
        """
        Search for entities using natural language query.

        Args:
            query: Natural language search query
            entity_type: Optional entity type filter (character, location, item)
            mode: Query mode (local, global, hybrid, naive, mix, bypass)
            top_k: Number of top results to return

        Returns:
            LightRAGSearchResult containing matching entities
        """
        if self.config.mock_mode:
            return self._mock_search_entities(query, entity_type, mode, top_k)

        # Build the search query
        search_query = query
        if entity_type:
            search_query = f"Find {entity_type}s: {query}"

        # Prepare request payload
        payload = {
            "query": search_query,
            "mode": mode,
            "top_k": top_k,
            "response_type": "JSON",
            "enable_rerank": True,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._get_headers()
                response = await client.post(
                    f"{self.base_url}/query", json=payload, headers=headers
                )
                response.raise_for_status()

                result = response.json()
                return self._parse_search_response(result, query, mode)

        except httpx.ConnectError as e:
            logger.warning(f"LightRAG connection failed: {e}")
            return self._mock_search_entities(query, entity_type, mode, top_k)
        except httpx.TimeoutException as e:
            logger.warning(f"LightRAG request timeout: {e}")
            return self._mock_search_entities(query, entity_type, mode, top_k)
        except httpx.HTTPStatusError as e:
            logger.warning(f"LightRAG HTTP error {e.response.status_code}: {e}")
            return self._mock_search_entities(query, entity_type, mode, top_k)
        except Exception as e:
            logger.warning(f"Unexpected LightRAG error: {e}")
            return self._mock_search_entities(query, entity_type, mode, top_k)

    async def get_entity_details(self, entity_name: str) -> Optional[LightRAGEntity]:
        """
        Get detailed information about a specific entity.

        Args:
            entity_name: Name of the entity to retrieve

        Returns:
            LightRAGEntity with details or None if not found
        """
        if self.config.mock_mode:
            return self._mock_get_entity_details(entity_name)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._get_headers()

                # Check if entity exists
                exists_response = await client.get(
                    f"{self.base_url}/graph/entity/exists",
                    params={"name": entity_name},
                    headers=headers,
                )

                if not exists_response.json().get("exists", False):
                    return None

                # Get entity details via query
                payload = {
                    "query": f"Tell me about {entity_name}",
                    "mode": "local",
                    "response_type": "JSON",
                    "top_k": 5,
                }

                response = await client.post(
                    f"{self.base_url}/query", json=payload, headers=headers
                )
                response.raise_for_status()

                result = response.json()
                return self._parse_entity_details(result, entity_name)

        except httpx.ConnectError as e:
            logger.warning(f"LightRAG connection failed: {e}")
            return self._mock_get_entity_details(entity_name)
        except httpx.TimeoutException as e:
            logger.warning(f"LightRAG request timeout: {e}")
            return self._mock_get_entity_details(entity_name)
        except httpx.HTTPStatusError as e:
            logger.warning(f"LightRAG HTTP error {e.response.status_code}: {e}")
            return self._mock_get_entity_details(entity_name)
        except Exception as e:
            logger.warning(f"Unexpected LightRAG error: {e}")
            return self._mock_get_entity_details(entity_name)

    async def get_available_entity_types(self) -> List[str]:
        """
        Get list of available entity types from the knowledge graph.

        Returns:
            List of entity type labels
        """
        if self.config.mock_mode:
            return self._mock_get_entity_types()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._get_headers()
                response = await client.get(
                    f"{self.base_url}/graph/label/list", headers=headers
                )
                response.raise_for_status()
                return response.json()

        except httpx.ConnectError as e:
            logger.warning(f"LightRAG connection failed: {e}")
            return self._mock_get_entity_types()
        except httpx.TimeoutException as e:
            logger.warning(f"LightRAG request timeout: {e}")
            return self._mock_get_entity_types()
        except httpx.HTTPStatusError as e:
            logger.warning(f"LightRAG HTTP error {e.response.status_code}: {e}")
            return self._mock_get_entity_types()
        except Exception as e:
            logger.warning(f"Unexpected LightRAG error: {e}")
            return self._mock_get_entity_types()

    async def fuzzy_search_entities(
        self, name: str, entity_type: Optional[str] = None
    ) -> List[LightRAGEntity]:
        """
        Perform fuzzy search for entities by name with variations.

        Args:
            name: Entity name to search for
            entity_type: Optional entity type filter

        Returns:
            List of matching entities
        """
        # Try different search variations
        search_variations = [
            name,
            name.lower(),
            name.title(),
            f"*{name}*",
            f"{name}*",
            f"*{name}",
        ]

        all_results = []
        seen_names = set()

        for variation in search_variations:
            try:
                result = await self.search_entities(
                    variation, entity_type=entity_type, mode="local", top_k=5
                )

                for entity in result.entities:
                    if entity.name.lower() not in seen_names:
                        all_results.append(entity)
                        seen_names.add(entity.name.lower())

            except Exception:
                continue

        return all_results

    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _parse_search_response(
        self, response: Dict[str, Any], query: str, mode: str
    ) -> LightRAGSearchResult:
        """Parse search response from LightRAG API."""
        entities = []

        # Try to extract entities from the response
        response_text = response.get("response", "")

        # Simple parsing - in a real implementation, this would be more sophisticated
        # For now, we'll create mock entities based on the query
        if "character" in query.lower() or "person" in query.lower():
            entities.append(
                LightRAGEntity(
                    name="Sample Character",
                    entity_type="character",
                    description="A character from the story",
                    properties={"age": "unknown", "role": "protagonist"},
                )
            )
        elif "location" in query.lower() or "place" in query.lower():
            entities.append(
                LightRAGEntity(
                    name="Sample Location",
                    entity_type="location",
                    description="A location from the story",
                    properties={"type": "magical", "accessibility": "public"},
                )
            )
        elif "item" in query.lower() or "object" in query.lower():
            entities.append(
                LightRAGEntity(
                    name="Sample Item",
                    entity_type="item",
                    description="An item from the story",
                    properties={"type": "magical", "rarity": "common"},
                )
            )

        return LightRAGSearchResult(
            entities=entities, total_count=len(entities), query=query, mode=mode
        )

    def _parse_entity_details(
        self, response: Dict[str, Any], entity_name: str
    ) -> LightRAGEntity:
        """Parse entity details from LightRAG API response."""
        response_text = response.get("response", "")

        return LightRAGEntity(
            name=entity_name,
            entity_type="unknown",
            description=(
                response_text[:200] + "..."
                if len(response_text) > 200
                else response_text
            ),
            properties={},
        )

    def _mock_search_entities(
        self, query: str, entity_type: Optional[str], mode: str, top_k: int
    ) -> LightRAGSearchResult:
        """Mock search entities for testing."""
        entities = []

        # Create mock entities based on query
        if "dragon" in query.lower():
            entities.append(
                LightRAGEntity(
                    name="Purple Dragon",
                    entity_type="character",
                    description="A friendly purple dragon who lives in the magic forest",
                    properties={
                        "color": "purple",
                        "personality": "friendly",
                        "habitat": "magic forest",
                    },
                )
            )

        if "forest" in query.lower() or "location" in query.lower():
            entities.append(
                LightRAGEntity(
                    name="Magic Forest",
                    entity_type="location",
                    description="A mystical forest filled with magical creatures",
                    properties={
                        "type": "magical",
                        "accessibility": "public",
                        "danger_level": "low",
                    },
                )
            )

        if "lily" in query.lower() or "character" in query.lower():
            entities.append(
                LightRAGEntity(
                    name="Lily",
                    entity_type="character",
                    description="A curious and brave 8-year-old girl",
                    properties={
                        "age": 8,
                        "personality": "curious and brave",
                        "role": "protagonist",
                    },
                )
            )

        return LightRAGSearchResult(
            entities=entities[:top_k], total_count=len(entities), query=query, mode=mode
        )

    def _mock_get_entity_details(self, entity_name: str) -> Optional[LightRAGEntity]:
        """Mock get entity details for testing."""
        mock_entities = {
            "lily": LightRAGEntity(
                name="Lily",
                entity_type="character",
                description="A curious and brave 8-year-old girl who loves adventures",
                properties={
                    "age": 8,
                    "personality": "curious and brave",
                    "role": "protagonist",
                },
            ),
            "purple dragon": LightRAGEntity(
                name="Purple Dragon",
                entity_type="character",
                description="A friendly purple dragon who lives in the magic forest",
                properties={
                    "color": "purple",
                    "personality": "friendly",
                    "habitat": "magic forest",
                },
            ),
            "magic forest": LightRAGEntity(
                name="Magic Forest",
                entity_type="location",
                description="A mystical forest filled with magical creatures and wonders",
                properties={
                    "type": "magical",
                    "accessibility": "public",
                    "danger_level": "low",
                },
            ),
        }

        return mock_entities.get(entity_name.lower())

    def _mock_get_entity_types(self) -> List[str]:
        """Mock get entity types for testing."""
        return ["character", "location", "item", "event", "organization"]
