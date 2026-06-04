"""Test that the deep research loop does NOT get stuck.

Traces the full flow:
  start → supply_raw_research → select_topics → supply_deep_research(topic1)
  → should pause at deep_parse for topic 2 (not loop forever)
"""
import httpx, time, json, sys

BASE = "http://localhost:8000"
WEEK = f"2026-W{int(time.time()) % 50 + 10}"  # unique week
client = httpx.Client(base_url=BASE, timeout=180)

def status():
    r = client.get(f"/pipeline/{WEEK}/status")
    if r.status_code == 404:
        return None
    d = r.json()
    return d

def feedback(payload):
    r = client.post(f"/pipeline/{WEEK}/feedback", json=payload)
    r.raise_for_status()
    return r.json()

def wait_for_status(target_action=None, max_wait=120):
    """Poll until human_action_type matches or timeout."""
    for _ in range(max_wait // 2):
        time.sleep(2)
        s = status()
        if s and s.get("human_action_type") == target_action:
            return s
        if s:
            print(f"  ... status={s.get('status')} action={s.get('human_action_type')} pending={s.get('pending_topic_id')}")
    print(f"TIMEOUT waiting for action={target_action}")
    sys.exit(1)

# Step 1: Start
print(f"=== STEP 1: Start pipeline {WEEK} ===")
r = client.post(f"/pipeline/start", json={"week_id": WEEK})
r.raise_for_status()
d = r.json()
print(f"  status={d['status']} action={d.get('human_action_type')}")

# Step 2: Supply raw research
print("=== STEP 2: Supply raw research ===")
research_text = """
[
  {
    "date": "2026-05-01",
    "title": "Neural Architecture Search",
    "description": "Neural Architecture Search (NAS) automates the design of neural networks.",
    "content_type": "carousel",
    "platform": "instagram"
  },
  {
    "date": "2026-05-01",
    "title": "Edge AI Deployment",
    "description": "Edge AI enables real-time inference on mobile devices.",
    "content_type": "carousel",
    "platform": "instagram"
  }
]
"""
d = feedback({"action": "supply_raw_research", "raw_research_data": research_text})
print(f"  status={d['status']} action={d.get('human_action_type')}")

# Wait for planning to complete and hit deep_prompt interrupt
print("=== Waiting for select_topics interrupt ===")
s = wait_for_status("select_topics", max_wait=120)
print(f"  Got select_topics! status={s['status']}")

# Step 3: Get plan and select first 2 topics
plan = s.get("state", {}).get("weekly_plan", [])
topic_ids = [p.get("topic_id") for p in plan if p.get("topic_id")][:2]
if not topic_ids:
    print("ERROR: No topics in plan!")
    sys.exit(1)
print(f"=== STEP 3: Select topics: {topic_ids} ===")
d = feedback({"action": "select_topics", "selected_topics": topic_ids})
print(f"  status={d['status']} action={d.get('human_action_type')}")

# Wait for deep_parse interrupt (topic 1 prompt should be generated)
print("=== Waiting for paste_deep_research (topic 1) ===")
s = wait_for_status("paste_deep_research", max_wait=120)
pending = s.get("pending_topic_id")
print(f"  Got paste_deep_research! pending={pending}")
assert pending == topic_ids[0], f"Expected {topic_ids[0]} but got {pending}"

# Step 4: Supply deep research for topic 1
print(f"=== STEP 4: Supply deep research for {pending} ===")
d = feedback({
    "action": "supply_deep_research",
    "topic_id": pending,
    "deep_research_text": json.dumps({
        "theme": {"primary_color": "#1a1a2e", "secondary_color": "#16213e"},
        "caption": "Test caption",
        "hook": "Did you know?",
        "num_slides": 3,
        "slides": [
            {"slide_number": 1, "heading": "Title", "body_text": "Intro text", "image_description": "abstract", "image_placement": "background"},
            {"slide_number": 2, "heading": "Point 1", "body_text": "Detail", "image_description": "chart", "image_placement": "right"},
            {"slide_number": 3, "heading": "CTA", "body_text": "Follow us", "image_description": "logo", "image_placement": "center"},
        ],
        "cta": "Follow for more"
    })
})
print(f"  status={d['status']} action={d.get('human_action_type')} pending={d.get('pending_topic_id')}")

# KEY TEST: Wait and check if we get paste_deep_research for TOPIC 2 (not stuck in loop)
if len(topic_ids) > 1:
    print(f"=== Waiting for paste_deep_research (topic 2: {topic_ids[1]}) ===")
    s = wait_for_status("paste_deep_research", max_wait=180)
    pending2 = s.get("pending_topic_id")
    print(f"  Got paste_deep_research! pending={pending2}")
    if pending2 == topic_ids[1]:
        print(f"\n[OK] SUCCESS: Pipeline correctly moved to topic 2 ({pending2})")
    elif pending2 == topic_ids[0]:
        print(f"\n[FAIL] Pipeline is STUCK on topic 1 ({pending2}) - LOOP BUG!")
        sys.exit(1)
    else:
        print(f"\n[WARN] Unexpected pending topic: {pending2}")
else:
    # Only 1 topic selected, should move to content_creation
    print("=== Waiting for content creation ===")
    time.sleep(5)
    s = status()
    print(f"  status={s['status']} action={s.get('human_action_type')}")

print("\n=== DEEP RESEARCH LOOP TEST COMPLETE ===")
