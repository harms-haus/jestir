"""Template loading service for prompt management."""

import re
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TemplateLoader:
    """Loads and processes templates with variable substitution."""

    def __init__(self, templates_dir: Optional[str] = None):
        """Initialize the template loader with templates directory."""
        if templates_dir is None:
            # Default to templates directory in project root
            project_root = Path(__file__).parent.parent.parent.parent
            templates_dir = str(project_root / "templates")

        self.templates_dir = Path(templates_dir)
        self._template_cache: Dict[str, str] = {}

    def load_template(self, template_path: str) -> str:
        """Load a template from file with caching."""
        template_file = self.templates_dir / template_path

        if not template_file.exists():
            raise FileNotFoundError(f"Template file not found: {template_file}")

        # Check cache first
        cache_key = str(template_file)
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        # Load template
        with open(template_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Cache the template
        self._template_cache[cache_key] = content
        return content

    def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """Render a template with variable substitution."""
        template_content = self.load_template(template_path)
        return self._substitute_variables(template_content, context)

    def _substitute_variables(self, template: str, context: Dict[str, Any]) -> str:
        """Substitute {{key}} variables in template with context values."""

        def replace_variable(match):
            full_key = match.group(1)
            # Extract the actual variable name (before # if present)
            key = full_key.split("#")[0].strip()
            if key in context:
                value = context[key]
                # Convert to string and handle None values
                if value is None:
                    return ""
                return str(value)
            else:
                logger.warning(f"Template variable '{key}' not found in context")
                return f"{{{{{full_key}}}}}"  # Keep the original placeholder with documentation

        # Pattern to match {{key}} variables (including those with # documentation)
        pattern = r"\{\{([^}]+)\}\}"
        return re.sub(pattern, replace_variable, template)

    def load_character_template(self, character_type: str) -> str:
        """Load a character-specific template."""
        template_path = f"prompts/includes/character_{character_type}.txt"
        return self.load_template(template_path)

    def load_location_template(self, location_type: str) -> str:
        """Load a location-specific template."""
        template_path = f"prompts/includes/location_{location_type}.txt"
        return self.load_template(template_path)

    def load_system_prompt(self, prompt_type: str) -> str:
        """Load a system prompt template."""
        template_path = f"prompts/system_prompts/{prompt_type}.txt"
        return self.load_template(template_path)

    def load_user_prompt(self, prompt_type: str) -> str:
        """Load a user prompt template."""
        template_path = f"prompts/user_prompts/{prompt_type}.txt"
        return self.load_template(template_path)

    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._template_cache.clear()

    def get_available_templates(self) -> Dict[str, list]:
        """Get list of available templates by category."""
        templates: Dict[str, list] = {
            "system_prompts": [],
            "user_prompts": [],
            "includes": [],
        }

        for category in templates.keys():
            category_dir = self.templates_dir / "prompts" / category
            if category_dir.exists():
                for file_path in category_dir.glob("*.txt"):
                    templates[category].append(file_path.stem)

        return templates

    def validate_template(
        self, template_path: str, required_vars: list
    ) -> Dict[str, Any]:
        """Validate that a template has all required variables."""
        template_content = self.load_template(template_path)

        # Find all variables in template
        pattern = r"\{\{([^}]+)\}\}"
        found_vars_raw = re.findall(pattern, template_content)

        # Extract variable names (before # if present)
        found_vars = set()
        for var in found_vars_raw:
            var_name = var.split("#")[0].strip()
            found_vars.add(var_name)

        # Check for missing required variables
        missing_vars = set(required_vars) - found_vars
        extra_vars = found_vars - set(required_vars)

        return {
            "valid": len(missing_vars) == 0,
            "missing_vars": list(missing_vars),
            "extra_vars": list(extra_vars),
            "found_vars": list(found_vars),
        }
