"""Main FastAPI application entry point."""

import sys
import os
import time
sys.path.append(os.path.abspath("src"))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import init_system, close_system, get_logger
from api.routes import pipeline, memory, events, carousel


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

# Allow CORS for local frontend development (e.g. Next.js on 3000, Vite on 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_api_calls(request: Request, call_next):
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

# Include Routers
app.include_router(pipeline.router)
app.include_router(memory.router)
app.include_router(events.router)
app.include_router(carousel.router)


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}
