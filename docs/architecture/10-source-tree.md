# Source Tree

```plaintext
bedtime-story-generator/
├── src/
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py              # Entry point
│   │   ├── commands/            # CLI command definitions
│   │   │   ├── context.py
│   │   │   ├── outline.py
│   │   │   ├── story.py
│   │   │   └── entity.py
│   │   └── utils.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── context_generator.py
│   │   ├── outline_generator.py
│   │   ├── story_writer.py
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── entity_repository.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── entity.py
│   │   ├── relationship.py
│   │   └── story_context.py
│   ├── templates/
│   │   ├── __init__.py
│   │   └── template_manager.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── token_tracker.py
│   │   └── file_handler.py
│   └── config/
│       ├── __init__.py
│       └── settings.py
├── templates/               # External template files
│   ├── context/
│   │   ├── protagonist.txt
│   │   ├── antagonist.txt
│   │   └── location.txt
│   ├── outline/
│   │   └── default.txt
│   └── story/
│       └── default.txt
├── tests/
│   ├── unit/
│   │   ├── test_context_generator.py
│   │   ├── test_outline_generator.py
│   │   ├── test_story_writer.py
│   │   └── test_entity_repository.py
│   ├── integration/
│   │   ├── test_pipeline.py
│   │   └── test_lightrag_integration.py
│   └── fixtures/
│       ├── sample_context.yaml
│       └── mock_responses.json
├── output/                  # Generated stories (gitignored)
├── .env.example
├── .gitignore
├── pyproject.toml          # uv configuration
├── README.md
└── Makefile                # Common commands
```
