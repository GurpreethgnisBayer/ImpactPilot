# Impact Estimate

A reproducible Streamlit app that turns plain-language R&D ideas into structured Impact Estimates grounded in PubMed evidence.

## Features

- **4-step workflow:** Idea → Evidence → Assumptions → Brief
- **LLM-powered MeSH query generation** - Automatically generates PubMed queries using Medical Subject Headings (MeSH) terms
- **PubMed evidence search** with auto-updating queries and advanced filters
- **LLM-powered inference** with support for:
  - Local Ollama
  - OpenAI-compatible endpoints
  - **Azure OpenAI** (with deployment-based configuration)
- **Directional estimates** with evidence labels (evidence-supported vs heuristic/ballpark)
- **Deterministic calculations** with TCO and productivity metrics
- **Markdown brief generation** with disclaimer and citations
- **Fail-loud configuration** with test connection button

## Installation

### Local Installation

```bash
pip install -r requirements.txt
```

### Docker Installation

```bash
# Build the Docker image
docker build -t impact-estimate .

# Run the container
docker run -p 8501:8501 impact-estimate

# Run with environment variables (optional)
docker run -p 8501:8501 \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  -e OLLAMA_MODEL=llama3.1:8b \
  impact-estimate
```

Access the app at: http://localhost:8501

## Usage

### Running Locally

```bash
streamlit run app.py
```

### Configuration

Set environment variables to prefill LLM provider settings:

**Ollama:**
- `OLLAMA_HOST` - Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL` - Ollama model name (default: llama3.1:8b)

**OpenAI-compatible:**
- `OPENAI_BASE_URL` - OpenAI-compatible API base URL
- `OPENAI_API_KEY` - API key for authentication
- `OPENAI_MODEL` - Model name (default: gpt-4)

**Azure OpenAI:**
- `AZURE_OPENAI_ENDPOINT` - Azure OpenAI endpoint (e.g., https://your-resource.openai.azure.com)
- `AZURE_OPENAI_API_KEY` - Azure OpenAI API key
- `AZURE_OPENAI_DEPLOYMENT` - Deployment name
- `AZURE_OPENAI_API_VERSION` - API version (default: 2024-02-15-preview)

**General:**
- `LLM_PROVIDER` - Provider to use: "ollama", "openai_compatible", or "azure"

### Workflow

1. **Step 1: Idea** - Enter R&D idea details (title, description, type, stage)
   - LLM automatically generates a MeSH-formatted PubMed query if configured
   - Falls back to keyword extraction if LLM unavailable
2. **Step 2: Evidence** - Search PubMed and select relevant articles
   - Auto-generated MeSH queries with Medical Subject Headings
   - Advanced filters (journal, author, date, publication types)
3. **Step 3: Assumptions** - Click "Infer" to generate directional estimates using LLM
   - Evidence-supported estimates include PMID citations and quotes
   - Heuristic/ballpark estimates clearly labeled as directional
4. **Step 4: Brief** - Generate and download comprehensive markdown impact estimate
   - Full ranges displayed (e.g., 10–20 hours/month)
   - Midpoint-based calculations for TCO and productivity
   - Disclaimer and citations included

## Testing

```bash
python -m pytest -q
```

All 80+ tests validate:
- Query suggestion and PubMed search
- LLM provider configuration and health checks
- Evidence extraction and numeric parsing
- Assumption labeling (evidence-supported vs heuristic)
- LLM wiring (ensures provider.generate is called)
- Calculator midpoint computations
- Report generation with disclaimer and citations
