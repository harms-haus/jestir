# Template Testing and Preview Guide

This guide covers the template testing and preview functionality in Jestir, which allows you to test templates before using them in story generation.

## Overview

The template testing system provides:
- Template syntax validation
- Variable substitution preview
- Context validation
- Performance analysis
- Debugging tools
- Dry-run mode for safe testing

## Basic Usage

### Testing a Template

```bash
# Basic template test with name substitution
jestir template prompts/user_prompts/story_generation.txt --name "Alice"

# Test with context file
jestir template prompts/user_prompts/story_generation.txt --context context.yaml

# Test with validation
jestir template prompts/user_prompts/story_generation.txt --validate

# Test with debug information
jestir template prompts/user_prompts/story_generation.txt --name "Alice" --debug

# Dry run mode (no API calls)
jestir template prompts/user_prompts/story_generation.txt --name "Alice" --dry-run
```

### Template Debugging

```bash
# Comprehensive template analysis
jestir debug-template prompts/user_prompts/story_generation.txt --analyze

# Performance analysis
jestir debug-template prompts/user_prompts/story_generation.txt --analyze --performance

# Compare multiple templates
jestir debug-template prompts/user_prompts/story_generation.txt --compare "prompts/user_prompts/outline_generation.txt,prompts/user_prompts/context_extraction.txt"
```

## Template Syntax

### Variable Syntax

Templates use `{{variable_name}}` syntax for variable substitution:

```text
Hello {{name}}! This is a {{genre}} story for {{age_appropriate}} children.
```

### Variable Documentation

You can add documentation to variables using the `#` syntax:

```text
Hello {{name # protagonist name}}! This is a {{genre # story genre}} story.
```

### Supported Variable Types

- **String values**: `{{name}}`
- **Lists**: `{{characters}}` (rendered as string representation)
- **Dictionaries**: `{{plot_points}}` (rendered as string representation)
- **None values**: Rendered as empty string

## Context Loading

### From Context Files

When using `--context`, the system extracts variables from YAML context files:

```yaml
# context.yaml
name: "Alice"
genre: "adventure"
age_appropriate: "5-8 years"
entities:
  - name: "Alice"
    description: "A brave young girl"
  - name: "Bob"
    description: "A friendly dragon"
```

The system automatically creates variables:
- `alice` → "Alice"
- `alice_description` → "A brave young girl"
- `bob` → "Bob"
- `bob_description` → "A friendly dragon"

### Default Test Variables

If no context is provided, default test variables are used:

```python
{
    'name': 'Test Character',
    'protagonist': 'Test Character',
    'character': 'Test Character',
    'genre': 'adventure',
    'tone': 'friendly',
    'length': 'short',
    'age_appropriate': '5-8 years',
    'morals': 'friendship and courage'
}
```

## Validation Features

### Syntax Validation

The `--validate` flag checks for:
- Mismatched braces (`{{` vs `}}`)
- Empty variable names
- Nested braces (not supported)
- Variable naming issues
- Common typos

### Context Validation

When context is provided, the system validates:
- Missing required variables
- Unresolved variables after rendering
- Context coverage percentage
- Extra unused variables

### Example Validation Output

```
Validating template syntax...
✅ Template syntax is valid
Found 3 template variables:
  • name # protagonist name
  • genre # story genre
  • age_appropriate # target age range

Template Statistics:
  Length: 156 characters
  Lines: 3
  Variables: 3

Template context validation passed
Context coverage: 100.0%
```

## Debugging Features

### Template Analysis

The `--analyze` flag provides comprehensive analysis:

```
📊 Template Analysis Results:
==================================================
Template: prompts/user_prompts/story_generation.txt
Analysis Time: 0.045s
Variable Count: 8
Complexity Score: 45.2/100

⚡ Performance Metrics:
------------------------------
Template Size: 2,456 bytes
Line Count: 12
Documentation Coverage: 75.0%
Repeated Variables: 2
Est. Rendering Time: 2.5ms

⚠️  Potential Issues (2):
------------------------------
  • Variable 'character_name' has naming issues: contains spaces
  • Required variable 'target_word_count' lacks documentation

💡 Recommendations (3):
------------------------------
  • Add documentation for 1 variables
  • Improve variable naming conventions (use underscores, avoid spaces)
  • Consider reducing variable count or grouping related variables
```

### Performance Analysis

Performance metrics include:
- Template size (bytes and characters)
- Line count
- Variable count
- Documentation coverage
- Estimated rendering time
- Performance score (0-100)

### Template Comparison

Compare multiple templates to identify:
- Common issues across templates
- Performance differences
- Complexity variations
- Consistency recommendations

## Error Handling

### Common Errors

1. **Template Not Found**
   ```
   ❌ Template Not Found: Template file not found: nonexistent.txt
   💡 Troubleshooting:
      • Check that template file 'nonexistent.txt' exists
      • Verify the file path is correct
      • Use 'jestir validate-templates' to see available templates
   ```

2. **Syntax Errors**
   ```
   ❌ Template syntax errors found:
     • Mismatched braces: 3 opening, 2 closing
     • Empty variable name: {{ }}
   ```

3. **Context Loading Issues**
   ```
   Warning: Could not load context file: invalid yaml
   Using default test variables
   ```

### Troubleshooting Tips

1. **Check template syntax**: Use `--validate` to identify syntax issues
2. **Verify file paths**: Ensure template files exist and are accessible
3. **Check context format**: Ensure YAML context files are valid
4. **Use debug mode**: Add `--debug` for detailed variable information
5. **Test with dry run**: Use `--dry-run` to test without API calls

## Best Practices

### Template Design

1. **Use descriptive variable names**: `{{protagonist_name}}` instead of `{{name}}`
2. **Add documentation**: `{{genre # story genre}}`
3. **Avoid spaces in variable names**: Use underscores instead
4. **Group related variables**: Consider template organization
5. **Keep templates focused**: Avoid overly complex templates

### Testing Workflow

1. **Start with syntax validation**: `jestir template template.txt --validate`
2. **Test with sample data**: `jestir template template.txt --name "Test"`
3. **Validate with real context**: `jestir template template.txt --context context.yaml`
4. **Use debug mode for issues**: `jestir template template.txt --debug`
5. **Analyze performance**: `jestir debug-template template.txt --analyze --performance`

### Performance Optimization

1. **Monitor template size**: Keep templates under 10KB for best performance
2. **Limit variable count**: Avoid templates with >20 variables
3. **Use caching**: Templates are automatically cached
4. **Profile rendering**: Use performance analysis to identify bottlenecks

## Integration with Story Generation

Template testing integrates seamlessly with the story generation pipeline:

1. **Test templates before use**: Validate templates before story generation
2. **Debug issues early**: Catch problems before they affect story quality
3. **Optimize performance**: Ensure templates render efficiently
4. **Maintain consistency**: Use comparison tools to keep templates aligned

## Examples

### Example 1: Basic Template Test

```bash
# Test a simple template
jestir template prompts/includes/character_protagonist.txt --name "Alice"

# Output:
Testing template: prompts/includes/character_protagonist.txt
Rendering template with 1 variables...
📝 Template Preview:
==================================================
Alice is a brave and curious protagonist who loves adventure and helping others.
==================================================
✅ All variables resolved successfully
✅ Template test completed successfully!
```

### Example 2: Complex Template with Context

```bash
# Test with full context
jestir template prompts/user_prompts/story_generation.txt --context context.yaml --validate --debug

# Output:
Testing template: prompts/user_prompts/story_generation.txt
Validating template syntax...
✅ Template syntax is valid
Found 8 template variables:
  • genre # story genre
  • tone # narrative tone
  • length # story length
  • target_word_count # desired word count
  • age_appropriate # target age range
  • morals # moral lessons
  • characters # character list
  • plot_points # story structure

Template Statistics:
  Length: 2,456 characters
  Lines: 12
  Variables: 8

Loading context from: context.yaml
Loaded 12 variables from context
Template context validation passed
Context coverage: 100.0%

Rendering template with 12 variables...
📝 Template Preview:
==================================================
[Full rendered template content]
==================================================

🔍 Variable Substitutions:
------------------------------
genre: adventure
tone: friendly
length: short
target_word_count: 500
age_appropriate: 5-8 years
morals: friendship and courage
characters: ['Alice', 'Bob', 'Charlie']
plot_points: {'beginning': 'meeting', 'middle': 'adventure', 'end': 'resolution'}

✅ All variables resolved successfully
✅ Template test completed successfully!
```

### Example 3: Debug Analysis

```bash
# Comprehensive analysis
jestir debug-template prompts/user_prompts/story_generation.txt --analyze --performance

# Output:
Debugging template: prompts/user_prompts/story_generation.txt
Performing comprehensive template analysis...

📊 Template Analysis Results:
==================================================
Template: prompts/user_prompts/story_generation.txt
Analysis Time: 0.045s
Variable Count: 8
Complexity Score: 45.2/100

⚡ Performance Metrics:
------------------------------
Template Size: 2,456 bytes
Line Count: 12
Documentation Coverage: 75.0%
Repeated Variables: 2
Est. Rendering Time: 2.5ms

✅ No potential issues found

💡 Recommendations (2):
------------------------------
  • Add documentation for 2 variables
  • Consider organizing template into logical sections with comments

✅ Template debugging completed successfully!
```

This comprehensive template testing system ensures your templates work correctly before being used in story generation, helping you create high-quality, reliable templates for your bedtime stories.
