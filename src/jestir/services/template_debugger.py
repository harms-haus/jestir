"""Template debugging and analysis service."""

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .template_loader import TemplateLoader


@dataclass
class TemplateAnalysis:
    """Results of template analysis."""

    template_path: str
    analysis_time: float
    variable_count: int
    complexity_score: float
    potential_issues: list[str]
    recommendations: list[str]
    performance_metrics: dict[str, Any]


class TemplateDebugger:
    """Advanced template debugging and analysis service."""

    def __init__(self, template_loader: TemplateLoader | None = None):
        """Initialize the template debugger."""
        self.template_loader = template_loader or TemplateLoader()
        self._analysis_cache: dict[str, TemplateAnalysis] = {}

    def analyze_template(
        self,
        template_path: str,
        force_refresh: bool = False,
    ) -> TemplateAnalysis:
        """Perform comprehensive analysis of a template."""
        cache_key = str(Path(template_path).resolve())

        if not force_refresh and cache_key in self._analysis_cache:
            return self._analysis_cache[cache_key]

        start_time = time.time()

        try:
            # Load template content
            template_content = self.template_loader.load_template(template_path)

            # Analyze variables
            variables = self._analyze_variables(template_content)

            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(
                template_content,
                variables,
            )

            # Identify potential issues
            potential_issues = self._identify_potential_issues(
                template_content,
                variables,
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(
                template_content,
                variables,
                potential_issues,
            )

            # Performance metrics
            performance_metrics = self._calculate_performance_metrics(
                template_content,
                variables,
            )

            analysis_time = time.time() - start_time

            analysis = TemplateAnalysis(
                template_path=template_path,
                analysis_time=analysis_time,
                variable_count=len(variables),
                complexity_score=complexity_score,
                potential_issues=potential_issues,
                recommendations=recommendations,
                performance_metrics=performance_metrics,
            )

            # Cache the analysis
            self._analysis_cache[cache_key] = analysis

            return analysis

        except Exception as e:
            analysis_time = time.time() - start_time
            return TemplateAnalysis(
                template_path=template_path,
                analysis_time=analysis_time,
                variable_count=0,
                complexity_score=0.0,
                potential_issues=[f"Analysis failed: {e}"],
                recommendations=["Fix template loading issues before analysis"],
                performance_metrics={},
            )

    def _analyze_variables(self, template_content: str) -> list[dict[str, Any]]:
        """Analyze template variables in detail."""
        pattern = r"\{\{([^}]+)\}\}"
        found_vars_raw = re.findall(pattern, template_content)

        variables = []
        for var in found_vars_raw:
            var_name = var.split("#")[0].strip()
            has_doc = "#" in var
            documentation = var.split("#")[1].strip() if has_doc else None

            # Analyze variable usage patterns
            usage_count = template_content.count(f"{{{{{var}}}}}")

            # Check for naming conventions
            naming_issues = []
            if " " in var_name:
                naming_issues.append("contains spaces")
            if var_name.startswith("_") or var_name.endswith("_"):
                naming_issues.append("starts/ends with underscore")
            if not var_name.replace("_", "").replace("-", "").isalnum():
                naming_issues.append("contains special characters")

            variables.append(
                {
                    "raw": var,
                    "name": var_name,
                    "has_documentation": has_doc,
                    "documentation": documentation,
                    "usage_count": usage_count,
                    "naming_issues": naming_issues,
                    "is_required": not var_name.startswith("optional_"),
                    "is_conditional": "if_" in var_name or "when_" in var_name,
                },
            )

        return variables

    def _calculate_complexity_score(
        self,
        template_content: str,
        variables: list[dict[str, Any]],
    ) -> float:
        """Calculate template complexity score (0-100)."""
        score = 0.0

        # Base score from variable count
        score += min(len(variables) * 2, 40)  # Max 40 points for variables

        # Length complexity
        content_length = len(template_content)
        if content_length > 1000:
            score += 10
        if content_length > 5000:
            score += 10

        # Line complexity
        line_count = len(template_content.splitlines())
        if line_count > 20:
            score += 5
        if line_count > 50:
            score += 5

        # Variable complexity
        for var in variables:
            if var["usage_count"] > 3:
                score += 2  # Repeated variables
            if var["naming_issues"]:
                score += 1  # Naming issues
            if not var["has_documentation"]:
                score += 0.5  # Missing documentation

        # Nested structure complexity
        if "{{" in template_content and "}}" in template_content:
            # Check for complex patterns
            if re.search(r"\{\{[^}]*\s+\{\{[^}]*\}\}[^}]*\}\}", template_content):
                score += 15  # Nested patterns (even if not supported)

        return min(score, 100.0)

    def _identify_potential_issues(
        self,
        template_content: str,
        variables: list[dict[str, Any]],
    ) -> list[str]:
        """Identify potential issues with the template."""
        issues = []

        # Syntax issues
        open_braces = template_content.count("{{")
        close_braces = template_content.count("}}")
        if open_braces != close_braces:
            issues.append(
                f"Mismatched braces: {open_braces} opening, {close_braces} closing",
            )

        # Variable issues
        for var in variables:
            if not var["name"]:
                issues.append("Empty variable name found")
            elif var["naming_issues"]:
                issues.append(
                    f"Variable '{var['name']}' has naming issues: {', '.join(var['naming_issues'])}",
                )
            elif not var["has_documentation"] and var["is_required"]:
                issues.append(f"Required variable '{var['name']}' lacks documentation")

        # Performance issues
        if len(template_content) > 10000:
            issues.append("Template is very large (>10KB) - consider splitting")

        if len(variables) > 20:
            issues.append("Template has many variables (>20) - consider simplifying")

        # Duplicate variables
        var_names = [var["name"] for var in variables]
        duplicates = [name for name in set(var_names) if var_names.count(name) > 1]
        if duplicates:
            issues.append(f"Duplicate variable names: {', '.join(duplicates)}")

        # Unused variables (variables defined but not used)
        for var in variables:
            if var["usage_count"] == 0:
                issues.append(f"Variable '{var['name']}' is defined but never used")

        return issues

    def _generate_recommendations(
        self,
        template_content: str,
        variables: list[dict[str, Any]],
        issues: list[str],
    ) -> list[str]:
        """Generate recommendations for improving the template."""
        recommendations = []

        # Variable recommendations
        undocumented_vars = [
            var
            for var in variables
            if not var["has_documentation"] and var["is_required"]
        ]
        if undocumented_vars:
            recommendations.append(
                f"Add documentation for {len(undocumented_vars)} variables",
            )

        # Naming recommendations
        bad_named_vars = [var for var in variables if var["naming_issues"]]
        if bad_named_vars:
            recommendations.append(
                "Improve variable naming conventions (use underscores, avoid spaces)",
            )

        # Structure recommendations
        if len(template_content) > 5000:
            recommendations.append(
                "Consider splitting large template into smaller, focused templates",
            )

        if len(variables) > 15:
            recommendations.append(
                "Consider reducing variable count or grouping related variables",
            )

        # Performance recommendations
        if len(template_content) > 10000:
            recommendations.append(
                "Large template may impact performance - consider optimization",
            )

        # Documentation recommendations
        if not any(var["has_documentation"] for var in variables):
            recommendations.append(
                "Add documentation to template variables for better maintainability",
            )

        # Organization recommendations
        if len(template_content.splitlines()) > 30:
            recommendations.append(
                "Consider organizing template into logical sections with comments",
            )

        return recommendations

    def _calculate_performance_metrics(
        self,
        template_content: str,
        variables: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Calculate performance-related metrics."""
        return {
            "template_size_bytes": len(template_content.encode("utf-8")),
            "template_size_chars": len(template_content),
            "line_count": len(template_content.splitlines()),
            "variable_count": len(variables),
            "average_variable_length": sum(len(var["name"]) for var in variables)
            / len(variables)
            if variables
            else 0,
            "max_variable_length": max(len(var["name"]) for var in variables)
            if variables
            else 0,
            "documentation_coverage": sum(
                1 for var in variables if var["has_documentation"]
            )
            / len(variables)
            if variables
            else 0,
            "repeated_variables": sum(1 for var in variables if var["usage_count"] > 1),
            "estimated_rendering_time_ms": len(template_content) * 0.001
            + len(variables) * 0.1,  # Rough estimate
        }

    def debug_template_rendering(
        self,
        template_path: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Debug template rendering with detailed analysis."""
        start_time = time.time()

        try:
            # Test rendering
            rendered = self.template_loader.render_template(template_path, context)
            rendering_time = time.time() - start_time

            # Analyze results
            unresolved_vars = re.findall(r"\{\{([^}]+)\}\}", rendered)

            # Calculate coverage
            template_analysis = self.analyze_template(template_path)
            # Get variables from the template analysis - we need to re-analyze to get variables
            variables = self._analyze_variables(
                self.template_loader.load_template(template_path),
            )
            template_vars = {var["name"] for var in variables}
            context_vars = set(context.keys())
            coverage = (
                len(template_vars & context_vars) / len(template_vars)
                if template_vars
                else 1.0
            )

            return {
                "success": True,
                "rendering_time_ms": rendering_time * 1000,
                "rendered_length": len(rendered),
                "unresolved_variables": unresolved_vars,
                "context_coverage": coverage,
                "variables_used": len(template_vars & context_vars),
                "variables_total": len(template_vars),
                "performance_score": self._calculate_rendering_performance_score(
                    rendering_time,
                    len(rendered),
                ),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "rendering_time_ms": (time.time() - start_time) * 1000,
                "rendered_length": 0,
                "unresolved_variables": [],
                "context_coverage": 0.0,
                "variables_used": 0,
                "variables_total": 0,
                "performance_score": 0.0,
            }

    def _calculate_rendering_performance_score(
        self,
        rendering_time: float,
        rendered_length: int,
    ) -> float:
        """Calculate performance score for rendering (0-100)."""
        # Base score
        score = 100.0

        # Time penalty
        if rendering_time > 0.1:  # > 100ms
            score -= 20
        if rendering_time > 0.5:  # > 500ms
            score -= 30

        # Size penalty
        if rendered_length > 10000:  # > 10KB
            score -= 10
        if rendered_length > 50000:  # > 50KB
            score -= 20

        return max(score, 0.0)

    def compare_templates(self, template_paths: list[str]) -> dict[str, Any]:
        """Compare multiple templates and provide analysis."""
        analyses = [self.analyze_template(path) for path in template_paths]

        return {
            "template_count": len(template_paths),
            "average_complexity": sum(a.complexity_score for a in analyses)
            / len(analyses),
            "total_variables": sum(a.variable_count for a in analyses),
            "common_issues": self._find_common_issues(analyses),
            "performance_comparison": self._compare_performance(analyses),
            "recommendations": self._generate_comparison_recommendations(analyses),
        }

    def _find_common_issues(self, analyses: list[TemplateAnalysis]) -> list[str]:
        """Find common issues across multiple template analyses."""
        all_issues = []
        for analysis in analyses:
            all_issues.extend(analysis.potential_issues)

        # Count issue frequency
        issue_counts: dict[str, int] = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1

        # Return issues that appear in multiple templates
        common_issues = [issue for issue, count in issue_counts.items() if count > 1]
        return sorted(common_issues, key=lambda x: issue_counts[x], reverse=True)

    def _compare_performance(self, analyses: list[TemplateAnalysis]) -> dict[str, Any]:
        """Compare performance metrics across templates."""
        if not analyses:
            return {}

        sizes = [a.performance_metrics.get("template_size_bytes", 0) for a in analyses]
        variables = [a.variable_count for a in analyses]
        complexities = [a.complexity_score for a in analyses]

        return {
            "size_range": (min(sizes), max(sizes)),
            "variable_range": (min(variables), max(variables)),
            "complexity_range": (min(complexities), max(complexities)),
            "largest_template": max(
                analyses,
                key=lambda a: a.performance_metrics.get("template_size_bytes", 0),
            ).template_path,
            "most_complex": max(
                analyses,
                key=lambda a: a.complexity_score,
            ).template_path,
            "most_variables": max(
                analyses,
                key=lambda a: a.variable_count,
            ).template_path,
        }

    def _generate_comparison_recommendations(
        self,
        analyses: list[TemplateAnalysis],
    ) -> list[str]:
        """Generate recommendations based on template comparison."""
        recommendations = []

        if len(analyses) > 1:
            # Check for consistency
            variable_counts = [a.variable_count for a in analyses]
            if max(variable_counts) - min(variable_counts) > 10:
                recommendations.append(
                    "Template variable counts vary significantly - consider standardizing",
                )

            # Check for complexity consistency
            complexities = [a.complexity_score for a in analyses]
            if max(complexities) - min(complexities) > 30:
                recommendations.append(
                    "Template complexity varies significantly - consider balancing",
                )

        return recommendations

    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self._analysis_cache.clear()
