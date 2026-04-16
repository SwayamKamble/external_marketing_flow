

I'll design a comprehensive PRD with all your requirements — file-based memory, chat-editable content, event-driven architecture, modular functions, and full logging. Let me first check the latest on LangSmith and UV tooling.
---

# 📋 PRODUCT REQUIREMENTS DOCUMENT (PRD)
## AI Marketing Content Pipeline — "ContentForge"

**Version:** 1.0
**Date:** April 16, 2026
**Author:** System Architect

---

## 1. EXECUTIVE SUMMARY

ContentForge is an **event-driven, agentic content marketing pipeline** built on LangGraph that automates the research → planning → creation workflow for AI/tech social media content. The system uses a **human-in-the-loop** architecture where external LLMs (accessed manually) handle deep research, while internal LLM APIs (OpenAI/Groq via OpenAI SDK) handle parsing, scoring, planning, and content creation. Every artifact is saved as **.md files** in a structured file-based memory system. Every action is logged. Every function is **independently callable** for testing and debugging. LangSmith provides full observability of the agentic workflow. [1][2]

---

## 2. PRODUCT GOALS & CONSTRAINTS

### Goals
- Generate **1 post per day, 7 days/week** across Instagram, LinkedIn, X, and Threads
- **Multiple caption variants** per platform for A/B testing
- **File-based memory** — every output saved as `.md` files for human readability and editability
- **Event-driven architecture** — every node/function callable independently
- **User can select which topics** from the weekly plan to create content for
- **Chat-based editing** — user can converse with the system to refine any output
- Full **LangSmith tracing** for debugging every agent decision

### Constraints
- LLM APIs: **OpenAI SDK only** (works for both OpenAI and Groq models)
- Default model: **gpt-5-chat** (configurable per agent in config)
- External research: **manual human-in-loop** (no Perplexity/Gemini API)
- Image generation: **prompts only** — user generates externally
- Carousel rendering: **React + export tooling** (Puppeteer or Playwright for screenshots)
- Storage: **SQLite + file system** (no cloud DB)
- Environment: **uv** for Python package/environment management

---

## 3. SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────┐
│                         REACT FRONTEND (Node.js)                     │
│   Dashboard │ Research Loop │ Calendar │ Content Review │ Chat Edit  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ REST API + WebSocket (for chat)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND (Python)                         │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │               EVENT BUS / FUNCTION REGISTRY                    │ │
│  │   Every node is an independent callable function.              │ │
│  │   Can be triggered: via API, via pipeline, or via CLI.         │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                               │                                     │
│                               ▼                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    LANGGRAPH STATE MACHINE                     │ │
│  │                                                                │ │
│  │   ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐          │ │
│  │   │Node 1│→│Node 2│→│Node 3│→│Node N│→│Export│          │ │
│  │   └──────┘  └──────┘  └──────┘  └──────┘  └──────┘          │ │
│  │          ↕ Human Interrupt (pause/resume)                     │ │
│  │          ↕ Chat Edit (branch into edit sub-graph)             │ │
│  │                                                                │ │
│  │   Checkpointer: SQLite (auto-saves state at every node)       │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                               │                                     │
│  ┌───────────────┐  ┌────────┴────────┐  ┌──────────────────────┐ │
│  │  LLM GATEWAY  │  │  FILE MEMORY    │  │    LANGSMITH         │ │
│  │  OpenAI SDK   │  │  MANAGER        │  │    TRACING           │ │
│  │  (OpenAI +    │  │  (.md files +   │  │    Every LLM call,   │ │
│  │   Groq)       │  │   SQLite index) │  │    tool call, node   │ │
│  └───────────────┘  └─────────────────┘  │    transition logged  │ │
│                                           └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
         │                                            │
         ▼                                            ▼
┌─────────────────┐                        ┌────────────────────┐
│ CAROUSEL RENDER │                        │ LANGSMITH CLOUD    │
│ SERVICE         │                        │ Dashboard          │
│ React +         │                        │ Traces, costs,     │
│ Puppeteer       │                        │ latency, errors    │
│ → PNG/GIF export│                        └────────────────────┘
└─────────────────┘
```

---

## 4. THE COMPLETE PIPELINE — EVENT-DRIVEN NODE MAP

Every node below is a **standalone Python function** that:
- Takes typed input → returns typed output
- Can be called **independently** via CLI or API for testing
- Reads from / writes to **file-based memory**
- Is **traced by LangSmith** automatically
- Has its **system prompt stored in a dedicated file**

### 4.1 PIPELINE PHASES & NODES

```
PHASE 1: RESEARCH
├── Node 1.1: brand_context_loader
├── Node 1.2: research_prompt_generator
├── Node 1.3: [HUMAN INTERRUPT] → paste external research
└── Node 1.4: research_parser

PHASE 2: SCORING & PLANNING
├── Node 2.1: topic_scorer
├── Node 2.2: calendar_planner
├── Node 2.3: [HUMAN INTERRUPT] → approve plan + SELECT which topics to create
└── Node 2.4: deep_research_prompt_generator

PHASE 3: DEEP RESEARCH
├── Node 3.1: [HUMAN INTERRUPT] → paste deep research per selected topic
└── Node 3.2: deep_research_parser

PHASE 4: CONTENT CREATION (per selected topic — event-triggered)
├── Node 4.1: content_router (decides path based on format)
├── Node 4.2a: carousel_creator
│   ├── Sub 4.2a.1: theme_designer
│   ├── Sub 4.2a.2: slide_content_writer
│   ├── Sub 4.2a.3: react_code_generator
│   ├── Sub 4.2a.4: cover_image_prompt_generator
│   └── Sub 4.2a.5: caption_writer (× 4 platforms × 2 variants)
├── Node 4.2b: single_image_creator
│   ├── Sub 4.2b.1: theme_designer
│   ├── Sub 4.2b.2: image_prompt_generator
│   └── Sub 4.2b.3: caption_writer (× 4 platforms × 2 variants)
├── Node 4.2c: reel_creator
│   ├── Sub 4.2c.1: hook_writer
│   ├── Sub 4.2c.2: script_writer
│   ├── Sub 4.2c.3: storyboard_generator
│   ├── Sub 4.2c.4: thumbnail_prompt_generator
│   ├── Sub 4.2c.5: music_suggestion
│   └── Sub 4.2c.6: caption_writer (× 4 platforms × 2 variants)
└── Node 4.2d: news_post_creator
    ├── Sub 4.2d.1: headline_writer
    ├── Sub 4.2d.2: image_prompt_generator
    └── Sub 4.2d.3: caption_writer (× 4 platforms × 2 variants)

PHASE 5: REVIEW & EDIT
├── Node 5.1: content_aggregator
├── Node 5.2: [HUMAN REVIEW] → approve, reject, or CHAT TO EDIT
├── Node 5.3: chat_edit_agent (sub-graph for conversational refinement)
└── Node 5.4: validator (char limits, hashtag counts, completeness)

PHASE 6: EXPORT
├── Node 6.1: carousel_render_trigger (sends React code to renderer)
├── Node 6.2: file_packager (organizes exports per day/platform)
└── Node 6.3: week_summary_generator (creates overview .md)
```

### 4.2 EVENT-DRIVEN TRIGGERING — HOW IT WORKS

The key design principle: **you don't run the whole pipeline.** You trigger individual events.

```
┌─────────────────────────────────────────────────────┐
│                 EVENT REGISTRY                       │
│                                                     │
│  Event Name                    │ Triggers Node(s)   │
│  ─────────────────────────────│────────────────── │
│  pipeline.start               │ 1.1 → 1.2          │
│  research.submit              │ 1.4                 │
│  plan.approve                 │ 2.3 → 2.4          │
│  topic.select(topic_id)       │ 3.1 (for that topic)│
│  deep_research.submit(tid)    │ 3.2 → 4.1          │
│  content.create(topic_id)     │ 4.1 → 4.2x         │
│  content.edit(topic_id, msg)  │ 5.3 (chat agent)   │
│  content.regenerate(tid, part)│ specific sub-node   │
│  content.approve(topic_id)    │ 5.4 → 6.x          │
│  export.trigger(topic_id)     │ 6.1 → 6.2          │
│  export.all                   │ 6.1 → 6.2 → 6.3   │
│                                                     │
│  // TESTING - call any node directly                │
│  node.run(node_name, input)   │ that single node    │
└─────────────────────────────────────────────────────┘
```

**Example — Testing a single node from CLI or external code:**
```
# Instead of running the whole pipeline, just test caption_writer:
contentforge node.run caption_writer --input ./test_inputs/topic_001.json

# Or test the scorer on some sample topics:
contentforge node.run topic_scorer --input ./test_inputs/sample_topics.json

# Or trigger content creation for just one topic:
contentforge event content.create --topic-id topic_003
```

**Example — From the UI:**
```
User clicks "Create Content" on Tuesday's carousel card
  → Frontend sends: POST /api/events/content.create { topic_id: "topic_003" }
  → Backend triggers Node 4.1 → routes to carousel path → runs 4.2a.*
  → Saves all outputs to file memory + SQLite
  → Returns completed content to frontend
```

---

## 5. CHAT-BASED EDITING SYSTEM (Node 5.3)

This is a **sub-graph within LangGraph** — a mini conversational agent:

```
┌─────────────────────────────────────────────────────┐
│  CHAT EDIT SUB-GRAPH                                │
│                                                     │
│  User says: "Make the theme more minimal,           │
│              use blue instead of orange"             │
│                         │                           │
│                         ▼                           │
│              ┌───────────────────┐                  │
│              │ EDIT ROUTER       │                  │
│              │ Determines what   │                  │
│              │ to change:        │                  │
│              │ • theme? → 4.2a.1 │                  │
│              │ • caption? → 4.2a.5│                 │
│              │ • slides? → 4.2a.2│                  │
│              │ • image prompt?   │                  │
│              └─────────┬─────────┘                  │
│                        │                            │
│                        ▼                            │
│              ┌───────────────────┐                  │
│              │ TARGETED RE-RUN   │                  │
│              │ Only re-runs the  │                  │
│              │ specific sub-node │                  │
│              │ with edit context │                  │
│              └─────────┬─────────┘                  │
│                        │                            │
│                        ▼                            │
│              ┌───────────────────┐                  │
│              │ DIFF PRESENTER    │                  │
│              │ Shows: before/after│                 │
│              │ User: approve or  │                  │
│              │ continue chatting  │                  │
│              └───────────────────┘                  │
│                                                     │
│  The edit sub-graph has access to:                   │
│  • The full content state for this topic             │
│  • The file memory (.md files)                       │
│  • All system prompts (can adjust and re-run)        │
│  • Chat history for this edit session                │
└─────────────────────────────────────────────────────┘
```

---



## 6. FILE-BASED MEMORY SYSTEM (continued)

### 6.1 Directory Structure (full)

```
data/
├── brand/
│   ├── brand_dna.md                    # Brand identity, tone, audience
│   ├── style_guide.md                  # Visual style rules
│   ├── content_pillars.md              # Content categories & rules
│   └── platform_rules.md              # Per-platform constraints
│
├── weeks/
│   └── 2026-W16/                       # One folder per week
│       ├── _week_meta.md               # Week metadata, status, dates
│       ├── _week_log.md                # Full activity log for this week
│       │
│       ├── 01_research/
│       │   ├── research_prompts.md     # 4 prompts generated for external LLMs
│       │   ├── raw_research_news.md    # Pasted back from Perplexity/Gemini
│       │   ├── raw_research_tools.md
│       │   ├── raw_research_debates.md
│       │   ├── raw_research_tutorials.md
│       │   └── parsed_topics.md        # Structured topic bank after parsing
│       │
│       ├── 02_scoring/
│       │   ├── scored_topics.md        # All topics with scores & tags
│       │   └── scoring_reasoning.md    # LLM's reasoning for each score
│       │
│       ├── 03_plan/
│       │   ├── weekly_plan.md          # The 7-day calendar
│       │   ├── plan_reasoning.md       # Why each topic was assigned to each day
│       │   └── user_selections.md      # Which topics user selected to create
│       │
│       ├── 04_deep_research/
│       │   ├── topic_001/
│       │   │   ├── deep_prompt.md      # Prompt sent to external LLM
│       │   │   └── deep_research.md    # Pasted back research result
│       │   ├── topic_002/
│       │   │   ├── deep_prompt.md
│       │   │   └── deep_research.md
│       │   └── ... (per selected topic)
│       │
│       ├── 05_content/
│       │   ├── monday_topic_001/
│       │   │   ├── _content_meta.md         # Format, status, version
│       │   │   ├── theme.md                  # Color palette, visual style, assets
│       │   │   ├── image_prompt.md           # Image generation prompt
│       │   │   ├── captions/
│       │   │   │   ├── instagram_v1.md
│       │   │   │   ├── instagram_v2.md       # A/B variant
│       │   │   │   ├── linkedin_v1.md
│       │   │   │   ├── linkedin_v2.md
│       │   │   │   ├── x_v1.md
│       │   │   │   ├── x_v2.md
│       │   │   │   ├── threads_v1.md
│       │   │   │   └── threads_v2.md
│       │   │   └── edit_history.md           # Chat edit log
│       │   │
│       │   ├── tuesday_topic_003/            # CAROUSEL example
│       │   │   ├── _content_meta.md
│       │   │   ├── theme.md
│       │   │   ├── slides/
│       │   │   │   ├── slide_01_cover.md     # Each slide's content
│       │   │   │   ├── slide_02.md
│       │   │   │   ├── slide_03.md
│       │   │   │   ├── slide_04.md
│       │   │   │   ├── slide_05.md
│       │   │   │   └── slide_06_cta.md
│       │   │   ├── cover_image_prompt.md
│       │   │   ├── react_component.jsx       # React code for carousel
│       │   │   ├── captions/
│       │   │   │   ├── instagram_v1.md
│       │   │   │   ├── instagram_v2.md
│       │   │   │   ├── linkedin_v1.md
│       │   │   │   ├── linkedin_v2.md
│       │   │   │   ├── x_v1.md
│       │   │   │   ├── x_v2.md
│       │   │   │   ├── threads_v1.md
│       │   │   │   └── threads_v2.md
│       │   │   └── edit_history.md
│       │   │
│       │   ├── wednesday_topic_005/          # REEL example
│       │   │   ├── _content_meta.md
│       │   │   ├── hook.md                   # First 3 seconds
│       │   │   ├── script.md                 # Full narration script
│       │   │   ├── storyboard.md             # Scene-by-scene breakdown
│       │   │   ├── thumbnail_prompt.md
│       │   │   ├── music_suggestion.md
│       │   │   ├── captions/
│       │   │   │   └── (same 8 files)
│       │   │   └── edit_history.md
│       │   │
│       │   └── ... (per selected topic)
│       │
│       ├── 06_exports/
│       │   ├── monday/
│       │   │   ├── image_prompt.txt          # Copy-paste ready
│       │   │   ├── instagram_caption.txt
│       │   │   ├── linkedin_caption.txt
│       │   │   ├── x_caption.txt
│       │   │   ├── threads_caption.txt
│       │   │   └── content_brief.md
│       │   ├── tuesday/
│       │   │   ├── carousel_slides/          # Rendered PNGs
│       │   │   │   ├── slide_01.png
│       │   │   │   ├── slide_02.png
│       │   │   │   └── ...
│       │   │   ├── carousel.gif              # Animated preview
│       │   │   └── (captions + brief)
│       │   └── ...
│       │
│       └── week_summary.md                   # Auto-generated overview
│
├── logs/
│   ├── 2026-W16/
│   │   ├── pipeline_events.log              # Every event fired
│   │   ├── llm_calls.log                    # Every LLM call with I/O
│   │   ├── node_executions.log              # Node entry/exit with timing
│   │   └── errors.log                       # Any failures
│   └── ...
│
├── templates/                                # Reusable across weeks
│   ├── carousel_react_templates/
│   │   ├── minimal_dark.jsx
│   │   ├── bold_gradient.jsx
│   │   ├── clean_white.jsx
│   │   └── tech_neon.jsx
│   └── caption_templates/
│       ├── instagram_carousel.md
│       ├── instagram_news.md
│       ├── linkedin_thought_leadership.md
│       ├── x_hook.md
│       └── threads_casual.md
│
└── pipeline.db                              # SQLite — index & state
```

### 6.2 File Memory Contract

Every `.md` file follows a consistent structure with YAML frontmatter:

```markdown
---
id: "topic_001"
week: "2026-W16"
node: "caption_writer"
created_at: "2026-04-16T10:23:45Z"
updated_at: "2026-04-16T11:05:12Z"
version: 2
model_used: "gpt-5-chat"
token_count: 847
edit_history:
  - v1: "2026-04-16T10:23:45Z"
  - v2: "2026-04-16T11:05:12Z (user chat edit: make it shorter)"
status: "approved"
---

# Instagram Caption — V2

🚨 Claude 4 just dropped and everything changes.

Here's what you need to know:
...

---
**Hashtags:** #AI #Claude4 #Anthropic #TechNews ...
**CTA:** Share this with someone who needs to know 👇
**Char Count:** 1,847 / 2,200
```

### 6.3 How Agents Use File Memory

```
┌──────────────────────────────────────────────────────────────┐
│                    FILE MEMORY MANAGER                         │
│                                                              │
│  read_context(week_id, phase, topic_id)                      │
│    → Reads all .md files for that topic/phase                │
│    → Returns structured context dict                          │
│    → Used by agents to understand what came before           │
│                                                              │
│  write_artifact(week_id, phase, topic_id, node, content)     │
│    → Writes .md file with proper frontmatter                 │
│    → Updates SQLite index                                    │
│    → Logs to activity log                                    │
│                                                              │
│  get_brand_context()                                         │
│    → Reads all brand/*.md files                              │
│    → Returns unified brand context for system prompts        │
│                                                              │
│  get_edit_history(week_id, topic_id)                         │
│    → Reads edit_history.md                                   │
│    → Returns conversation log for chat edit agent            │
│                                                              │
│  version_artifact(week_id, topic_id, node, new_content)      │
│    → Increments version in frontmatter                       │
│    → Keeps old version accessible                            │
│    → Logs the change reason                                  │
│                                                              │
│  search_past_weeks(query, limit=5)                           │
│    → SQLite full-text search across past weeks               │
│    → Returns relevant past content for reference             │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. SYSTEM PROMPTS — DEDICATED FOLDER

Every agent/node has its system prompt stored in a **separate file** for easy debugging and iteration:

```
prompts/
├── _global_context.md              # Injected into ALL agents
│
├── research/
│   ├── research_prompt_generator.md
│   ├── research_parser.md
│   └── deep_research_prompt_generator.md
│
├── scoring/
│   ├── topic_scorer.md
│   └── calendar_planner.md
│
├── content/
│   ├── content_router.md
│   ├── theme_designer.md
│   ├── caption_writer.md
│   ├── image_prompt_engineer.md
│   ├── carousel/
│   │   ├── slide_content_writer.md
│   │   └── react_code_generator.md
│   ├── reel/
│   │   ├── hook_writer.md
│   │   ├── script_writer.md
│   │   ├── storyboard_generator.md
│   │   └── music_suggester.md
│   └── news/
│       └── headline_writer.md
│
├── editing/
│   ├── edit_router.md
│   └── diff_presenter.md
│
├── export/
│   ├── validator.md
│   └── week_summary_generator.md
│
└── README.md                       # How to modify prompts, format rules
```

### 7.1 System Prompt Loading Pattern

```
Every node function works like this:

1. Load global context:    prompts/_global_context.md
2. Load brand context:     data/brand/brand_dna.md (via file memory)
3. Load node-specific:     prompts/{category}/{node_name}.md
4. Load topic context:     data/weeks/{week}/05_content/{topic}/*.md
5. Merge into final prompt → Send to LLM
```

### 7.2 Example System Prompt File

**File: `prompts/content/caption_writer.md`**
```markdown
---
node: caption_writer
model: gpt-5-chat
temperature: 0.8
max_tokens: 2000
description: "Writes platform-specific captions with A/B variants"
inputs: [topic_context, theme, content_format, platform_rules]
outputs: [caption_v1, caption_v2]
---

# ROLE
You are an expert social media copywriter specializing in AI/tech content.

# TASK
Write two caption variants for the given platform and content.

# RULES
- Variant A: Story-telling approach (start with a hook/anecdote)
- Variant B: Direct value approach (start with the key insight)
- STRICTLY respect the character limit for the platform
- Include a clear CTA appropriate for the platform
- Hashtags must be relevant and mix niche + broad
- Never use generic filler — every sentence must add value
- Match the brand tone: {brand_tone}

# PLATFORM CONTEXT
Platform: {platform_name}
Character Limit: {char_limit}
Hashtag Count: {hashtag_range}
Tone Guide: {platform_tone}
CTA Style: {cta_style}

# CONTENT CONTEXT
Topic: {topic_title}
Format: {content_format}
Content Intent: {content_intent} (savable / shareable)
Theme: {theme_summary}
Key Points: {key_points}

# OUTPUT FORMAT
Return JSON:
{
  "variant_a": {
    "caption": "...",
    "hashtags": ["...", "..."],
    "cta": "...",
    "char_count": 0
  },
  "variant_b": {
    "caption": "...",
    "hashtags": ["...", "..."],
    "cta": "...",
    "char_count": 0
  }
}
```

---

## 8. LOGGING SYSTEM — EVERYTHING IS TRACKED

### 8.1 Log Levels & What Gets Logged

```
┌────────────────────────────────────────────────────────────────┐
│                    LOGGING ARCHITECTURE                         │
│                                                                │
│  LEVEL 1: PIPELINE EVENTS (pipeline_events.log)                │
│  ─────────────────────────────────────────────                │
│  [2026-04-16 10:00:01] EVENT pipeline.start week=2026-W16     │
│  [2026-04-16 10:00:02] EVENT node.enter node=brand_loader     │
│  [2026-04-16 10:00:03] EVENT node.exit node=brand_loader       │
│  [2026-04-16 10:01:15] EVENT human.interrupt type=research     │
│  [2026-04-16 10:45:00] EVENT human.resume data_size=4.2KB      │
│  [2026-04-16 10:45:01] EVENT node.enter node=research_parser   │
│  [2026-04-16 11:30:00] EVENT content.edit topic=topic_003      │
│                         msg="make theme more minimal"          │
│                                                                │
│  LEVEL 2: LLM CALLS (llm_calls.log)                           │
│  ─────────────────────────────────                             │
│  [2026-04-16 10:45:02] LLM_CALL                               │
│    node: research_parser                                       │
│    model: groq/llama-3.3-70b                                   │
│    input_tokens: 3,421                                         │
│    output_tokens: 1,205                                        │
│    latency_ms: 890                                             │
│    cost_usd: $0.003                                            │
│    langsmith_trace_id: "abc123..."                              │
│    input_file: 01_research/raw_research_news.md                │
│    output_file: 01_research/parsed_topics.md                   │
│                                                                │
│  LEVEL 3: NODE EXECUTION (node_executions.log)                 │
│  ──────────────────────────────────────────                    │
│  [2026-04-16 10:45:01] NODE_START                              │
│    node: research_parser                                       │
│    input_state_keys: [raw_research, brand_context]             │
│    files_read: [raw_research_news.md, raw_research_tools.md]   │
│  [2026-04-16 10:45:08] NODE_END                                │
│    node: research_parser                                       │
│    output_state_keys: [topic_bank]                             │
│    files_written: [parsed_topics.md]                           │
│    duration_ms: 7,200                                          │
│    status: success                                             │
│                                                                │
│  LEVEL 4: ERRORS (errors.log)                                  │
│  ────────────────────────                                      │
│  [2026-04-16 10:45:05] ERROR                                   │
│    node: caption_writer                                        │
│    error: "Caption exceeded 2200 chars (got 2,347)"            │
│    action: "Auto-retry with truncation instruction"            │
│    retry_count: 1                                              │
│    resolved: true                                              │
│                                                                │
│  LEVEL 5: LANGSMITH (automatic — external dashboard)           │
│  ─────────────────────────────────────────────                │
│  Every LLM call auto-traced with full I/O, latency, costs     │
│  Viewable at: smith.langchain.com/project/contentforge         │
└────────────────────────────────────────────────────────────────┘
```

LangSmith records a trace (the whole request) as a series of runs (individual steps like "LLM", "tool", "node", etc.) — this gives you full visibility into every agent decision without building custom tracing.

---

## 9. LLM GATEWAY — UNIFIED OPENAI SDK

Since OpenAI SDK works for both OpenAI and Groq:

```
┌──────────────────────────────────────────────────────┐
│                   LLM GATEWAY                         │
│                                                      │
│  config/llm_config.yaml:                             │
│                                                      │
│  providers:                                          │
│    openai:                                           │
│      base_url: "https://api.openai.com/v1"           │
│      api_key: "${OPENAI_API_KEY}"                    │
│      default_model: "gpt-5-chat"                     │
│    groq:                                             │
│      base_url: "https://api.groq.com/openai/v1"     │
│      api_key: "${GROQ_API_KEY}"                      │
│      default_model: "llama-3.3-70b-versatile"        │
│                                                      │
│  node_model_mapping:                                 │
│    research_parser:        groq      # fast & cheap  │
│    topic_scorer:           openai    # needs judgment │
│    calendar_planner:       openai    # strategic     │
│    theme_designer:         openai    # creative      │
│    caption_writer:         openai    # tone mastery  │
│    image_prompt_engineer:  openai    # visual detail │
│    reel_scriptwriter:      openai    # creative      │
│    slide_content_writer:   openai    # structured    │
│    react_code_generator:   openai    # code quality  │
│    validator:              groq      # rule-checking │
│    edit_router:            groq      # fast routing  │
│                                                      │
│  The gateway:                                        │
│  1. Reads which model to use for the calling node    │
│  2. Loads the system prompt from prompts/ folder     │
│  3. Calls OpenAI SDK with appropriate base_url       │
│  4. Logs everything (tokens, latency, cost)          │
│  5. Auto-traces via LangSmith env vars               │
│  6. Returns structured output                        │
│  7. Handles retries with exponential backoff         │
└──────────────────────────────────────────────────────┘
```

---

## 10. LANGGRAPH STATE SCHEMA (Updated)

```
ContentForgeState {
  // ── METADATA ──
  week_id:              str          # "2026-W16"
  pipeline_status:      str          # "research" | "scoring" | "planning" | ...
  current_node:         str          # which node is active
  
  // ── BRAND (loaded from files) ──
  brand_context:        dict         # from brand_dna.md
  platform_rules:       dict         # from platform_rules.md
  
  // ── RESEARCH ──
  research_prompts:     list[str]    # 4 prompts for external LLMs
  raw_research:         list[str]    # 4 pasted results
  
  // ── TOPICS ──
  topic_bank:           list[Topic]  # parsed & scored topics
  
  // ── PLAN ──  
  weekly_plan:          list[PlanItem]  # 7-day calendar
  selected_topics:      list[str]       # topic IDs user chose to create
  
  // ── DEEP RESEARCH ──
  deep_research: {
    topic_id: {
      prompt: str,
      result: str
    }
  }
  
  // ── CONTENT (per topic) ──
  content: {
    topic_id: {
      format:          str
      theme:           Theme
      slides:          list[Slide]    # carousel only
      image_prompts:   list[str]
      react_code:      str            # carousel only
      reel_script:     ReelScript     # reel only
      captions: {
        platform: {
          v1: Caption,
          v2: Caption
        }
      }
      status:          str            # "draft" | "editing" | "approved"
      edit_chat:       list[Message]  # chat edit history
    }
  }
  
  // ── CONTROL FLOW ──
  human_action_required:  bool
  human_action_type:      str         # "paste_research" | "approve_plan" | ...
  pending_topic_id:       str | null  # which topic needs attention
  errors:                 list[Error]
}
```

---

## 11. API ROUTES — FASTAPI

```
┌──────────────────────────────────────────────────────────────────┐
│                       REST API ROUTES                             │
│                                                                  │
│  PIPELINE CONTROL                                                │
│  POST   /api/pipeline/start                  # Start new week    │
│  GET    /api/pipeline/status                 # Current state     │
│  POST   /api/pipeline/resume                 # Resume after pause│
│                                                                  │
│  EVENT-DRIVEN TRIGGERS                                           │
│  POST   /api/events/{event_name}             # Fire any event    │
│  POST   /api/nodes/{node_name}/run           # Run single node   │
│         body: { input: {...} }               # (for testing)     │
│                                                                  │
│  RESEARCH                                                        │
│  GET    /api/research/prompts                # Get prompts to copy│
│  POST   /api/research/submit                 # Paste results back│
│         body: { prompt_index: 0, result: "..." }                │
│                                                                  │
│  PLANNING                                                        │
│  GET    /api/plan                            # Get weekly plan   │
│  PUT    /api/plan                            # Edit plan         │
│  POST   /api/plan/approve                    # Approve plan      │
│         body: { selected_topics: ["t001", "t003", ...] }        │
│                                                                  │
│  DEEP RESEARCH                                                   │
│  GET    /api/deep-research/prompts           # Get per-topic     │
│  POST   /api/deep-research/submit            # Paste per-topic   │
│         body: { topic_id: "t001", result: "..." }               │
│                                                                  │
│  CONTENT                                                         │
│  POST   /api/content/create/{topic_id}       # Trigger creation  │
│  GET    /api/content/{topic_id}              # Get content        │
│  POST   /api/content/{topic_id}/approve      # Approve           │
│  POST   /api/content/{topic_id}/regenerate   # Regen specific    │
│         body: { part: "caption", platform: "instagram" }        │
│                                                                  │
│  CHAT EDITING                                                    │
│  POST   /api/content/{topic_id}/chat         # Send edit message │
│         body: { message: "make it more minimal" }               │
│  GET    /api/content/{topic_id}/chat/history  # Edit chat log    │
│                                                                  │
│  EXPORT                                                          │
│  POST   /api/export/{topic_id}               # Export one topic  │
│  POST   /api/export/all                      # Export full week  │
│  GET    /api/export/{topic_id}/download       # Download package │
│                                                                  │
│  FILES & MEMORY                                                  │
│  GET    /api/files/{week_id}/{path}          # Read any .md file │
│  PUT    /api/files/{week_id}/{path}          # Manually edit file│
│  GET    /api/files/{week_id}/tree            # File tree view    │
│                                                                  │
│  LOGS                                                            │
│  GET    /api/logs/{week_id}/{log_type}       # View logs         │
│  GET    /api/logs/{week_id}/llm-costs        # Cost summary      │
│                                                                  │
│  WEBSOCKET                                                       │
│  WS     /ws/chat/{topic_id}                  # Real-time chat    │
│  WS     /ws/pipeline/status                  # Live status       │
└──────────────────────────────────────────────────────────────────┘
```

---

## 12. COMPLETE PROJECT STRUCTURE

```
contentforge/
│
├── .python-version                    # Python version for uv
├── pyproject.toml                     # uv project config + dependencies
├── uv.lock                            # Locked dependencies
├── .env                               # API keys (gitignored)
├── .env.example                       # Template for API keys
├── README.md                          # Setup & usage guide
│
├── config/
│   ├── llm_config.yaml               # Model mapping per node
│   ├── platform_rules.yaml            # Caption limits, hashtags, tone
│   ├── content_mix.yaml               # Weekly framework template
│   └── pipeline_config.yaml           # Timeouts, retries, feature flags
│
├── prompts/                           # ALL system prompts (§7 above)
│   ├── _global_context.md
│   ├── research/
│   ├── scoring/
│   ├── content/
│   ├── editing/
│   ├── export/
│   └── README.md
│
├── src/
│   └── contentforge/
│       ├── __init__.py
│       │
│       ├── core/                      # Core infrastructure
│       │   ├── __init__.py
│       │   ├── state.py               # LangGraph state schema (Pydantic)
│       │   ├── graph.py               # LangGraph graph definition
│       │   ├── events.py              # Event bus + registry
│       │   ├── llm_gateway.py         # Unified OpenAI SDK wrapper
│       │   ├── file_memory.py         # File-based memory manager
│       │   ├── db.py                  # SQLite operations
│       │   ├── logger.py              # Multi-level logging system
│       │   ├── prompt_loader.py       # Load & template system prompts
│       │   └── config_loader.py       # YAML config loading
│       │
│       ├── nodes/                     # Each node = one file = one function
│       │   ├── __init__.py
│       │   ├── _base.py               # Base node class with logging/tracing
│       │   │
│       │   ├── research/
│       │   │   ├── __init__.py
│       │   │   ├── brand_context_loader.py
│       │   │   ├── research_prompt_generator.py
│       │   │   └── research_parser.py
│       │   │
│       │   ├── scoring/
│       │   │   ├── __init__.py
│       │   │   ├── topic_scorer.py
│       │   │   └── calendar_planner.py
│       │   │
│       │   ├── deep_research/
│       │   │   ├── __init__.py
│       │   │   ├── deep_research_prompt_generator.py
│       │   │   └── deep_research_parser.py
│       │   │
│       │   ├── content/
│       │   │   ├── __init__.py
│       │   │   ├── content_router.py
│       │   │   ├── theme_designer.py
│       │   │   ├── caption_writer.py
│       │   │   ├── image_prompt_engineer.py
│       │   │   ├── carousel/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── slide_content_writer.py
│       │   │   │   ├── react_code_generator.py
│       │   │   │   └── carousel_creator.py    # orchestrates sub-nodes
│       │   │   ├── reel/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── hook_writer.py
│       │   │   │   ├── script_writer.py
│       │   │   │   ├── storyboard_generator.py
│       │   │   │   ├── music_suggester.py
│       │   │   │   └── reel_creator.py        # orchestrates sub-nodes
│       │   │   └── news/
│       │   │       ├── __init__.py
│       │   │       ├── headline_writer.py
│       │   │       └── news_creator.py        # orchestrates sub-nodes
│       │   │
│       │   ├── editing/
│       │   │   ├── __init__.py
│       │   │   ├── edit_router.py
│       │   │   ├── chat_edit_agent.py
│       │   │   └── diff_presenter.py
│       │   │
│       │   └── export/
│       │       ├── __init__.py
│       │       ├── content_aggregator.py
│       │       ├── validator.py
│       │       ├── file_packager.py
│       │       └── week_summary_generator.py
│       │
│       └── utils/
│           ├── __init__.py
│           ├── markdown.py             # .md file read/write with frontmatter
│           ├── templates.py            # String template rendering
│           └── platform_helpers.py     # Char counting, hashtag validation
│
├── api/                               # FastAPI backend
│   ├── __init__.py
│   ├── main.py                        # App entry point
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── pipeline.py
│   │   ├── events.py
│   │   ├── research.py
│   │   ├── plan.py
│   │   ├── content.py
│   │   ├── chat.py
│   │   ├── export.py
│   │   ├── files.py
│   │   └── logs.py
│   ├── websockets/
│   │   ├── __init__.py
│   │   ├── chat_ws.py
│   │   └── status_ws.py
│   └── middleware/
│       ├── __init__.py
│       └── error_handler.py
│
├── carousel_renderer/                 # Separate React app
│   ├── package.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── SlideRenderer.jsx          # Takes slide JSON → renders
│   │   ├── templates/
│   │   │   ├── MinimalDark.jsx
│   │   │   ├── BoldGradient.jsx
│   │   │   ├── CleanWhite.jsx
│   │   │   └── TechNeon.jsx
│   │   └── themes/
│   │       └── themeProvider.js
│   └── scripts/
│       └── export.js                  # Puppeteer: render → screenshot
│
├── frontend/                          # Main UI (React)
│   ├── package.json
│   ├── src/
│   │   ├── App.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── ResearchLoop.jsx
│   │   │   ├── CalendarView.jsx
│   │   │   ├── ContentReview.jsx
│   │   │   ├── ChatEditor.jsx
│   │   │   ├── ExportView.jsx
│   │   │   ├── FileExplorer.jsx       # Browse .md files
│   │   │   └── LogViewer.jsx          # View pipeline logs
│   │   ├── components/
│   │   │   ├── TopicCard.jsx
│   │   │   ├── PostPreview.jsx
│   │   │   ├── CaptionEditor.jsx
│   │   │   ├── PlatformTabs.jsx
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── DiffView.jsx
│   │   │   ├── PipelineStatus.jsx
│   │   │   └── FileTree.jsx
│   │   └── api/
│   │       └── client.js              # Axios/fetch wrapper
│   └── ...
│
├── data/                              # Runtime data (§6 above)
│   ├── brand/
│   ├── weeks/
│   ├── logs/
│   ├── templates/
│   └── pipeline.db
│
├── tests/
│   ├── __init__.py
│   ├── test_nodes/                    # Test each node independently
│   │   ├── test_research_parser.py
│   │   ├── test_topic_scorer.py
│   │   ├── test_caption_writer.py
│   │   └── ...
│   ├── test_file_memory.py
│   ├── test_llm_gateway.py
│   ├── test_events.py
│   └── fixtures/                      # Sample inputs for testing
│       ├── sample_research.md
│       ├── sample_topics.json
│       └── sample_content.json
│
├── scripts/
│   ├── setup.sh                       # Full project setup
│   ├── run_node.py                    # CLI: run any node standalone
│   └── fire_event.py                  # CLI: fire any event
│
└── docs/
    ├── ARCHITECTURE.md                # This PRD
    ├── SETUP.md                       # Setup instructions
    ├── PROMPT_GUIDE.md                # How to edit system prompts
    ├── EVENT_REFERENCE.md             # All events documented
    └── NODE_REFERENCE.md              # All nodes documented
```

---

## 13. SETUP INSTRUCTIONS — UV ENVIRONMENT

### 13.1 Initial Setup

```bash
# 1. Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone the project
git clone <repo-url> contentforge
cd contentforge

# 3. Create Python environment with uv
uv init                                    # If starting fresh
uv python install 3.12                     # Install Python 3.12
uv venv                                   # Create virtual environment

# 4. Install all Python dependencies
uv add langgraph langchain langchain-openai langchain-community
uv add langsmith                           # Tracing & observability
uv add fastapi uvicorn[standard]           # API server
uv add websockets                          # WebSocket support
uv add pydantic pyyaml                     # Config & validation
uv add python-frontmatter                  # .md frontmatter parsing
uv add aiosqlite                           # Async SQLite
uv add rich                                # Beautiful CLI output
uv add httpx                               # Async HTTP client
uv add python-dotenv                       # .env loading

# 5. Install dev dependencies
uv add --dev pytest pytest-asyncio ruff mypy

# 6. Setup frontend
cd frontend && npm install && cd ..
cd carousel_renderer && npm install && cd ..

# 7. Setup environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 13.2 Environment Variables (`.env`)

```bash
# ── LLM PROVIDERS ──
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...

# ── LANGSMITH TRACING ──
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=contentforge
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com

# ── APP CONFIG ──
DATA_DIR=./data
LOG_LEVEL=DEBUG
PIPELINE_DB_PATH=./data/pipeline.db
```

LangSmith automatically traces all agent operations when these environment variables are set — no additional code needed for basic tracing.

### 13.3 Running the System

```bash
# Start the Python API backend
uv run uvicorn api.main:app --reload --port 8000

# Start the React frontend (separate terminal)
cd frontend && npm run dev

# Start the carousel renderer (separate terminal)
cd carousel_renderer && npm run dev

# ── TESTING INDIVIDUAL NODES ──
# Run a single node with test input:
uv run python scripts/run_node.py --node topic_scorer \
  --input tests/fixtures/sample_topics.json

# Fire a single event:
uv run python scripts/fire_event.py --event content.create \
  --topic-id topic_003

# Run all tests:
uv run pytest tests/ -v

# Run specific node test:
uv run pytest tests/test_nodes/test_caption_writer.py -v
```

---

## 14. LANGSMITH INTEGRATION — FULL OBSERVABILITY

LangSmith integrates smoothly with LangGraph and can trace both LLM calls and tools with minimal instrumentation.

### 14.1 What Gets Traced Automatically

```
┌─────────────────────────────────────────────────────────┐
│               LANGSMITH DASHBOARD VIEW                   │
│                                                         │
│  Project: contentforge                                   │
│                                                         │
│  ┌─ Trace: "week_2026-W16_pipeline" ──────────────────┐ │
│  │                                                     │ │
│  │  ├─ Node: brand_context_loader      [23ms]         │ │
│  │  ├─ Node: research_prompt_generator  [2.1s]        │ │
│  │  │   └─ LLM: gpt-5-chat            [1.8s]         │ │
│  │  │       ├─ Input tokens: 1,240                    │ │
│  │  │       ├─ Output tokens: 890                     │ │
│  │  │       └─ Cost: $0.021                           │ │
│  │  ├─ [INTERRUPT: human_research]     [45m paused]   │ │
│  │  ├─ Node: research_parser           [3.2s]         │ │
│  │  │   └─ LLM: groq/llama-3.3-70b    [890ms]        │ │
│  │  ├─ Node: topic_scorer              [4.1s]         │ │
│  │  │   └─ LLM: gpt-5-chat            [3.8s]         │ │
│  │  └─ ... (every node visible)                       │ │
│  │                                                     │ │
│  │  Total cost: $0.47 │ Total tokens: 28,450          │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                         │
│  ┌─ Trace: "chat_edit_topic_003" ──────────────────────┐│
│  │  ├─ edit_router: identified "theme" change          ││
│  │  ├─ theme_designer: re-run with edit context        ││
│  │  └─ diff_presenter: before/after comparison         ││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

### 14.2 Custom Tracing Tags

Every node call adds metadata tags for filtering in LangSmith:

```
Tags structure:
  - week: "2026-W16"
  - phase: "content_creation"
  - node: "caption_writer"
  - topic_id: "topic_003"
  - format: "carousel"
  - platform: "instagram"
  - variant: "A"
  - trigger: "event" | "pipeline" | "manual_test"
```

This lets you filter in LangSmith: *"Show me all caption_writer calls for carousels that cost more than $0.05"*

---

## 15. COMPLETE PIPELINE FLOW — USER JOURNEY

Here's exactly what happens from the user's perspective:

```
WEEK START (e.g., Sunday evening)
│
├── 1. User opens Dashboard → clicks "Start New Week"
│      → System creates week folder, loads brand context
│      → System generates 4 research prompts
│      → UI shows: 4 prompt cards with "Copy" buttons
│
├── 2. User copies Prompt #1 → pastes into Perplexity
│      → Gets results → pastes back into UI text box
│      → Repeats for Prompts #2, #3, #4
│      → Clicks "Submit All Research"
│      → System parses → scores → shows Topic Bank (15-25 topics)
│
├── 3. System auto-generates Weekly Plan (7 days)
│      → UI shows calendar view with topic cards
│      → User reviews: can drag/drop, swap topics, change formats
│      → User SELECTS which topics to create (maybe 5 of 7 for now)
│      → Clicks "Approve Plan"
│
├── 4. System generates Deep Research Prompts (only for selected topics)
│      → UI shows: 5 prompt cards (one per selected topic)
│      → User copies each → pastes into Gemini/ChatGPT
│      → Gets detailed info → pastes back per topic
│      → Clicks "Submit Deep Research"
│
├── 5. User clicks "Create Content" on any topic card
│      (EVENT-DRIVEN — doesn't run whole pipeline!)
│      → System routes based on format
│      → Generates: theme, image prompts, captions (2 variants each),
│        slides/script/storyboard (format-dependent)
│      → All saved as .md files
│      → UI shows full content preview
│
├── 6. User reviews content in ContentReview page
│      → Sees: theme, image prompt, captions per platform (tabbed)
│      → CAN CHAT: "I want the LinkedIn caption to be more formal"
│        → System re-runs only caption_writer for LinkedIn
│        → Shows before/after diff
│        → User approves or continues chatting
│      → CAN CHAT: "Change the color palette to dark mode"
│        → System re-runs only theme_designer
│        → Cascades: if theme changes, image prompt auto-updates
│
├── 7. User approves each post individually
│      → Triggers validation (char limits, completeness)
│      → Triggers export (renders carousels, packages files)
│
├── 8. User goes to ExportView
│      → Downloads: image prompts, captions (.txt), carousel slides (.png)
│      → Opens File Explorer to browse/edit any .md file directly
│
└── 9. Throughout the week, user can:
       → Come back and create content for remaining topics
       → Edit any existing content via chat
       → View logs to understand what the system did
       → Check LangSmith for cost/performance analysis
```

---

## 16. TECHNICAL PATTERNS & DECISIONS

### 16.1 Event-Driven Node Execution Pattern

Every node follows this contract:

```
EVERY NODE FUNCTION SIGNATURE:

async def node_name(
    input: NodeInput,           # Typed Pydantic model
    context: PipelineContext,   # week_id, topic_id, brand, config
    memory: FileMemory,         # File read/write access
    llm: LLMGateway,           # LLM caller (auto-selects model)
    logger: PipelineLogger      # Structured logging
) -> NodeOutput:                # Typed Pydantic model

KEY RULES:
1. PURE FUNCTION: Same input → same behavior (LLM randomness aside)
2. FILE I/O: All reads/writes go through FileMemory (never raw file ops)
3. LLM CALLS: All go through LLMGateway (never raw API calls)
4. LOGGING: Every significant step logged via PipelineLogger
5. TESTABLE: Can instantiate with mock FileMemory + mock LLM for tests
6. NO SIDE EFFECTS: Doesn't modify global state, only returns output
```

### 16.2 How a Node is Called in 3 Different Ways

```
WAY 1: Via Pipeline (LangGraph)
─────────────────────────────
LangGraph invokes the node as part of the graph traversal.
State is managed by LangGraph checkpointer (SQLite).

WAY 2: Via Event (API)
──────────────────────
POST /api/events/content.create { topic_id: "topic_003" }
→ Event bus looks up which node(s) to call
→ Loads latest state from SQLite + file memory
→ Calls the node function directly
→ Saves output to file memory + SQLite
→ Returns result to API caller

WAY 3: Via CLI (Testing)
────────────────────────
uv run python scripts/run_node.py --node caption_writer \
  --input tests/fixtures/caption_input.json
→ Loads input from JSON file
→ Creates mock context with test week
→ Calls node function
→ Prints output to terminal + saves to test_output/
→ Traces appear in LangSmith (tagged: trigger=manual_test)
```

### 16.3 Chat Edit — How It Connects

```
User message: "Make the Instagram caption shorter and punchier"
                    │
                    ▼
           ┌────────────────┐
           │  EDIT ROUTER    │   (Groq — fast)
           │                 │
           │  Analyzes msg → │
           │  Determines:    │
           │  • target: caption │
           │  • platform: instagram │
           │  • action: rewrite │
           │  • style: "shorter, punchier" │
           └────────┬────────┘
                    │
                    ▼
           ┌────────────────┐
           │ CAPTION WRITER  │   (OpenAI — re-run)
           │                 │
           │ Gets:           │
           │ • Original caption (from .md file) │
           │ • Edit instruction │
           │ • Brand context │
           │ • Platform rules │
           │                 │
           │ System prompt   │
           │ includes:       │
           │ "USER WANTS     │
           │  EDIT: shorter, │
           │  punchier.      │
           │  Original was:  │
           │  [old caption]" │
           └────────┬────────┘
                    │
                    ▼
           ┌────────────────┐
           │ DIFF PRESENTER  │
           │                 │
           │ Shows user:     │
           │ BEFORE: "🚨 Claude 4 just dropped..." (1,847 chars) │
           │ AFTER:  "Claude 4 is here. ..." (1,204 chars) │
           │                 │
           │ [Approve] [Try Again] [Custom Edit] │
           └────────────────┘
                    │
                    ▼
           Saves new version to:
           data/weeks/2026-W16/05_content/monday_topic_001/
             captions/instagram_v1.md (version: 3)
           Updates edit_history.md with chat log
```

---

## 17. CAROUSEL RENDERER — ARCHITECTURE

```
┌─────────────────────────────────────────────────────┐
│              CAROUSEL RENDER SERVICE                  │
│                                                     │
│  Input: react_component.jsx + theme.json             │
│  Output: slide_01.png, slide_02.png, ... + .gif      │
│                                                     │
│  FLOW:                                               │
│  1. Python backend generates React code (.jsx)       │
│  2. Sends to carousel_renderer service via HTTP      │
│     POST /render { jsx: "...", theme: {...} }        │
│  3. React app renders slides in headless browser     │
│  4. Puppeteer screenshots each slide at 1080×1350px  │
│     (Instagram carousel optimal size)                │
│  5. Optionally stitches into animated GIF preview    │
│  6. Returns image URLs / saves to exports folder     │
│                                                     │
│  TEMPLATES:                                          │
│  • MinimalDark  — dark bg, clean type, subtle glow   │
│  • BoldGradient — gradient bg, large bold headers    │
│  • CleanWhite   — white bg, colored accents          │
│  • TechNeon     — dark bg, neon highlights, code font│
│  • (Extensible: add new .jsx template files)         │
│                                                     │
│  The react_code_generator agent picks a template     │
│  and customizes it with topic-specific content        │
│  and the theme_designer's color/font choices.        │
└─────────────────────────────────────────────────────┘
```

---

## 18. DEPENDENCY GRAPH — BUILD ORDER

If building this incrementally, here's the order:

```
SPRINT 1: Foundation (Week 1)
├── uv environment setup
├── config/ (all YAML files)
├── prompts/ (all system prompt files — even if draft)
├── src/contentforge/core/
│   ├── state.py
│   ├── config_loader.py
│   ├── llm_gateway.py
│   ├── file_memory.py
│   ├── prompt_loader.py
│   ├── logger.py
│   └── db.py
├── LangSmith integration (env vars + auto-tracing)
└── scripts/run_node.py (CLI test runner)

SPRINT 2: Research Phase (Week 2)
├── nodes/research/* (all 3 nodes)
├── api/routes/pipeline.py + research.py
├── tests for research nodes
└── Basic frontend: Dashboard + ResearchLoop pages

SPRINT 3: Scoring & Planning (Week 2-3)
├── nodes/scoring/* (scorer + planner)
├── api/routes/plan.py
├── tests for scoring nodes
└── Frontend: CalendarView page

SPRINT 4: Content Creation (Week 3-4)
├── nodes/content/* (all creators, all sub-nodes)
├── api/routes/content.py
├── events.py (event bus)
├── tests for content nodes
└── Frontend: ContentReview page

SPRINT 5: Chat Editing (Week 4)
├── nodes/editing/* (edit router, chat agent, diff)
├── api/routes/chat.py + websockets/
└── Frontend: ChatEditor component

SPRINT 6: Export & Polish (Week 5)
├── nodes/export/*
├── carousel_renderer/ (React + Puppeteer)
├── api/routes/export.py + files.py + logs.py
└── Frontend: ExportView + FileExplorer + LogViewer

SPRINT 7: Testing & Refinement (Week 5-6)
├── End-to-end testing
├── Prompt tuning (iterate on system prompts)
├── UI polish
└── Documentation
```

---

## 19. APPENDIX A — pyproject.toml

```toml
[project]
name = "contentforge"
version = "0.1.0"
description = "AI Marketing Content Pipeline"
requires-python = ">=3.12"

dependencies = [
    # ── LangChain / LangGraph ──
    "langgraph>=0.4.0",
    "langchain>=0.3.0",
    "langchain-openai>=0.3.0",
    "langchain-community>=0.3.0",
    "langsmith>=0.2.0",
    
    # ── API Server ──
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "websockets>=13.0",
    
    # ── Data & Config ──
    "pydantic>=2.10.0",
    "pyyaml>=6.0",
    "python-frontmatter>=1.1.0",
    "aiosqlite>=0.20.0",
    
    # ── Utilities ──
    "httpx>=0.27.0",
    "python-dotenv>=1.0.0",
    "rich>=13.9.0",
    "jinja2>=3.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

## 20. APPENDIX B — QUICK REFERENCE CARD

```
┌─────────────────────────────────────────────────────────┐
│              CONTENTFORGE — QUICK REFERENCE               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  START WEEK:     POST /api/pipeline/start               │
│  SUBMIT RESEARCH: POST /api/research/submit             │
│  APPROVE PLAN:   POST /api/plan/approve                 │
│  CREATE CONTENT: POST /api/events/content.create        │
│  CHAT EDIT:      WS /ws/chat/{topic_id}                 │
│  EXPORT:         POST /api/export/{topic_id}            │
│                                                         │
│  TEST A NODE:    uv run python scripts/run_node.py      │
│                  --node {name} --input {file}            │
│                                                         │
│  FIRE AN EVENT:  uv run python scripts/fire_event.py    │
│                  --event {name} --topic-id {id}          │
│                                                         │
│  VIEW LOGS:      GET /api/logs/{week_id}/pipeline       │
│  VIEW FILES:     GET /api/files/{week_id}/tree          │
│  VIEW TRACES:    https://smith.langchain.com             │
│                                                         │
│  ALL PROMPTS:    prompts/ folder                        │
│  ALL CONFIGS:    config/ folder                         │
│  ALL DATA:       data/weeks/{week_id}/ folder           │
│                                                         │
│  RUN BACKEND:    uv run uvicorn api.main:app --reload   │
│  RUN FRONTEND:   cd frontend && npm run dev             │
│  RUN TESTS:      uv run pytest tests/ -v               │
│  LINT:           uv run ruff check src/                 │
└─────────────────────────────────────────────────────────┘
```

---

