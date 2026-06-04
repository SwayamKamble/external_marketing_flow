"""Node to score and filter topics in the topic bank.

Optimized: deterministic scoring without LLM call.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from contentforge.core.state import Topic
from contentforge.nodes._base import BaseNode, NodeContext

TOP_TOPIC_LIMIT = 7


def _topic_get(topic: Topic | dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(topic, dict):
        return topic.get(key, default)
    return getattr(topic, key, default)


def _deterministic_score(topic: Topic) -> tuple[float, str]:
    """Score a topic deterministically based on its attributes.
    
    Criteria:
    - Has key_points (richer = better): +2 per point (max 4)
    - Has suggested_angle (specific angle = better): +2
    - Has suggested_format: +1
    - Has tags: +0.5 per tag (max 2)
    - Title length (not too short, not too long): +1
    - Has category: +0.5
    - Has source: +0.5
    """
    score = 3.0  # Base score
    reasons = []

    kp = _topic_get(topic, "key_points", [])
    if kp:
        bonus = min(len(kp) * 0.5, 2.0)
        score += bonus
        reasons.append(f"{len(kp)} key points (+{bonus})")

    angle = _topic_get(topic, "suggested_angle", "")
    if angle and len(angle) > 10:
        score += 2.0
        reasons.append("strong angle (+2)")

    fmt = _topic_get(topic, "suggested_format", None)
    if fmt:
        score += 1.0
        reasons.append("has format (+1)")

    tags = _topic_get(topic, "tags", [])
    if tags:
        bonus = min(len(tags) * 0.25, 1.0)
        score += bonus
        reasons.append(f"{len(tags)} tags (+{bonus})")

    title = _topic_get(topic, "title", "")
    if 15 < len(title) < 100:
        score += 0.5
        reasons.append("good title length (+0.5)")

    if _topic_get(topic, "category", ""):
        score += 0.5
        reasons.append("has category (+0.5)")

    if _topic_get(topic, "source", ""):
        score += 0.5
        reasons.append("has source (+0.5)")

    # Cap at 10
    score = min(score, 10.0)
    reasoning = f"Deterministic score: {', '.join(reasons)}"
    return round(score, 1), reasoning


class TopicScorer(BaseNode):
    """Scores generated topics based on virality and brand fit.

    OPTIMIZED: Uses deterministic scoring instead of LLM call.
    Evaluates topic attributes (key_points, angle, format, tags) to
    assign a score from 0-10 instantly, eliminating 10-20s LLM latency.
    """

    node_name = "topic_scorer"
    category = "scoring"
    description = "Scores topics in the bank for virality, value, and brand fit."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        """Score all topics deterministically (no LLM call)."""
        topic_bank = input_data.get("topic_bank", [])
        if not topic_bank:
            if context.logger:
                context.logger.error(self.node_name, "topic_bank is empty.")
            return {"topic_bank": []}

        updated_bank = []
        for topic in topic_bank:
            if isinstance(topic, dict):
                topic = Topic(**topic)
            
            score, reasoning = _deterministic_score(topic)
            topic.score = score
            topic.scoring_reasoning = reasoning
            updated_bank.append(topic)

        # Sort by score descending and keep only the top N for planning.
        updated_bank.sort(key=lambda x: x.score, reverse=True)
        top_bank = updated_bank[:TOP_TOPIC_LIMIT]

        if context.logger:
            context.logger.event("topic_scorer.deterministic", {
                "count": len(top_bank),
                "input_count": len(updated_bank),
                "top_score": top_bank[0].score if top_bank else 0,
            })

        # Save artifact for visibility
        content = "\n\n".join(
            f"## [{t.score}/10] {t.title}\n{t.scoring_reasoning}" for t in top_bank
        )
        self.save_artifact(
            context=context,
            phase="02_scoring",
            filename="topic_scores.md",
            content=content,
        )

        return {"topic_bank": top_bank}
