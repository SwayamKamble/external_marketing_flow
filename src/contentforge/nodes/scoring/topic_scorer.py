"""Node to score and filter topics in the topic bank."""

from __future__ import annotations

import json
from typing import Any

from contentforge.core.state import Topic
from contentforge.nodes._base import BaseNode, NodeContext


class TopicScorer(BaseNode):
    """Scores generated topics based on virality and brand fit.

    Evaluates the current topic bank and assigns a score (0.0 to 10.0)
    and reasoning to each topic, helping the planner select the best ones.
    """

    node_name = "topic_scorer"
    category = "scoring"
    description = "Scores topics in the bank for virality, value, and brand fit."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        """Score all topics in the topic_bank."""
        topic_bank = input_data.get("topic_bank", [])
        if not topic_bank:
            if context.logger:
                context.logger.error(self.node_name, "topic_bank is empty.")
            return {"topic_bank": []}

        # Build prompt
        system_prompt, config = self.load_prompt(context)

        # Prepare payload for LLM (just id, title, summary, key points to save tokens)
        payload = [
            {
                "id": t.id,
                "title": t.title,
                "summary": t.summary,
                "key_points": t.key_points,
            }
            for t in topic_bank
        ]
        
        result = await self.call_llm(
            context=context,
            system_prompt=system_prompt,
            user_message=f"Here is the topic bank. Please score each topic:\n\n{json.dumps(payload, indent=2)}",
            response_format={"type": "json_object"},
            model=config.get("model", "gpt-5-chat"),
            temperature=config.get("temperature", 0.3),
        )

        if not result.success:
            if context.logger:
                context.logger.error(self.node_name, f"LLM scoring failed: {result.error}")
            return {"topic_bank": topic_bank}

        try:
            parsed = json.loads(result.content)
            scores_data = parsed.get("scores", [])
        except json.JSONDecodeError as e:
            if context.logger:
                context.logger.error(self.node_name, f"Invalid JSON returned: {e}")
            return {"topic_bank": topic_bank}

        # Map scores to topic objects
        score_map = {item.get("id"): item for item in scores_data}
        
        updated_bank = []
        for topic in topic_bank:
            score_info = score_map.get(topic.id)
            if score_info:
                topic.score = float(score_info.get("score", topic.score))
                topic.scoring_reasoning = score_info.get("reasoning", "")
            updated_bank.append(topic)
            
        # Sort by score descending
        updated_bank.sort(key=lambda x: x.score, reverse=True)

        # Save artifact for visibility
        content = "\n\n".join(
            f"## [{t.score}/10] {t.title}\n{t.scoring_reasoning}" for t in updated_bank
        )
        self.save_artifact(
            context=context,
            phase="02_scoring",
            filename="topic_scores.md",
            content=content,
        )

        return {"topic_bank": updated_bank}
