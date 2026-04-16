"""Main FastAPI application entry point."""

import sys
import os
sys.path.append(os.path.abspath("src"))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import init_system, close_system
from api.routes import pipeline, memory, events


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

# Include Routers
app.include_router(pipeline.router)
app.include_router(memory.router)
app.include_router(events.router)


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}
