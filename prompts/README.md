# System Prompts — ContentForge

## Overview

Every agent/node in the ContentForge pipeline has its system prompt stored
as a dedicated `.md` file in this directory. This makes prompts easy to:

- **Read and edit** — plain markdown, no code changes needed
- **Version control** — track prompt changes in git
- **Debug** — see exactly what instructions each agent receives
- **Iterate** — tweak prompts without touching Python code

## Directory Structure

```
prompts/
├── _global_context.md          # Injected into ALL agents
├── research/
│   ├── research_prompt_generator.md
│   ├── research_parser.md
│   └── deep_research_prompt_generator.md
├── scoring/
│   ├── topic_scorer.md
│   └── calendar_planner.md
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
├── editing/
│   ├── edit_router.md
│   └── diff_presenter.md
├── export/
│   ├── validator.md
│   └── week_summary_generator.md
└── README.md                   # This file
```

## Prompt File Format

Every prompt file uses YAML frontmatter + markdown body:

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
You are an expert social media copywriter...

# TASK
Write two caption variants...

# RULES
- Variant A: Story-telling approach
- Variant B: Direct value approach
...

# OUTPUT FORMAT
Return JSON:
{ ... }
```

## Template Variables

Prompts support Jinja2 template variables using `{{ variable_name }}` syntax.
Common variables:

| Variable | Source | Description |
|----------|--------|-------------|
| `{{ brand_tone }}` | brand_dna.md | Brand voice/tone |
| `{{ platform_name }}` | platform_rules.yaml | Target platform |
| `{{ char_limit }}` | platform_rules.yaml | Character limit |
| `{{ topic_title }}` | Pipeline state | Current topic |
| `{{ content_format }}` | Pipeline state | carousel/reel/etc |
| `{{ key_points }}` | Deep research | Research findings |

## Editing Tips

1. **Test before deploying** — Use `scripts/run_node.py` to test a node with a modified prompt
2. **Be specific** — Vague instructions produce vague output
3. **Include examples** — Show the agent what good output looks like
4. **Constrain the output** — Use JSON format specs to get structured responses
5. **Iterate** — Small changes, test, repeat
