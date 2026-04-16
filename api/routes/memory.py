"""Endpoints for reading artifacts and memory."""

from fastapi import APIRouter, HTTPException

from api.schemas import ArtifactResponse
from api.dependencies import get_memory

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/artifact/{week_id}/{phase}/{filename}", response_model=ArtifactResponse)
async def read_pipeline_artifact(week_id: str, phase: str, filename: str, topic_id: str = ""):
    """Reads a generated markdown/json artifact from file memory."""
    memory = get_memory()
    
    t_id = topic_id if topic_id else None
    
    result = memory.read_artifact(week_id=week_id, phase=phase, filename=filename, topic_id=t_id)
    
    if not result.get("exists", False):
        raise HTTPException(status_code=404, detail=f"Artifact {filename} not found.")
        
    return ArtifactResponse(
        week_id=week_id,
        phase=phase,
        filename=filename,
        content=result.get("content", ""),
        metadata=result.get("metadata", {})
    )


@router.get("/brand/context")
async def get_brand_context():
    """Returns the loaded brand style guidelines and DNA."""
    memory = get_memory()
    return memory.get_brand_context()
