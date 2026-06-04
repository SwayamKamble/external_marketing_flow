"""Node to build a 7-day content plan.

Optimized: deterministic planning without LLM call.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from contentforge.core.state import PlanItem, ContentFormat
from contentforge.nodes._base import BaseNode, NodeContext


# Default weekly framework — matches config/content_mix.yaml
_WEEKLY_FRAMEWORK = [
    ("monday",    ContentFormat.CAROUSEL,     "savable"),
    ("tuesday",   ContentFormat.SINGLE_IMAGE, "shareable"),
    ("wednesday", ContentFormat.REEL,         "reach"),
    ("thursday",  ContentFormat.CAROUSEL,     "savable"),
    ("friday",    ContentFormat.NEWS_POST,    "timely"),
    ("saturday",  ContentFormat.SINGLE_IMAGE, "engagement"),
    ("sunday",    ContentFormat.REEL,         "reach"),
]


def _week_start_date(week_id: str) -> datetime:
    """Convert 'YYYY-WNN' to the Monday date of that week."""
    try:
        year, week = week_id.split("-W")
        # ISO week date: Monday is day 1
        return datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")
    except Exception:
        return datetime.now()


class CalendarPlanner(BaseNode):
    """Generates a weekly content schedule.

    OPTIMIZED: Deterministic planning. Maps top-scored topics to the
    weekly framework directly, eliminating the 15-20s LLM call.
    Topics are assigned by score rank to day slots.
    """

    node_name = "calendar_planner"
    category = "scoring"
    description = "Maps top-scored topics to a weekly content calendar."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        topic_bank = input_data.get("topic_bank", [])
        if not topic_bank:
            if context.logger:
                context.logger.error(self.node_name, "topic_bank is empty.")
            return {"weekly_plan": [], "pipeline_status": "planning"}

        # Sort by score (should already be sorted, but ensure)
        sorted_topics = sorted(topic_bank, key=lambda x: x.score, reverse=True)

        # Calculate dates for the week
        week_id = input_data.get("week_id", "")
        base_date = _week_start_date(week_id)

        weekly_plan = []
        used_topic_ids = set()

        for day_idx, (day_name, default_fmt, intent) in enumerate(_WEEKLY_FRAMEWORK):
            date_str = (base_date + timedelta(days=day_idx)).strftime("%Y-%m-%d")

            # Find best available topic for this slot
            assigned_topic = None
            for t in sorted_topics:
                if t.id not in used_topic_ids:
                    assigned_topic = t
                    break

            if not assigned_topic:
                break  # Ran out of topics

            used_topic_ids.add(assigned_topic.id)

            # Use the topic's suggested format if available, otherwise use default
            fmt = default_fmt
            if assigned_topic.suggested_format:
                try:
                    fmt = ContentFormat(assigned_topic.suggested_format.value if hasattr(assigned_topic.suggested_format, 'value') else assigned_topic.suggested_format)
                except (ValueError, AttributeError):
                    pass

            plan_item = PlanItem(
                day=day_name,
                date=date_str,
                topic_id=assigned_topic.id,
                topic_title=assigned_topic.title,
                content_format=fmt,
                content_intent=intent,
                reasoning=f"Score: {assigned_topic.score}/10. {assigned_topic.scoring_reasoning}"
            )
            weekly_plan.append(plan_item)

        if context.logger:
            context.logger.event("calendar_planner.deterministic", {
                "plan_items": len(weekly_plan),
                "topics_available": len(sorted_topics),
            })

        # Save artifact for user review
        md_content = "# Weekly Content Plan\n\n"
        for p in weekly_plan:
            md_content += f"## {p.day.capitalize()} ({p.date})\n"
            md_content += f"- **Topic:** {p.topic_title}\n"
            md_content += f"- **Format:** {p.content_format.value}\n"
            md_content += f"- **Intent:** {p.content_intent}\n"
            md_content += f"- **Why:** {p.reasoning}\n\n"

        self.save_artifact(
            context=context,
            phase="03_plan",
            filename="weekly_plan.md",
            content=md_content,
        )

        return {
            "weekly_plan": weekly_plan,
            "selected_topics": [],
            "topic_queue": [],
            "pending_topic_id": None,
            "topic_index": 0,
            "topic_total": len(weekly_plan),
            "pipeline_status": "planning",
            "human_action_required": True,
            "human_action_type": "select_topics"
        }
