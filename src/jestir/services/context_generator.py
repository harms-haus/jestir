"""Context generation service using OpenAI for entity and relationship extraction."""

import json
import re
import asyncio
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from ..models.story_context import StoryContext
from ..models.entity import Entity
from ..models.relationship import Relationship
from ..models.api_config import ExtractionAPIConfig, LightRAGAPIConfig
from .lightrag_client import LightRAGClient
from .template_loader import TemplateLoader

# Set up logging
logger = logging.getLogger(__name__)


class ContextGenerator:
    """Generates story context from natural language input using OpenAI."""

    def __init__(
        self,
        config: Optional[ExtractionAPIConfig] = None,
        lightrag_config: Optional[LightRAGAPIConfig] = None,
        template_loader: Optional[TemplateLoader] = None,
    ):
        """Initialize the context generator with OpenAI and LightRAG configuration."""
        self.config = config or self._load_config_from_env()
        self.client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)
        self.lightrag_config = lightrag_config or self._load_lightrag_config_from_env()
        self.lightrag_client = LightRAGClient(self.lightrag_config)
        self.template_loader = template_loader or TemplateLoader()

    def _load_config_from_env(self) -> ExtractionAPIConfig:
        """Load configuration from environment variables."""
        import os

        return ExtractionAPIConfig(
            api_key=os.getenv("OPENAI_EXTRACTION_API_KEY", ""),
            base_url=os.getenv(
                "OPENAI_EXTRACTION_BASE_URL", "https://api.openai.com/v1"
            ),
            model=os.getenv("OPENAI_EXTRACTION_MODEL", "gpt-4o-mini"),
            max_tokens=int(os.getenv("OPENAI_EXTRACTION_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("OPENAI_EXTRACTION_TEMPERATURE", "0.1")),
        )

    def _load_lightrag_config_from_env(self) -> LightRAGAPIConfig:
        """Load LightRAG configuration from environment variables."""
        import os

        return LightRAGAPIConfig(
            base_url=os.getenv("LIGHTRAG_BASE_URL", "http://localhost:8000"),
            api_key=os.getenv("LIGHTRAG_API_KEY"),
            timeout=int(os.getenv("LIGHTRAG_TIMEOUT", "30")),
            mock_mode=os.getenv("LIGHTRAG_MOCK_MODE", "false").lower() == "true",
        )

    def generate_context(self, input_text: str) -> StoryContext:
        """Generate a complete story context from natural language input."""
        context = StoryContext()

        # Add the user input
        context.add_user_input("initial_request", input_text)

        # Extract entities and relationships using OpenAI
        entities, relationships = self._extract_entities_and_relationships(input_text)

        # Check for existing entities in LightRAG
        try:
            entities = asyncio.run(self._enrich_entities_with_lightrag(entities))
        except Exception as e:
            logger.error(f"Failed to enrich entities with LightRAG data: {e}")
            logger.info("Continuing with original entities without LightRAG enrichment")

        # Add entities to context
        for entity in entities:
            context.add_entity(entity)

        # Add relationships to context
        for relationship in relationships:
            context.add_relationship(relationship)

        # Extract plot points
        plot_points = self._extract_plot_points(input_text)
        for plot_point in plot_points:
            context.add_plot_point(plot_point)

        return context

    def _extract_entities_and_relationships(
        self, input_text: str
    ) -> tuple[List[Entity], List[Relationship]]:
        """Extract entities and relationships using OpenAI."""
        prompt = self._build_extraction_prompt(input_text)

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing story input and extracting structured information.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            content = response.choices[0].message.content
            if content is None:
                return self._fallback_extraction(input_text)
            return self._parse_extraction_response(content)

        except Exception as e:
            # Fallback to basic extraction if OpenAI fails
            return self._fallback_extraction(input_text)

    def _build_extraction_prompt(self, input_text: str) -> str:
        """Build the prompt for entity and relationship extraction using templates."""
        try:
            # Load system prompt template
            system_prompt = self.template_loader.load_system_prompt(
                "context_extraction"
            )

            # Load user prompt template and substitute variables
            user_prompt = self.template_loader.render_template(
                "prompts/user_prompts/context_extraction.txt",
                {"input_text": input_text},
            )

            return user_prompt
        except Exception as e:
            logger.warning(f"Failed to load templates, using fallback: {e}")
            return self._fallback_extraction_prompt(input_text)

    def _fallback_extraction_prompt(self, input_text: str) -> str:
        """Fallback extraction prompt when templates fail."""
        return f"""
Analyze the following story input and extract entities and relationships. Return a JSON response with this exact structure:

{{
    "entities": [
        {{
            "id": "char_001",
            "type": "character",
            "subtype": "protagonist",
            "name": "Character Name",
            "description": "Brief description",
            "existing": false,
            "properties": {{}}
        }}
    ],
    "relationships": [
        {{
            "type": "visits",
            "subject": "char_001",
            "object": "loc_001",
            "location": null,
            "mentioned_at": ["original text reference"],
            "metadata": {{}}
        }}
    ]
}}

Entity types: character, location, item
Character subtypes: protagonist, antagonist, supporting, animal
Location subtypes: interior, exterior, magical, real
Item subtypes: magical, tool, treasure, everyday

Relationship types: visits, finds, creates, owns, meets, helps, fights

Story input: "{input_text}"

Extract all mentioned characters, locations, items, and their relationships. Mark entities as existing=false for now (LightRAG integration will be added later).
"""

    def _parse_extraction_response(
        self, content: str
    ) -> tuple[List[Entity], List[Relationship]]:
        """Parse the OpenAI response to extract entities and relationships."""
        try:
            # Extract JSON from response
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")

            data = json.loads(json_match.group())

            entities = []
            for entity_data in data.get("entities", []):
                entity = Entity(**entity_data)
                entities.append(entity)

            relationships = []
            for rel_data in data.get("relationships", []):
                relationship = Relationship(**rel_data)
                relationships.append(relationship)

            return entities, relationships

        except Exception as e:
            # Fallback to basic extraction
            return self._fallback_extraction(content)

    def _fallback_extraction(
        self, input_text: str
    ) -> tuple[List[Entity], List[Relationship]]:
        """Fallback extraction when OpenAI fails."""
        entities: List[Entity] = []
        relationships: List[Relationship] = []

        # Basic entity extraction using simple patterns
        words = input_text.split()
        entity_id = 1

        # Look for capitalized words that might be names
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2:
                entity = Entity(
                    id=f"char_{entity_id:03d}",
                    type="character",
                    subtype="protagonist",
                    name=word.strip(".,!?"),
                    description=f"Character mentioned in story: {word}",
                    existing=False,
                )
                entities.append(entity)
                entity_id += 1

        return entities, relationships

    def _extract_plot_points(self, input_text: str) -> List[str]:
        """Extract key plot points from the input."""
        # Simple plot point extraction
        plot_points = []

        # Look for action words and key phrases
        action_patterns = [
            r"wants to (.+?)(?:\.|$)",
            r"needs to (.+?)(?:\.|$)",
            r"goes to (.+?)(?:\.|$)",
            r"finds (.+?)(?:\.|$)",
            r"discovers (.+?)(?:\.|$)",
        ]

        for pattern in action_patterns:
            matches = re.findall(pattern, input_text, re.IGNORECASE)
            for match in matches:
                plot_points.append(match.strip())

        return plot_points

    async def _enrich_entities_with_lightrag(
        self, entities: List[Entity]
    ) -> List[Entity]:
        """Enrich entities with existing data from LightRAG API."""
        enriched_entities: List[Entity] = []

        if not entities:
            logger.debug("No entities to enrich with LightRAG data")
            return enriched_entities

        logger.info(f"Enriching {len(entities)} entities with LightRAG data")

        for entity in entities:
            try:
                logger.debug(
                    f"Searching LightRAG for entity: {entity.name} (type: {entity.type})"
                )

                # Search for existing entity in LightRAG
                search_results = await self.lightrag_client.fuzzy_search_entities(
                    entity.name, entity_type=entity.type
                )

                if search_results:
                    # Found existing entity, update with LightRAG data
                    lightrag_entity = search_results[0]  # Take the best match
                    logger.info(
                        f"Found existing entity in LightRAG: {lightrag_entity.name} -> {entity.name}"
                    )

                    # Update entity with existing data
                    entity.existing = True
                    entity.rag_id = f"rag_{entity.id}"

                    # Enhance description with LightRAG data
                    if lightrag_entity.description:
                        original_desc = entity.description
                        entity.description = lightrag_entity.description
                        logger.debug(
                            f"Enhanced description for {entity.name}: '{original_desc}' -> '{entity.description[:100]}...'"
                        )

                    # Merge properties
                    if lightrag_entity.properties:
                        if entity.properties is None:
                            entity.properties = {}
                        original_props = entity.properties.copy()
                        entity.properties.update(lightrag_entity.properties)
                        logger.debug(
                            f"Updated properties for {entity.name}: {original_props} -> {entity.properties}"
                        )

                    # Add relationships if available
                    if lightrag_entity.relationships:
                        entity.properties = entity.properties or {}
                        entity.properties["relationships"] = (
                            lightrag_entity.relationships
                        )
                        logger.debug(
                            f"Added relationships for {entity.name}: {lightrag_entity.relationships}"
                        )
                else:
                    logger.debug(
                        f"No existing entity found in LightRAG for: {entity.name}"
                    )

            except Exception as e:
                # If LightRAG lookup fails, keep entity as is
                logger.warning(
                    f"LightRAG lookup failed for entity '{entity.name}': {e}"
                )
                logger.debug(f"Continuing with original entity data for: {entity.name}")

            enriched_entities.append(entity)

        # Log summary
        existing_count = sum(1 for e in enriched_entities if e.existing)
        logger.info(
            f"Entity enrichment complete: {existing_count}/{len(entities)} entities found in LightRAG"
        )

        return enriched_entities
