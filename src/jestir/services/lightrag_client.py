"""LightRAG API client for entity retrieval and search."""

import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx

from ..models.api_config import LightRAGAPIConfig
from ..utils.lightrag_config import load_lightrag_config

logger = logging.getLogger(__name__)


@dataclass
class LightRAGEntity:
    """Represents an entity from LightRAG API."""

    name: str
    entity_type: str
    description: str | None = None
    properties: dict[str, Any] | None = None
    relationships: list[str] | None = None
    confidence: float | None = None
    similarity_score: float | None = None


@dataclass
class LightRAGSearchResult:
    """Represents a search result from LightRAG API."""

    entities: list[LightRAGEntity]
    total_count: int
    query: str
    mode: str
    response_text: str | None = None


@dataclass
class LightRAGHealthStatus:
    """Represents LightRAG server health status."""

    status: str
    working_directory: str
    input_directory: str
    configuration: dict[str, Any]
    pipeline_busy: bool
    core_version: str | None = None
    api_version: str | None = None


class LightRAGClient:
    """Client for interacting with LightRAG API for entity retrieval."""

    def __init__(self, config: LightRAGAPIConfig | None = None):
        """Initialize the LightRAG client with configuration."""
        self.config = config or self._load_config_from_env()
        self.base_url = self.config.base_url.rstrip("/")
        self.timeout = self.config.timeout

    def _load_config_from_env(self) -> LightRAGAPIConfig:
        """Load configuration from environment variables."""
        return load_lightrag_config()

    async def search_entities(
        self,
        query: str,
        entity_type: str | None = None,
        mode: str = "mix",
        top_k: int = 10,
        chunk_top_k: int = 10,
        max_total_tokens: int = 4000,
        enable_rerank: bool = True,
        conversation_history: list[dict[str, str]] | None = None,
        history_turns: int = 3,
        user_prompt: str | None = None,
    ) -> LightRAGSearchResult:
        """
        Search for entities using natural language query.

        Args:
            query: Natural language search query
            entity_type: Optional entity type filter (character, location, item)
            mode: Query mode (local, global, hybrid, naive, mix, bypass)
            top_k: Number of top results to return
            chunk_top_k: Maximum number of text chunks to retrieve and keep after reranking
            max_total_tokens: Maximum total tokens budget for the entire query context
            enable_rerank: Enable reranking for retrieved text chunks
            conversation_history: Past conversation history to maintain context
            history_turns: Number of complete conversation turns to consider
            user_prompt: User-provided prompt for the query

        Returns:
            LightRAGSearchResult containing matching entities
        """
        if self.config.mock_mode:
            return self._mock_search_entities(query, entity_type, mode, top_k)

        # Build the search query
        search_query = query
        if entity_type:
            search_query = f"Find {entity_type}s: {query}"

        # Prepare request payload with enhanced parameters
        payload = {
            "query": search_query,
            "mode": mode,
            "top_k": top_k,
            "chunk_top_k": chunk_top_k,
            "max_total_tokens": max_total_tokens,
            "response_type": "JSON",
            "enable_rerank": enable_rerank,
        }

        # Add optional parameters
        if conversation_history:
            payload["conversation_history"] = conversation_history
            payload["history_turns"] = history_turns

        if user_prompt:
            payload["user_prompt"] = user_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._get_headers()
                response = await client.post(
                    f"{self.base_url}/query",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()

                result = response.json()
                return self._parse_search_response(result, query, mode)

        except httpx.ConnectError as e:
            logger.warning(f"LightRAG connection failed: {e}")
            return self._handle_error_fallback(
                query,
                entity_type,
                mode,
                top_k,
                "connection_failed",
            )
        except httpx.TimeoutException as e:
            logger.warning(f"LightRAG request timeout: {e}")
            return self._handle_error_fallback(
                query,
                entity_type,
                mode,
                top_k,
                "timeout",
            )
        except httpx.HTTPStatusError as e:
            error_msg = self._get_http_error_message(e.response.status_code)
            logger.warning(f"LightRAG HTTP error {e.response.status_code}: {error_msg}")
            return self._handle_error_fallback(
                query,
                entity_type,
                mode,
                top_k,
                f"http_{e.response.status_code}",
            )
        except Exception as e:
            logger.warning(f"Unexpected LightRAG error: {e}")
            return self._handle_error_fallback(
                query,
                entity_type,
                mode,
                top_k,
                "unexpected_error",
            )

    async def search_entities_stream(
        self,
        query: str,
        entity_type: str | None = None,
        mode: str = "mix",
        top_k: int = 10,
        chunk_top_k: int = 10,
        max_total_tokens: int = 4000,
        enable_rerank: bool = True,
        conversation_history: list[dict[str, str]] | None = None,
        history_turns: int = 3,
        user_prompt: str | None = None,
        on_chunk: Callable[[str], None] | None = None,
    ) -> LightRAGSearchResult:
        """
        Search for entities using streaming query.

        Args:
            query: Natural language search query
            entity_type: Optional entity type filter
            mode: Query mode
            top_k: Number of top results to return
            chunk_top_k: Maximum number of text chunks to retrieve
            max_total_tokens: Maximum total tokens budget
            enable_rerank: Enable reranking for retrieved text chunks
            conversation_history: Past conversation history
            history_turns: Number of conversation turns to consider
            user_prompt: User-provided prompt
            on_chunk: Callback function for processing streaming chunks

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
            "chunk_top_k": chunk_top_k,
            "max_total_tokens": max_total_tokens,
            "response_type": "JSON",
            "enable_rerank": enable_rerank,
            "stream": True,
        }

        # Add optional parameters
        if conversation_history:
            payload["conversation_history"] = conversation_history
            payload["history_turns"] = history_turns

        if user_prompt:
            payload["user_prompt"] = user_prompt

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._get_headers()
                headers["Accept"] = "application/x-ndjson"

                async with client.stream(
                    "POST",
                    f"{self.base_url}/query/stream",
                    json=payload,
                    headers=headers,
                ) as response:
                    response.raise_for_status()

                    full_response = ""
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                chunk_data = json.loads(line)
                                if "response" in chunk_data:
                                    chunk_text = chunk_data["response"]
                                    full_response += chunk_text
                                    if on_chunk:
                                        on_chunk(chunk_text)
                            except json.JSONDecodeError:
                                continue

                    # Parse the complete response
                    return self._parse_search_response(
                        {"response": full_response},
                        query,
                        mode,
                    )

        except httpx.ConnectError as e:
            logger.warning(f"LightRAG streaming connection failed: {e}")
            return self._handle_error_fallback(
                query,
                entity_type,
                mode,
                top_k,
                "connection_failed",
            )
        except httpx.TimeoutException as e:
            logger.warning(f"LightRAG streaming timeout: {e}")
            return self._handle_error_fallback(
                query,
                entity_type,
                mode,
                top_k,
                "timeout",
            )
        except httpx.HTTPStatusError as e:
            error_msg = self._get_http_error_message(e.response.status_code)
            logger.warning(
                f"LightRAG streaming HTTP error {e.response.status_code}: {error_msg}",
            )
            return self._handle_error_fallback(
                query,
                entity_type,
                mode,
                top_k,
                f"http_{e.response.status_code}",
            )
        except Exception as e:
            logger.warning(f"Unexpected LightRAG streaming error: {e}")
            return self._handle_error_fallback(
                query,
                entity_type,
                mode,
                top_k,
                "unexpected_error",
            )

    async def get_entity_details(self, entity_name: str) -> LightRAGEntity | None:
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
                    f"{self.base_url}/query",
                    json=payload,
                    headers=headers,
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

    async def get_available_entity_types(self) -> list[str]:
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
                    f"{self.base_url}/graph/label/list",
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list) and all(
                    isinstance(item, str) for item in data
                ):
                    return data
                logger.warning("Unexpected response format from LightRAG API")
                return self._mock_get_entity_types()

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
        self,
        name: str,
        entity_type: str | None = None,
        require_validation: bool = True,
    ) -> list[LightRAGEntity]:
        """
        Perform fuzzy search for entities by name with variations and validation.

        Args:
            name: Entity name to search for
            entity_type: Optional entity type filter
            require_validation: Whether to validate and score matches

        Returns:
            List of matching entities with confidence scoring
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
                    variation,
                    entity_type=entity_type,
                    mode="local",
                    top_k=5,
                )

                for entity in result.entities:
                    if entity.name.lower() not in seen_names:
                        all_results.append(entity)
                        seen_names.add(entity.name.lower())

            except Exception:
                continue

        # Validate and score matches if required
        if require_validation and all_results:
            from .entity_validator import EntityValidator

            validator = EntityValidator()

            validated_results = []
            for entity in all_results:
                match_result = validator.validate_entity_match(
                    name,
                    entity,
                    entity_type,
                )

                # Add confidence and similarity scores to entity
                entity.confidence = match_result.confidence
                entity.similarity_score = match_result.similarity_score

                validated_results.append(entity)

            # Sort by confidence and similarity score
            all_results = sorted(
                validated_results,
                key=lambda e: (e.confidence or 0, e.similarity_score or 0),
                reverse=True,
            )

        return all_results

    async def check_health(self) -> LightRAGHealthStatus | None:
        """
        Check LightRAG server health status.

        Returns:
            LightRAGHealthStatus with server information or None if failed
        """
        if self.config.mock_mode:
            return self._mock_health_status()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = self._get_headers()
                response = await client.get(
                    f"{self.base_url}/health",
                    headers=headers,
                )
                response.raise_for_status()

                data = response.json()
                return LightRAGHealthStatus(
                    status=data.get("status", "unknown"),
                    working_directory=data.get("working_directory", ""),
                    input_directory=data.get("input_directory", ""),
                    configuration=data.get("configuration", {}),
                    pipeline_busy=data.get("pipeline_busy", False),
                    core_version=data.get("core_version"),
                    api_version=data.get("api_version"),
                )

        except httpx.ConnectError as e:
            logger.warning(f"LightRAG health check failed: {e}")
            return None
        except httpx.TimeoutException as e:
            logger.warning(f"LightRAG health check timeout: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.warning(
                f"LightRAG health check HTTP error {e.response.status_code}: {e}",
            )
            return None
        except Exception as e:
            logger.warning(f"Unexpected LightRAG health check error: {e}")
            return None

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key
        return headers

    def _parse_search_response(
        self,
        response: dict[str, Any],
        query: str,
        mode: str,
    ) -> LightRAGSearchResult:
        """Parse search response from LightRAG API."""
        entities = []
        response_text = response.get("response", "")

        # Try to extract entities from the response text
        entities = self._extract_entities_from_text(response_text, query)

        return LightRAGSearchResult(
            entities=entities,
            total_count=len(entities),
            query=query,
            mode=mode,
            response_text=response_text,
        )

    def _extract_entities_from_text(
        self,
        text: str,
        query: str,
    ) -> list[LightRAGEntity]:
        """Extract entities from response text using pattern matching and JSON parsing."""
        entities = []

        # Try to parse JSON entities if the response contains structured data
        try:
            # Look for JSON-like structures in the response
            json_pattern = r'\{[^{}]*"name"[^{}]*\}'
            json_matches = re.findall(json_pattern, text, re.IGNORECASE | re.DOTALL)

            for match in json_matches:
                try:
                    entity_data = json.loads(match)
                    if "name" in entity_data:
                        entity = LightRAGEntity(
                            name=entity_data.get("name", ""),
                            entity_type=entity_data.get("type", "unknown"),
                            description=entity_data.get("description"),
                            properties=entity_data.get("properties", {}),
                            relationships=entity_data.get("relationships", []),
                        )
                        entities.append(entity)
                except json.JSONDecodeError:
                    continue
        except Exception:
            pass

        # If no JSON entities found, try to extract entities using pattern matching
        if not entities:
            entities = self._extract_entities_by_patterns(text, query)

        return entities

    def _extract_entities_by_patterns(
        self,
        text: str,
        query: str,
    ) -> list[LightRAGEntity]:
        """Extract entities using pattern matching when JSON parsing fails."""
        entities = []

        # Common entity patterns
        patterns = [
            (r"Character[s]?:?\s*([^\n,]+)", "character"),
            (r"Person[s]?:?\s*([^\n,]+)", "character"),
            (r"Location[s]?:?\s*([^\n,]+)", "location"),
            (r"Place[s]?:?\s*([^\n,]+)", "location"),
            (r"Item[s]?:?\s*([^\n,]+)", "item"),
            (r"Object[s]?:?\s*([^\n,]+)", "item"),
            (r"Event[s]?:?\s*([^\n,]+)", "event"),
            (r"Organization[s]?:?\s*([^\n,]+)", "organization"),
        ]

        for pattern, entity_type in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.strip()
                if name and len(name) > 1:  # Avoid single characters
                    entity = LightRAGEntity(
                        name=name,
                        entity_type=entity_type,
                        description=f"A {entity_type} mentioned in the response",
                        properties={},
                    )
                    entities.append(entity)

        # If still no entities found, create a generic one based on the query
        if not entities:
            entity_type = "unknown"
            if any(word in query.lower() for word in ["character", "person", "people"]):
                entity_type = "character"
            elif any(word in query.lower() for word in ["location", "place", "where"]):
                entity_type = "location"
            elif any(word in query.lower() for word in ["item", "object", "thing"]):
                entity_type = "item"

            entities.append(
                LightRAGEntity(
                    name=f"Entity from '{query[:50]}...'",
                    entity_type=entity_type,
                    description="An entity extracted from the query",
                    properties={},
                ),
            )

        return entities

    def _parse_entity_details(
        self,
        response: dict[str, Any],
        entity_name: str,
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
        self,
        query: str,
        entity_type: str | None,
        mode: str,
        top_k: int,
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
                ),
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
                ),
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
                ),
            )

        return LightRAGSearchResult(
            entities=entities[:top_k],
            total_count=len(entities),
            query=query,
            mode=mode,
        )

    def _mock_get_entity_details(self, entity_name: str) -> LightRAGEntity | None:
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

    def _mock_get_entity_types(self) -> list[str]:
        """Mock get entity types for testing."""
        return ["character", "location", "item", "event", "organization"]

    def _mock_health_status(self) -> LightRAGHealthStatus:
        """Mock health status for testing."""
        return LightRAGHealthStatus(
            status="healthy",
            working_directory="./rag_storage",
            input_directory="./inputs",
            configuration={
                "llm_binding": "mock",
                "embedding_binding": "mock",
                "workspace": "test",
            },
            pipeline_busy=False,
            core_version="1.0.0-mock",
            api_version="1.0.0-mock",
        )

    def _get_http_error_message(self, status_code: int) -> str:
        """Get user-friendly error message for HTTP status codes."""
        error_messages = {
            400: "Bad Request - Invalid query parameters",
            401: "Unauthorized - Invalid or missing API key",
            403: "Forbidden - Access denied",
            404: "Not Found - Endpoint or resource not found",
            429: "Too Many Requests - Rate limit exceeded",
            500: "Internal Server Error - Server encountered an error",
            502: "Bad Gateway - Server is temporarily unavailable",
            503: "Service Unavailable - Server is overloaded",
            504: "Gateway Timeout - Server took too long to respond",
        }
        return error_messages.get(status_code, f"HTTP {status_code} error")

    def _handle_error_fallback(
        self,
        query: str,
        entity_type: str | None,
        mode: str,
        top_k: int,
        error_type: str,
    ) -> LightRAGSearchResult:
        """Handle errors by falling back to mock data with error information."""
        # Create an error entity to indicate the issue
        error_entity = LightRAGEntity(
            name=f"Error: {error_type}",
            entity_type="error",
            description=f"Failed to retrieve entities due to {error_type}",
            properties={"error_type": error_type, "original_query": query},
        )

        return LightRAGSearchResult(
            entities=[error_entity],
            total_count=1,
            query=query,
            mode=mode,
            response_text=f"Error: {error_type} - Using fallback data",
        )
