"""Endpoints for rendering carousel previews."""

from __future__ import annotations

import base64
import os
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

from api.dependencies import get_node_context
from api.schemas import CarouselImage, CarouselRenderResponse
from contentforge.core.graph import build_pipeline_graph
from contentforge.core.state import ContentForgeState

router = APIRouter(prefix="/carousel", tags=["carousel"])


@router.post("/render/{week_id}/{topic_id}", response_model=CarouselRenderResponse)
async def render_carousel_preview(week_id: str, topic_id: str):
    """Render carousel TSX to image previews via the Node renderer service."""
    context = get_node_context(week_id=week_id)
    app = build_pipeline_graph(context)
    config = {"configurable": {"thread_id": week_id}}

    snapshot = app.get_state(config)
    if not snapshot or not snapshot.values:
        raise HTTPException(status_code=404, detail="Pipeline thread not found")

    state_obj = ContentForgeState(**snapshot.values)
    topic_content = state_obj.content.get(topic_id)
    if not topic_content:
        raise HTTPException(status_code=404, detail=f"Topic '{topic_id}' content not found")

    if topic_content.content_format != "carousel":
        raise HTTPException(status_code=422, detail="Topic content format is not carousel")

    if not topic_content.rendered_code:
        raise HTTPException(status_code=422, detail="Carousel React code is not available yet")

    renderer_url = os.getenv("CAROUSEL_RENDERER_URL", "http://localhost:4000")
    render_topic_id = f"{week_id}_{topic_id}"

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{renderer_url}/render",
                json={
                    "jsx_code": topic_content.rendered_code,
                    "theme": topic_content.theme.model_dump() if topic_content.theme else {},
                    "topic_id": render_topic_id,
                },
            )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Renderer service unavailable: {e}")

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Renderer failed: {response.text}")

    payload = response.json()
    files = payload.get("files", [])

    images: list[CarouselImage] = []
    for file_path in files:
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            continue

        mime = "image/png"
        encoded = base64.b64encode(p.read_bytes()).decode("ascii")
        images.append(CarouselImage(filename=p.name, data_url=f"data:{mime};base64,{encoded}"))

    if not images:
        raise HTTPException(status_code=502, detail="Renderer returned no image files")

    return CarouselRenderResponse(
        week_id=week_id,
        topic_id=topic_id,
        count=len(images),
        images=images,
    )
