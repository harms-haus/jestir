# External APIs

## OpenAI API (Information Extraction)

- **Purpose:** Extract entities and relationships from natural language input
- **Documentation:** https://platform.openai.com/docs
- **Base URL(s):** https://api.openai.com/v1 (configurable via `OPENAI_EXTRACTION_BASE_URL` environment variable)
- **Authentication:** API key via `OPENAI_EXTRACTION_API_KEY` environment variable
- **Model:** Configurable via `OPENAI_EXTRACTION_MODEL` environment variable (default: gpt-4o-mini)
- **Max Tokens:** Configurable via `OPENAI_EXTRACTION_MAX_TOKENS` environment variable
- **Temperature:** Configurable via `OPENAI_EXTRACTION_TEMPERATURE` environment variable (default: 0.1)
- **Rate Limits:** 90,000 TPM for GPT-4, monitoring via TokenTracker
- **Recommended Models:** GPT-4o-mini, GPT-4o, gpt-oss:20b (for accuracy in structured data extraction)

**Key Endpoints Used:**

- `POST /chat/completions` - Entity and relationship extraction

## OpenAI API (Creative Generation)

- **Purpose:** Generate story outlines and creative content
- **Documentation:** https://platform.openai.com/docs
- **Base URL(s):** https://api.openai.com/v1 (configurable via `OPENAI_CREATIVE_BASE_URL` environment variable)
- **Authentication:** API key via `OPENAI_CREATIVE_API_KEY` environment variable
- **Model:** Configurable via `OPENAI_CREATIVE_MODEL` environment variable (default: gpt-4o)
- **Max Tokens:** Configurable via `OPENAI_CREATIVE_MAX_TOKENS` environment variable
- **Temperature:** Configurable via `OPENAI_CREATIVE_TEMPERATURE` environment variable (default: 0.7)
- **Rate Limits:** 90,000 TPM for GPT-4, monitoring via TokenTracker
- **Recommended Models:** GPT-4o, GPT-4, gpt-oss:120b (for creative quality and narrative coherence)

**Key Endpoints Used:**

- `POST /chat/completions` - Outline and story generation

**Integration Notes:** Retry logic with exponential backoff, timeout handling, streaming responses for long content

## Environment Variables Summary

### Information Extraction Endpoint
- `OPENAI_EXTRACTION_API_KEY` - API key for extraction endpoint
- `OPENAI_EXTRACTION_BASE_URL` - Base URL for extraction API (default: https://api.openai.com/v1)
- `OPENAI_EXTRACTION_MODEL` - Model for extraction (default: gpt-4o-mini)
- `OPENAI_EXTRACTION_MAX_TOKENS` - Maximum tokens for extraction requests
- `OPENAI_EXTRACTION_TEMPERATURE` - Temperature for extraction (default: 0.1)

### Creative Generation Endpoint
- `OPENAI_CREATIVE_API_KEY` - API key for creative endpoint
- `OPENAI_CREATIVE_BASE_URL` - Base URL for creative API (default: https://api.openai.com/v1)
- `OPENAI_CREATIVE_MODEL` - Model for creative generation (default: gpt-4o)
- `OPENAI_CREATIVE_MAX_TOKENS` - Maximum tokens for creative requests
- `OPENAI_CREATIVE_TEMPERATURE` - Temperature for creative generation (default: 0.7)

### Example Configuration
```bash
# Use different models for different tasks
export OPENAI_EXTRACTION_MODEL="gpt-oss:20b"
export OPENAI_CREATIVE_MODEL="gpt-oss:120b"

# Use different endpoints if needed
export OPENAI_EXTRACTION_BASE_URL="https://your-extraction-endpoint.com/v1"
export OPENAI_CREATIVE_BASE_URL="https://your-creative-endpoint.com/v1"

# Fine-tune parameters
export OPENAI_EXTRACTION_TEMPERATURE="0.1"  # Lower for consistent extraction
export OPENAI_CREATIVE_TEMPERATURE="0.8"    # Higher for more creativity
```
