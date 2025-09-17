"""Story writing service using OpenAI for final story generation."""

import re
from pathlib import Path

from openai import OpenAI

from ..models.api_config import CreativeAPIConfig
from ..models.story_context import StoryContext
from .template_loader import TemplateLoader
from .token_tracker import TokenTracker


class StoryWriter:
    """Generates final stories from outlines using OpenAI."""

    def __init__(
        self,
        config: CreativeAPIConfig | None = None,
        template_loader: TemplateLoader | None = None,
        token_tracker: TokenTracker | None = None,
    ):
        """Initialize the story writer with OpenAI configuration."""
        self.config = config or self._load_config_from_env()
        self.client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)
        self.template_loader = template_loader or TemplateLoader()
        self.token_tracker = token_tracker or TokenTracker()

    def _load_config_from_env(self) -> CreativeAPIConfig:
        """Load configuration from environment variables."""
        import os

        return CreativeAPIConfig(
            api_key=os.getenv("OPENAI_CREATIVE_API_KEY", ""),
            base_url=os.getenv("OPENAI_CREATIVE_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("OPENAI_CREATIVE_MODEL", "gpt-4o-mini"),
            max_tokens=int(os.getenv("OPENAI_CREATIVE_MAX_TOKENS", "4000")),
            temperature=float(os.getenv("OPENAI_CREATIVE_TEMPERATURE", "0.8")),
        )

    def generate_story(self, context: StoryContext, outline: str) -> str:
        """Generate a final story from the given context and outline."""
        prompt = self._build_story_prompt(context, outline)

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert children's story writer who creates engaging, age-appropriate bedtime stories with clear narrative flow, character development, and positive moral lessons.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            # Track token usage
            if hasattr(response, "usage") and response.usage:
                self.token_tracker.track_usage(
                    service="story_writer",
                    operation="generate_story",
                    model=self.config.model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    input_text=f"{context.model_dump()!s}\n\nOutline:\n{outline}",
                    output_text=response.choices[0].message.content or "",
                )

            content = response.choices[0].message.content
            if content is None:
                return self._fallback_story(context, outline)

            return self._format_story(content)

        except Exception as e:
            # Fallback to basic story if OpenAI fails
            return self._fallback_story(context, outline)

    def _build_story_prompt(self, context: StoryContext, outline: str) -> str:
        """Build the prompt for story generation using templates."""
        try:
            # Extract key information from context
            entities = list(context.entities.values())
            characters = [e for e in entities if e.type == "character"]
            locations = [e for e in entities if e.type == "location"]
            items = [e for e in entities if e.type == "item"]

            # Build character descriptions
            character_descriptions = []
            for char in characters:
                desc = f"- {char.name}: {char.description}"
                if char.subtype:
                    desc += f" ({char.subtype})"
                character_descriptions.append(desc)

            # Build location descriptions
            location_descriptions = []
            for loc in locations:
                desc = f"- {loc.name}: {loc.description}"
                if loc.subtype:
                    desc += f" ({loc.subtype})"
                location_descriptions.append(desc)

            # Build item descriptions
            item_descriptions = []
            for item in items:
                desc = f"- {item.name}: {item.description}"
                if item.subtype:
                    desc += f" ({item.subtype})"
                item_descriptions.append(desc)

            # Get plot points
            plot_points_text = "\n".join(f"- {point}" for point in context.plot_points)

            # Get user inputs
            user_inputs_text = "\n".join(
                f"- {input_id}: {text}"
                for input_id, text in context.user_inputs.items()
            )

            # Prepare context for template
            template_context = {
                "genre": context.settings.get("genre", "adventure"),
                "tone": context.settings.get("tone", "gentle"),
                "length": context.settings.get("length", "short"),
                "target_word_count": self._get_target_word_count(
                    context.settings.get("length", "short"),
                ),
                "age_appropriate": context.settings.get("age_appropriate", True),
                "morals": (
                    ", ".join(context.settings.get("morals", []))
                    if context.settings.get("morals")
                    else "None specified"
                ),
                "characters": (
                    "\n".join(character_descriptions)
                    if character_descriptions
                    else "- No specific characters mentioned"
                ),
                "locations": (
                    "\n".join(location_descriptions)
                    if location_descriptions
                    else "- No specific locations mentioned"
                ),
                "items": (
                    "\n".join(item_descriptions)
                    if item_descriptions
                    else "- No specific items mentioned"
                ),
                "plot_points": (
                    plot_points_text
                    if plot_points_text
                    else "- No specific plot points mentioned"
                ),
                "user_inputs": (
                    user_inputs_text
                    if user_inputs_text
                    else "No specific request provided"
                ),
                "outline": outline,
            }

            # Load and render template
            return self.template_loader.render_template(
                "prompts/user_prompts/story_generation.txt",
                template_context,
            )
        except Exception as e:
            # Fallback to hardcoded prompt if template loading fails
            return self._fallback_story_prompt(context, outline)

    def _fallback_story_prompt(self, context: StoryContext, outline: str) -> str:
        """Fallback story prompt when templates fail."""
        # Extract key information from context
        entities = list(context.entities.values())
        characters = [e for e in entities if e.type == "character"]
        locations = [e for e in entities if e.type == "location"]
        items = [e for e in entities if e.type == "item"]

        # Build character descriptions
        character_descriptions = []
        for char in characters:
            desc = f"- {char.name}: {char.description}"
            if char.subtype:
                desc += f" ({char.subtype})"
            character_descriptions.append(desc)

        # Build location descriptions
        location_descriptions = []
        for loc in locations:
            desc = f"- {loc.name}: {loc.description}"
            if loc.subtype:
                desc += f" ({loc.subtype})"
            location_descriptions.append(desc)

        # Build item descriptions
        item_descriptions = []
        for item in items:
            desc = f"- {item.name}: {item.description}"
            if item.subtype:
                desc += f" ({item.subtype})"
            item_descriptions.append(desc)

        # Get plot points
        plot_points_text = "\n".join(f"- {point}" for point in context.plot_points)

        # Get user inputs
        user_inputs_text = "\n".join(
            f"- {input_id}: {text}" for input_id, text in context.user_inputs.items()
        )

        return f"""Write a complete bedtime story based on the provided outline and context.

**Story Requirements:**
- Genre: {context.settings.get("genre", "adventure")}
- Tone: {context.settings.get("tone", "gentle")}
- Length: {context.settings.get("length", "short")} (aim for {self._get_target_word_count(context.settings.get("length", "short"))} words)
- Age Appropriate: {context.settings.get("age_appropriate", True)}
- Morals: {", ".join(context.settings.get("morals", [])) if context.settings.get("morals") else "None specified"}

**Characters:**
{chr(10).join(character_descriptions) if character_descriptions else "- No specific characters mentioned"}

**Locations:**
{chr(10).join(location_descriptions) if location_descriptions else "- No specific locations mentioned"}

**Items/Objects:**
{chr(10).join(item_descriptions) if item_descriptions else "- No specific items mentioned"}

**Plot Points:**
{plot_points_text if plot_points_text else "- No specific plot points mentioned"}

**Original Request:**
{user_inputs_text if user_inputs_text else "No specific request provided"}

**Story Outline to Follow:**
{outline}

**Requirements for the story:**
1. Write in plain markdown format with proper paragraph breaks
2. Use engaging, age-appropriate language
3. Include dialogue to bring characters to life
4. Follow the outline structure but expand each scene into full narrative
5. Ensure smooth transitions between scenes
6. Include descriptive details about settings and characters
7. Build tension and resolution appropriately
8. End with a clear moral lesson or positive message
9. Use simple, clear sentences suitable for bedtime reading
10. Include emotional depth and character growth

**Format the story as:**
# [Story Title]

[Story content in markdown format with proper paragraphs, dialogue, and narrative flow]

Write the complete story now:"""

    def _get_target_word_count(self, length: str) -> int:
        """Get target word count based on length setting."""
        length_targets = {
            "very_short": 200,
            "short": 500,
            "medium": 1000,
            "long": 2000,
            "very_long": 3000,
        }
        return length_targets.get(length, 500)

    def _format_story(self, content: str) -> str:
        """Format the generated story content."""
        # Clean up the content
        content = content.strip()

        # Ensure it starts with a proper heading
        if not content.startswith("#"):
            content = f"# The Adventure\n\n{content}"

        # Clean up formatting
        lines = content.split("\n")
        formatted_lines = []

        for line in lines:
            line = line.strip()
            if line:
                formatted_lines.append(line)
            else:
                formatted_lines.append("")

        # Join lines and clean up multiple empty lines
        formatted_content = "\n".join(formatted_lines)
        formatted_content = re.sub(r"\n\s*\n\s*\n", "\n\n", formatted_content)

        return formatted_content

    def _fallback_story(self, context: StoryContext, outline: str) -> str:
        """Generate a basic fallback story when OpenAI fails."""
        # Extract main character
        characters = [e for e in context.entities.values() if e.type == "character"]
        main_character = characters[0].name if characters else "The Hero"

        # Get plot points
        plot_points = context.plot_points
        main_plot = plot_points[0] if plot_points else "goes on an adventure"

        return f"""# {main_character}'s Adventure

Once upon a time, there was a brave little character named {main_character}.

{main_character} lived in a magical place and was known for being kind and helpful to everyone they met. One day, {main_character} decided to {main_plot}.

As {main_character} began their journey, they encountered many challenges along the way. But {main_character} was determined and never gave up, even when things seemed difficult.

Through their adventure, {main_character} learned important lessons about courage, friendship, and believing in themselves. They discovered that with determination and a kind heart, they could overcome any obstacle.

In the end, {main_character} achieved their goal and returned home wiser and stronger than before. The adventure had taught them that the greatest treasures in life are not gold or jewels, but the lessons we learn and the friends we make along the way.

And so, {main_character} lived happily ever after, always ready for the next adventure that might come their way.

The End.
"""

    def load_outline_from_file(self, outline_file: str) -> str:
        """Load an outline from a markdown file."""
        outline_path = Path(outline_file)
        if not outline_path.exists():
            raise FileNotFoundError(f"Outline file not found: {outline_file}")

        with open(outline_path, encoding="utf-8") as f:
            return f.read()

    def load_context_from_file(self, context_file: str) -> StoryContext:
        """Load a StoryContext from a YAML file."""
        import yaml

        context_path = Path(context_file)
        if not context_path.exists():
            raise FileNotFoundError(f"Context file not found: {context_file}")

        with open(context_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return StoryContext(**data)

    def save_story_to_file(self, story: str, output_file: str) -> None:
        """Save the story to a markdown file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(story)

    def update_context_with_story(self, context: StoryContext, story: str) -> None:
        """Update the context with the generated story."""
        context.story = story
        context._update_timestamp()

    def calculate_word_count(self, text: str) -> int:
        """Calculate word count for the given text."""
        # Remove markdown formatting and count words
        clean_text = re.sub(r"[#*_`\[\]()]", "", text)
        words = clean_text.split()
        return len(words)

    def calculate_reading_time(self, word_count: int) -> str:
        """Calculate estimated reading time in minutes."""
        # Average reading speed for children: 150-200 words per minute
        # Use 175 words per minute as a reasonable estimate
        minutes = max(1, round(word_count / 175))
        if minutes == 1:
            return "1 minute"
        return f"{minutes} minutes"
