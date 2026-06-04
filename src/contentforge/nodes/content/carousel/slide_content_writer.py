"""Slide writing node."""

from __future__ import annotations

import json
from typing import Any

from contentforge.core.state import CarouselSlide, enum_value
from contentforge.nodes._base import BaseNode, NodeContext


class SlideContentWriter(BaseNode):
    """Generates strict carousel slide content from deep research only."""

    node_name = "slide_content_writer"
    category = "content"
    description = "Writes the paginated content for a visual carousel."

    @staticmethod
    def _coerce_plain_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return ""
            try:
                parsed = json.loads(text)
            except Exception:
                return text
            return SlideContentWriter._coerce_plain_text(parsed)
        if isinstance(value, list):
            parts = [SlideContentWriter._coerce_plain_text(v) for v in value]
            return " ".join(p for p in parts if p).strip()
        if isinstance(value, dict):
            preferred_keys = ("heading", "title", "body_text", "summary", "description", "content", "text")
            parts: list[str] = []
            for k in preferred_keys:
                if k in value:
                    chunk = SlideContentWriter._coerce_plain_text(value.get(k))
                    if chunk:
                        parts.append(chunk)
            if not parts:
                for _, v in value.items():
                    chunk = SlideContentWriter._coerce_plain_text(v)
                    if chunk:
                        parts.append(chunk)
            return " ".join(parts).strip()
        return str(value).strip()

    @staticmethod
    def _slides_from_content_spec(spec: dict[str, Any] | None) -> list[CarouselSlide]:
        spec = spec or {}
        slides_raw = spec.get("slides", [])
        slides: list[CarouselSlide] = []
        for i, s in enumerate(slides_raw):
            if not isinstance(s, dict):
                continue
            heading = SlideContentWriter._coerce_plain_text(s.get("heading", "")).strip()
            body_text = SlideContentWriter._coerce_plain_text(s.get("body_text", "")).strip()
            if heading.startswith("{") or heading.startswith("["):
                heading = ""
            if body_text.startswith("{") or body_text.startswith("["):
                body_text = ""
            if not heading:
                continue
            slides.append(
                CarouselSlide(
                    slide_number=s.get("slide_number", i + 1),
                    slide_type=s.get("slide_type", ""),
                    heading=heading,
                    body_text=body_text,
                    visual_concept=s.get("visual_concept", s.get("image_description", "")),
                    image_description=s.get("image_description", ""),
                    image_placement=s.get("image_placement", ""),
                    heading_font=str(s.get("heading_font", "")).strip(),
                    heading_font_weight=str(s.get("heading_font_weight", "")).strip(),
                    body_font=str(s.get("body_font", "")).strip(),
                    body_font_weight=str(s.get("body_font_weight", "")).strip(),
                    slide_theme=s.get("theme"),
                )
            )
        return slides

    @staticmethod
    def _normalize_sentence(text: str) -> str:
        """Normalize a text fragment into a proper sentence."""
        import re
        sentence = re.sub(r"\s+", " ", (text or "").strip())
        if not sentence:
            return ""
        if sentence[-1] not in ".!?":
            sentence += "."
        return sentence

    @classmethod
    def _build_fallback_slides(cls, structured_text: str, topic_title: str) -> list[CarouselSlide]:
        """Build deterministic 6-slide carousel when deep JSON slides are too weak."""
        import re
        cleaned = re.sub(r"```[\s\S]*?```", " ", structured_text or "", flags=re.IGNORECASE)
        lines = [cls._normalize_sentence(line) for line in re.split(r"[\n\r]+", cleaned)]
        lines = [ln for ln in lines if ln and len(ln) > 30]

        if not lines:
            lines = [f"{topic_title} is trending with meaningful implications for builders and creators."]

        insight_pool: list[str] = []
        for ln in lines:
            for seg in re.split(r"(?<=[.!?])\s+", ln):
                seg = cls._normalize_sentence(seg)
                if seg and len(seg) > 25 and seg.lower() not in (s.lower() for s in insight_pool):
                    insight_pool.append(seg)
                if len(insight_pool) >= 24:
                    break
            if len(insight_pool) >= 24:
                break

        while len(insight_pool) < 12:
            insight_pool.append(
                f"{topic_title} matters because it changes execution speed, quality, and outcomes for real-world teams."
            )

        headings = [
            f"{topic_title}: What Changed",
            "Why This Matters Now",
            "Evidence And Data",
            "Practical Takeaways",
            "Execution Ideas",
            "Bottom Line",
        ]

        slides: list[CarouselSlide] = []
        for idx, heading in enumerate(headings, start=1):
            body = " ".join(insight_pool[(idx - 1) * 2 : (idx - 1) * 2 + 2]).strip()
            body = cls._normalize_sentence(body)
            if len(body) < 40:
                body = f"{topic_title} has immediate relevance for builders. Use this signal to guide next content decisions."
            slides.append(
                CarouselSlide(
                    slide_number=idx,
                    heading=heading,
                    body_text=body,
                    image_description=(
                        f"Editorial visual supporting '{heading}' for topic '{topic_title}'"
                        if idx in (1, 3, 6)
                        else ""
                    ),
                    image_placement=("background" if idx in (1, 6) else ("right" if idx == 3 else "")),
                    visual_concept=f"Data-driven, premium editorial treatment for {heading}",
                )
            )
        return slides

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        topic_id = input_data.get("pending_topic_id")
        content_dict = input_data.get("content", {})
        
        tc = content_dict.get(topic_id)
        if not tc or enum_value(tc.content_format) != "carousel":
            return {}

        deep_res = input_data.get("deep_research", {}).get(topic_id)
        deep_spec = {}
        if deep_res:
            deep_spec = deep_res.get("content_spec", {}) if isinstance(deep_res, dict) else (getattr(deep_res, "content_spec", {}) or {})
        deep_spec_slides = self._slides_from_content_spec(deep_spec if isinstance(deep_spec, dict) else {})

        # STRICT: only deep research slides are valid for carousel.
        if len(deep_spec_slides) >= 2:
            tc.carousel_slides = deep_spec_slides
            updated_content = dict(content_dict)
            updated_content[topic_id] = tc
            if context.logger:
                context.logger.event("slide_writer.sync_from_deep_research", {
                    "topic_id": topic_id,
                    "slides": len(deep_spec_slides),
                })
            # Save artifact
            content = "# Carousel Slides\n\n"
            for slide in deep_spec_slides:
                content += f"## Slide {slide.slide_number}: {slide.heading}\n"
                content += f"{slide.body_text}\n"
                content += f"*(Visual: {slide.visual_concept})*\n"
                if slide.image_description:
                    content += f"**Image:** {slide.image_description} (Placement: {slide.image_placement})\n"
                content += "\n"
            self.save_artifact(
                context=context,
                phase="05_content",
                topic_id=topic_id,
                filename="carousel_slides.md",
                content=content,
            )
            return {"content": updated_content, "carousel_status": "done"}

        # FIX: Instead of returning carousel_status="generating_slides" (which
        # causes an infinite loop since slide_writer has no generative LLM),
        # build deterministic fallback slides from the research text and mark done.
        topic_title = topic_id
        topic_bank = input_data.get("topic_bank", [])
        for t in topic_bank:
            t_id = t.id if hasattr(t, "id") else t.get("id") if isinstance(t, dict) else None
            if t_id == topic_id:
                topic_title = t.title if hasattr(t, "title") else t.get("title", topic_id) if isinstance(t, dict) else topic_id
                break

        structured_text = ""
        if deep_res:
            if isinstance(deep_res, dict):
                structured_text = deep_res.get("result", "")
            else:
                structured_text = getattr(deep_res, "result", "") or ""

        fallback_slides = self._build_fallback_slides(structured_text, topic_title)
        tc.carousel_slides = fallback_slides

        updated_content = dict(content_dict)
        updated_content[topic_id] = tc
        if context.logger:
            context.logger.event(
                "slide_writer.fallback_generated",
                {
                    "topic_id": topic_id,
                    "slides": len(fallback_slides),
                    "reason": "deep_research slides invalid, generated deterministic fallback to prevent infinite loop",
                },
            )

        # Save artifact
        content = "# Carousel Slides (Fallback)\n\n"
        for slide in fallback_slides:
            content += f"## Slide {slide.slide_number}: {slide.heading}\n"
            content += f"{slide.body_text}\n"
            content += f"*(Visual: {slide.visual_concept})*\n"
            if slide.image_description:
                content += f"**Image:** {slide.image_description} (Placement: {slide.image_placement})\n"
            content += "\n"
        self.save_artifact(
            context=context,
            phase="05_content",
            topic_id=topic_id,
            filename="carousel_slides.md",
            content=content,
        )
        return {"content": updated_content, "carousel_status": "done"}
