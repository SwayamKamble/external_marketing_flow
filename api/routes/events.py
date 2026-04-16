"""Server-Sent Events (SSE) or WebSocket route for live updates."""

import asyncio
import json
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.dependencies import get_logger

router = APIRouter(prefix="/events", tags=["events"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Streams the pipeline tail log to the frontend via WebSockets."""
    await websocket.accept()
    logger = get_logger()
    
    # In a real app we'd tail the specific week_id log file.
    # For this implementation, we will tail the shared events.jsonl
    log_file = os.path.join(logger.log_dir, "events.jsonl")
    
    try:
        if not os.path.exists(log_file):
            await websocket.send_text(json.dumps({"error": "No event log found yet."}))
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
                    await websocket.send_text(json.dumps(event_data))
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
