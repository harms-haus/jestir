"""Context generation service using OpenAI for entity and relationship extraction."""

import asyncio
import json
import logging
import re
from difflib import SequenceMatcher

from openai import OpenAI

from ..models.api_config import ExtractionAPIConfig, LightRAGAPIConfig
from ..models.entity import Entity
from ..models.relationship import Relationship
from ..models.story_context import StoryContext
from ..utils.lightrag_config import load_lightrag_config
from .lightrag_client import LightRAGClient, LightRAGSearchResult
from .template_loader import TemplateLoader
from .token_tracker import TokenTracker

# Set up logging
logger = logging.getLogger(__name__)


class ContextGenerator:
    """Generates story context from natural language input using OpenAI."""

    def __init__(
        self,
        config: ExtractionAPIConfig | None = None,
        lightrag_config: LightRAGAPIConfig | None = None,
        template_loader: TemplateLoader | None = None,
        token_tracker: TokenTracker | None = None,
    ):
        """Initialize the context generator with OpenAI and LightRAG configuration."""
        self.config = config or self._load_config_from_env()
        self.client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)
        self.lightrag_config = lightrag_config or self._load_lightrag_config_from_env()
        self.lightrag_client = LightRAGClient(self.lightrag_config)
        self.template_loader = template_loader or TemplateLoader()
        self.token_tracker = token_tracker or TokenTracker()

    def _load_config_from_env(self) -> ExtractionAPIConfig:
        """Load configuration from environment variables."""
        import os

        return ExtractionAPIConfig(
            api_key=os.getenv("OPENAI_EXTRACTION_API_KEY", ""),
            base_url=os.getenv(
                "OPENAI_EXTRACTION_BASE_URL",
                "https://api.openai.com/v1",
            ),
            model=os.getenv("OPENAI_EXTRACTION_MODEL", "gpt-4o-mini"),
            max_tokens=int(os.getenv("OPENAI_EXTRACTION_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("OPENAI_EXTRACTION_TEMPERATURE", "0.1")),
        )

    def _load_lightrag_config_from_env(self) -> LightRAGAPIConfig:
        """Load LightRAG configuration from environment variables."""
        return load_lightrag_config()

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
        self,
        input_text: str,
    ) -> tuple[list[Entity], list[Relationship]]:
        """Extract entities and relationships using enhanced LightRAG + OpenAI approach."""
        try:
            # First try the enhanced LightRAG-based extraction
            entities, relationships = asyncio.run(
                self._extract_entities_with_lightrag_labels(input_text),
            )
            if entities:
                return entities, relationships
        except Exception as e:
            logger.warning(f"Enhanced LightRAG extraction failed: {e}")
            logger.info("Falling back to standard OpenAI extraction")

        # Fallback to standard OpenAI extraction
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

            # Track token usage
            if hasattr(response, "usage") and response.usage:
                self.token_tracker.track_usage(
                    service="context_generator",
                    operation="extract_entities_and_relationships",
                    model=self.config.model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    input_text=input_text,
                    output_text=response.choices[0].message.content or "",
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
                "context_extraction",
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
        self,
        content: str,
    ) -> tuple[list[Entity], list[Relationship]]:
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
                try:
                    relationship = Relationship(**rel_data)
                    relationships.append(relationship)
                except Exception as rel_error:
                    # Log the relationship parsing error but continue
                    logger.warning(
                        f"Failed to parse relationship {rel_data}: {rel_error}",
                    )
                    continue

            return entities, relationships

        except Exception as e:
            # Fallback to basic extraction
            logger.warning(f"Failed to parse extraction response: {e}")
            return self._fallback_extraction(content)

    def _fallback_extraction(
        self,
        input_text: str,
    ) -> tuple[list[Entity], list[Relationship]]:
        """Fallback extraction when OpenAI fails."""
        entities: list[Entity] = []
        relationships: list[Relationship] = []

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

    def _extract_plot_points(self, input_text: str) -> list[str]:
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

    async def _extract_entities_with_lightrag_labels(
        self,
        input_text: str,
    ) -> tuple[list[Entity], list[Relationship]]:
        """Enhanced entity extraction using LightRAG graph labels and iterative querying."""
        try:
            # Step 1: Get available graph labels from LightRAG
            graph_labels = await self.lightrag_client.get_available_entity_types()
            if not graph_labels:
                logger.warning("No graph labels available from LightRAG")
                return [], []

            logger.debug(f"Retrieved {len(graph_labels)} graph labels from LightRAG")

            # Step 2: Extract entity names using OpenAI with graph labels
            entity_names = await self._extract_entity_names_with_labels(
                input_text,
                graph_labels,
            )
            if not entity_names:
                logger.info(f"No entity names extracted from input:\n{input_text}")
                return [], []

            logger.debug(f"Extracted {len(entity_names)} entity names: {entity_names}")

            # Step 3: Iteratively query for entity information
            entities = await self._iterative_entity_lookup(entity_names, graph_labels)

            # Step 4: Extract relationships using OpenAI with graph labels
            relationships = await self._extract_relationships_with_labels(
                input_text,
                entities,
                graph_labels,
            )

            return entities, relationships

        except Exception as e:
            logger.error(f"Enhanced LightRAG extraction failed: {e}")
            # Fallback to OpenAI with graph labels if we have them
            if graph_labels:
                try:
                    return await self._fallback_extraction_with_labels(
                        input_text,
                        graph_labels,
                    )
                except Exception as fallback_error:
                    logger.error(
                        f"Fallback extraction with labels also failed: {fallback_error}",
                    )
                    raise
            else:
                raise

    async def _extract_entity_names_with_labels(
        self,
        input_text: str,
        graph_labels: list[str],
    ) -> list[str]:
        """Extract entity names from prompt using OpenAI with graph node labels."""
        try:
            # Create a prompt that asks OpenAI to identify which graph labels are mentioned

            prompt = f"""
Analyze the following story_input and identify which graph_labels from the knowledge base are likely to refer to entities mentioned in the story_input.

<graph_labels>{", ".join(graph_labels)}</graph_labels>

<story_input>{input_text}</story_input>

Respond with this exact JSON structure:
{{
    "mentioned_labels": ["label1", "label2", "label3"]
}}

Only include graph_labels that you are confident are likely to refer to entities mentioned in the story_input. Be conservative.

IMPORTANT: Return only the JSON object, no additional text or explanations.
"""

            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing story input and identifying which entities from a knowledge base are mentioned.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.1,
            )

            # Track token usage
            if hasattr(response, "usage") and response.usage:
                self.token_tracker.track_usage(
                    service="context_generator",
                    operation="extract_entity_names_with_labels",
                    model=self.config.model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    input_text=input_text,
                    output_text=response.choices[0].message.content or "",
                )

            content = response.choices[0].message.content

            logger.debug(f"Entity names with labels response: {response}")
            if content:
                return self._parse_entity_names_response(content)

        except Exception as e:
            logger.warning(f"Failed to extract entity names with labels: {e}")

        return []

    def _parse_entity_names_response(self, content: str) -> list[str]:
        """Parse entity names from OpenAI response."""
        try:
            # Extract JSON from response
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                return []

            data = json.loads(json_match.group())
            mentioned_labels = data.get("mentioned_labels", [])

            if isinstance(mentioned_labels, list):
                return [label for label in mentioned_labels if isinstance(label, str)]

        except Exception as e:
            logger.warning(
                f"Failed to parse entity names response: {e}\nRESPONSE:\n{content}",
            )

        return []

    async def _iterative_entity_lookup(
        self,
        entity_names: list[str],
        graph_labels: list[str],
    ) -> list[Entity]:
        """Iteratively query for entity information until list is empty or no results."""
        entities: list[Entity] = []
        remaining_names = entity_names.copy()

        logger.debug(
            f"Starting iterative lookup with {len(remaining_names)} entity names",
        )

        while remaining_names:
            logger.debug(
                f"Querying for {len(remaining_names)} remaining entities: {remaining_names}",
            )

            # Query for information about all remaining entities
            query_result = await self._query_entities_data(remaining_names)

            if not query_result or not query_result.entities:
                logger.debug("No entities found in query result, stopping iteration")
                break

            # Find matches and extract descriptions
            found_entities = []
            for entity_data in query_result.entities:
                # Try to match entity name to remaining names
                matched_name = self._find_matching_entity_name(
                    entity_data.name,
                    remaining_names,
                )
                if matched_name:
                    # Create Entity object
                    entity = Entity(
                        id=f"char_{len(entities) + 1:03d}",
                        type=entity_data.entity_type,
                        subtype=self._determine_subtype(entity_data.entity_type),
                        name=entity_data.name,
                        description=entity_data.description
                        or f"Entity: {entity_data.name}",
                        existing=True,
                        rag_id=f"rag_{len(entities) + 1:03d}",
                        properties=entity_data.properties or {},
                    )
                    entities.append(entity)
                    found_entities.append(matched_name)
                    logger.debug(f"Found entity: {entity_data.name} -> {matched_name}")

            # Remove found entities from remaining list
            for found_name in found_entities:
                if found_name in remaining_names:
                    remaining_names.remove(found_name)

            # If no entities were found in this iteration, stop
            if not found_entities:
                logger.debug("No entities found in this iteration, stopping")
                break

            logger.debug(
                f"Found {len(found_entities)} entities, {len(remaining_names)} remaining",
            )

        logger.info(f"Iterative lookup complete: found {len(entities)} entities")
        return entities

    async def _query_entities_data(
        self,
        entity_names: list[str],
    ) -> LightRAGSearchResult:
        """Query LightRAG for information about specific entities."""
        if not entity_names:
            return LightRAGSearchResult(
                entities=[],
                total_count=0,
                query="",
                mode="mix",
            )

        try:
            # Create a query that asks for information about the specific entities
            query = f"""
Get detailed information about each of the following entities:
{", ".join(entity_names)}

For each entity, provide:
- Name
- Type (character, location, item, etc.)
- Description
- Properties
- Relationships

Return the information in a structured format.
"""

            # Use the search_entities method
            search_result = await self.lightrag_client.search_entities(
                query=query,
                mode="mix",
                top_k=len(entity_names) * 2,  # Get more results to ensure we find all
                max_total_tokens=4000,
            )

            return search_result

        except Exception as e:
            logger.error(f"Failed to query entities data: {e}")
            return LightRAGSearchResult(
                entities=[],
                total_count=0,
                query="",
                mode="mix",
            )

    def _find_matching_entity_name(
        self,
        entity_name: str,
        remaining_names: list[str],
    ) -> str | None:
        """Find which remaining name matches the entity name."""
        entity_lower = entity_name.lower()

        # Try exact match first
        for name in remaining_names:
            if name.lower() == entity_lower:
                return name

        # Try partial match
        for name in remaining_names:
            if name.lower() in entity_lower or entity_lower in name.lower():
                return name

        # Try similarity matching
        from difflib import SequenceMatcher

        best_match = None
        best_score = 0.0

        for name in remaining_names:
            similarity = SequenceMatcher(None, name.lower(), entity_lower).ratio()
            if similarity > best_score and similarity > 0.6:  # Minimum threshold
                best_score = similarity
                best_match = name

        return best_match

    def _determine_subtype(self, entity_type: str) -> str:
        """Determine entity subtype based on entity type."""
        subtype_mapping = {
            "character": "protagonist",
            "location": "exterior",
            "item": "everyday",
            "event": "story_event",
            "organization": "group",
        }
        return subtype_mapping.get(entity_type, "unknown")

    def _generate_candidate_phrases(self, input_text: str) -> list[str]:
        """Generate candidate phrases from input text with proper noun filtering."""
        # Common short words that are not part of proper nouns
        common_short_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "up",
            "about",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "among",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "must",
            "shall",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "its",
            "our",
            "their",
            "what",
            "when",
            "where",
            "why",
            "how",
            "who",
            "which",
            "whose",
            "whom",
        }

        # Split into words and clean them
        words = re.findall(r"\b\w+\b", input_text.lower())
        words = [word for word in words if len(word) > 1]

        phrases = set()

        # Add single words (excluding common short words)
        for word in words:
            if word not in common_short_words and len(word) > 2:
                phrases.add(word)

        # Add neighboring pairs (excluding those starting/ending with common words)
        for i in range(len(words) - 1):
            pair = f"{words[i]} {words[i + 1]}"
            if (
                words[i] not in common_short_words
                and words[i + 1] not in common_short_words
            ):
                phrases.add(pair)

        # Add neighboring trios (excluding those starting/ending with common words)
        for i in range(len(words) - 2):
            trio = f"{words[i]} {words[i + 1]} {words[i + 2]}"
            if (
                words[i] not in common_short_words
                and words[i + 2] not in common_short_words
            ):
                phrases.add(trio)

        # Convert back to original case for better matching
        original_phrases = set()
        for phrase in phrases:
            # Find the phrase in original text to preserve case
            phrase_lower = phrase.lower()
            start_pos = input_text.lower().find(phrase_lower)
            if start_pos != -1:
                original_phrase = input_text[start_pos : start_pos + len(phrase)]
                original_phrases.add(original_phrase)

        return list(original_phrases)

    def _calculate_similarity_scores(
        self,
        candidate_phrases: list[str],
        graph_labels: list[str],
    ) -> list[tuple[str, str, float]]:
        """Calculate similarity scores between candidate phrases and graph labels."""
        scored_matches = []

        for phrase in candidate_phrases:
            best_match = None
            best_score = 0.0

            for label in graph_labels:
                # Use SequenceMatcher for similarity scoring
                similarity = SequenceMatcher(
                    None,
                    phrase.lower(),
                    label.lower(),
                ).ratio()

                if similarity > best_score:
                    best_score = similarity
                    best_match = label

            if best_match and best_score > 0.3:  # Minimum threshold
                scored_matches.append((phrase, best_match, best_score))

        # Sort by similarity score (highest first)
        scored_matches.sort(key=lambda x: x[2], reverse=True)
        return scored_matches

    def _select_best_matches(
        self,
        scored_matches: list[tuple[str, str, float]],
    ) -> list[str]:
        """Select the best matches ensuring one phrase per entity."""
        selected_phrases = []
        used_labels = set()

        for phrase, label, score in scored_matches:
            if (
                label not in used_labels and score >= 0.9
            ):  # Higher threshold for selection
                selected_phrases.append(phrase)
                used_labels.add(label)
                logger.debug(
                    f"Selected phrase '{phrase}' -> '{label}' (score: {score:.3f})",
                )

        return selected_phrases

    async def _batch_lookup_entities(self, phrases: list[str]) -> list[Entity]:
        """Batch lookup entities using LightRAG."""
        if not phrases:
            return []

        try:
            # Create a batch query for LightRAG
            query = f"""
Get information about each of the following entities separately.
<entities>{", ".join(phrases)}</entities>"""

            # Use the search_entities method with a specific prompt
            search_result = await self.lightrag_client.search_entities(
                query=query,
                mode="mix",
                top_k=len(phrases) * 2,  # Get more results to ensure we find all
                max_total_tokens=4000,
            )

            entities: list[Entity] = []
            for entity_data in search_result.entities:
                try:
                    # Parse the entity data from LightRAG response
                    entity = Entity(
                        id=f"char_{len(entities) + 1:03d}",
                        type=entity_data.entity_type,
                        subtype="unknown",  # LightRAGEntity doesn't have subtype, use default
                        name=entity_data.name,
                        description=entity_data.description
                        or f"Entity: {entity_data.name}",
                        existing=True,
                        rag_id=f"rag_{len(entities) + 1:03d}",
                        properties=entity_data.properties or {},
                    )
                    entities.append(entity)
                except Exception as e:
                    logger.warning(
                        f"Failed to parse entity from LightRAG response: {e}\nRESPONSE:\n{search_result.response_text}",
                    )
                    continue

            logger.info(
                f"Successfully looked up {len(entities)} entities from LightRAG",
            )
            return entities

        except Exception as e:
            logger.error(f"Batch entity lookup failed: {e}")
            # Fallback: create basic entities from phrases
            return self._create_fallback_entities(phrases)

    def _create_fallback_entities(self, phrases: list[str]) -> list[Entity]:
        """Create fallback entities when LightRAG batch lookup fails."""
        entities = []
        for i, phrase in enumerate(phrases):
            entity = Entity(
                id=f"char_{i + 1:03d}",
                type="character",
                subtype="protagonist",
                name=phrase,
                description=f"Entity mentioned in story: {phrase}",
                existing=False,
            )
            entities.append(entity)
        return entities

    async def _extract_relationships_with_labels(
        self,
        input_text: str,
        entities: list[Entity],
        graph_labels: list[str],
    ) -> list[Relationship]:
        """Extract relationships using OpenAI with graph labels context."""
        try:
            # Build a prompt that includes the graph labels for better context
            entity_names = [entity.name for entity in entities]
            labels_context = f"Available entity types in the knowledge base: {', '.join(graph_labels[:20])}"  # Limit to first 20 labels

            prompt = f"""
Analyze the following story input and extract relationships between the mentioned entities.

{labels_context}

Mentioned entities: {", ".join(entity_names)}

Return a JSON response with this exact structure:
{{
    "relationships": [
        {{
            "type": "visits",
            "subject": "entity_name_1",
            "object": "entity_name_2",
            "location": null,
            "mentioned_at": ["original text reference"],
            "metadata": {{}}
        }}
    ]
}}

Relationship types: visits, finds, creates, owns, meets, helps, fights, talks_to, goes_to, discovers

Story input: "{input_text}"

Extract all relationships between the mentioned entities.
"""

            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing story input and extracting structured relationship information.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            # Track token usage
            if hasattr(response, "usage") and response.usage:
                self.token_tracker.track_usage(
                    service="context_generator",
                    operation="extract_relationships_with_labels",
                    model=self.config.model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    input_text=input_text,
                    output_text=response.choices[0].message.content or "",
                )

            content = response.choices[0].message.content
            if content:
                return self._parse_relationships_from_response(content)

        except Exception as e:
            logger.warning(f"Failed to extract relationships with labels: {e}")

        return []

    def _parse_relationships_from_response(self, content: str) -> list[Relationship]:
        """Parse relationships from OpenAI response."""
        try:
            # Extract JSON from response
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if not json_match:
                return []

            data = json.loads(json_match.group())
            relationships = []

            for rel_data in data.get("relationships", []):
                try:
                    relationship = Relationship(**rel_data)
                    relationships.append(relationship)
                except Exception as e:
                    logger.warning(f"Failed to parse relationship {rel_data}: {e}")
                    continue

            return relationships

        except Exception as e:
            logger.warning(f"Failed to parse relationships response: {e}")
            return []

    async def _fallback_extraction_with_labels(
        self,
        input_text: str,
        graph_labels: list[str],
    ) -> tuple[list[Entity], list[Relationship]]:
        """Fallback extraction using OpenAI with graph labels context."""
        try:
            # Build a prompt that includes the graph labels for better entity extraction
            labels_context = f"Available entity types in the knowledge base: {', '.join(graph_labels[:20])}"

            prompt = f"""
Analyze the following story input and extract entities and relationships.

{labels_context}

Return a JSON response with this exact structure:
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

Relationship types: visits, finds, creates, owns, meets, helps, fights, talks_to, goes_to, discovers

Story input: "{input_text}"

Extract all mentioned characters, locations, items, and their relationships. Choose entity types from the available knowledge base when possible.
"""

            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing story input and extracting structured information with knowledge base context.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            # Track token usage
            if hasattr(response, "usage") and response.usage:
                self.token_tracker.track_usage(
                    service="context_generator",
                    operation="fallback_extraction_with_labels",
                    model=self.config.model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    input_text=input_text,
                    output_text=response.choices[0].message.content or "",
                )

            content = response.choices[0].message.content
            if content:
                return self._parse_extraction_response(content)
            return [], []

        except Exception as e:
            logger.error(f"Fallback extraction with labels failed: {e}")
            return [], []

    async def _enrich_entities_with_lightrag(
        self,
        entities: list[Entity],
    ) -> list[Entity]:
        """Enrich entities with existing data from LightRAG API."""
        enriched_entities: list[Entity] = []

        if not entities:
            logger.debug("No entities to enrich with LightRAG data")
            return enriched_entities

        logger.info(f"Enriching {len(entities)} entities with LightRAG data")

        for entity in entities:
            try:
                logger.debug(
                    f"Searching LightRAG for entity: {entity.name} (type: {entity.type})",
                )

                # Search for existing entity in LightRAG with validation
                search_results = await self.lightrag_client.fuzzy_search_entities(
                    entity.name,
                    entity_type=entity.type,
                    require_validation=True,
                )

                if search_results:
                    # Get the best match (already sorted by confidence)
                    lightrag_entity = search_results[0]

                    # Log match quality information
                    confidence = lightrag_entity.confidence or 0.0
                    similarity = lightrag_entity.similarity_score or 0.0

                    if confidence >= 0.8:
                        logger.info(
                            f"High confidence match: '{lightrag_entity.name}' for '{entity.name}' "
                            f"(confidence: {confidence:.2f}, similarity: {similarity:.2f})",
                        )
                    elif confidence >= 0.5:
                        logger.warning(
                            f"Moderate confidence match: '{lightrag_entity.name}' for '{entity.name}' "
                            f"(confidence: {confidence:.2f}, similarity: {similarity:.2f}) - "
                            f"Please verify this is the correct entity",
                        )
                    else:
                        logger.warning(
                            f"Low confidence match: '{lightrag_entity.name}' for '{entity.name}' "
                            f"(confidence: {confidence:.2f}, similarity: {similarity:.2f}) - "
                            f"This may not be the correct entity",
                        )

                    # Only use the match if it meets minimum confidence threshold
                    if confidence >= 0.5:
                        # Update entity with existing data
                        entity.existing = True
                        entity.rag_id = f"rag_{entity.id}"

                        # Enhance description with LightRAG data
                        if lightrag_entity.description:
                            original_desc = entity.description
                            entity.description = lightrag_entity.description
                            logger.debug(
                                f"Enhanced description for {entity.name}: '{original_desc}' -> '{entity.description[:100]}...'",
                            )

                        # Merge properties
                        if lightrag_entity.properties:
                            if entity.properties is None:
                                entity.properties = {}
                            original_props = entity.properties.copy()
                            entity.properties.update(lightrag_entity.properties)
                            logger.debug(
                                f"Updated properties for {entity.name}: {original_props} -> {entity.properties}",
                            )

                        # Add relationships if available
                        if lightrag_entity.relationships:
                            entity.properties = entity.properties or {}
                            entity.properties["relationships"] = (
                                lightrag_entity.relationships
                            )
                            logger.debug(
                                f"Added relationships for {entity.name}: {lightrag_entity.relationships}",
                            )
                    else:
                        logger.info(
                            f"Skipping low confidence match for '{entity.name}' - using original entity data",
                        )
                else:
                    logger.debug(
                        f"No existing entity found in LightRAG for: {entity.name}",
                    )

            except Exception as e:
                # If LightRAG lookup fails, keep entity as is
                logger.warning(
                    f"LightRAG lookup failed for entity '{entity.name}': {e}",
                )
                logger.debug(f"Continuing with original entity data for: {entity.name}")

            enriched_entities.append(entity)

        # Log summary
        existing_count = sum(1 for e in enriched_entities if e.existing)
        logger.info(
            f"Entity enrichment complete: {existing_count}/{len(entities)} entities found in LightRAG",
        )

        return enriched_entities

    def load_context_from_file(self, file_path: str) -> StoryContext:
        """Load an existing context from a YAML file."""

        import yaml

        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return StoryContext(**data)

    def update_context(
        self,
        input_text: str,
        existing_context: StoryContext,
    ) -> StoryContext:
        """Update an existing context with new natural language input."""
        # Add the new user input
        existing_context.add_user_input("update_request", input_text)

        # Extract new entities and relationships from the input
        new_entities, new_relationships = self._extract_entities_and_relationships(
            input_text,
        )

        # Check for existing entities in LightRAG
        try:
            new_entities = asyncio.run(
                self._enrich_entities_with_lightrag(new_entities),
            )
        except Exception as e:
            logger.error(f"Failed to enrich new entities with LightRAG data: {e}")
            logger.info("Continuing with new entities without LightRAG enrichment")

        # Merge new entities with existing ones
        for entity in new_entities:
            # Check if entity already exists (by name and type)
            existing_entity = self._find_existing_entity(entity, existing_context)
            if existing_entity:
                # Update existing entity with new information
                self._merge_entity(existing_entity, entity)
            else:
                # Add new entity
                existing_context.add_entity(entity)

        # Add new relationships
        for relationship in new_relationships:
            existing_context.add_relationship(relationship)

        # Extract new plot points
        new_plot_points = self._extract_plot_points(input_text)
        for plot_point in new_plot_points:
            existing_context.add_plot_point(plot_point)

        return existing_context

    def _find_existing_entity(
        self,
        new_entity: Entity,
        context: StoryContext,
    ) -> Entity | None:
        """Find an existing entity that matches the new entity."""
        for existing_entity in context.entities.values():
            if (
                existing_entity.name.lower() == new_entity.name.lower()
                and existing_entity.type == new_entity.type
            ):
                return existing_entity
        return None

    def _merge_entity(self, existing_entity: Entity, new_entity: Entity) -> None:
        """Merge new entity information into existing entity."""
        # Update description if new one is more detailed
        if len(new_entity.description) > len(existing_entity.description):
            existing_entity.description = new_entity.description

        # Merge properties
        if new_entity.properties:
            if existing_entity.properties is None:
                existing_entity.properties = {}
            existing_entity.properties.update(new_entity.properties)

        # Update subtype if different
        if new_entity.subtype != existing_entity.subtype:
            # Keep the more specific subtype
            subtype_priority = {
                "protagonist": 4,
                "antagonist": 3,
                "supporting": 2,
                "animal": 1,
            }
            existing_priority = subtype_priority.get(existing_entity.subtype, 0)
            new_priority = subtype_priority.get(new_entity.subtype, 0)
            if new_priority > existing_priority:
                existing_entity.subtype = new_entity.subtype
