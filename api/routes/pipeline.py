"""Pipeline execution endpoints."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from api.schemas import StartPipelineRequest, PipelineStatusResponse, FeedbackRequest
from api.dependencies import get_node_context, get_memory
from contentforge.core.graph import build_pipeline_graph, DEFAULT_INTERRUPTS
from contentforge.core.state import ContentForgeState, ContentStatus

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

def get_interrupt_status(snapshot) -> tuple[bool, str | None]:
    """Derive human action state from LangGraph interrupt checkpoint."""
    next_nodes = getattr(snapshot, "next", None) or []
    nn = next_nodes[0] if next_nodes else None
    if nn == "research_parser":
        return True, "paste_research"
    if nn == "deep_prompt":
        # Graph paused AFTER planner (interrupt_after) - next node is deep_prompt.
        # User must select topics before deep_prompt can run.
        return True, "select_topics"
    if nn == "deep_parse":
        return True, "paste_deep_research"
    if nn == "edit_router":
        return True, "review_content"
    return False, None
def _get_prompt_content(week_id: str, status: str, action_type: str | None, pending_topic_id: str | None) -> str | None:
    """Load the relevant prompt content from disk for embedding in status responses."""
    try:
        memory = get_memory()
        if action_type == "paste_research" or (not action_type and status == "research"):
            result = memory.read_artifact(week_id=week_id, phase="01_research", filename="research_prompts.md")
            if result.get("exists"):
                return result["content"]
        elif action_type == "paste_deep_research" or status == "deep_research":
            if pending_topic_id:
                result = memory.read_artifact(
                    week_id=week_id, phase="04_deep_research",
                    filename=f"deep_research_prompt_{pending_topic_id}.md"
                )
                if result.get("exists"):
                    return result["content"]
            # Fallback: try generic
            result = memory.read_artifact(week_id=week_id, phase="04_deep_research", filename="deep_research_prompts.md")
            if result.get("exists"):
                return result["content"]
    except Exception:
        pass
    return None

@router.post("/start", response_model=PipelineStatusResponse)
async def start_pipeline(req: StartPipelineRequest, background_tasks: BackgroundTasks):
    """Initializes and runs the LangGraph pipeline for a specific week."""
    
    context = get_node_context(week_id=req.week_id)
    app = build_pipeline_graph(context)
    
    # LangGraph requires a specific thread config to track memory
    config = {"configurable": {"thread_id": req.week_id}}
    
    # Initial state
    initial_state = ContentForgeState(
        week_id=req.week_id,
        pipeline_status="research",
        raw_research=[],
        topic_bank=[],
        weekly_plan=[],
        selected_topics=[],
        topic_queue=[],
        deep_research={},
        raw_deep_research={},
        content={},
        pending_topic_id=None,
        human_action_required=False,
        human_action_type=None,
        carousel_status="",
    )

    # Delete existing thread history in checkpointer to start the pipeline fresh from the entry point.
    try:
        if hasattr(app, "checkpointer") and app.checkpointer:
            if hasattr(app.checkpointer, "delete_thread"):
                app.checkpointer.delete_thread(req.week_id)
            elif hasattr(app.checkpointer, "adelete_thread"):
                await app.checkpointer.adelete_thread(req.week_id)
    except Exception as exc:
        if context.logger:
            context.logger.error("api_start_pipeline", f"Failed to clear thread checkpointer: {exc}")

    # Hard reset existing thread state for this week_id so stale carousel
    # fallback slides from prior runs cannot leak into a new start.
    try:
        app.update_state(config, initial_state.model_dump())
    except Exception:
        pass
    
    # Start graph — it will run through brand_loader + prompt_gen
    # then hit the research_parser interrupt and pause. This is fast (~2-5s).
    import asyncio
    try:
        await asyncio.wait_for(
            app.ainvoke(initial_state.model_dump(), config=config),
            timeout=60
        )
    except asyncio.TimeoutError:
        if context.logger:
            context.logger.error("api_start_pipeline", "Start timed out after 60s")
    except Exception as e:
        if context.logger:
            context.logger.error("api_start_pipeline", f"Failed starting graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    snapshot = app.get_state(config)
    state_obj = ContentForgeState(**snapshot.values)
    req_action, type_action = get_interrupt_status(snapshot)
    
    prompt = _get_prompt_content(req.week_id, state_obj.pipeline_status, type_action, state_obj.pending_topic_id)
    
    return PipelineStatusResponse(
        week_id=req.week_id,
        status="review" if type_action == "review_content" else state_obj.pipeline_status,
        pending_topic_id=state_obj.pending_topic_id,
        human_action_required=req_action,
        human_action_type=type_action,
        state=state_obj.model_dump(),
        prompt_content=prompt,
    )


@router.get("/{week_id}/status", response_model=PipelineStatusResponse)
async def get_status(week_id: str):
    """Gets the current status of the pipeline (reads from LangGraph checkpointer)."""
    context = get_node_context(week_id=week_id)
    app = build_pipeline_graph(context)
    config = {"configurable": {"thread_id": week_id}}
    
    snapshot = app.get_state(config)
    
    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail="Pipeline thread not found")
        
    state_obj = ContentForgeState(**snapshot.values)
    req_action, type_action = get_interrupt_status(snapshot)
    
    prompt = _get_prompt_content(week_id, state_obj.pipeline_status, type_action, state_obj.pending_topic_id)
    
    return PipelineStatusResponse(
        week_id=week_id,
        status="review" if type_action == "review_content" else state_obj.pipeline_status,
        pending_topic_id=state_obj.pending_topic_id,
        human_action_required=req_action,
        human_action_type=type_action,
        state=state_obj.model_dump(),
        prompt_content=prompt,
    )


@router.post("/{week_id}/feedback", response_model=PipelineStatusResponse)
async def provide_feedback(week_id: str, payload: FeedbackRequest):
    """Provide feedback/approval to unblock a waiting pipeline graph."""
    context = get_node_context(week_id=week_id)
    app = build_pipeline_graph(context)
    config = {"configurable": {"thread_id": week_id}}
    
    snapshot = app.get_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail="Pipeline thread not found")
        
    state_obj = ContentForgeState(**snapshot.values)

    if context.logger:
        context.logger.event(
            "api.feedback.received",
            {
                "week_id": week_id,
                "action": payload.action,
                "human_action_type": state_obj.human_action_type,
                "status_before": state_obj.pipeline_status,
            },
        )
    
    # We must patch the state before continuing
    update_data = {
        "human_action_required": False,
        "human_action_type": None
    }
    plan_topic_ids = [item.topic_id for item in state_obj.weekly_plan if item.topic_id]

    if payload.action == "edit":
        if not payload.feedback.strip():
            raise HTTPException(status_code=422, detail="feedback is required for action='edit'")
        update_data["human_feedback"] = payload.feedback
        update_data["pipeline_status"] = "review"
    elif payload.action == "supply_raw_research":
        if not payload.raw_research_data or not payload.raw_research_data.strip():
            raise HTTPException(status_code=422, detail="raw_research_data is required for action='supply_raw_research'")
        try:
            memory = get_memory()
            memory.write_artifact(
                week_id=week_id,
                phase="01_research",
                filename="submitted_raw_research.md",
                content=payload.raw_research_data,
                metadata={
                    "source": "human_submission",
                    "action": "supply_raw_research",
                    "week_id": week_id,
                },
            )
        except AssertionError:
            pass
        update_data["raw_research"] = [payload.raw_research_data]
    elif payload.action == "select_topics":
        selected = payload.selected_topics or []
        selected = [t for t in selected if t]
        if not selected:
            raise HTTPException(status_code=422, detail="selected_topics is required and cannot be empty")

        invalid = [t for t in selected if t not in plan_topic_ids]
        if invalid:
            raise HTTPException(status_code=422, detail=f"Invalid selected_topics: {invalid}")

        update_data["selected_topics"] = selected
        update_data["topic_queue"] = selected
        update_data["pending_topic_id"] = selected[0]
        update_data["topic_index"] = 1
        update_data["topic_total"] = len(selected)
    elif payload.action == "supply_deep_research":
        # Always prefer the current pending_topic_id from graph state
        topic_id = state_obj.pending_topic_id or payload.topic_id
        if not topic_id:
            raise HTTPException(status_code=422, detail="topic_id is required for action='supply_deep_research'")

        # If frontend sent a different topic_id, log it but use the real pending one
        if payload.topic_id and state_obj.pending_topic_id and payload.topic_id != state_obj.pending_topic_id:
            if context.logger:
                context.logger.event("api.topic_id_autocorrect", {
                    "sent": payload.topic_id,
                    "actual_pending": state_obj.pending_topic_id,
                })
            topic_id = state_obj.pending_topic_id

        research_text = payload.deep_research_text
        if not research_text and payload.deep_research_data:
            research_text = payload.deep_research_data.get(topic_id)

        if not research_text or not research_text.strip():
            raise HTTPException(status_code=422, detail="deep_research_text (or deep_research_data[topic_id]) is required")

        try:
            memory = get_memory()
            memory.write_artifact(
                week_id=week_id,
                phase="04_deep_research",
                topic_id=topic_id,
                filename="submitted_deep_research.md",
                content=research_text,
                metadata={
                    "source": "human_submission",
                    "action": "supply_deep_research",
                    "week_id": week_id,
                    "topic_id": topic_id,
                },
            )
        except AssertionError:
            pass

        merged = dict(state_obj.raw_deep_research)
        merged[topic_id] = research_text
        update_data["raw_deep_research"] = merged
    elif payload.action in ("approve", "approve_content"):
        if state_obj.pending_topic_id and state_obj.pending_topic_id in state_obj.content:
            updated_content = dict(state_obj.content)
            tc = updated_content[state_obj.pending_topic_id]
            tc.status = ContentStatus.APPROVED
            updated_content[state_obj.pending_topic_id] = tc
            update_data["content"] = updated_content
            update_data["pipeline_status"] = "export"
    elif payload.action == "approve_plan":
        # No-op action kept for compatibility with existing frontend behavior.
        # The pipeline will wait for explicit `select_topics` before deep research.
        pass
    # 'approve' just clears the interrupt markers and proceeds

    # ALWAYS use the same graph with DEFAULT_INTERRUPTS.
    # LangGraph handles resume-and-re-interrupt correctly with invoke(None).
    resume_app = build_pipeline_graph(context)

    # Determine which node was interrupted so update_state injects correctly
    snapshot_next = getattr(snapshot, "next", None)
    interrupted_node = snapshot_next[0] if snapshot_next else None

    # as_node logic:
    # - as_node=None: the interrupted node will RUN with the updated state.
    #   Used for: supply_raw_research, supply_deep_research, select_topics
    # - as_node=interrupted_node: marks the node as "done", graph moves to the NEXT node.
    #   Used for: approve, approve_content, edit (we don't want to re-run the node)
    skip_node = payload.action in ("approve", "approve_content", "edit")
    use_as_node = interrupted_node if skip_node else None

    try:
        if context.logger:
            context.logger.event("api.resume.pre_update", {
                "interrupted_node": interrupted_node,
                "as_node": use_as_node,
                "update_keys": list(update_data.keys()),
            })
        resume_app.update_state(config, update_data, as_node=use_as_node)
    except Exception as e:
        if context.logger:
            context.logger.error("api_resume_pipeline", f"Failed updating state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    # Run the graph synchronously. LangGraph will:
    # - Resume from the current interrupt
    # - Run nodes until the next interrupt_before fires
    # - Return when paused or finished
    # This handles the deep research loop correctly:
    #   deep_parse → router → deep_prompt → deep_parse (re-interrupt)
    import asyncio

    try:
        await asyncio.wait_for(
            resume_app.ainvoke(None, config=config),
            timeout=120  # 2 min max — most steps are now instant
        )
    except asyncio.TimeoutError:
        if context.logger:
            context.logger.error("api_resume_pipeline", "Graph invocation timed out after 300s")
    except Exception as exc:
        if context.logger:
            context.logger.error("api_resume_pipeline", f"Graph failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))

    # Read the final state after the graph paused at the next interrupt
    snapshot_new = resume_app.get_state(config)
    new_state = ContentForgeState(**snapshot_new.values)
    req_action, type_action = get_interrupt_status(snapshot_new)

    if context.logger:
        context.logger.event(
            "api.feedback.completed",
            {
                "week_id": week_id,
                "action": payload.action,
                "status_after": new_state.pipeline_status,
                "pending_topic_id": new_state.pending_topic_id,
                "human_action_type": type_action,
            },
        )
    
    # Prefer prompt_content from state (set by deep_research_prompt_generator) over disk
    prompt = None
    if hasattr(snapshot_new, 'values') and snapshot_new.values:
        prompt = snapshot_new.values.get('prompt_content')
    if not prompt:
        prompt = _get_prompt_content(week_id, new_state.pipeline_status, type_action, new_state.pending_topic_id)

    return PipelineStatusResponse(
        week_id=week_id,
        status="review" if type_action == "review_content" else new_state.pipeline_status,
        pending_topic_id=new_state.pending_topic_id,
        human_action_required=req_action,
        human_action_type=type_action,
        state=new_state.model_dump(),
        prompt_content=prompt,
    )
