# ContentForge — Setup Guide

## Prerequisites

- **Python 3.12+**
- **uv** — Install with: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **Node.js 18+** (for frontend, Phase 3)

## Step 1: Environment Setup

```bash
cd e:\startup\marketing_workflow

# Create virtual environment
uv venv

# Activate (Windows cmd)
.venv\Scripts\activate

# Install all dependencies
uv sync

# Install dev dependencies
uv sync --extra dev
```

## Step 2: Configuration

```bash
# Copy env template
copy .env.example .env
```

Edit `.env` with your actual values:

```
LLM_BASE_URL=https://coder-resource.services.ai.azure.com/openai/v1/
LLM_API_KEY=your-actual-key
LLM_DEFAULT_MODEL=gpt-5-chat
```

## Step 3: Initialize Database

```bash
uv run python -c "
import sys; sys.path.insert(0, 'src')
from contentforge.core.db import DatabaseManager
db = DatabaseManager('./data/pipeline.db')
db.initialize()
print('Database initialized successfully')
"
```

## Step 4: Verify Setup

```bash
# Test config loading
uv run python -c "
import sys; sys.path.insert(0, 'src')
from contentforge.core.config_loader import ConfigLoader
config = ConfigLoader('./config')
print('LLM Config:', config.get_llm_config()['default_model'])
print('Platforms:', list(config.get_platform_rules()['platforms'].keys()))
print('Setup verified!')
"

# Test file memory
uv run python -c "
import sys; sys.path.insert(0, 'src')
from contentforge.core.file_memory import FileMemory
mem = FileMemory('./data')
brand = mem.get_brand_context()
print('Brand files:', list(brand.keys()))
print('File memory working!')
"

# Start the API server
uv run uvicorn api.main:app --reload --port 8000
# Visit http://localhost:8000/docs
```

## Step 5: Brand Configuration

Edit the files in `data/brand/` with your actual brand info:
- `brand_dna.md` — Your brand identity, audience, and voice
- `style_guide.md` — Visual style rules
- `content_pillars.md` — Content categories and guidelines
- `platform_rules.md` — Platform-specific rules

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `uv` not found | Run the install script from Prerequisites |
| Python 3.12 not found | `uv python install 3.12` |
| Import errors | Ensure `src/` is on PYTHONPATH or run from project root |
| LLM calls fail | Check `.env` has correct API key and base URL |
| DB errors | Delete `data/pipeline.db` and re-run Step 3 |
