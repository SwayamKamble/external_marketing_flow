"""Test if pending_topic_id is stable across status polls."""
import httpx

BASE = "http://localhost:8000"
WEEK = "2026-W38"

for i in range(3):
    r = httpx.get(f"{BASE}/pipeline/{WEEK}/status", timeout=10)
    d = r.json()
    print(f"Poll {i+1}: pending={d.get('pending_topic_id')} status={d.get('status')}")
