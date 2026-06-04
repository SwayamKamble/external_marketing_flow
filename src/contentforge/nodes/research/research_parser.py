"""Node to parse raw research text into structured topic entities."""

from __future__ import annotations

import json
import re
from typing import Any
import uuid

from contentforge.core.state import Topic, ContentFormat
from contentforge.nodes._base import BaseNode, NodeContext


CONTENT_TYPE_TO_FORMAT = {
    "reel": ContentFormat.REEL,
    "carousel": ContentFormat.CAROUSEL,
    "post": ContentFormat.SINGLE_IMAGE,
    "animated_post": ContentFormat.SINGLE_IMAGE,
    "single_image": ContentFormat.SINGLE_IMAGE,
    "news_post": ContentFormat.NEWS_POST,
}


def _parse_content_format(value: Any) -> ContentFormat:
    format_str = str(value or "").strip().lower()
    return CONTENT_TYPE_TO_FORMAT.get(format_str, ContentFormat.SINGLE_IMAGE)


def _extract_json_from_text(text: str) -> str | None:
    """Try to extract a JSON array or object from messy text."""
    text = _sanitize_jsonish_research(text)

    # Prefer the largest top-level array span. External research tools often
    # paste markdown links inside arrays, which makes non-greedy regex grabs
    # stop at citation brackets instead of the JSON closing bracket.
    array_start = text.find("[")
    array_end = text.rfind("]")
    if array_start != -1 and array_end > array_start:
        candidate = text[array_start:array_end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, list) and len(parsed) > 0:
                return json.dumps(parsed)
        except json.JSONDecodeError:
            pass

    # Try to find a JSON array in the text
    matches = re.findall(r'\[[\s\S]*?\]', text)
    for match in reversed(matches):  # Try largest matches first
        try:
            parsed = json.loads(match)
            if isinstance(parsed, list) and len(parsed) > 0:
                return json.dumps(parsed)
        except json.JSONDecodeError:
            continue
    
    # Try to find a JSON object with "topics" key
    matches = re.findall(r'\{[\s\S]*?\}', text)
    for match in reversed(matches):
        try:
            parsed = json.loads(match)
            if isinstance(parsed, dict) and "topics" in parsed:
                return json.dumps(parsed)
        except json.JSONDecodeError:
            continue
    
    return None


def _sanitize_jsonish_research(text: str) -> str:
    """Clean common paste artifacts that make otherwise valid JSON fail."""
    # Remove markdown citations accidentally placed between JSON fields:
    #   "description": "...", [source](url)
    #   "content_type": "carousel"
    text = re.sub(
        r',\s*\[[^\]]+\]\([^)]+\)\s*(?=\r?\n\s*")',
        ',\n',
        text,
    )
    # Remove citation fragments before object/array endings.
    text = re.sub(
        r',\s*\[[^\]]+\]\([^)]+\)\s*(?=\r?\n\s*[}\]])',
        '',
        text,
    )
    return text


def _clean_research_text(text: str) -> str:
    """Remove HTML tags, footnote references, and other noise from research text."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove YAML frontmatter
    text = re.sub(r'^---\r?\n[\s\S]*?\r?\n---\r?\n', '', text, count=1)
    # Remove footnote references like [^1]
    text = re.sub(r'\[\^?\d+\]', '', text)
    # Remove citation URLs at the bottom
    text = re.sub(r'\[\^\d+\]:\s*https?://\S+', '', text)
    return text.strip()


class ResearchParser(BaseNode):
    """Parses raw text research into structured Topic objects.

    This node takes the raw output pasted by the human (from external LLMs like
    ChatGPT/Perplexity), analyzes it, and extracts distinct, coherent topics
    ready for the scoring and planning phases.
    """

    node_name = "research_parser"
    category = "research"
    description = "Parses raw research text into a list of structured Topic objects."

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        """Parse raw research into Topic objects."""
        # Grab raw_research from input or state
        result = None
        raw_research = input_data.get("raw_research", [])
        if not raw_research:
            if context.logger:
                context.logger.error(self.node_name, "No raw research provided to parse.")
            return {"topic_bank": []}

        # Combine all research strings into one giant text block for parsing
        combined_text = "\n\n=== SOURCE ===\n\n".join(raw_research)
        
        # Pre-clean the text
        cleaned_text = _clean_research_text(combined_text)
        
        topics_data = []
        topics_data_was_direct = False
        
        # Try to extract JSON directly from the text first
        direct_json = _extract_json_from_text(cleaned_text)
        if direct_json:
            if context.logger:
                context.logger.event("research_parser.direct_json", {"found": True})
            try:
                parsed_direct = json.loads(direct_json)
                if isinstance(parsed_direct, dict):
                    if "topics" in parsed_direct:
                        parsed_direct = parsed_direct["topics"]
                    else:
                        for key in parsed_direct:
                            if isinstance(parsed_direct[key], list) and len(parsed_direct[key]) > 0:
                                parsed_direct = parsed_direct[key]
                                break
                
                if isinstance(parsed_direct, list):
                    for item in parsed_direct:
                        if isinstance(item, dict) and "title" in item:
                            topics_data.append({
                                "title": item.get("title", ""),
                                "summary": item.get("summary") or item.get("description", ""),
                                "category": item.get("category", "General"),
                                "source": item.get("source_url") or item.get("source") or "Assorted Web Search",
                                "date_of_report": item.get("date_of_report") or item.get("date", ""),
                                "key_points": item.get("key_points", []),
                                "tags": item.get("tags", []),
                                "suggested_format": item.get("suggested_format") or item.get("content_type", "carousel"),
                                "suggested_angle": item.get("suggested_angle") or item.get("why_it_matters", ""),
                            })
                            topics_data_was_direct = True
            except Exception as e:
                if context.logger:
                    context.logger.error(self.node_name, f"Failed to parse direct JSON: {e}")

        # Only call LLM if we failed to extract valid topics from the JSON directly
        if not topics_data:
            if context.logger:
                context.logger.event("research_parser.llm_fallback", {"reason": "No valid direct JSON topics found"})
                
            # Load prompt
            system_prompt, config = self.load_prompt(context)
    
            # LLM Call
            result = await self.call_llm(
                context=context,
                system_prompt=system_prompt,
                user_message=f"Here is the raw research gathered:\n\n{cleaned_text}",
                response_format={"type": "json_object"},
                model=config.get("model", "gpt-5-chat"),
                temperature=config.get("temperature", 0.3),  # Lower temp for parsing
                max_tokens=config.get("max_tokens", 4096),
            )
    
            if not result.success:
                if context.logger:
                    context.logger.error(self.node_name, f"Failed to parse research: {result.error}")
                return {"topic_bank": []}
    
            # Parse the JSON response
            try:
                parsed = json.loads(result.content)
                topics_data = parsed.get("topics", [])
                
                # If "topics" key is missing, try to use the raw array
                if not topics_data and isinstance(parsed, dict):
                    # Some LLMs return differently structured JSON
                    for key in parsed:
                        if isinstance(parsed[key], list) and len(parsed[key]) > 0:
                            topics_data = parsed[key]
                            break
            except json.JSONDecodeError as e:
                if context.logger:
                    context.logger.error(self.node_name, f"Invalid JSON returned: {e}")
                raise ValueError(f"Failed to parse topic JSON:\n{result.content}")
    
            if not topics_data:
                if context.logger:
                    context.logger.error(self.node_name, f"LLM returned 0 topics. Response: {result.content[:500]}")

        # Convert to Pydantic objects
        topic_bank = []
        for t_dict in topics_data:
            try:
                # Ensure it has an ID
                topic_id = f"topic_{uuid.uuid4().hex[:8]}"

                fmt = _parse_content_format(t_dict.get("suggested_format"))

                topic = Topic(
                    id=topic_id,
                    title=t_dict.get("title", "Untitled Topic"),
                    summary=t_dict.get("summary", ""),
                    category=t_dict.get("category", "General"),
                    source=t_dict.get("source", "Assorted Web Search"),
                    date_of_report=t_dict.get("date_of_report", ""),
                    key_points=t_dict.get("key_points", []),
                    tags=t_dict.get("tags", []),
                    suggested_format=fmt,
                    suggested_angle=t_dict.get("suggested_angle", ""),
                )
                topic_bank.append(topic)
            except Exception as e:
                if context.logger:
                    context.logger.error(self.node_name, f"Could not create Topic object: {e} | data: {t_dict}")
                # Skip invalid ones instead of failing the whole batch
                continue

        if context.logger:
            context.logger.event("research_parser.result", {
                "topics_extracted": len(topic_bank),
                "topics_data_count": len(topics_data),
            })

        # Return updated state
        last_llm_result = ""
        model_used = "bypassed"
        if not topics_data_was_direct:
            last_llm_result = result.content if result.success else ""
            model_used = result.model
        elif topics_data:
            last_llm_result = direct_json

        # Save artifact for debug/history
        self.save_artifact(
            context=context,
            phase="01_research",
            filename="parsed_topics.md",
            content="\n\n".join(
                f"## {t.title}\n{t.summary}\n- Angle: {t.suggested_angle}\n- Format: {t.suggested_format.value}"
                for t in topic_bank
            ) if topic_bank else "# No topics extracted\n\nThe LLM returned 0 topics from the research.",
            metadata={"parsed_count": len(topic_bank), "model": model_used}
        )

        return {
            "topic_bank": topic_bank,
            "raw_research": [],
            "pipeline_status": "scoring",
            "last_llm_result": last_llm_result,
        }
