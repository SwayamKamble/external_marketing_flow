"""Endpoints for rendering carousel previews."""

from __future__ import annotations

import base64
import os
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

from api.dependencies import get_node_context
from api.schemas import CarouselImage, CarouselRenderResponse, CarouselRenderRequest
from contentforge.core.graph import build_pipeline_graph
from contentforge.core.state import ContentForgeState

router = APIRouter(prefix="/carousel", tags=["carousel"])


@router.post("/render/{week_id}/{topic_id}", response_model=CarouselRenderResponse)
async def render_carousel_preview(
    week_id: str, 
    topic_id: str, 
    payload: CarouselRenderRequest | None = None
):
    """Render carousel HTML/CSS to image previews via the Node renderer service."""
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

    render_topic_id = f"{week_id}_{topic_id}"
    
    # 1. Determine the HTML slides code
    html_code = ""
    if payload and payload.html_content:
        html_code = payload.html_content
    else:
        # Check if the slides.html file exists on disk
        project_root = Path(__file__).resolve().parents[2]
        local_html_path = project_root / "data" / "exports" / render_topic_id / "slides.html"
        if local_html_path.exists():
            try:
                html_code = local_html_path.read_text(encoding="utf-8")
            except Exception:
                pass

    if not html_code:
        html_code = topic_content.rendered_code

    if not html_code:
        raise HTTPException(status_code=422, detail="Carousel HTML code is not available yet")

    renderer_url = os.getenv("CAROUSEL_RENDERER_URL", "http://localhost:4000")

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{renderer_url}/render",
                json={
                    "jsx_code": html_code,
                    "theme": topic_content.theme.model_dump() if topic_content.theme else {},
                    "topic_id": render_topic_id,
                    "slides": [s.model_dump() for s in (topic_content.carousel_slides or [])],
                },
            )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Renderer service unavailable: {e}")

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Renderer failed: {response.text}")

    payload_data = response.json()
    files = payload_data.get("files", [])

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
