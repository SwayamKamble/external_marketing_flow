"""Full E2E test using the user's actual research data via the API."""
import asyncio
import sys
import os
import json
import httpx

sys.path.insert(0, os.path.abspath("src"))
sys.path.insert(0, os.path.abspath("."))

BASE = "http://localhost:8000"
WEEK = "2026-W42"


async def main():
    # Read the user's actual research data
    with open("data/weeks/2026-W41/01_research/submitted_raw_research.md", "r", encoding="utf-8") as f:
        raw_research = f.read()

    async with httpx.AsyncClient(timeout=180) as client:
        # STEP 1: Start pipeline
        print("STEP 1: Start pipeline")
        r = await client.post(f"{BASE}/pipeline/start", json={"week_id": WEEK})
        data = r.json()
        print(f"  Status: {data['status']}")
        print(f"  Action: {data.get('human_action_type')}")

        # STEP 2: Supply the user's actual research
        print("\nSTEP 2: Supply raw research (user's actual Perplexity output)")
        r = await client.post(
            f"{BASE}/pipeline/{WEEK}/feedback",
            json={"action": "supply_raw_research", "raw_research_data": raw_research},
        )
        data = r.json()
        topic_bank = data.get("state", {}).get("topic_bank", [])
        weekly_plan = data.get("state", {}).get("weekly_plan", [])
        print(f"  Status: {data['status']}")
        print(f"  Topic Bank: {len(topic_bank)} topics")
        print(f"  Weekly Plan: {len(weekly_plan)} items")
        for t in topic_bank[:5]:
            title = t.get("title", "?")
            fmt = t.get("suggested_format", "?")
            print(f"    - [{fmt}] {title}")
        if len(topic_bank) == 0:
            print("\n  FAILED: 0 topics extracted!")
            return

        # STEP 3: Select first topic
        plan_topic_ids = [item.get("topic_id") for item in weekly_plan if item.get("topic_id")]
        if not plan_topic_ids:
            print("\n  FAILED: No topic IDs in weekly plan!")
            return
        selected = plan_topic_ids[:1]
        print(f"\nSTEP 3: Select topics: {selected}")
        r = await client.post(
            f"{BASE}/pipeline/{WEEK}/feedback",
            json={"action": "select_topics", "selected_topics": selected},
        )
        data = r.json()
        print(f"  Status: {data['status']}")
        print(f"  Action: {data.get('human_action_type')}")
        pending = data.get("pending_topic_id")
        print(f"  Pending Topic: {pending}")

        if data.get("human_action_type") != "paste_deep_research":
            print(f"\n  UNEXPECTED ACTION: {data.get('human_action_type')} (expected paste_deep_research)")

        # STEP 4: Supply deep research
        deep_text = json.dumps({
            "theme": {"primary_color": "#1a1a2e", "secondary_color": "#16213e", "accent_color": "#0f3460",
                      "background_color": "#0a0a0a", "text_color": "#ffffff", "font_heading": "Inter",
                      "font_body": "Inter", "mood": "professional"},
            "caption": "AI is evolving fast. Here's what happened this week. #AI #Tech",
            "hook": "This changes everything for AI developers",
            "num_slides": 5,
            "slides": [
                {"slide_number": 1, "heading": "Title Slide", "body_text": "Weekly AI Roundup",
                 "image_description": "abstract tech pattern", "image_placement": "background"},
                {"slide_number": 2, "heading": "Key Update", "body_text": "Major model release this week",
                 "image_description": "neural network visualization", "image_placement": "right"},
                {"slide_number": 3, "heading": "Impact", "body_text": "How this affects developers",
                 "image_description": "developer workspace", "image_placement": "left"},
                {"slide_number": 4, "heading": "Action Steps", "body_text": "What you should do now",
                 "image_description": "checklist icon", "image_placement": "center"},
                {"slide_number": 5, "heading": "Follow for More", "body_text": "Stay updated with AI news",
                 "image_description": "social media icons", "image_placement": "bottom"},
            ],
            "cta": "Follow @swayam for daily AI updates"
        })
        print(f"\nSTEP 4: Supply deep research for {pending}")
        r = await client.post(
            f"{BASE}/pipeline/{WEEK}/feedback",
            json={
                "action": "supply_deep_research",
                "topic_id": pending,
                "deep_research_text": deep_text,
            },
        )
        data = r.json()
        content_keys = list(data.get("state", {}).get("content", {}).keys())
        print(f"  Status: {data['status']}")
        print(f"  Action: {data.get('human_action_type')}")
        print(f"  Content: {content_keys}")

        if content_keys:
            print("\n=== SUCCESS! Full pipeline completed! ===")
        else:
            print("\n=== PARTIAL: Content generation may still be running ===")


asyncio.run(main())
