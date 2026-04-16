"""Node to build a 7-day content plan."""

from __future__ import annotations

import json
from typing import Any

from contentforge.core.state import PlanItem, ContentFormat
from contentforge.nodes._base import BaseNode, NodeContext


class CalendarPlanner(BaseNode):
    """Generates a weekly content schedule.

    Uses the scored topic bank and the week's content mix framework
    to map topics to days, ensuring distribution and variety.
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

        # Load content mix configuration
        content_mix = {}
        if context.config:
            content_mix = context.config.get_content_mix()

        # Build prompt mapping out the top topics and the framework
        system_prompt, config = self.load_prompt(
            context,
            extra_variables={"content_mix": content_mix.get("weekly_framework", {})}
        )

        # Only pass top 15 topics to the LLM to save tokens and focus on quality
        top_topics = sorted(topic_bank, key=lambda x: x.score, reverse=True)[:15]
        payload = [
            {
                "id": t.id,
                "title": t.title,
                "score": t.score,
                "suggested_format": t.suggested_format.value if t.suggested_format else "carousel",
                "suggested_angle": t.suggested_angle,
            }
            for t in top_topics
        ]
        
        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message=f"Please create the content plan bridging these frameworks over the topics:\n\n{json.dumps(payload, indent=2)}",
            response_format={"type": "json_object"},
            model=config.get("model", "gpt-5-chat"),
            temperature=config.get("temperature", 0.4),
        )

        if not result.success:
            if context.logger:
                context.logger.error(self.node_name, f"Planning failed: {result.error}")
            return {"weekly_plan": [], "pipeline_status": "planning"}

        try:
            parsed = json.loads(result.content)
            plan_data = parsed.get("plan", [])
        except json.JSONDecodeError as e:
            if context.logger:
                context.logger.error(self.node_name, f"Invalid JSON returned: {e}")
            return {"weekly_plan": [], "pipeline_status": "planning"}

        # Build list of PlanItems
        weekly_plan = []
        for item in plan_data:
            topic_id = item.get("topic_id")
            
            try:
                fmt = ContentFormat(item.get("content_format", "carousel"))
            except ValueError:
                fmt = ContentFormat.CAROUSEL
                
            plan_item = PlanItem(
                day=item.get("day", ""),
                date=item.get("date", ""),
                topic_id=topic_id,
                topic_title=item.get("topic_title", ""),
                content_format=fmt,
                content_intent=item.get("content_intent", ""),
                reasoning=item.get("reasoning", "")
            )
            weekly_plan.append(plan_item)
        
        # Save artifact for user review
        md_content = "# Weekly Content Plan\n\n"
        for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
            day_plan = [p for p in weekly_plan if p.day.lower() == day]
            if day_plan:
                p = day_plan[0]
                md_content += f"## {day.capitalize()}\n"
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
