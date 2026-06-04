"""Quick poll to check current topic state for W26."""
import httpx, time

BASE = "http://localhost:8000"
WEEK = "2026-W26"
c = httpx.Client(base_url=BASE, timeout=30)
for i in range(5):
    r = c.get(f"/pipeline/{WEEK}/status")
    d = r.json()
    pending = d.get("pending_topic_id")
    status = d.get("status")
    action = d.get("human_action_type")
    next_nodes = d.get("state", {}).get("topic_queue", [])
    dr_keys = list(d.get("state", {}).get("deep_research", {}).keys())
    print(f"Poll {i}: pending={pending} status={status} action={action} dr_done={dr_keys} queue={next_nodes}")
    time.sleep(2)
