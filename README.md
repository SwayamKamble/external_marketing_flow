# ContentForge — AI Marketing Content Pipeline

An event-driven, agentic content marketing pipeline built on LangGraph that automates the research → planning → creation workflow for AI/tech social media content.

## Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Setup

```bash
# 1. Create and activate virtual environment
uv venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Linux/macOS

# 2. Install dependencies
uv sync

# 3. Configure environment variables
copy .env.example .env
# Edit .env with your API keys

# 4. Initialize the database
uv run python -c "from contentforge.core.db import DatabaseManager; db = DatabaseManager(); db.initialize(); print('DB initialized')"
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `LLM_BASE_URL` | Azure OpenAI endpoint URL | Yes |
| `LLM_API_KEY` | API key for LLM provider | Yes |
| `LLM_DEFAULT_MODEL` | Default model name (e.g., `gpt-5-chat`) | Yes |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith tracing (`true`/`false`) | No |
| `LANGCHAIN_API_KEY` | LangSmith API key | No |
| `LANGCHAIN_PROJECT` | LangSmith project name | No |

### Running

```bash
# Start the API server
uv run uvicorn api.main:app --reload --port 8000

# Run a pipeline node (testing)
uv run python scripts/run_node.py --node caption_writer --input tests/fixtures/sample.json

# Fire a pipeline event
uv run python scripts/fire_event.py --event pipeline.start

# List available nodes
uv run python scripts/run_node.py --list

# Run tests
uv run pytest tests/ -v
```

## Architecture

```
User → React Frontend → FastAPI Backend → LangGraph Pipeline → File Memory (.md)
                                              ↕                      ↕
                                         LLM Gateway            SQLite Index
                                        (OpenAI SDK)            (search + state)
                                              ↕
                                         LangSmith
                                        (tracing)
```

## Project Structure

```
contentforge/
├── config/          # YAML configuration files
├── prompts/         # System prompts for each agent node
├── src/contentforge/
│   ├── core/        # Infrastructure: LLM gateway, file memory, logger, events
│   ├── nodes/       # Pipeline nodes (each = one function)
│   └── utils/       # Helpers: markdown, templates, platform rules
├── api/             # FastAPI backend
├── data/            # Runtime data: brand/, weeks/, logs/
├── scripts/         # CLI tools: run_node.py, fire_event.py
└── tests/           # Test suite
```

## Pipeline Phases

1. **Research** — Generate prompts, human pastes external research, system parses topics
2. **Scoring & Planning** — Score topics, generate 7-day calendar, human selects topics
3. **Deep Research** — Per-topic deep dive prompts, human pastes detailed research
4. **Content Creation** — Route by format → generate theme, captions, slides/scripts
5. **Review & Edit** — Human reviews, chat-based editing with targeted node re-runs
6. **Export** — Validate, render carousels, package for publishing

## Documentation

- [Setup Guide](docs/SETUP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Prompt Guide](prompts/README.md)
- [PRD](prd.md)
