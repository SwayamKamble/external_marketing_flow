"""Pipeline execution endpoints."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from api.schemas import StartPipelineRequest, PipelineStatusResponse, FeedbackRequest
from api.dependencies import get_node_context
from contentforge.core.graph import build_pipeline_graph
from contentforge.core.state import ContentForgeState, ContentStatus

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

@router.post("/start", response_model=PipelineStatusResponse)
async def start_pipeline(req: StartPipelineRequest, background_tasks: BackgroundTasks):
    """Initializes and runs the LangGraph pipeline for a specific week."""
    
    context = get_node_context(week_id=req.week_id)
    app = build_pipeline_graph(context)
    
    # LangGraph requires a specific thread config to track memory
    config = {"configurable": {"thread_id": req.week_id}}
    
    # Initial state
    initial_state = ContentForgeState(
        pipeline_status="research",
        raw_research=[],
        topic_bank=[],
        content={},
        carousel_status="",
    )
    
    # Start graph (would be async/backgrounded in real prod, but we'll await a chunk for now)
    try:
        final_state = await app.ainvoke(initial_state.model_dump(), config=config)
    except Exception as e:
        context.logger.error("api_start_pipeline", f"Failed starting graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    # Re-wrap the dictionary output into our Pydantic model for clean representation
    state_obj = ContentForgeState(**final_state)
    
    return PipelineStatusResponse(
        week_id=req.week_id,
        status=state_obj.pipeline_status,
        pending_topic_id=state_obj.pending_topic_id,
        human_action_required=state_obj.human_action_required,
        human_action_type=state_obj.human_action_type,
        state=state_obj.model_dump()
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
    
    return PipelineStatusResponse(
        week_id=week_id,
        status=state_obj.pipeline_status,
        pending_topic_id=state_obj.pending_topic_id,
        human_action_required=state_obj.human_action_required,
        human_action_type=state_obj.human_action_type,
        state=state_obj.model_dump()
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
    elif payload.action == "supply_raw_research":
        if not payload.raw_research_data or not payload.raw_research_data.strip():
            raise HTTPException(status_code=422, detail="raw_research_data is required for action='supply_raw_research'")
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
        topic_id = payload.topic_id or state_obj.pending_topic_id
        if not topic_id:
            raise HTTPException(status_code=422, detail="topic_id is required for action='supply_deep_research'")

        if state_obj.pending_topic_id and topic_id != state_obj.pending_topic_id:
            raise HTTPException(
                status_code=422,
                detail=f"topic_id '{topic_id}' does not match pending_topic_id '{state_obj.pending_topic_id}'"
            )

        research_text = payload.deep_research_text
        if not research_text and payload.deep_research_data:
            research_text = payload.deep_research_data.get(topic_id)

        if not research_text or not research_text.strip():
            raise HTTPException(status_code=422, detail="deep_research_text (or deep_research_data[topic_id]) is required")

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
    elif payload.action == "approve_plan":
        # No-op action kept for compatibility with existing frontend behavior.
        # The pipeline will wait for explicit `select_topics` before deep research.
        pass
    # 'approve' just clears the interrupt markers and proceeds
        
    try:
        # Continue the graph with the state updates
        final_state = await app.ainvoke(update_data, config=config)
    except Exception as e:
        context.logger.error("api_resume_pipeline", f"Failed resuming graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    new_state = ContentForgeState(**final_state)
    
    return PipelineStatusResponse(
        week_id=week_id,
        status=new_state.pipeline_status,
        pending_topic_id=new_state.pending_topic_id,
        human_action_required=new_state.human_action_required,
        human_action_type=new_state.human_action_type,
        state=new_state.model_dump()
    )
