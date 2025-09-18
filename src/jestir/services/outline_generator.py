"""Outline generation service using OpenAI for story structure creation."""

from pathlib import Path

from openai import OpenAI

from ..models.api_config import CreativeAPIConfig
from ..models.story_context import StoryContext
from .length_validator import LengthValidator
from .template_loader import TemplateLoader
from .token_tracker import TokenTracker


class OutlineGenerator:
    """Generates story outlines from context using OpenAI."""

    def __init__(
        self,
        config: CreativeAPIConfig | None = None,
        template_loader: TemplateLoader | None = None,
        token_tracker: TokenTracker | None = None,
        length_validator: LengthValidator | None = None,
    ):
        """Initialize the outline generator with OpenAI configuration."""
        self.config = config or self._load_config_from_env()
        self.client = OpenAI(api_key=self.config.api_key, base_url=self.config.base_url)
        self.template_loader = template_loader or TemplateLoader()
        self.token_tracker = token_tracker or TokenTracker()
        self.length_validator = length_validator or LengthValidator()

    def _load_config_from_env(self) -> CreativeAPIConfig:
        """Load configuration from environment variables."""
        import os

        return CreativeAPIConfig(
            api_key=os.getenv("OPENAI_CREATIVE_API_KEY", ""),
            base_url=os.getenv("OPENAI_CREATIVE_BASE_URL", "https://api.openai.com/v1"),
            model=os.getenv("OPENAI_CREATIVE_MODEL", "gpt-4o-mini"),
            max_tokens=int(os.getenv("OPENAI_CREATIVE_MAX_TOKENS", "2000")),
            temperature=float(os.getenv("OPENAI_CREATIVE_TEMPERATURE", "0.7")),
        )

    def generate_outline(self, context: StoryContext) -> str:
        """Generate a story outline from the given context."""
        prompt = self._build_outline_prompt(context)

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert children's story writer who creates engaging, age-appropriate story outlines with clear structure and moral lessons.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )

            # Track token usage
            if hasattr(response, "usage") and response.usage:
                self.token_tracker.track_usage(
                    service="outline_generator",
                    operation="generate_outline",
                    model=self.config.model,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    input_text=str(context.model_dump()),
                    output_text=response.choices[0].message.content or "",
                )

            content = response.choices[0].message.content
            if content is None:
                return self._fallback_outline(context)

            outline = self._format_outline(content)

            # Validate and optimize outline length
            length_spec = context.get_effective_length_spec()
            validation_result = self.length_validator.validate_outline_length(
                outline,
                length_spec,
            )

            if validation_result["adjustment_needed"]:
                # Try to optimize the outline
                outline = self.length_validator.optimize_outline_for_length(
                    outline,
                    length_spec,
                )

            return outline

        except Exception as e:
            # Fallback to basic outline if OpenAI fails
            return self._fallback_outline(context)

    def _build_outline_prompt(self, context: StoryContext) -> str:
        """Build the prompt for outline generation using templates."""
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

            # Get length specification
            length_spec = context.get_effective_length_spec()

            # Prepare context for template
            template_context = {
                "genre": context.settings.get("genre", "adventure"),
                "tone": context.settings.get("tone", "gentle"),
                "length": context.settings.get("length", "short"),
                "target_word_count": length_spec.get_target_word_count(),
                "target_reading_time": length_spec.get_target_reading_time(),
                "length_type": length_spec.length_type,
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
            }

            # Load and render template
            return self.template_loader.render_template(
                "prompts/user_prompts/outline_generation.txt",
                template_context,
            )
        except Exception as e:
            # Fallback to hardcoded prompt if template loading fails
            return self._fallback_outline_prompt(context)

    def _fallback_outline_prompt(self, context: StoryContext) -> str:
        """Fallback outline prompt when templates fail."""
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

        return f"""Create a detailed story outline for a {context.settings.get("genre", "adventure")} bedtime story with a {context.settings.get("tone", "gentle")} tone.

**Story Requirements:**
- Genre: {context.settings.get("genre", "adventure")}
- Tone: {context.settings.get("tone", "gentle")}
- Length: {context.settings.get("length", "short")}
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

**Requirements for the outline:**
1. Create a clear 3-act structure (Beginning, Middle, End)
2. Include 4-6 main scenes/events
3. Ensure age-appropriate content
4. Include character development and growth
5. Add a clear moral lesson or positive message
6. Make it engaging and suitable for bedtime reading
7. Use markdown formatting with clear headings

**Format the outline as:**
# Story Outline: [Title]

## Act I: Beginning
### Scene 1: [Scene Name]
- [Brief description of what happens]
- [Character development/conflict introduction]

### Scene 2: [Scene Name]
- [Brief description of what happens]
- [Plot development]

## Act II: Middle
### Scene 3: [Scene Name]
- [Brief description of what happens]
- [Rising action/conflict development]

### Scene 4: [Scene Name]
- [Brief description of what happens]
- [Character growth/challenges]

### Scene 5: [Scene Name]
- [Brief description of what happens]
- [Climax preparation]

## Act III: End
### Scene 6: [Scene Name]
- [Brief description of what happens]
- [Resolution and moral lesson]

## Key Themes
- [Theme 1]
- [Theme 2]

## Moral Lesson
[Clear, age-appropriate moral lesson]

Generate the outline now:"""

    def _format_outline(self, content: str) -> str:
        """Format the generated outline content."""
        # Clean up the content
        content = content.strip()

        # Ensure it starts with a proper heading
        if not content.startswith("#"):
            content = f"# Story Outline\n\n{content}"

        # Add some basic formatting improvements
        lines = content.split("\n")
        formatted_lines = []

        for line in lines:
            line = line.strip()
            if line:
                formatted_lines.append(line)
            else:
                formatted_lines.append("")

        return "\n".join(formatted_lines)

    def _fallback_outline(self, context: StoryContext) -> str:
        """Generate a basic fallback outline when OpenAI fails."""
        # Extract main character
        characters = [e for e in context.entities.values() if e.type == "character"]
        main_character = characters[0].name if characters else "The Hero"

        # Get plot points
        plot_points = context.plot_points
        main_plot = plot_points[0] if plot_points else "goes on an adventure"

        return f"""# Story Outline: {main_character}'s Adventure

## Act I: Beginning
### Scene 1: The Setup
- {main_character} is introduced
- The adventure begins when they {main_plot}

### Scene 2: The Call to Adventure
- {main_character} faces their first challenge
- They must make an important decision

## Act II: Middle
### Scene 3: The Journey
- {main_character} encounters obstacles
- They learn important lessons along the way

### Scene 4: The Challenge
- {main_character} faces their biggest test
- They must overcome their fears

### Scene 5: The Turning Point
- {main_character} discovers inner strength
- The situation begins to improve

## Act III: End
### Scene 6: The Resolution
- {main_character} achieves their goal
- They return home wiser and stronger

## Key Themes
- Courage and determination
- The importance of trying your best

## Moral Lesson
Even when things seem difficult, with courage and determination, you can overcome any challenge and achieve your goals.
"""

    def load_context_from_file(self, context_file: str) -> StoryContext:
        """Load a StoryContext from a YAML file."""
        import yaml

        context_path = Path(context_file)
        if not context_path.exists():
            raise FileNotFoundError(f"Context file not found: {context_file}")

        with open(context_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return StoryContext(**data)

    def save_outline_to_file(self, outline: str, output_file: str) -> None:
        """Save the outline to a markdown file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(outline)

    def update_context_with_outline(self, context: StoryContext, outline: str) -> None:
        """Update the context with the generated outline."""
        context.outline = outline
        context._update_timestamp()
