# Template System Examples

This directory contains example context files that demonstrate how to use the Jestir template system effectively.

## Overview

The template system allows you to customize story generation prompts without changing code. Templates use `{{variable}}` syntax for variable substitution, and each template includes documentation showing what variables are available.

## Example Files

### 1. `basic_adventure.yaml`
A simple adventure story featuring:
- **Genre**: Adventure
- **Tone**: Gentle
- **Length**: Short
- **Key Elements**: Brave rabbit protagonist, magical quest, mentor character
- **Template Variables Used**: All standard variables for outline and story generation

### 2. `fantasy_quest.yaml`
A more complex fantasy story featuring:
- **Genre**: Fantasy
- **Tone**: Exciting
- **Length**: Medium
- **Key Elements**: Wizard apprentice, dragon ally, evil antagonist, magical artifacts
- **Template Variables Used**: Extended character and location descriptions

### 3. `simple_friendship.yaml`
A gentle friendship story featuring:
- **Genre**: Friendship
- **Tone**: Gentle
- **Length**: Very Short
- **Key Elements**: Animal characters, helping others, simple plot
- **Template Variables Used**: Basic variables with focus on character relationships

## How to Use These Examples

### 1. Generate Context from Text
```bash
# Use the CLI to generate context from natural language
python -m jestir context "A brave little rabbit named Thumper goes on an adventure to find the magical carrot that will save his village from the great drought." -o my_context.yaml
```

### 2. Use Pre-made Context Files
```bash
# Generate outline from example context
python -m jestir outline examples/context_examples/basic_adventure.yaml -o my_outline.md

# Generate story from outline and context
python -m jestir write my_outline.md -c examples/context_examples/basic_adventure.yaml -o my_story.md
```

### 3. Customize Templates
You can modify the template files in `templates/prompts/` to change how stories are generated:

- **User Prompts**: Control the detailed instructions sent to the AI
- **System Prompts**: Set the AI's role and behavior
- **Include Templates**: Define how specific character and location types are described

### 4. Validate Templates
```bash
# Check all templates for issues
python -m jestir validate-templates

# Get detailed validation results
python -m jestir validate-templates --verbose
```

## Template Variable Reference

### Common Variables Used in Templates

#### Story Settings
- `{{genre}}` - The story genre (adventure, fantasy, mystery, etc.)
- `{{tone}}` - The emotional tone (gentle, exciting, mysterious, etc.)
- `{{length}}` - The desired story length (short, medium, long, etc.)
- `{{age_appropriate}}` - Whether content is age-appropriate (true/false)
- `{{morals}}` - Comma-separated list of moral lessons to include

#### Content Variables
- `{{characters}}` - Formatted list of character descriptions
- `{{locations}}` - Formatted list of location descriptions
- `{{items}}` - Formatted list of item/object descriptions
- `{{plot_points}}` - Formatted list of key plot points
- `{{user_inputs}}` - Formatted list of original user requests

#### Story Generation Specific
- `{{target_word_count}}` - Target number of words for the story
- `{{outline}}` - The complete story outline to follow

#### Context Extraction Specific
- `{{input_text}}` - The original story input text from the user

## Template Documentation Format

Templates include documentation using the format:
```html
<!-- Template Variables:
{{variable_name#Description of what this variable contains}}
-->
```

This makes it easy to understand what each variable is for and how to use it.

## Best Practices

1. **Start Simple**: Begin with basic examples and gradually add complexity
2. **Use Descriptive Names**: Make entity names and descriptions clear and memorable
3. **Include Relationships**: Define how characters and locations connect to each other
4. **Set Clear Morals**: Specify the lessons you want the story to teach
5. **Validate Templates**: Run `validate-templates` regularly to catch issues early

## Troubleshooting

### Common Issues
- **Missing Variables**: Use `validate-templates --verbose` to see what's missing
- **Template Syntax**: Ensure variables use `{{variable}}` format
- **File Paths**: Check that template files exist in the correct directories
- **YAML Format**: Validate YAML syntax in context files

### Getting Help
- Run `python -m jestir --help` for general help
- Run `python -m jestir validate-templates --help` for template validation help
- Check the template files themselves for variable documentation
