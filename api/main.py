"""ContentForge API — FastAPI backend (stub).

Full implementation in Phase 3. This stub ensures the server can start.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ContentForge",
    description="AI Marketing Content Pipeline API",
    version="0.1.0",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "ContentForge",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# Routes will be added in Phase 3:
# from api.routes import pipeline, events, research, plan, content, chat, export, files, logs
