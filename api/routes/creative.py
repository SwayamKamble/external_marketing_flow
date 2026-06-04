"""Creative Manager API routes.

Completely separate from pipeline routes. Own prefix: /creative/
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from contentforge.creative_manager.db import CreativeManagerDB
from contentforge.creative_manager.engine import CreativeManagerEngine

router = APIRouter(prefix="/creative", tags=["creative-manager"])

# ── Singleton instances ──
_db: CreativeManagerDB | None = None
_engine = CreativeManagerEngine()


def _get_db() -> CreativeManagerDB:
    global _db
    if _db is None:
        _db = CreativeManagerDB(db_path="data/creative_manager.db")
        _db.initialize()
    return _db


# ── Request/Response schemas ──

class StartSessionRequest(BaseModel):
    week_id: str = Field(..., description="Week identifier, e.g. '2026-W23'")
    niche: str = Field("AI & Tech", description="Content niche for topic discovery")
    topic_count: int = Field(12, description="Number of topics to discover")


class StartSessionResponse(BaseModel):
    session_id: str
    week_id: str
    status: str
    research_prompt: str
    niche: str


class SubmitResearchRequest(BaseModel):
    raw_research: str = Field(..., description="Pasted research text (JSON from ChatGPT/Perplexity)")


class SelectTopicsRequest(BaseModel):
    topic_ids: list[str] = Field(..., description="Selected topic IDs")


class UpdatePlanRequest(BaseModel):
    plan_id: int
    updates: dict[str, Any]


class SessionResponse(BaseModel):
    session_id: str
    week_id: str
    status: str
    niche: str
    topics: list[dict[str, Any]]
    weekly_plan: list[dict[str, Any]]
    research_prompt: str
    created_at: str
    updated_at: str


# ── Endpoints ──

@router.post("/start", response_model=StartSessionResponse)
async def start_session(req: StartSessionRequest):
    """Start a new Creative Manager session for a week."""
    db = _get_db()

    session_id = f"cm_{req.week_id}_{uuid.uuid4().hex[:8]}"
    prompt = _engine.generate_research_prompt(niche=req.niche, topic_count=req.topic_count)

    db.create_session(
        session_id=session_id,
        week_id=req.week_id,
        niche=req.niche,
        research_prompt=prompt,
    )

    return StartSessionResponse(
        session_id=session_id,
        week_id=req.week_id,
        status="input_needed",
        research_prompt=prompt,
        niche=req.niche,
    )


@router.get("/{session_id}/status", response_model=SessionResponse)
async def get_session_status(session_id: str):
    """Get full session status with topics and plan."""
    db = _get_db()
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    topics = db.get_topics(session_id)
    plan = db.get_plan(session_id)

    return SessionResponse(
        session_id=session["id"],
        week_id=session["week_id"],
        status=session["status"],
        niche=session.get("niche", "AI & Tech"),
        topics=topics,
        weekly_plan=plan,
        research_prompt=session.get("research_prompt", ""),
        created_at=session["created_at"],
        updated_at=session["updated_at"],
    )


@router.post("/{session_id}/submit-research")
async def submit_research(session_id: str, req: SubmitResearchRequest):
    """Submit pasted research text. Parses topics and scores them."""
    db = _get_db()
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    topics = _engine.parse_topics(req.raw_research)
    if not topics:
        raise HTTPException(
            status_code=400,
            detail="Could not parse any topics from the research text. Make sure it's valid JSON."
        )

    # Save topics to DB
    topic_dicts = [t.model_dump() for t in topics]
    db.save_topics(session_id, topic_dicts)
    db.update_session_status(session_id, "topics_ready")

    return {
        "status": "topics_ready",
        "topics_count": len(topics),
        "topics": topic_dicts,
    }


@router.post("/{session_id}/select-topics")
async def select_topics(session_id: str, req: SelectTopicsRequest):
    """User selects which topics to include in the weekly plan."""
    db = _get_db()
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.select_topics(session_id, req.topic_ids)

    return {"status": "ok", "selected_count": len(req.topic_ids)}


@router.post("/{session_id}/plan-week")
async def plan_week(session_id: str):
    """Generate the weekly content calendar from selected topics."""
    db = _get_db()
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    all_topics_raw = db.get_topics(session_id)
    # Filter to selected only
    from contentforge.creative_manager.models import TopicIdea, EngagementScores, PlatformAngle

    selected_topics: list[TopicIdea] = []
    for t in all_topics_raw:
        if not t.get("selected"):
            continue
        scores_raw = t.get("engagement_scores", {})
        scores = EngagementScores(**scores_raw) if isinstance(scores_raw, dict) else EngagementScores()

        angles_raw = t.get("platform_angles", [])
        angles = []
        for a in angles_raw:
            if isinstance(a, dict):
                angles.append(PlatformAngle(**a))

        selected_topics.append(TopicIdea(
            id=t["id"],
            title=t["title"],
            summary=t.get("summary", ""),
            category=t.get("category", ""),
            source=t.get("source", ""),
            educational_angle=t.get("educational_angle", ""),
            why_it_works=t.get("why_it_works", ""),
            teaching_points=t.get("teaching_points", []),
            best_platforms=t.get("best_platforms", []),
            engagement_scores=scores,
            platform_angles=angles,
            selected=True,
        ))

    if not selected_topics:
        raise HTTPException(status_code=400, detail="No topics selected. Select topics first.")

    plan = _engine.plan_week(selected_topics, session["week_id"])
    plan_dicts = [p.model_dump() for p in plan]

    db.save_plan(session_id, plan_dicts)
    db.update_session_status(session_id, "planned")

    return {
        "status": "planned",
        "plan": plan_dicts,
    }


@router.put("/{session_id}/update-plan")
async def update_plan(session_id: str, req: UpdatePlanRequest):
    """Update a specific day in the plan."""
    db = _get_db()
    session = db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.update_plan_day(req.plan_id, req.updates)
    return {"status": "ok"}


@router.get("/sessions")
async def list_sessions(limit: int = 20):
    """List all Creative Manager sessions."""
    db = _get_db()
    sessions = db.list_sessions(limit=limit)
    return {"sessions": sessions}


# ──────────────────────────────────────────────────────────────────────
# Quick Prompt Pipeline Endpoints (revamped 6-step flow)
# ──────────────────────────────────────────────────────────────────────

from contentforge.creative_manager.prompt_interpreter import PromptInterpreter
from contentforge.creative_manager.models import (
    SeriesPlan, StructuredIntent, SeriesDay, DiscoveredTopic,
)

_interpreter: PromptInterpreter | None = None


def _get_interpreter() -> PromptInterpreter:
    global _interpreter
    if _interpreter is None:
        _interpreter = PromptInterpreter()
    return _interpreter


class QuickStartRequest(BaseModel):
    series_length: int = Field(7, description="Number of days in the series (3, 5, 7, 10, 14, 30)")
    content_filter: str = Field("", description="Content filter: educational, news, trending_ai, or empty for all")
    user_topic: str = Field("", description="Optional: user's topic. If provided, skip discovery and go straight to research prompt.")
    platform: str = Field("instagram", description="Target platform: instagram, linkedin, x")


class QuickSubmitTopicsRequest(BaseModel):
    raw_json: str = Field(..., description="Pasted JSON from Perplexity with discovered topics")


class QuickSelectTopicRequest(BaseModel):
    topic_id: str = Field(..., description="ID of the selected topic")


class QuickResearchRequest(BaseModel):
    raw_research: str = Field(..., description="Pasted JSON from Claude/Perplexity with deep research")


class QuickChatRequest(BaseModel):
    message: str = Field(..., description="User's message / edit request")


@router.post("/quick/start")
async def quick_start(req: QuickStartRequest):
    """Step 1: Start a new Quick Prompt session.

    Two paths:
    - Path A (user_topic provided): Skip discovery, generate deep research prompt directly.
    - Path B (no user_topic): Generate topic discovery prompt for Perplexity.
    """
    db = _get_db()
    interpreter = _get_interpreter()

    effective_filter = req.content_filter or "educational"
    has_topic = bool(req.user_topic.strip())
    platform = req.platform or "instagram"

    # Build structured intent
    intent = StructuredIntent(
        series_length=req.series_length,
        content_filter=req.content_filter,
        platform=platform,
        topic_theme=req.user_topic.strip() if has_topic else "",
    )

    session_id = f"qp_{uuid.uuid4().hex[:12]}"

    if has_topic:
        # PATH A: User already has a topic — skip discovery, go straight to research prompt
        topic_obj = DiscoveredTopic(
            id=f"topic_{uuid.uuid4().hex[:8]}",
            title=req.user_topic.strip(),
            summary=f"User-provided topic: {req.user_topic.strip()}",
            target_audience="AI enthusiasts, developers, tech professionals, students",
            category=effective_filter,
        )

        deep_research_prompt = interpreter.generate_deep_research_prompt(
            topic_obj, req.series_length, effective_filter, platform
        )

        intent.target_audience = topic_obj.target_audience

        db.create_quick_session(
            session_id=session_id,
            user_prompt=f"{req.series_length}-day series: {req.user_topic.strip()}",
            structured_intent=intent.model_dump(),
            content_filter=req.content_filter,
            discovery_prompt="",
        )
        db.update_quick_session(
            session_id,
            selected_topic=topic_obj.model_dump(),
            deep_research_prompt=deep_research_prompt,
            status="research_prompt_ready",
        )

        return {
            "session_id": session_id,
            "status": "research_prompt_ready",
            "series_length": req.series_length,
            "content_filter": req.content_filter,
            "platform": platform,
            "user_topic": req.user_topic.strip(),
            "selected_topic": topic_obj.model_dump(),
            "deep_research_prompt": deep_research_prompt,
            "discovery_prompt": "",
        }
    else:
        # PATH B: No topic — generate discovery prompt for Perplexity
        discovery_prompt = interpreter.generate_topic_discovery_prompt(
            req.series_length, effective_filter, platform
        )

        db.create_quick_session(
            session_id=session_id,
            user_prompt=f"{req.series_length}-day {effective_filter} series",
            structured_intent=intent.model_dump(),
            content_filter=req.content_filter,
            discovery_prompt=discovery_prompt,
        )
        db.update_quick_session(
            session_id,
            status="discovery_prompt_ready",
        )

        return {
            "session_id": session_id,
            "status": "discovery_prompt_ready",
            "series_length": req.series_length,
            "content_filter": req.content_filter,
            "platform": platform,
            "user_topic": "",
            "discovery_prompt": discovery_prompt,
            "deep_research_prompt": "",
        }


@router.post("/quick/{session_id}/submit-topics")
async def quick_submit_topics(session_id: str, req: QuickSubmitTopicsRequest):
    """Step 2→3: Parse pasted topics JSON and show discovered topics for selection."""
    db = _get_db()
    interpreter = _get_interpreter()

    session = db.get_quick_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Quick prompt session not found")

    topics = interpreter.parse_discovered_topics(req.raw_json)
    if not topics:
        raise HTTPException(
            status_code=400,
            detail="Could not parse any topics from the JSON. Make sure it contains a list of topic objects."
        )

    topics_dicts = [t.model_dump() for t in topics]
    db.update_quick_session(
        session_id,
        discovered_topics=topics_dicts,
        status="topics_discovered",
    )

    return {
        "status": "topics_discovered",
        "topics_count": len(topics),
        "topics": topics_dicts,
    }


@router.post("/quick/{session_id}/select-topic")
async def quick_select_topic(session_id: str, req: QuickSelectTopicRequest):
    """Step 3→4: User selects a topic, pipeline generates deep research prompt."""
    db = _get_db()
    interpreter = _get_interpreter()

    session = db.get_quick_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Quick prompt session not found")

    discovered = session.get("discovered_topics", [])
    if not discovered:
        raise HTTPException(status_code=400, detail="No discovered topics found. Submit topics first.")

    # Find selected topic
    selected = None
    for t in discovered:
        if t.get("id") == req.topic_id:
            selected = t
            break

    if not selected:
        raise HTTPException(status_code=400, detail=f"Topic '{req.topic_id}' not found in discovered topics.")

    topic_obj = DiscoveredTopic(**selected)
    si = session.get("structured_intent", {})
    series_length = si.get("series_length", 7)
    content_filter = session.get("content_filter", "educational")
    platform = si.get("platform", "instagram")

    # Generate deep research prompt
    deep_research_prompt = interpreter.generate_deep_research_prompt(
        topic_obj, series_length, content_filter, platform
    )

    # Update intent with the selected topic theme
    si["topic_theme"] = topic_obj.title
    si["target_audience"] = topic_obj.target_audience or si.get("target_audience", "")
    si["sub_topics"] = topic_obj.suggested_angles

    db.update_quick_session(
        session_id,
        selected_topic=selected,
        deep_research_prompt=deep_research_prompt,
        structured_intent=si,
        user_prompt=f"{series_length}-day series: {topic_obj.title}",
        status="research_prompt_ready",
    )

    return {
        "status": "research_prompt_ready",
        "selected_topic": selected,
        "deep_research_prompt": deep_research_prompt,
    }


@router.post("/quick/{session_id}/submit-research")
async def quick_submit_research(session_id: str, req: QuickResearchRequest):
    """Step 4→5: Parse deep research JSON into day-wise plan."""
    db = _get_db()
    interpreter = _get_interpreter()

    session = db.get_quick_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Quick prompt session not found")

    plan = interpreter.parse_series_research(req.raw_research)
    if not plan:
        try:
            with open("data/failed_research.txt", "w", encoding="utf-8") as f:
                f.write(req.raw_research)
        except Exception:
            pass
        raise HTTPException(
            status_code=400,
            detail="Could not parse the research. Make sure it's valid JSON with a 'days' array."
        )

    # Merge intent from session
    stored_intent = session.get("structured_intent", {})
    if stored_intent:
        plan.intent = StructuredIntent(**stored_intent)

    db.update_quick_session(
        session_id,
        series_plan=plan.model_dump(),
        status="plan_review",
    )

    return {
        "status": "plan_review",
        "days_count": len(plan.days),
        "plan": plan.model_dump(),
    }


@router.post("/quick/{session_id}/chat")
async def quick_chat_edit(session_id: str, req: QuickChatRequest):
    """Chat edit — available at ALL stages after step 1.

    Handles both plan edits (when a plan exists) and general conversation.
    Persists full chat history to DB.
    """
    db = _get_db()
    interpreter = _get_interpreter()

    session = db.get_quick_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Quick prompt session not found")

    chat_history = session.get("chat_history", [])

    plan_raw = session.get("series_plan", {})
    has_plan = plan_raw and plan_raw.get("days")

    if has_plan:
        # Plan exists — apply chat edit via LLM
        try:
            current_plan = SeriesPlan(
                intent=StructuredIntent(**plan_raw.get("intent", {})),
                days=[SeriesDay(**d) for d in plan_raw.get("days", [])],
                status=plan_raw.get("status", "draft"),
                chat_history=chat_history,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load plan: {str(e)}")

        try:
            updated_plan = await interpreter.apply_chat_edit(current_plan, req.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to apply edit: {str(e)}")

        # Extract chat history from the updated plan (apply_chat_edit appends to it)
        new_chat_history = updated_plan.chat_history

        db.update_quick_session(
            session_id,
            series_plan=updated_plan.model_dump(),
            chat_history=new_chat_history,
        )

        return {
            "status": session.get("status", "plan_review"),
            "plan": updated_plan.model_dump(),
            "chat_history": new_chat_history,
        }
    else:
        # No plan yet — store as a general message
        chat_history.append({"role": "user", "message": req.message})
        chat_history.append({
            "role": "assistant",
            "message": f"Noted! I've recorded your request. This will be applied when the plan is generated."
        })

        db.update_quick_session(
            session_id,
            chat_history=chat_history,
        )

        return {
            "status": session.get("status", "created"),
            "chat_history": chat_history,
        }


@router.post("/quick/{session_id}/approve")
async def quick_approve(session_id: str):
    """Step 5→6: Approve the plan and generate a production-ready prompt."""
    db = _get_db()
    interpreter = _get_interpreter()

    session = db.get_quick_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Quick prompt session not found")

    plan_raw = session.get("series_plan", {})
    if not plan_raw or not plan_raw.get("days"):
        raise HTTPException(status_code=400, detail="No series plan found.")

    try:
        plan = SeriesPlan(
            intent=StructuredIntent(**plan_raw.get("intent", {})),
            days=[SeriesDay(**d) for d in plan_raw.get("days", [])],
            status="approved",
            chat_history=session.get("chat_history", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load plan: {str(e)}")

    production_prompt = interpreter.generate_production_prompt(plan)

    plan.status = "finalized"
    db.update_quick_session(
        session_id,
        series_plan=plan.model_dump(),
        production_prompt=production_prompt,
        status="finalized",
    )

    return {
        "status": "finalized",
        "production_prompt": production_prompt,
        "plan": plan.model_dump(),
    }


@router.get("/quick/{session_id}/status")
async def quick_status(session_id: str):
    """Get full Quick Prompt session status."""
    db = _get_db()
    session = db.get_quick_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Quick prompt session not found")
    return session


@router.get("/quick/sessions")
async def list_quick_sessions(limit: int = 20):
    """List all Quick Prompt sessions for dashboard."""
    db = _get_db()
    sessions = db.list_quick_sessions(limit=limit)
    return {"sessions": sessions}

