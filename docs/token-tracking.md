# Token Usage Tracking

Jestir includes comprehensive token usage tracking to help you monitor and optimize your OpenAI API costs. This feature tracks token consumption across all API calls and provides detailed analytics and optimization suggestions.

## Features

- **Automatic Token Counting**: Tracks tokens for all OpenAI API calls across context generation, outline generation, and story writing
- **Cost Estimation**: Calculates costs based on current OpenAI pricing for different models
- **Usage Analytics**: Provides detailed breakdowns by service, operation, model, and time period
- **Optimization Suggestions**: Analyzes usage patterns and suggests cost-saving measures
- **Context Integration**: Stores token usage data in context.yaml files for complete history tracking
- **Export Capabilities**: Export detailed reports in JSON or YAML format

## Usage

### Basic Token Tracking

Token tracking is automatically enabled for all Jestir commands. No additional configuration is required.

```bash
# Generate context (tracks tokens automatically)
jestir context "A brave little girl goes on an adventure"

# Generate outline (tracks tokens automatically)
jestir outline context.yaml

# Write story (tracks tokens automatically)
jestir write outline.md
```

### Viewing Token Statistics

Use the `stats` command to view token usage statistics:

```bash
# Basic stats for current context
jestir stats

# Stats with optimization suggestions
jestir stats --suggestions

# Weekly report
jestir stats --period weekly

# Export report to file
jestir stats --export report.json --format json
```

### Command Options

- `--context, -c`: Context file to analyze (default: context.yaml)
- `--period, -p`: Report period (daily, weekly, monthly)
- `--format, -f`: Output format (table, json, yaml)
- `--export, -e`: Export report to file
- `--suggestions, -s`: Show optimization suggestions

## Token Usage Data

### Stored in Context Files

Token usage is automatically stored in your context.yaml files:

```yaml
metadata:
  token_usage:
    total_tokens: 2025
    total_cost_usd: 0.0147
    total_calls: 3
    last_updated: "2024-12-19T10:30:00"
    usage_history:
      - timestamp: "2024-12-19T10:30:00"
        service: "context_generator"
        operation: "extract_entities_and_relationships"
        model: "gpt-4o-mini"
        prompt_tokens: 150
        completion_tokens: 75
        total_tokens: 225
        cost_usd: 0.0001
        # ... more fields
```

### Usage Summary

The stats command provides comprehensive analytics:

```
📊 Token Usage Statistics (Monthly)
==================================================
Total Tokens: 2,025
Total Cost: $0.0147
Total API Calls: 3
Average Tokens per Call: 675.0
Average Cost per Call: $0.0049

📈 Usage by Service:
------------------------------
context_generator:
  Tokens: 225
  Cost: $0.0001
  Calls: 1
outline_generator:
  Tokens: 500
  Cost: $0.0002
  Calls: 1
story_writer:
  Tokens: 1,300
  Cost: $0.0145
  Calls: 1

🤖 Usage by Model:
------------------------------
gpt-4o-mini:
  Tokens: 725
  Cost: $0.0002
  Calls: 2
  Avg Tokens/Call: 362.5
gpt-4o:
  Tokens: 1,300
  Cost: $0.0145
  Calls: 1
  Avg Tokens/Call: 1300.0
```

## Cost Optimization

### Optimization Suggestions

The system analyzes your usage patterns and provides suggestions:

```
💡 Optimization Suggestions:
------------------------------
1. Consider using GPT-4o-mini for gpt-4o operations
   You've spent $0.01 on gpt-4o. GPT-4o-mini offers similar quality at much lower cost.
   Potential Savings: $0.01
   Action: Switch to gpt-4o-mini model in your API configuration

2. Optimize generate_story prompts
   generate_story uses 1300 tokens per call on average. Consider shortening prompts or using more specific instructions.
   Potential Savings: $0.00
   Action: Review and optimize prompt templates for this operation
```

### Cost-Saving Tips

1. **Use GPT-4o-mini for most operations**: It offers similar quality at much lower cost
2. **Optimize prompts**: Shorter, more specific prompts use fewer tokens
3. **Batch operations**: Process multiple stories together when possible
4. **Monitor usage**: Regular use of `jestir stats` helps identify cost patterns

## Model Pricing

Current pricing (as of December 2024) per 1K tokens:

| Model | Input | Output | Description |
|-------|-------|--------|-------------|
| gpt-4o | $0.005 | $0.015 | Most capable model |
| gpt-4o-mini | $0.00015 | $0.0006 | Fast and efficient |
| gpt-4 | $0.03 | $0.06 | High capability model |
| gpt-3.5-turbo | $0.0015 | $0.002 | Fast and cost-effective |

## Programmatic Usage

### Using TokenTracker Directly

```python
from jestir.services.token_tracker import TokenTracker

# Create tracker
tracker = TokenTracker()

# Track usage after API call
tracker.track_usage(
    service="my_service",
    operation="my_operation",
    model="gpt-4o-mini",
    prompt_tokens=100,
    completion_tokens=50,
    input_text="my input",
    output_text="my output"
)

# Generate report
report = tracker.generate_report(period="monthly")
print(f"Total cost: ${report.summary.total_cost_usd:.2f}")

# Save to context
tracker.save_usage_to_context("my_context.yaml")
```

### Custom Pricing Configuration

```python
from jestir.models.token_usage import TokenPricing
from jestir.services.token_tracker import TokenTracker

# Define custom pricing
custom_pricing = {
    "my-model": TokenPricing(
        model="my-model",
        input_price_per_1k=0.001,
        output_price_per_1k=0.002,
        description="My custom model"
    )
}

# Create tracker with custom pricing
tracker = TokenTracker(pricing_config=custom_pricing)
```

## Troubleshooting

### No Token Data

If you don't see token data in your stats:

1. Ensure you're using OpenAI API keys (not mock mode)
2. Check that your context file exists and contains token usage data
3. Verify that API calls are being made successfully

### High Costs

If you're seeing unexpectedly high costs:

1. Check which models you're using (`jestir stats` shows model breakdown)
2. Consider switching to gpt-4o-mini for most operations
3. Review your prompts for unnecessary verbosity
4. Use the optimization suggestions (`jestir stats --suggestions`)

### Export Issues

If export isn't working:

1. Ensure you have write permissions in the target directory
2. Check that the file extension matches the format (`.json` for JSON, `.yaml` for YAML)
3. Verify the export path is valid

## Integration with CI/CD

Token tracking data can be integrated into your CI/CD pipeline:

```bash
# Generate report in CI
jestir stats --format json --export token-report.json

# Check if costs exceed threshold
COST=$(jestir stats --format json | jq '.summary.total_cost_usd')
if (( $(echo "$COST > 1.0" | bc -l) )); then
    echo "Warning: Token costs exceeded $1.00 threshold"
    exit 1
fi
```

## Best Practices

1. **Regular Monitoring**: Run `jestir stats` regularly to track usage patterns
2. **Cost Alerts**: Set up monitoring for cost thresholds in production
3. **Model Selection**: Use gpt-4o-mini for most operations, gpt-4o only when needed
4. **Prompt Optimization**: Keep prompts concise and specific
5. **Batch Processing**: Process multiple stories together when possible
6. **Export Reports**: Regularly export reports for historical analysis

## Future Enhancements

Planned improvements include:

- Real-time cost monitoring dashboard
- Automated cost alerts and notifications
- Advanced analytics and trend analysis
- Integration with external monitoring tools
- Custom cost budgets and limits
- Usage forecasting and planning tools
