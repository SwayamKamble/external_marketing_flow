# ContentForge Pipeline Architecture

This document explains exactly how the LangGraph-powered Python pipeline operates under the hood. The system is designed as an autonomous, event-driven state machine that moves marketing content linearly through distinct phases, occasionally pausing for human intervention.

## 1. The Core Engine (LangGraph)
At the heart of ContentForge is **LangGraph** (`src/contentforge/core/graph.py`). LangGraph allows us to build cyclical workflows (graphs) where each node is an LLM agent or python function.

### The State Object (`ContentForgeState`)
Data is passed between nodes using a strictly typed Pydantic object defined in `src/contentforge/core/state.py`.
- When a node finishes, it returns a dictionary with keys matching the state.
- LangGraph applies these updates to the global state.
- All subsequent nodes get the updated state.

### Interrupts (Human-in-the-Loop)
The pipeline is entirely autonomous *except* when it hits defined interrupt breakpoints:
- `research_parser`: Pauses so the user can paste external research metrics.
- `deep_prompt`: Pauses so the user can run a deep-research prompt for one pending topic.
- `edit_router`: Pauses to wait for human approval or chat feedback before finalizing.

The planning phase now enforces explicit topic selection before deep research starts:
- `calendar_planner` emits `human_action_type=select_topics`.
- The API requires `action=select_topics` with a non-empty `selected_topics` list.

LangGraph saves everything to an SQLite checkpoint (`MemorySaver`), meaning if the server crashes, the exact state of your research is perfectly preserved.

## 2. The Nodes (Agents)
The system is divided into ~20 independent nodes, subclassed from `BaseNode`. Each node follows a specific pattern:
1. **Load State:** Read the `ContentForgeState`.
2. **Load Prompts:** Dynamically load Jinja templates from `prompts/` and merge them with `./data/brand/brand_dna.md`.
3. **Execute LLM Model:** Call Azure/OpenAI with strict JSON constraints.
4. **Save Artifact:** Call `self.save_artifact()` which strips the file into `data/weeks/{week_id}/{phase}/filename.md` and indexes it in the SQLite DB.
5. **Return Status:** Return the updated state payload back to LangGraph.

### Phase 1: Research
- **BrandContextLoader**: Bootstraps the pipeline with your company's DNA.
- **ResearchPromptGenerator / Parser**: Converts raw internet data into discrete `Topic` objects.

### Phase 2: Scoring & Planning
- **TopicScorer**: Grades topics based on virality, brand fit, and effort.
- **CalendarPlanner**: Maps the top topics to 7 days based on the `.yaml` content mix.

### Phase 3: Deep Research (Per Topic Loop)
- **DeepResearchPromptGenerator**: Creates one deep-research prompt for the current pending topic.
- **DeepResearchParser**: Parses one returned deep-research payload and advances queue pointers.
- Graph loops `deep_prompt -> deep_parse -> deep_prompt` until all selected topics have deep research.

### Phase 4: Content Creation (Selected Topics Progression)
- **ContentRouter**: Ensures only user-selected topics are routed and picks the next non-exported topic.
- **ContentRouter**: A conditional node that looks at a topic's `format` (e.g., Carousel vs. Reel) and routes the execution flow down a specific sub-graph.
- **ThemeDesigner**: Automatically selects specific hex values and fonts that fit the specific topic's mood but respect the Brand Guidelines.
- **CaptionWriter**: Uses Python's `asyncio.gather` tool to concurrently spin up an agent for Instagram, LinkedIn, X, and Threads. Each agent creates 2 A/B variants.

#### The Carousel Subgraph
If the content format is a Carousel, the Graph triggers:
1. `SlideContentWriter`: Paginates facts into 8 slides.
2. `ReactCodeGenerator`: Turns the JSON slides into raw `TailwindCSS` + `React` functional components optimized for browser screenshotting.

### Phase 5: Editing
- **EditRouter**: Validates if the content needs approval.
- **ChatEditAgent**: An NLP router. If you tell the frontend, "Make the hook punchier", this agent intercepts the current state dictionary, applies a patch, and updates the state entirely autonomously.

### Phase 6: Export and Topic Handoff
- **ContentAggregator** marks the current topic as exported.
- **FilePackager** writes delivery output for the current topic.
- Post-packaging graph routing checks remaining selected topics and loops back to `content_router` until every selected topic is exported.

## 3. The FastAPI Wrapper
All of this AI orchestration is wrapped inside `api/main.py`:
- `POST /pipeline/start` initiates LangGraph.
- `GET /pipeline/{week_id}/status` retrieves what node the AI is currently thinking about.
- `POST /pipeline/{week_id}/feedback` handles strict HITL actions (`select_topics`, `supply_raw_research`, `supply_deep_research`, `edit`, approvals).
- `POST /carousel/render/{week_id}/{topic_id}` renders carousel previews to images through the Node renderer.
- `WS /events/ws` tails the logger and broadcasts real-time execution telemetry to the web browser.

The `DBManager` manages a background FTS5 SQLite table enabling sub-millisecond semantic search across all generated files from past weeks.
