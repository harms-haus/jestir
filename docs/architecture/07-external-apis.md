# External APIs

## OpenAI API

- **Purpose:** Generate context, outlines, and stories using GPT models
- **Documentation:** https://platform.openai.com/docs
- **Base URL(s):** https://api.openai.com/v1 (configurable via `OPENAI_BASE_URL` environment variable)
- **Authentication:** API key via `OPENAI_API_KEY` environment variable
- **Rate Limits:** 90,000 TPM for GPT-4, monitoring via TokenTracker

**Key Endpoints Used:**

- `POST /chat/completions` - All content generation

**Integration Notes:** Retry logic with exponential backoff, timeout handling, streaming responses for long content
