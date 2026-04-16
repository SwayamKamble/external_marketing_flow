"""Pipeline execution endpoints."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from api.schemas import StartPipelineRequest, PipelineStatusResponse, FeedbackRequest
from api.dependencies import get_node_context
from contentforge.core.graph import build_pipeline_graph
from contentforge.core.state import ContentForgeState

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
    
    if payload.action == "edit":
        update_data["human_feedback"] = payload.feedback
    elif payload.action == "supply_raw_research" and payload.raw_research_data:
        update_data["raw_research"] = [payload.raw_research_data]
    elif payload.action == "supply_deep_research" and payload.deep_research_data:
        update_data["raw_deep_research"] = payload.deep_research_data
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
