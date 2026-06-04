"""Node to parse returned deep research into state."""

from __future__ import annotations

import json
import re
from typing import Any

from contentforge.core.state import CarouselSlide, ContentFormat, ContentStatus, DeepResearchItem, Theme, TopicContent
from contentforge.nodes._base import BaseNode, NodeContext


class DeepResearchParser(BaseNode):
    node_name = "deep_research_parser"
    category = "research"
    description = "Parses pasted deep research data into the structured state."
    _FALLBACK_MARKERS = (
        "content generation fallback",
        "re-run deep research",
    )
    _MIN_CAROUSEL_SLIDES = 6
    _PLACEHOLDER_THEME_VALUES = (
        "google font",
        "heading font",
        "body font",
        "same as above",
        "same",
        "placeholder",
        "#hex",
        "hex",
        "dark",
        "light",
        "premium",
    )

    @staticmethod
    def _coerce_plain_text(value: Any) -> str:
        """Convert JSON-ish values into readable plain text for slide fields."""
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
            return DeepResearchParser._coerce_plain_text(parsed)
        if isinstance(value, list):
            parts = [DeepResearchParser._coerce_plain_text(v) for v in value]
            return " ".join(p for p in parts if p).strip()
        if isinstance(value, dict):
            preferred_keys = (
                "heading",
                "title",
                "body_text",
                "summary",
                "description",
                "content",
                "text",
                "why_it_matters",
            )
            parts: list[str] = []
            for k in preferred_keys:
                if k in value:
                    chunk = DeepResearchParser._coerce_plain_text(value.get(k))
                    if chunk:
                        parts.append(chunk)
            if not parts:
                for k, v in value.items():
                    chunk = DeepResearchParser._coerce_plain_text(v)
                    if chunk:
                        parts.append(f"{k}: {chunk}")
            return " ".join(parts).strip()
        return str(value).strip()

    @staticmethod
    def _normalize_jsonish(candidate: str) -> str:
        text = candidate.replace("\ufeff", "")
        text = text.replace("\u201c", '\\"').replace("\u201d", '\\"')
        text = text.replace("\u2018", "'").replace("\u2019", "'")
        # Remove floating markdown link citations that appear outside JSON string quotes
        # Case 1: ", [citation](url) -> replace with ",
        text = re.sub(r'",\s*\[[^\]]+\]\([^)]+\)', '",', text)
        # Case 2: " [citation](url) -> replace with " (preventing matching opening quotes)
        def _replace_outside_citations(match: re.Match) -> str:
            start_idx = match.start()
            before = text[max(0, start_idx - 10):start_idx]
            if re.search(r':\s*$', before):
                return match.group(0)
            return '"'
        text = re.sub(r'"\s*\[[^\]]+\]\([^)]+\)', _replace_outside_citations, text)
        return text.strip()

    @staticmethod
    def _shape_payload(parsed: dict[str, Any], raw_text_for_context: str) -> dict[str, Any]:
        if "content_spec" in parsed:
            return parsed
        if any(k in parsed for k in ("theme", "slides", "caption", "reel_script", "structured_research")):
            return {"structured_research": raw_text_for_context, "content_spec": parsed}
        return {}

    def _extract_json_payload(self, text: str) -> dict[str, Any] | None:
        candidates: list[str] = []
        fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
        candidates.extend(fenced)

        cleaned = re.sub(r"```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        candidates.append(cleaned)

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end > start:
            candidates.append(cleaned[start : end + 1])

        for raw_candidate in candidates:
            candidate = self._normalize_jsonish(raw_candidate)
            if not candidate:
                continue
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                shaped = self._shape_payload(parsed, text)
                if shaped:
                    return shaped
        return None

    @staticmethod
    def _slides_from_content_spec(spec: dict[str, Any] | None) -> list[CarouselSlide]:
        spec = spec or {}
        slides_raw = spec.get("slides", [])
        slides: list[CarouselSlide] = []
        for i, slide in enumerate(slides_raw):
            if not isinstance(slide, dict):
                continue
            heading = DeepResearchParser._coerce_plain_text(slide.get("heading", "")).strip()
            body_text = DeepResearchParser._coerce_plain_text(slide.get("body_text", "")).strip()
            if heading.startswith("{") or heading.startswith("["):
                heading = ""
            if body_text.startswith("{") or body_text.startswith("["):
                body_text = ""
            lower_blob = f"{heading}\n{body_text}".lower()
            if not heading:
                continue
            if any(marker in lower_blob for marker in DeepResearchParser._FALLBACK_MARKERS):
                continue
            slides.append(
                CarouselSlide(
                    slide_number=slide.get("slide_number", i + 1),
                    slide_type=slide.get("slide_type", ""),
                    heading=heading,
                    body_text=body_text,
                    image_description=slide.get("image_description", ""),
                    image_placement=slide.get("image_placement", ""),
                    visual_concept=slide.get("visual_concept", slide.get("image_description", "")),
                    heading_font=str(slide.get("heading_font", "")).strip(),
                    heading_font_weight=str(slide.get("heading_font_weight", "")).strip(),
                    body_font=str(slide.get("body_font", "")).strip(),
                    body_font_weight=str(slide.get("body_font_weight", "")).strip(),
                    slide_theme=slide.get("theme"),
                )
            )
        return slides

    @staticmethod
    def _normalize_sentence(text: str) -> str:
        sentence = re.sub(r"\s+", " ", (text or "").strip())
        if not sentence:
            return ""
        if sentence[-1] not in ".!?":
            sentence += "."
        return sentence

    @classmethod
    def _is_missing_theme_value(cls, field: str, value: Any) -> bool:
        text = str(value or "").strip()
        if not text:
            return True
        lowered = text.lower()
        if any(marker in lowered for marker in cls._PLACEHOLDER_THEME_VALUES):
            return True
        if field in ("primary_color", "secondary_color", "accent_color", "background_color", "text_color"):
            return re.fullmatch(r"#[0-9a-fA-F]{6}", text) is None
        return False

    @staticmethod
    def _fallback_theme_for_topic(topic_id: str, topic_title: str) -> dict[str, str]:
        seed = sum(ord(ch) for ch in f"{topic_id}|{topic_title}")
        palettes = [
            ("#111827", "#374151", "#f59e0b", "#030712", "#f9fafb"),
            ("#102a43", "#243b53", "#38bdf8", "#061826", "#f1f5f9"),
            ("#1f2937", "#4b5563", "#a3e635", "#111827", "#f8fafc"),
            ("#2d1b3d", "#51306b", "#f472b6", "#16091f", "#fff7ed"),
            ("#132018", "#31533a", "#34d399", "#07130b", "#ecfdf5"),
            ("#301a1a", "#5b3030", "#fb7185", "#160808", "#fff1f2"),
        ]
        font_pairs = [
            ("Space Grotesk", "DM Sans"),
            ("Outfit", "Source Sans 3"),
            ("Poppins", "Lato"),
            ("Sora", "Inter"),
            ("Bricolage Grotesque", "Manrope"),
            ("Archivo", "Nunito Sans"),
        ]
        primary, secondary, accent, background, text = palettes[seed % len(palettes)]
        font_heading, font_body = font_pairs[(seed // len(palettes)) % len(font_pairs)]
        return {
            "primary_color": primary,
            "secondary_color": secondary,
            "accent_color": accent,
            "background_color": background,
            "text_color": text,
            "font_heading": font_heading,
            "font_body": font_body,
            "mood": "Topic-specific editorial",
            "style_notes": "Generated fallback because submitted deep research did not include a complete usable theme.",
        }

    def _build_carousel_fallback_slides(self, structured_text: str, topic_title: str) -> list[CarouselSlide]:
        """Build a deterministic 6-slide carousel when deep JSON slides are too weak."""
        cleaned = re.sub(r"```[\s\S]*?```", " ", structured_text or "", flags=re.IGNORECASE)
        lines = [self._normalize_sentence(line) for line in re.split(r"[\n\r]+", cleaned)]
        lines = [ln for ln in lines if ln and len(ln) > 30]

        if not lines:
            lines = [f"{topic_title} is trending with meaningful implications for builders and creators."]

        insight_pool: list[str] = []
        for ln in lines:
            for seg in re.split(r"(?<=[.!?])\s+", ln):
                seg = self._normalize_sentence(seg)
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
            body = self._normalize_sentence(body)
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

    def _build_single_fallback_slide(self, structured_text: str, topic_title: str) -> list[CarouselSlide]:
        """Build one deterministic slide for single-image/news formats from deep research text."""
        cleaned = re.sub(r"```[\s\S]*?```", " ", structured_text or "", flags=re.IGNORECASE)
        lines = [self._normalize_sentence(line) for line in re.split(r"[\n\r]+", cleaned)]
        lines = [ln for ln in lines if ln and len(ln) > 20]

        heading = topic_title.strip() or "Key Insight"
        body_candidates: list[str] = []
        for ln in lines:
            for seg in re.split(r"(?<=[.!?])\s+", ln):
                seg = self._normalize_sentence(seg)
                if seg and len(seg) > 25:
                    body_candidates.append(seg)
                if len(body_candidates) >= 3:
                    break
            if len(body_candidates) >= 3:
                break

        body_text = " ".join(body_candidates[:2]).strip()
        if len(body_text) < 40:
            body_text = f"{heading} has immediate relevance for builders and creators based on the submitted deep research."

        return [
            CarouselSlide(
                slide_number=1,
                heading=heading,
                body_text=self._normalize_sentence(body_text),
                image_description="",
                image_placement="",
                visual_concept=f"Editorial single-card visual for {heading}",
            )
        ]

    @staticmethod
    def _format_for_topic(weekly_plan: list[Any], topic_id: str) -> ContentFormat:
        fmt = ContentFormat.CAROUSEL
        for item in weekly_plan:
            item_tid = item.topic_id if hasattr(item, "topic_id") else item.get("topic_id")
            if item_tid != topic_id:
                continue
            item_fmt = item.content_format if hasattr(item, "content_format") else item.get("content_format")
            if item_fmt:
                try:
                    fmt = ContentFormat(item_fmt)
                except ValueError:
                    pass
            break
        return fmt

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        raw_deep_research_dict = input_data.get("raw_deep_research", {})
        pending_topic_id = input_data.get("pending_topic_id")

        if not pending_topic_id:
            return {"pipeline_status": "deep_research", "human_action_required": True, "human_action_type": "paste_deep_research"}
        if not raw_deep_research_dict:
            return {"pipeline_status": "deep_research", "human_action_required": True, "human_action_type": "paste_deep_research"}

        raw_text = raw_deep_research_dict.get(pending_topic_id)
        if not raw_text:
            return {"pipeline_status": "deep_research", "human_action_required": True, "human_action_type": "paste_deep_research"}

        deep_res_objects = dict(input_data.get("deep_research", {}))
        content_dict = dict(input_data.get("content", {}))
        weekly_plan = input_data.get("weekly_plan", [])
        fmt = self._format_for_topic(weekly_plan, pending_topic_id)
        topic_bank = input_data.get("topic_bank", [])
        topic_title = pending_topic_id
        for t in topic_bank:
            t_id = t.id if hasattr(t, "id") else t.get("id")
            if t_id == pending_topic_id:
                topic_title = t.title if hasattr(t, "title") else t.get("title", pending_topic_id)
                break

        payload = self._extract_json_payload(raw_text)
        if not payload:
            if context.logger:
                context.logger.event(
                    "deep_research_parser.json_recovery",
                    {"topic_id": pending_topic_id, "reason": "non_json_submission"},
                )
            payload = {
                "structured_research": raw_text,
                "content_spec": {
                    "theme": {},
                    "slides": [],
                    "reel_script": [],
                    "caption": {},
                },
            }

        if payload:
            structured_text = payload.get("structured_research", raw_text)
            content_spec = payload.get("content_spec", payload)
            self.save_artifact(context=context, phase="04_deep_research", topic_id=pending_topic_id, filename="structured_research.md", content=f"# Structured Research\n\n{structured_text}")
            self.save_artifact(context=context, phase="04_deep_research", topic_id=pending_topic_id, filename="content_spec.json", content=json.dumps(content_spec, indent=2))

            theme_data = content_spec.get("theme") or {}
            if not isinstance(theme_data, dict):
                theme_data = {}
            theme_fields = ("primary_color", "secondary_color", "accent_color", "background_color", "text_color", "font_heading", "font_body")
            missing_theme_fields = [field for field in theme_fields if self._is_missing_theme_value(field, theme_data.get(field))]
            if missing_theme_fields:
                fallback_theme = self._fallback_theme_for_topic(pending_topic_id, topic_title)
                for field in theme_fields:
                    if self._is_missing_theme_value(field, theme_data.get(field)):
                        theme_data[field] = fallback_theme[field]
                if not str(theme_data.get("mood") or "").strip():
                    theme_data["mood"] = fallback_theme["mood"]
                if not str(theme_data.get("style_notes") or "").strip():
                    theme_data["style_notes"] = fallback_theme["style_notes"]
                if context.logger:
                    context.logger.event(
                        "deep_research_parser.theme_fallback",
                        {"topic_id": pending_topic_id, "filled_fields": missing_theme_fields},
                    )

            current_signature = tuple(str(theme_data.get(field) or "").strip().lower() for field in theme_fields)
            for existing_topic_id, existing_item in deep_res_objects.items():
                existing_spec = existing_item.get("content_spec", {}) if isinstance(existing_item, dict) else (getattr(existing_item, "content_spec", None) or {})
                existing_theme = existing_spec.get("theme") if isinstance(existing_spec, dict) else {}
                if not isinstance(existing_theme, dict):
                    continue
                existing_signature = tuple(str(existing_theme.get(field) or "").strip().lower() for field in theme_fields)
                if current_signature == existing_signature:
                    fallback_theme = self._fallback_theme_for_topic(pending_topic_id, topic_title)
                    for field in theme_fields:
                        theme_data[field] = fallback_theme[field]
                    theme_data["mood"] = fallback_theme["mood"]
                    theme_data["style_notes"] = fallback_theme["style_notes"]
                    current_signature = tuple(str(theme_data.get(field) or "").strip().lower() for field in theme_fields)
                    if context.logger:
                        context.logger.event(
                            "deep_research_parser.theme_deduplicated",
                            {"topic_id": pending_topic_id, "duplicate_of": existing_topic_id},
                        )
                    break

            content_spec["theme"] = theme_data
            deep_res_objects[pending_topic_id] = DeepResearchItem(
                topic_id=pending_topic_id,
                prompt="human_pasted",
                result=structured_text,
                content_spec=content_spec,
            )
            theme = Theme(
                primary_color=theme_data.get("primary_color") or "",
                secondary_color=theme_data.get("secondary_color") or "",
                accent_color=theme_data.get("accent_color") or "",
                background_color=theme_data.get("background_color") or "",
                text_color=theme_data.get("text_color") or "",
                font_heading=theme_data.get("font_heading") or "",
                font_body=theme_data.get("font_body") or "",
                mood=theme_data.get("mood") or "",
                style_notes=theme_data.get("style_notes") or "",
            )
            slides = self._slides_from_content_spec(content_spec)
            if fmt in (ContentFormat.SINGLE_IMAGE, ContentFormat.NEWS_POST) and len(slides) < 1:
                slides = self._build_single_fallback_slide(structured_text, topic_title)
                if context.logger:
                    context.logger.event(
                        "deep_research_parser.single_slide_recovery",
                        {"topic_id": pending_topic_id, "slides": len(slides)},
                    )

            if fmt == ContentFormat.CAROUSEL and len(slides) < self._MIN_CAROUSEL_SLIDES:
                fallback_slides = self._build_carousel_fallback_slides(structured_text, topic_title)
                if len(slides) >= 2:
                    # Keep valid model slides and append deterministic detail slides.
                    merged = slides + fallback_slides
                    # Keep unique headings while preserving order, then cap to 8.
                    seen: set[str] = set()
                    deduped: list[CarouselSlide] = []
                    for s in merged:
                        key = f"{s.heading}|{s.body_text}"
                        if key in seen:
                            continue
                        seen.add(key)
                        deduped.append(s)
                    slides = deduped[:8]
                else:
                    slides = fallback_slides
                if context.logger:
                    context.logger.event(
                        "deep_research_parser.carousel_slide_recovery",
                        {
                            "topic_id": pending_topic_id,
                            "original_slides": len(self._slides_from_content_spec(content_spec)),
                            "recovered_slides": len(slides),
                        },
                    )

            existing_tc = content_dict.get(pending_topic_id)
            tc = existing_tc or TopicContent(topic_id=pending_topic_id, content_format=fmt, status=ContentStatus.PENDING)
            tc.content_format = fmt
            tc.theme = theme
            tc.carousel_slides = slides
            tc.video_script = content_spec.get("reel_script", []) or tc.video_script
            tc.status = ContentStatus.PENDING
            content_dict[pending_topic_id] = tc
            self.save_artifact(context=context, phase="05_content", topic_id=pending_topic_id, filename="theme.json", content=json.dumps(tc.theme.model_dump(), indent=2))

        selected_topics = input_data.get("selected_topics", [])
        existing_queue = input_data.get("topic_queue", [])
        if existing_queue:
            # Prefer explicit queue order selected by the user/planner.
            queue = [tid for tid in existing_queue if tid and tid != pending_topic_id]
        else:
            # Fallback: derive remaining topics from selected list.
            queue = [tid for tid in selected_topics if tid and tid != pending_topic_id and tid not in deep_res_objects]
        next_topic = queue[0] if queue else None
        updated_raw = dict(raw_deep_research_dict)
        updated_raw.pop(pending_topic_id, None)

        return {
            "deep_research": deep_res_objects,
            "raw_deep_research": updated_raw,
            "content": content_dict,
            "selected_topics": selected_topics,
            "topic_queue": queue,
            "pending_topic_id": next_topic,
            "topic_index": (selected_topics.index(next_topic) + 1) if next_topic and next_topic in selected_topics else len(selected_topics),
            "topic_total": len(selected_topics),
            "pipeline_status": "deep_research" if next_topic else "content_creation",
        }
