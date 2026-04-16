"""Server-Sent Events (SSE) or WebSocket route for live updates."""

import asyncio
import json
import os
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.dependencies import get_logger

router = APIRouter(prefix="/events", tags=["events"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Streams the pipeline tail log to the frontend via WebSockets."""
    await websocket.accept()
    logger = get_logger()
    
    # Tail the shared pipeline event log emitted by PipelineLogger.event(...)
    log_file = os.path.join(logger.log_dir, "pipeline_events.log")

    def normalize_event(event_data: dict) -> dict:
        details = event_data.get("details") or {}
        timestamp = event_data.get("timestamp")
        if not timestamp:
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        return {
            "timestamp": timestamp,
            "level": event_data.get("level", "EVENT"),
            "event": event_data.get("event", event_data.get("node", "unknown")),
            "data": details,
        }
    
    try:
        if not os.path.exists(log_file):
            # Wait for file to be created by the pipeline
            while not os.path.exists(log_file):
                await asyncio.sleep(1)

        with open(log_file, "r") as f:
            # Seek to end to only get new events
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(0.5)
                    continue
                
                # We have a new log line, send it to the client
                try:
                    event_data = json.loads(line)
                    await websocket.send_text(json.dumps(normalize_event(event_data)))
                except json.JSONDecodeError:
                    pass # Ignore mangled lines
                    
    except WebSocketDisconnect:
        # Client disconnected normally
        pass
    except Exception as e:
        # Some other error
        try:
             await websocket.close(reason=str(e))
        except:
             pass
