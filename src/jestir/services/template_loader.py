"""Template loading service for prompt management."""

import contextlib
import logging
import re
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TemplateLoader:
    """Loads and processes templates with variable substitution."""

    def __init__(self, templates_dir: str | None = None):
        """Initialize the template loader with templates directory."""
        if templates_dir is None:
            # Default to templates directory in project root
            project_root = Path(__file__).parent.parent.parent.parent
            templates_dir = str(project_root / "templates")

        self.templates_dir = Path(templates_dir)
        self._template_cache: dict[str, str] = {}

    def load_template(self, template_path: str) -> str:
        """Load a template from file with caching."""
        template_file = self.templates_dir / template_path

        if not template_file.exists():
            available_templates = self._get_available_template_list()
            raise FileNotFoundError(
                f"Template file not found: {template_path}\n"
                f"Expected location: {template_file}\n"
                f"Available templates: {available_templates}",
            )

        # Check cache first
        cache_key = str(template_file)
        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        try:
            # Load template
            with open(template_file, encoding="utf-8") as f:
                content = f.read()

            # Cache the template
            self._template_cache[cache_key] = content
            return content

        except PermissionError:
            raise PermissionError(
                f"Cannot read template file: {template_path}\n"
                f"Check file permissions for: {template_file}",
            )
        except UnicodeDecodeError as e:
            raise ValueError(
                f"Invalid file encoding in template: {template_path}\n"
                f"Template files must be UTF-8 encoded. Error: {e}",
            )

    def render_template(self, template_path: str, context: dict[str, Any]) -> str:
        """Render a template with variable substitution."""
        start_time = time.time()

        try:
            template_content = self.load_template(template_path)
            result = self._substitute_variables(template_content, context)

            # Record successful metrics
            processing_time = (
                time.time() - start_time
            ) * 1000  # Convert to milliseconds
            self._record_template_metrics(
                template_path,
                processing_time,
                len(template_content),
                len(context),
                success=True,
            )

            return result

        except Exception as e:
            # Record failed metrics
            processing_time = (time.time() - start_time) * 1000
            template_content = ""
            with contextlib.suppress(BaseException):
                template_content = self.load_template(template_path)

            self._record_template_metrics(
                template_path,
                processing_time,
                len(template_content),
                len(context),
                success=False,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise

    def _substitute_variables(self, template: str, context: dict[str, Any]) -> str:
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
            logger.warning(f"Template variable '{key}' not found in context")
            return f"{{{{{full_key}}}}}"  # Keep the original placeholder with documentation

        # Pattern to match {{key}} variables (including those with # documentation)
        pattern = r"\{\{([^}]+)\}\}"
        return re.sub(pattern, replace_variable, template)

    def _record_template_metrics(
        self,
        template_path: str,
        processing_time_ms: float,
        template_size_bytes: int,
        variable_count: int,
        success: bool,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Record template processing metrics."""
        try:
            from .template_monitor import record_template_metrics

            record_template_metrics(
                template_path,
                processing_time_ms,
                template_size_bytes,
                variable_count,
                success,
                error_type,
                error_message,
            )
        except ImportError:
            # Monitoring not available, skip silently
            pass

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

    def get_available_templates(self) -> dict[str, list]:
        """Get list of available templates by category."""
        templates: dict[str, list] = {
            "system_prompts": [],
            "user_prompts": [],
            "includes": [],
        }

        for category in templates:
            category_dir = self.templates_dir / "prompts" / category
            if category_dir.exists():
                for file_path in category_dir.glob("*.txt"):
                    templates[category].append(file_path.stem)

        return templates

    def validate_template(
        self,
        template_path: str,
        required_vars: list,
    ) -> dict[str, Any]:
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

    def validate_template_syntax(self, template_path: str) -> dict[str, Any]:
        """Validate template syntax and return detailed analysis."""
        try:
            template_content = self.load_template(template_path)
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "syntax_errors": [f"Failed to load template: {e}"],
                "variables": [],
                "warnings": [],
            }

        syntax_errors = []
        warnings = []
        variables = []

        # Find all variables in template (including empty ones)
        pattern = r"\{\{([^}]*)\}\}"
        found_vars_raw = re.findall(pattern, template_content)

        # Analyze each variable
        for var in found_vars_raw:
            var_name = var.split("#")[0].strip()
            variables.append(
                {
                    "raw": var,
                    "name": var_name,
                    "has_documentation": "#" in var,
                    "documentation": var.split("#")[1].strip() if "#" in var else None,
                },
            )

            # Check for common syntax issues
            if not var_name:
                syntax_errors.append(f"Empty variable name: {{{{ {var} }}}}")
            elif (
                " " in var_name
                and not var_name.startswith(" ")
                and not var_name.endswith(" ")
            ):
                warnings.append(
                    f"Variable name contains spaces: '{var_name}' - consider using underscores",
                )
            elif var_name.startswith(" ") or var_name.endswith(" "):
                syntax_errors.append(
                    f"Variable name has leading/trailing spaces: '{var_name}'",
                )

        # Check for unmatched braces
        open_braces = template_content.count("{{")
        close_braces = template_content.count("}}")
        if open_braces != close_braces:
            syntax_errors.append(
                f"Mismatched braces: {open_braces} opening, {close_braces} closing",
            )

        # Check for nested braces (not supported)
        nested_pattern = r"\{\{[^}]*\{\{[^}]*\}\}[^}]*\}\}"
        if re.search(nested_pattern, template_content):
            syntax_errors.append("Nested braces detected - this is not supported")

        # Check for common typos
        common_typos = {
            "{{": ["{", "{[", "{{{"],
            "}}": ["}", "}]", "}}}"],
        }

        for correct, typos in common_typos.items():
            for typo in typos:
                if typo in template_content and correct not in template_content:
                    warnings.append(f"Possible typo: '{typo}' should be '{correct}'")

        return {
            "valid": len(syntax_errors) == 0,
            "syntax_errors": syntax_errors,
            "warnings": warnings,
            "variables": variables,
            "variable_count": len(variables),
            "template_length": len(template_content),
            "line_count": len(template_content.splitlines()),
        }

    def validate_template_with_context(
        self,
        template_path: str,
        context: dict[str, Any],
        required_vars: list | None = None,
    ) -> dict[str, Any]:
        """Validate template against provided context and required variables."""
        # First validate syntax
        syntax_result = self.validate_template_syntax(template_path)
        if not syntax_result["valid"]:
            return {
                "valid": False,
                "error_type": "syntax",
                "syntax_result": syntax_result,
                "context_validation": None,
            }

        # Get variables from template
        template_vars = {var["name"] for var in syntax_result["variables"]}

        # Check against required variables if provided
        missing_required: set[str] = set()
        if required_vars:
            missing_required = set(required_vars) - template_vars

        # Check context coverage
        missing_in_context = template_vars - set(context.keys())
        extra_in_context = set(context.keys()) - template_vars

        # Test rendering
        rendering_errors = []
        try:
            rendered = self.render_template(template_path, context)
            # Check for unresolved variables after rendering
            pattern = r"\{\{([^}]+)\}\}"
            unresolved = re.findall(pattern, rendered)
            if unresolved:
                rendering_errors.append(
                    f"Unresolved variables after rendering: {unresolved}",
                )
        except Exception as e:
            rendering_errors.append(f"Rendering failed: {e}")

        context_validation = {
            "missing_required": list(missing_required),
            "missing_in_context": list(missing_in_context),
            "extra_in_context": list(extra_in_context),
            "rendering_errors": rendering_errors,
            "context_coverage": len(template_vars - missing_in_context)
            / len(template_vars)
            if template_vars
            else 1.0,
        }

        return {
            "valid": len(missing_required) == 0 and len(rendering_errors) == 0,
            "syntax_result": syntax_result,
            "context_validation": context_validation,
            "overall_coverage": context_validation["context_coverage"],
        }

    def _get_available_template_list(self) -> str:
        """Get a formatted list of available templates for error messages."""
        try:
            templates = self.get_available_templates()
            template_list = []

            for category, template_names in templates.items():
                for name in template_names:
                    template_list.append(f"{category}/{name}.txt")

            if template_list:
                return ", ".join(sorted(template_list))
            return "No templates found"
        except Exception:
            return "Unable to list templates"
