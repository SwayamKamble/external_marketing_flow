"""Main FastAPI application entry point. Reloaded: 2026-05-28T18:05:00."""

import sys
import os
import time
sys.path.append(os.path.abspath("src"))

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(errors="replace")

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import init_system, close_system, get_logger
from api.routes import pipeline, memory, events, carousel, creative


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    await init_system()
    yield
    # Shutdown
    await close_system()


app = FastAPI(
    title="ContentForge Pipeline API",
    description="Event-driven autonomous marketing pipeline engine.",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow CORS for local frontend development
# Using wildcard for local dev to avoid port mismatch issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(pipeline.router)
app.include_router(memory.router)
app.include_router(events.router)
app.include_router(carousel.router)
app.include_router(creative.router)


@app.middleware("http")
async def log_api_calls(request: Request, call_next):
    # Skip logging for OPTIONS preflight to avoid interference
    if request.method == "OPTIONS":
        return await call_next(request)
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    try:
        logger = get_logger()
        logger.event(
            "api.request",
            {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 1),
            },
        )
    except Exception:
        pass
    return response


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}
