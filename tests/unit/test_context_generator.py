"""Unit tests for ContextGenerator service."""

import json
from unittest.mock import Mock, patch

from jestir.models.api_config import ExtractionAPIConfig
from jestir.models.story_context import StoryContext
from jestir.services.context_generator import ContextGenerator


class TestContextGenerator:
    """Test cases for ContextGenerator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = ExtractionAPIConfig(
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
            max_tokens=1000,
            temperature=0.1,
        )
        self.generator = ContextGenerator(self.config)

    def test_init_with_config(self):
        """Test initialization with provided config."""
        assert self.generator.config == self.config
        assert self.generator.client is not None

    @patch.dict("os.environ", {"OPENAI_EXTRACTION_API_KEY": "env-key"})
    def test_init_with_env_config(self):
        """Test initialization with environment variables."""
        generator = ContextGenerator()
        assert generator.config.api_key == "env-key"

    def test_generate_context_basic(self):
        """Test basic context generation."""
        input_text = "A brave knight named Arthur goes to the enchanted forest to find a magical sword."

        with patch.object(
            self.generator,
            "_extract_entities_and_relationships",
        ) as mock_extract:
            mock_extract.return_value = ([], [])

            context = self.generator.generate_context(input_text)

            assert isinstance(context, StoryContext)
            assert "initial_request" in context.user_inputs
            assert context.user_inputs["initial_request"] == input_text

    def test_extract_entities_and_relationships_success(self):
        """Test successful entity and relationship extraction."""
        input_text = "Arthur visits the forest"

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            {
                "entities": [
                    {
                        "id": "char_001",
                        "type": "character",
                        "subtype": "protagonist",
                        "name": "Arthur",
                        "description": "A brave knight",
                        "existing": False,
                        "properties": {},
                    },
                ],
                "relationships": [
                    {
                        "type": "visits",
                        "subject": "char_001",
                        "object": "loc_001",
                        "location": None,
                        "mentioned_at": ["Arthur visits the forest"],
                        "metadata": {},
                    },
                ],
            },
        )

        with patch.object(
            self.generator.client.chat.completions,
            "create",
            return_value=mock_response,
        ):
            entities, relationships = (
                self.generator._extract_entities_and_relationships(input_text)
            )

            assert len(entities) == 1
            assert entities[0].name == "Arthur"
            assert len(relationships) == 1
            assert relationships[0].type == "visits"

    def test_extract_entities_and_relationships_fallback(self):
        """Test fallback extraction when OpenAI fails."""
        input_text = "Arthur visits the forest"

        with patch.object(
            self.generator.client.chat.completions,
            "create",
            side_effect=Exception("API Error"),
        ):
            entities, relationships = (
                self.generator._extract_entities_and_relationships(input_text)
            )

            # Should use fallback extraction
            assert isinstance(entities, list)
            assert isinstance(relationships, list)

    def test_fallback_extraction(self):
        """Test fallback extraction logic."""
        input_text = "Arthur the Brave Knight goes to the Enchanted Forest"

        entities, relationships = self.generator._fallback_extraction(input_text)

        # Should extract capitalized words as entities
        assert len(entities) > 0
        assert any(entity.name == "Arthur" for entity in entities)

    def test_extract_plot_points(self):
        """Test plot point extraction."""
        input_text = "Arthur wants to find the sword. He needs to go to the forest. He discovers a magical cave."

        plot_points = self.generator._extract_plot_points(input_text)

        assert len(plot_points) > 0
        assert any("find the sword" in point for point in plot_points)
        assert any("go to the forest" in point for point in plot_points)

    def test_parse_extraction_response_valid_json(self):
        """Test parsing valid JSON response."""
        content = '{"entities": [], "relationships": []}'

        entities, relationships = self.generator._parse_extraction_response(content)

        assert entities == []
        assert relationships == []

    def test_parse_extraction_response_invalid_json(self):
        """Test parsing invalid JSON response."""
        content = "This is not JSON"

        with patch.object(
            self.generator,
            "_fallback_extraction",
            return_value=([], []),
        ) as mock_fallback:
            entities, relationships = self.generator._parse_extraction_response(content)

            mock_fallback.assert_called_once_with(content)

    def test_build_extraction_prompt(self):
        """Test extraction prompt building."""
        input_text = "Arthur visits the forest"
        prompt = self.generator._build_extraction_prompt(input_text)

        assert input_text in prompt
        assert "entities" in prompt
        assert "relationships" in prompt
        assert "JSON" in prompt
