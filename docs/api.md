# ContentForge API Reference

This document outlines the REST API and WebSocket endpoints exposed by the ContentForge engine.

## Base URL
Default local server runs on `http://localhost:8000`

---

## 1. Pipeline Execution (`/pipeline`)

### Start Pipeline
`POST /pipeline/start`
Initializes and starts the LangGraph background processing for a specified week.

**Request Body:**
```json
{
  "week_id": "2026-W16"
}
```

**Response:** `200 OK`
```json
{
  "week_id": "2026-W16",
  "status": "research",
  "pending_topic_id": null,
  "human_action_required": false,
  "human_action_type": null,
  "state": { ... }
}
```

### Get Status
`GET /pipeline/{week_id}/status`
Retrieves the real-time state of the graph for the requested week. Used to check if human intervention is required.

**Response:** `200 OK` (Same schema as `/start`)

### Submit Feedback
`POST /pipeline/{week_id}/feedback`
Resumes a blocked pipeline graph by supplying one of the strict HITL actions.

**Request Body:**
```json
{
  "action": "select_topics",  // "approve", "approve_plan", "approve_content", "edit", "select_topics", "supply_raw_research", "supply_deep_research"
  "selected_topics": ["topic_a", "topic_b"],
  "topic_id": "topic_a",
  "deep_research_text": "External deep research result for topic_a",
  "feedback": "Make it shorter.",
  "raw_research_data": "...",
  "deep_research_data": {
    "topic_a": "..."
  }
}
```

**Validation Rules:**
- `select_topics` requires non-empty `selected_topics` and every topic must exist in `weekly_plan`.
- `supply_raw_research` requires `raw_research_data`.
- `supply_deep_research` requires a topic-scoped payload (`topic_id` + `deep_research_text`, or `deep_research_data[topic_id]`) and must match `pending_topic_id` when present.
- `edit` requires non-empty `feedback`.

**Response:** `200 OK` (Updated state showing the graph progressing)

---

## 2. Carousel Preview (`/carousel`)

### Render Carousel Preview
`POST /carousel/render/{week_id}/{topic_id}`
Renders generated carousel TSX code into slide PNG previews using the Node renderer service.

**Response:** `200 OK`
```json
{
  "week_id": "2026-W16",
  "topic_id": "topic_a",
  "count": 3,
  "images": [
    {
      "filename": "slide_01.png",
      "data_url": "data:image/png;base64,..."
    }
  ]
}
```

---

## 3. Memory & Artifacts (`/memory`)

### Get Brand Context
`GET /memory/brand/context`
Returns the cached brand configuration (DNA and style guides) loaded from disk.

**Response:** `200 OK`
```json
{
  "brand_dna": { ... },
  "style_guide": { ... },
  "content_pillars": { ... }
}
```

### Read Artifact
`GET /memory/artifact/{week_id}/{phase}/{filename}?topic_id={topic_id}`
Returns the raw content of a stored markdown or JSON artifact from the file system.

**Response:** `200 OK`
```json
{
  "week_id": "2026-W16",
  "phase": "05_content",
  "filename": "carousel_slides.md",
  "content": "# Slide 1\n...",
  "metadata": {}
}
```

---

## 4. Real-Time Events (`/events`)

### Log Streaming
`WS /events/ws`
A WebSocket endpoint that tails the engine event log. Used by the frontend console to display real-time progress bars and node executions.

**Message Format (Server -> Client):**
```json
{
  "timestamp": "2026-04-16T15:00:00Z",
  "level": "INFO",
  "event": "node_execution.start",
  "data": {
    "node_name": "caption_writer",
    "topic_id": "ai_agents_1"
  }
}
```
