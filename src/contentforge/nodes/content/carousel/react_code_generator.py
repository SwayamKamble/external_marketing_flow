"""Design Engine – HTML/CSS/JS slide compiler.

Transforms structured slide data + rich per-slide theme objects from deep
research into fully-designed, self-contained HTML documents.  Every slide's
layout, component selection, visual hierarchy, image strategy, and decorative
treatment is driven by the ``slide_theme`` dict attached to each
``CarouselSlide``.

Layout system (7 types):
    centered, split-left, split-right, full-bleed, asymmetric, stacked, editorial

Component library:
    stat-card, progress-bar, tag-pill, timeline-dot, quote-block, code-block,
    kpi-card, comparison-table, icon-grid, badge

Slide types (from deep research ``slide_type``):
    hook, content, data, quote, cta, comparison, timeline, summary
"""

from __future__ import annotations

import html as html_mod
import json
import re
from pathlib import Path
from typing import Any

from contentforge.nodes._base import BaseNode, NodeContext


# ─────────────────────────────────────────────────────────
# Helper utilities
# ─────────────────────────────────────────────────────────

def _esc(text: str) -> str:
    """HTML-escape user content."""
    return html_mod.escape(text or "", quote=False)


def _get(d: dict | None, *keys: str, default: Any = "") -> Any:
    """Safely traverse nested dicts."""
    cur: Any = d or {}
    for k in keys:
        if isinstance(cur, dict):
            cur = cur.get(k, default)
        else:
            return default
    return cur if cur is not None else default


def _lower(val: Any) -> str:
    return str(val or "").strip().lower()


def _list(val: Any) -> list:
    if isinstance(val, list):
        return val
    return []


# ─────────────────────────────────────────────────────────
# Body text formatter (bullet / numbered list support)
# ─────────────────────────────────────────────────────────

def _format_body_html(body_text: str, accent_var: str = "var(--accent)") -> str:
    escaped = _esc(body_text)
    lines = [ln.strip() for ln in escaped.split("\n") if ln.strip()]
    if not lines:
        return ""

    parts: list[str] = []
    in_list = False

    for line in lines:
        bullet = re.match(r"^[-*•\u2022]\s*(.*)", line)
        number = re.match(r"^(\d+)\.\s*(.*)", line)

        if bullet or number:
            if not in_list:
                parts.append('<ul style="margin:12px 0;padding-left:28px;list-style:none;">')
                in_list = True
            marker = bullet.group(1) if bullet else number.group(2)  # type: ignore[union-attr]
            icon = f'<span style="position:absolute;left:-28px;color:{accent_var};font-weight:800;">▸</span>' if bullet else f'<span style="position:absolute;left:-28px;color:{accent_var};font-weight:800;">{number.group(1)}.</span>'  # type: ignore[union-attr]
            parts.append(
                f'<li style="position:relative;margin-bottom:14px;line-height:1.55;font-size:28px;">'
                f'{icon}{marker}</li>'
            )
        else:
            if in_list:
                parts.append("</ul>")
                in_list = False
            parts.append(f'<p style="margin:0 0 16px;line-height:1.6;font-size:28px;">{line}</p>')

    if in_list:
        parts.append("</ul>")

    return "\n".join(parts)


# ─────────────────────────────────────────────────────────
# Component renderers
# ─────────────────────────────────────────────────────────

def _render_component(comp: dict, accent: str, text_color: str, bg: str) -> str:
    """Render a single recommended_component dict into HTML."""
    ctype = _lower(comp.get("component", ""))
    purpose = _esc(str(comp.get("purpose", "")))
    position = _lower(comp.get("position", ""))
    priority = _lower(comp.get("visual_priority", ""))

    opacity = "1" if priority in ("high", "primary") else "0.85"

    if "stat" in ctype or "kpi" in ctype or "metric" in ctype:
        return f'''<div style="
            display:inline-flex;flex-direction:column;align-items:center;
            padding:24px 32px;border-radius:16px;
            background:rgba(255,255,255,0.06);border:1.5px solid rgba(255,255,255,0.1);
            backdrop-filter:blur(8px);opacity:{opacity};min-width:140px;
        ">
            <span style="font-size:42px;font-weight:900;color:{accent};line-height:1.1;">—</span>
            <span style="font-size:14px;opacity:0.7;margin-top:6px;text-align:center;max-width:120px;">{purpose}</span>
        </div>'''

    if "progress" in ctype or "bar" in ctype:
        return f'''<div style="width:100%;max-width:360px;opacity:{opacity};">
            <div style="font-size:13px;opacity:0.7;margin-bottom:6px;">{purpose}</div>
            <div style="height:10px;border-radius:5px;background:rgba(255,255,255,0.1);overflow:hidden;">
                <div style="width:72%;height:100%;border-radius:5px;background:linear-gradient(90deg,{accent},rgba(255,255,255,0.3));"></div>
            </div>
        </div>'''

    if "tag" in ctype or "pill" in ctype or "chip" in ctype:
        return f'''<div style="display:flex;flex-wrap:wrap;gap:8px;opacity:{opacity};">
            <span style="padding:6px 16px;border-radius:20px;background:{accent};color:{bg};font-size:13px;font-weight:700;">{purpose or "Tag"}</span>
            <span style="padding:6px 16px;border-radius:20px;background:rgba(255,255,255,0.08);font-size:13px;font-weight:600;border:1px solid rgba(255,255,255,0.12);">Insight</span>
        </div>'''

    if "timeline" in ctype or "dot" in ctype:
        return f'''<div style="display:flex;align-items:flex-start;gap:14px;opacity:{opacity};">
            <div style="width:14px;height:14px;border-radius:50%;background:{accent};flex-shrink:0;margin-top:4px;box-shadow:0 0 8px {accent};"></div>
            <span style="font-size:16px;line-height:1.5;">{purpose}</span>
        </div>'''

    if "quote" in ctype or "blockquote" in ctype:
        return f'''<div style="
            border-left:4px solid {accent};padding:16px 24px;margin:8px 0;
            font-style:italic;font-size:22px;line-height:1.6;opacity:0.9;
            background:rgba(255,255,255,0.03);border-radius:0 12px 12px 0;
        ">"{purpose}"</div>'''

    if "code" in ctype or "terminal" in ctype:
        return f'''<div style="
            background:rgba(0,0,0,0.4);border-radius:12px;padding:20px 24px;
            font-family:'JetBrains Mono','Fira Code',monospace;font-size:14px;
            line-height:1.7;border:1px solid rgba(255,255,255,0.08);opacity:{opacity};
            color:rgba(255,255,255,0.85);
        "><span style="color:{accent};">$</span> {purpose}</div>'''

    if "comparison" in ctype or "table" in ctype or "versus" in ctype:
        return f'''<div style="
            display:grid;grid-template-columns:1fr 1fr;gap:12px;opacity:{opacity};
        ">
            <div style="padding:16px;border-radius:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);text-align:center;font-size:15px;">Before</div>
            <div style="padding:16px;border-radius:12px;background:rgba(255,255,255,0.05);border:1px solid {accent};text-align:center;font-size:15px;font-weight:700;">After</div>
        </div>'''

    if "icon" in ctype or "grid" in ctype or "emoji" in ctype:
        return f'''<div style="
            display:grid;grid-template-columns:repeat(3,1fr);gap:10px;opacity:{opacity};
        ">
            <div style="text-align:center;padding:12px;border-radius:10px;background:rgba(255,255,255,0.04);font-size:24px;">⚡</div>
            <div style="text-align:center;padding:12px;border-radius:10px;background:rgba(255,255,255,0.04);font-size:24px;">🎯</div>
            <div style="text-align:center;padding:12px;border-radius:10px;background:rgba(255,255,255,0.04);font-size:24px;">🚀</div>
        </div>'''

    # Fallback: generic card component
    if purpose:
        return f'''<div style="
            padding:14px 20px;border-radius:12px;background:rgba(255,255,255,0.04);
            border:1px solid rgba(255,255,255,0.08);font-size:14px;opacity:{opacity};
        ">{purpose}</div>'''

    return ""


# ─────────────────────────────────────────────────────────
# Decorative elements driven by visual_mood
# ─────────────────────────────────────────────────────────

def _build_decorations(st: dict, accent: str, primary: str) -> str:
    """Generate decorative CSS overlays driven by visual_mood list."""
    moods = _list(st.get("visual_mood", []))
    mood_str = " ".join(_lower(m) for m in moods)

    # Determine glow intensity and style based on mood keywords
    if any(kw in mood_str for kw in ("dramatic", "bold", "intense", "powerful")):
        return f'''
        <div style="position:absolute;top:-80px;right:-80px;width:400px;height:400px;border-radius:50%;
            background:radial-gradient(circle,rgba(255,255,255,0.08) 0%,transparent 70%);
            pointer-events:none;z-index:1;"></div>
        <div style="position:absolute;bottom:-120px;left:-60px;width:500px;height:500px;border-radius:50%;
            background:radial-gradient(circle,{accent}22 0%,transparent 60%);
            pointer-events:none;z-index:1;"></div>
        <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:800px;height:800px;border-radius:50%;
            background:radial-gradient(circle,{primary}0d 0%,transparent 50%);
            pointer-events:none;z-index:0;"></div>'''

    if any(kw in mood_str for kw in ("minimal", "clean", "simple", "calm")):
        return f'''
        <div style="position:absolute;bottom:0;left:0;right:0;height:2px;
            background:linear-gradient(90deg,transparent,{accent}44,transparent);
            pointer-events:none;z-index:1;"></div>'''

    if any(kw in mood_str for kw in ("futuristic", "tech", "cyber", "digital")):
        return f'''
        <div style="position:absolute;top:0;left:0;right:0;bottom:0;
            background:repeating-linear-gradient(0deg,transparent,transparent 40px,rgba(255,255,255,0.015) 40px,rgba(255,255,255,0.015) 41px);
            pointer-events:none;z-index:1;"></div>
        <div style="position:absolute;top:-100px;right:-100px;width:350px;height:350px;border-radius:50%;
            background:radial-gradient(circle,{accent}18 0%,transparent 70%);
            pointer-events:none;z-index:1;"></div>
        <div style="position:absolute;bottom:-80px;left:-80px;width:300px;height:300px;border-radius:50%;
            background:radial-gradient(circle,{primary}15 0%,transparent 70%);
            pointer-events:none;z-index:1;"></div>'''

    if any(kw in mood_str for kw in ("warm", "organic", "natural", "earthy")):
        return f'''
        <div style="position:absolute;top:-60px;right:-60px;width:300px;height:300px;border-radius:50%;
            background:radial-gradient(circle,{accent}15 0%,transparent 65%);
            pointer-events:none;z-index:1;"></div>
        <div style="position:absolute;bottom:-40px;left:-40px;width:250px;height:250px;border-radius:40%;
            background:radial-gradient(circle,{primary}12 0%,transparent 60%);
            pointer-events:none;z-index:1;transform:rotate(45deg);"></div>'''

    if any(kw in mood_str for kw in ("corporate", "professional", "formal")):
        return f'''
        <div style="position:absolute;top:0;left:0;bottom:0;width:6px;
            background:{accent};pointer-events:none;z-index:5;"></div>
        <div style="position:absolute;top:0;left:0;right:0;height:4px;
            background:linear-gradient(90deg,{accent},{primary});pointer-events:none;z-index:5;"></div>'''

    # Default: subtle editorial glow
    return f'''
    <div style="position:absolute;top:-80px;right:-80px;width:320px;height:320px;border-radius:50%;
        background:radial-gradient(circle,{accent}12 0%,transparent 70%);
        pointer-events:none;z-index:1;"></div>
    <div style="position:absolute;bottom:-60px;left:-60px;width:260px;height:260px;border-radius:50%;
        background:radial-gradient(circle,{primary}10 0%,transparent 70%);
        pointer-events:none;z-index:1;"></div>'''


# ─────────────────────────────────────────────────────────
# Accent bar styles (top edge treatment)
# ─────────────────────────────────────────────────────────

def _build_accent_bar(st: dict, accent: str, primary: str, secondary: str) -> str:
    """Generate a top-edge accent bar whose style varies per-slide theme."""
    design_styles = _list(st.get("design_style", []))
    style_str = " ".join(_lower(s) for s in design_styles)

    if any(kw in style_str for kw in ("minimal", "clean", "simple")):
        return f'<div style="position:absolute;top:0;left:0;right:0;height:4px;background:{accent};z-index:5;"></div>'

    if any(kw in style_str for kw in ("bold", "dramatic", "editorial")):
        return f'<div style="position:absolute;top:0;left:0;right:0;height:12px;background:linear-gradient(90deg,{accent},{primary},{secondary});z-index:5;"></div>'

    if any(kw in style_str for kw in ("futuristic", "tech", "cyber")):
        return f'''<div style="position:absolute;top:0;left:0;right:0;height:6px;z-index:5;
            background:repeating-linear-gradient(90deg,{accent} 0px,{accent} 40px,transparent 40px,transparent 48px);"></div>'''

    if any(kw in style_str for kw in ("elegant", "premium", "luxury")):
        return f'<div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,transparent 10%,{accent} 50%,transparent 90%);z-index:5;"></div>'

    # Default
    return f'<div style="position:absolute;top:0;left:0;right:0;height:8px;background:linear-gradient(90deg,{accent},{primary},{accent});z-index:5;"></div>'


# ─────────────────────────────────────────────────────────
# Image slot builder
# ─────────────────────────────────────────────────────────

def _build_image_slot(
    st: dict,
    slide: Any,
    accent: str,
    is_split: bool,
    coverage: str,
) -> str:
    """Build the image upload placeholder driven by image strategy."""
    img_data = st.get("image", {}) if isinstance(st.get("image"), dict) else {}
    visual_concept = img_data.get("description") or slide.visual_concept or slide.image_description or ""
    gen_prompt = img_data.get("generation_prompt", "")
    visual_style = _lower(img_data.get("visual_style", ""))

    if not visual_concept.strip():
        return ""

    # Determine dimensions from coverage
    if is_split:
        width_style = "width:45%;height:100%;min-height:100%;padding:16px;display:flex;flex-direction:column;justify-content:center;box-sizing:border-box;"
    elif coverage in ("full", "100%"):
        width_style = "padding:0;height:40%;min-height:200px;flex:1 1 auto;"
    elif coverage in ("half", "50%"):
        width_style = "padding:8px 60px 0;height:30%;min-height:160px;flex:1 1 auto;"
    elif coverage in ("quarter", "25%", "thumbnail", "small"):
        width_style = "padding:8px 60px 0;height:18%;min-height:100px;flex:0 0 auto;"
    else:
        width_style = "padding:8px 60px 0;height:24%;min-height:130px;flex:1 1 auto;"

    # CSS filter from visual_style
    css_filter = ""
    if "grayscale" in visual_style or "monochrome" in visual_style:
        css_filter = "filter:grayscale(1);"
    elif "sepia" in visual_style or "vintage" in visual_style:
        css_filter = "filter:sepia(0.6);"
    elif "high-contrast" in visual_style or "high contrast" in visual_style:
        css_filter = "filter:contrast(1.3);"

    tooltip = _esc(gen_prompt or visual_concept)

    return f'''
    <div class="image-slot" style="{width_style}z-index:2;position:relative;">
        <div style="
            border-radius:14px;
            border:2px dashed rgba(255,255,255,0.15);
            background:rgba(255,255,255,0.03);
            padding:20px;text-align:center;height:100%;box-sizing:border-box;
            display:flex;align-items:center;justify-content:center;position:relative;
        ">
            <label style="cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:8px;width:100%;height:100%;justify-content:center;">
                <span style="font-size:28px;">🖼️</span>
                <span style="font-size:12px;opacity:0.5;line-height:1.35;max-width:280px;">{_esc(visual_concept)}</span>
                <input type="file" accept="image/*" style="display:none;" />
            </label>
            <img src="" style="display:none;width:100%;height:100%;object-fit:cover;border-radius:10px;position:absolute;top:0;left:0;{css_filter}" title="{tooltip}" />
            <button class="remove-btn" style="
                display:none;position:absolute;top:6px;right:6px;
                background:#ef4444;color:#fff;border:none;border-radius:50%;
                width:22px;height:22px;align-items:center;justify-content:center;
                cursor:pointer;z-index:10;font-size:11px;
            ">✕</button>
        </div>
    </div>'''


# ─────────────────────────────────────────────────────────
# Design constraint processor
# ─────────────────────────────────────────────────────────

def _apply_constraints(constraints: list, base_styles: dict) -> dict:
    """Modify base CSS properties based on design_constraints list."""
    c_str = " ".join(_lower(c) for c in constraints)

    if "minimal text" in c_str or "minimal content" in c_str:
        base_styles["body_max_height"] = "200px"
        base_styles["body_font_size"] = "24px"

    if "high contrast" in c_str:
        base_styles["heading_shadow"] = "0 3px 12px rgba(0,0,0,0.5)"

    if "no decorative" in c_str or "no decoration" in c_str:
        base_styles["show_decorations"] = False

    if "large typography" in c_str or "big text" in c_str:
        base_styles["heading_size"] = "72px"
        base_styles["body_font_size"] = "34px"

    if "compact" in c_str or "dense" in c_str:
        base_styles["padding"] = "40px"
        base_styles["heading_size"] = "42px"

    return base_styles


# ─────────────────────────────────────────────────────────
# Main node
# ─────────────────────────────────────────────────────────

class ReactCodeGenerator(BaseNode):
    """Design Engine: generates self-contained HTML/CSS/JS slides.

    Reads per-slide ``slide_theme`` data to drive layout selection,
    component rendering, visual hierarchy, image strategy, and
    decorative treatments.  Every slide can look completely different
    based on its theme object.
    """

    node_name = "react_code_generator"
    category = "content"
    description = "Design Engine – generates themed HTML/CSS/JS slides."

    # ── slide type resolution ──

    @staticmethod
    def _resolve_slide_type(slide: Any, idx: int, total: int) -> str:
        """Determine slide type from data, falling back to index heuristics."""
        st = _lower(getattr(slide, "slide_type", ""))
        if st in ("hook", "cover", "intro"):
            return "hook"
        if st in ("cta", "outro", "action", "closing"):
            return "cta"
        if st in ("data", "stats", "metrics", "evidence"):
            return "data"
        if st in ("quote", "testimonial", "blockquote"):
            return "quote"
        if st in ("comparison", "versus", "vs"):
            return "comparison"
        if st in ("timeline", "journey", "milestones"):
            return "timeline"
        if st in ("summary", "recap", "overview"):
            return "summary"
        if st in ("content", "insight", "explanation", "detail"):
            return "content"
        # Index-based fallback
        if idx == 0:
            return "hook"
        if idx == total - 1:
            return "cta"
        return "content"

    # ── layout resolution ──

    @staticmethod
    def _resolve_layout(st: dict, slide: Any) -> str:
        """Determine layout type from slide_theme, falling back to image_placement."""
        layout_type = _lower(_get(st, "layout", "type"))

        mapping = {
            "centered": "centered",
            "center": "centered",
            "split-left": "split-left",
            "split left": "split-left",
            "left": "split-left",
            "split-right": "split-right",
            "split right": "split-right",
            "right": "split-right",
            "full-bleed": "full-bleed",
            "full bleed": "full-bleed",
            "full": "full-bleed",
            "fullscreen": "full-bleed",
            "asymmetric": "asymmetric",
            "offset": "asymmetric",
            "stacked": "stacked",
            "vertical": "stacked",
            "editorial": "editorial",
            "magazine": "editorial",
            "column": "editorial",
            "columns": "editorial",
        }

        if layout_type in mapping:
            return mapping[layout_type]

        # Fall back to image_placement
        placement = _lower(slide.image_placement) if hasattr(slide, "image_placement") else ""
        if "left" in placement:
            return "split-left"
        if "right" in placement:
            return "split-right"
        if any(kw in placement for kw in ("background", "full", "whole")):
            return "full-bleed"

        return "stacked"

    # ── heading renderer with highlight words ──

    @staticmethod
    def _render_heading(heading: str, st: dict, accent: str) -> str:
        """Render heading text with optional highlight words."""
        highlight_words = _list(_get(st, "visual_hierarchy", "highlight_words"))
        highlight_color = _get(st, "visual_hierarchy", "highlight_color") or accent

        rendered = _esc(heading)
        if highlight_words:
            escaped_words = [re.escape(str(w).strip()) for w in highlight_words if str(w).strip()]
            if escaped_words:
                pattern = "|".join(escaped_words)
                regex = re.compile(rf"\b({pattern})\b", re.IGNORECASE)
                rendered = regex.sub(
                    rf'<span style="color:{highlight_color};font-weight:900;">\1</span>',
                    rendered,
                )
        return rendered

    # ── heading size resolver ──

    @staticmethod
    def _resolve_heading_size(st: dict, slide_type: str, default: str = "52px") -> str:
        size = _lower(_get(st, "visual_hierarchy", "headline_size"))
        if size in ("large", "h1", "xl"):
            return "64px"
        if size in ("medium", "h2", "lg"):
            return "52px"
        if size in ("small", "h3", "md"):
            return "42px"
        if size in ("xs", "tiny"):
            return "34px"
        # Type-based defaults
        if slide_type == "hook":
            return "64px"
        if slide_type == "cta":
            return "58px"
        if slide_type == "data":
            return "46px"
        return default

    # ── heading weight resolver ──

    @staticmethod
    def _resolve_heading_weight(st: dict, slide: Any) -> str:
        w = _lower(_get(st, "visual_hierarchy", "headline_weight"))
        if w in ("bold", "900", "black"):
            return "900"
        if w in ("semibold", "700", "semi-bold"):
            return "700"
        if w in ("medium", "600"):
            return "600"
        if w in ("normal", "regular", "400"):
            return "400"
        if w in ("light", "300"):
            return "300"
        hw = _lower(getattr(slide, "heading_font_weight", ""))
        return hw if hw else "800"

    # ── process ──

    async def process(self, input_data: dict[str, Any], context: NodeContext) -> dict[str, Any]:
        topic_id = input_data.get("pending_topic_id")
        week_id = input_data.get("week_id", "")
        content_dict = input_data.get("content", {})

        tc = content_dict.get(topic_id)
        if not tc or not tc.carousel_slides or not tc.theme:
            return {}

        theme = tc.theme
        slides = tc.carousel_slides
        total_slides = len(slides)

        # ── Global theme colors ──
        theme_bg = theme.background_color or "#0f172a"
        theme_text = theme.text_color or "#f8fafc"
        theme_primary = theme.primary_color or "#3b82f6"
        theme_secondary = theme.secondary_color or "#10b981"
        theme_accent = theme.accent_color or "#eab308"

        font_heading_global = f"'{theme.font_heading}', sans-serif" if theme.font_heading else "'Inter', sans-serif"
        font_body_global = f"'{theme.font_body}', sans-serif" if theme.font_body else "'Inter', sans-serif"

        # ── Collect all fonts ──
        all_fonts = {"Inter"}
        if theme.font_heading:
            all_fonts.add(theme.font_heading)
        if theme.font_body:
            all_fonts.add(theme.font_body)
        for s in slides:
            if s.heading_font:
                all_fonts.add(s.heading_font)
            if s.body_font:
                all_fonts.add(s.body_font)

        font_import_rules = ""
        for f in sorted(all_fonts):
            f_url = f.strip().replace(" ", "+")
            font_import_rules += f"@import url('https://fonts.googleapis.com/css2?family={f_url}:wght@300;400;500;600;700;800;900&display=swap');\n"

        # ── Build each slide ──
        slides_html_list: list[str] = []

        for idx, slide in enumerate(slides):
            st = slide.slide_theme or {}
            slide_type = self._resolve_slide_type(slide, idx, total_slides)
            layout = self._resolve_layout(st, slide)

            # Per-slide font resolution
            h_font = f"'{slide.heading_font}', sans-serif" if slide.heading_font else font_heading_global
            b_font = f"'{slide.body_font}', sans-serif" if slide.body_font else font_body_global
            h_weight = self._resolve_heading_weight(st, slide)
            h_size = self._resolve_heading_size(st, slide_type)
            b_weight = slide.body_font_weight or "400"

            # Visual hierarchy
            rendered_heading = self._render_heading(slide.heading or "", st, theme_accent)
            body_html = _format_body_html(slide.body_text or "", "var(--accent)")

            # Image strategy
            img_coverage = _lower(_get(st, "image", "coverage"))
            is_split = layout in ("split-left", "split-right")
            image_slot_html = _build_image_slot(st, slide, theme_accent, is_split, img_coverage)
            has_image = bool(image_slot_html.strip())

            # Components
            components = _list(st.get("recommended_components", []))
            components_html_parts: list[str] = []
            for comp in components:
                if isinstance(comp, dict):
                    rendered = _render_component(comp, theme_accent, theme_text, theme_bg)
                    if rendered:
                        components_html_parts.append(rendered)

            components_html = ""
            if components_html_parts:
                items = "\n".join(components_html_parts)
                components_html = f'''
                <div style="display:flex;flex-wrap:wrap;gap:14px;padding:8px 0;z-index:2;align-items:flex-start;">
                    {items}
                </div>'''

            # Design constraints
            constraints = _list(st.get("design_constraints", []))
            styles = {
                "body_max_height": "420px",
                "body_font_size": "28px",
                "heading_shadow": "0 2px 8px rgba(0,0,0,0.25)",
                "show_decorations": True,
                "heading_size": h_size,
                "padding": "56px",
            }
            styles = _apply_constraints(constraints, styles)
            h_size = styles["heading_size"]

            # Decorations
            decorations_html = _build_decorations(st, theme_accent, theme_primary) if styles["show_decorations"] else ""

            # Accent bar
            accent_bar_html = _build_accent_bar(st, theme_accent, theme_primary, theme_secondary)

            # CSS recommendations
            css_recs = _list(_get(st, "html_generation_rules", "css_recommendations"))
            extra_css = " ".join(str(r) for r in css_recs if isinstance(r, str))

            # Progress dots
            dot_elements = []
            for i in range(total_slides):
                active = i == idx
                dot_color = "var(--accent)" if active else "rgba(255,255,255,0.2)"
                dot_scale = "scale(1.2)" if active else "scale(1)"
                dot_elements.append(
                    f'<span style="width:10px;height:10px;border-radius:50%;'
                    f'background:{dot_color};transform:{dot_scale};'
                    f'transition:all 0.3s ease;display:inline-block;margin:0 4px;"></span>'
                )
            dots_html = "".join(dot_elements)
            slide_num = slide.slide_number or (idx + 1)

            # ── Layout-specific content assembly ──
            px = styles["padding"]

            # Badge (only for content/data/summary slides, driven by components or slide_type)
            badge_html = ""
            show_badge = slide_type in ("content", "data", "summary", "comparison", "timeline")
            badge_comp = next((c for c in components if isinstance(c, dict) and "badge" in _lower(c.get("component", ""))), None)
            if badge_comp:
                badge_label = _esc(str(badge_comp.get("purpose", f"SLIDE {slide_num}")))
                badge_html = f'''
                <div style="z-index:2;flex-shrink:0;">
                    <span style="font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:2.5px;
                        padding:8px 22px;border-radius:4px;background:var(--accent);color:var(--bg);display:inline-block;">
                        {badge_label}
                    </span>
                </div>'''
            elif show_badge:
                type_labels = {
                    "data": "📊 DATA",
                    "comparison": "⚖️ COMPARE",
                    "timeline": "📅 TIMELINE",
                    "summary": "📋 SUMMARY",
                    "content": f"SLIDE {slide_num}",
                }
                badge_text = type_labels.get(slide_type, f"SLIDE {slide_num}")
                badge_html = f'''
                <div style="z-index:2;flex-shrink:0;">
                    <span style="font-size:13px;font-weight:800;text-transform:uppercase;letter-spacing:2px;
                        padding:8px 22px;border-radius:4px;background:var(--accent);color:var(--bg);display:inline-block;">
                        {badge_text}
                    </span>
                </div>'''

            # Heading block
            heading_block = f'''
            <div style="z-index:2;flex-shrink:0;">
                <div style="font-size:{h_size};line-height:1.12;font-weight:{h_weight};
                    font-family:{h_font};color:var(--text);
                    text-shadow:{styles['heading_shadow']};overflow-wrap:anywhere;">
                    {rendered_heading}
                </div>
            </div>'''

            # Divider
            divider_html = f'''
            <div style="z-index:2;flex-shrink:0;">
                <div style="width:120px;height:5px;background:var(--accent);border-radius:3px;"></div>
            </div>'''

            # Body block
            body_block = f'''
            <div style="z-index:2;flex:0 1 auto;overflow:hidden;">
                <div style="font-size:{styles['body_font_size']};line-height:1.6;
                    font-family:{b_font};font-weight:{b_weight};opacity:0.92;
                    overflow-wrap:anywhere;max-height:{styles['body_max_height']};overflow:hidden;">
                    {body_html}
                </div>
            </div>'''

            # Brand header (only for content-type slides, not hook/cta)
            brand_header_html = ""
            if slide_type not in ("hook", "cta"):
                brand_header_html = f'''
                <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:0 {px};margin-bottom:12px;z-index:2;width:100%;box-sizing:border-box;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="width:44px;height:44px;border-radius:50%;
                            background:linear-gradient(135deg,var(--accent),var(--primary));
                            display:flex;align-items:center;justify-content:center;
                            font-weight:900;font-size:18px;color:var(--bg);
                            box-shadow:0 2px 8px rgba(0,0,0,0.2);">T</div>
                        <div style="display:flex;flex-direction:column;">
                            <span style="font-size:16px;font-weight:800;color:var(--text);letter-spacing:0.5px;">tech_by_pravesh</span>
                            <span style="font-size:12px;opacity:0.6;font-weight:500;">AI &amp; Automation Builder</span>
                        </div>
                    </div>
                    <div style="font-size:14px;font-weight:800;color:var(--accent);
                        background:rgba(255,255,255,0.04);padding:6px 14px;border-radius:20px;
                        border:1px solid rgba(255,255,255,0.08);letter-spacing:1px;">
                        {slide_num} / {total_slides}
                    </div>
                </div>'''

            # Arrow for navigation
            arrow_html = ""
            if idx < total_slides - 1:
                arrow_html = '''
                <div style="width:64px;height:64px;border-radius:50%;display:flex;align-items:center;
                    justify-content:center;box-shadow:0 4px 16px rgba(0,0,0,0.35);background:var(--accent);">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--bg)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                </div>'''

            # Footer
            footer_html = f'''
            <div style="display:flex;justify-content:space-between;align-items:center;
                margin-top:auto;z-index:2;padding:0 {px};width:100%;box-sizing:border-box;">
                {arrow_html if arrow_html else '<div style="width:64px;"></div>'}
                <div style="display:flex;align-items:center;">
                    {dots_html}
                </div>
                <div style="font-size:18px;font-weight:700;opacity:0.6;color:var(--text);letter-spacing:0.5px;">@tech_by_pravesh</div>
            </div>'''

            # ══════════════════════════════════════════════
            # SLIDE TYPE SPECIFIC LAYOUTS
            # ══════════════════════════════════════════════

            if slide_type == "hook":
                # ── HOOK / COVER SLIDE ──
                body_esc = _esc(slide.body_text or "")
                storytelling = _esc(str(_get(st, "storytelling_purpose", "")))
                inside_content = f'''
                <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                    text-align:center;height:100%;padding:40px {px};box-sizing:border-box;flex:1;gap:20px;">
                    <span style="font-size:15px;font-weight:900;color:var(--accent);text-transform:uppercase;
                        letter-spacing:4px;display:block;">
                        🔥 EXCLUSIVE INSIGHT
                    </span>
                    <div style="font-size:{h_size};line-height:1.12;font-weight:{h_weight};
                        font-family:{h_font};color:var(--text);
                        text-shadow:0 4px 14px rgba(0,0,0,0.4);max-width:920px;">
                        {rendered_heading}
                    </div>
                    <div style="width:160px;height:6px;background:var(--accent);border-radius:3px;"></div>
                    {"<div style='font-size:30px;line-height:1.6;font-family:" + b_font + ";opacity:0.88;max-width:800px;font-weight:500;'>" + body_esc + "</div>" if body_esc else ""}
                    {components_html}
                </div>'''

            elif slide_type == "cta":
                # ── CTA / OUTRO SLIDE ──
                body_esc = _esc(slide.body_text or "")
                inside_content = f'''
                <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                    text-align:center;height:100%;padding:40px {px};box-sizing:border-box;flex:1;gap:18px;">
                    <span style="font-size:15px;font-weight:900;color:var(--accent);text-transform:uppercase;
                        letter-spacing:3px;display:block;">
                        🚀 TAKE ACTION
                    </span>
                    <div style="font-size:{h_size};line-height:1.15;font-weight:900;
                        font-family:{h_font};color:var(--text);
                        text-shadow:0 4px 12px rgba(0,0,0,0.4);max-width:920px;">
                        {rendered_heading}
                    </div>
                    {"<div style='font-size:28px;line-height:1.55;font-family:" + b_font + ";opacity:0.88;max-width:800px;margin-bottom:16px;'>" + body_esc + "</div>" if body_esc else ""}
                    {components_html}
                    <div style="display:flex;gap:36px;justify-content:center;align-items:center;
                        background:rgba(255,255,255,0.03);border:1.5px solid rgba(255,255,255,0.08);
                        border-radius:20px;padding:18px 40px;margin-top:12px;">
                        <div style="text-align:center;"><span style="font-size:36px;display:block;margin-bottom:4px;">❤️</span><span style="font-size:13px;font-weight:700;opacity:0.8;">Like</span></div>
                        <div style="text-align:center;"><span style="font-size:36px;display:block;margin-bottom:4px;">💬</span><span style="font-size:13px;font-weight:700;opacity:0.8;">Comment</span></div>
                        <div style="text-align:center;"><span style="font-size:36px;display:block;margin-bottom:4px;">✈️</span><span style="font-size:13px;font-weight:700;opacity:0.8;">Share</span></div>
                        <div style="text-align:center;"><span style="font-size:36px;display:block;margin-bottom:4px;">🔖</span><span style="font-size:13px;font-weight:700;color:var(--accent);">Save</span></div>
                    </div>
                </div>'''

            elif slide_type == "quote":
                # ── QUOTE SLIDE ──
                body_esc = _esc(slide.body_text or "")
                inside_content = f'''
                <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                    text-align:center;height:100%;padding:40px {px};box-sizing:border-box;flex:1;gap:24px;">
                    <span style="font-size:80px;color:var(--accent);opacity:0.3;line-height:1;">❝</span>
                    <div style="font-size:38px;line-height:1.45;font-weight:600;
                        font-family:{h_font};color:var(--text);font-style:italic;
                        max-width:860px;text-shadow:0 2px 8px rgba(0,0,0,0.2);">
                        {rendered_heading}
                    </div>
                    <div style="width:100px;height:4px;background:var(--accent);border-radius:2px;"></div>
                    {"<div style='font-size:22px;font-family:" + b_font + ";opacity:0.7;font-weight:500;'>" + body_esc + "</div>" if body_esc else ""}
                    {components_html}
                </div>'''

            elif slide_type == "data":
                # ── DATA / STATS SLIDE ──
                if layout in ("split-left", "split-right"):
                    text_side = f'''
                    <div style="display:flex;flex-direction:column;flex:1;justify-content:center;
                        padding:24px {px};z-index:2;box-sizing:border-box;gap:14px;">
                        {badge_html}
                        {heading_block}
                        {divider_html}
                        {body_block}
                        {components_html}
                    </div>'''
                    if layout == "split-left":
                        inside_content = f'''
                        <div style="display:flex;flex-direction:row;flex:1;overflow:hidden;width:100%;height:100%;box-sizing:border-box;">
                            {image_slot_html}
                            {text_side}
                        </div>'''
                    else:
                        inside_content = f'''
                        <div style="display:flex;flex-direction:row;flex:1;overflow:hidden;width:100%;height:100%;box-sizing:border-box;">
                            {text_side}
                            {image_slot_html}
                        </div>'''
                else:
                    inside_content = f'''
                    <div style="display:flex;flex-direction:column;padding:16px {px};gap:14px;flex:1;z-index:2;">
                        {badge_html}
                        {heading_block}
                        {divider_html}
                        {components_html}
                        {body_block}
                        {image_slot_html}
                    </div>'''

            else:
                # ── CONTENT / COMPARISON / TIMELINE / SUMMARY ──
                # Layout-driven assembly

                if layout == "centered":
                    inside_content = f'''
                    <div style="display:flex;flex-direction:column;align-items:center;text-align:center;
                        padding:16px {px};gap:14px;flex:1;z-index:2;justify-content:center;">
                        {badge_html}
                        {heading_block}
                        {divider_html}
                        {body_block}
                        {components_html}
                        {image_slot_html}
                    </div>'''

                elif layout in ("split-left", "split-right"):
                    text_side = f'''
                    <div style="display:flex;flex-direction:column;flex:1;justify-content:center;
                        padding:20px {px};z-index:2;box-sizing:border-box;gap:12px;">
                        {badge_html}
                        {heading_block}
                        {divider_html}
                        {body_block}
                        {components_html}
                    </div>'''
                    if layout == "split-left":
                        inside_content = f'''
                        <div style="display:flex;flex-direction:row;flex:1;overflow:hidden;width:100%;height:100%;box-sizing:border-box;">
                            {image_slot_html}
                            {text_side}
                        </div>'''
                    else:
                        inside_content = f'''
                        <div style="display:flex;flex-direction:row;flex:1;overflow:hidden;width:100%;height:100%;box-sizing:border-box;">
                            {text_side}
                            {image_slot_html}
                        </div>'''

                elif layout == "full-bleed":
                    inside_content = f'''
                    <div style="display:flex;flex-direction:column;flex:1;z-index:2;position:relative;">
                        {image_slot_html}
                        <div style="padding:20px {px};display:flex;flex-direction:column;gap:12px;
                            background:linear-gradient(to top,var(--bg) 60%,transparent);
                            position:relative;z-index:3;margin-top:-80px;flex:1;justify-content:flex-end;">
                            {badge_html}
                            {heading_block}
                            {divider_html}
                            {body_block}
                            {components_html}
                        </div>
                    </div>'''

                elif layout == "asymmetric":
                    inside_content = f'''
                    <div style="display:flex;flex-direction:row;flex:1;overflow:hidden;width:100%;height:100%;box-sizing:border-box;">
                        <div style="width:60%;display:flex;flex-direction:column;justify-content:center;
                            padding:20px {px};z-index:2;box-sizing:border-box;gap:12px;">
                            {badge_html}
                            {heading_block}
                            {divider_html}
                            {body_block}
                            {components_html}
                        </div>
                        <div style="width:40%;display:flex;flex-direction:column;justify-content:center;
                            padding:16px;box-sizing:border-box;">
                            {image_slot_html}
                        </div>
                    </div>'''

                elif layout == "editorial":
                    inside_content = f'''
                    <div style="display:flex;flex-direction:column;padding:16px {px};gap:16px;flex:1;z-index:2;">
                        {badge_html}
                        {heading_block}
                        {divider_html}
                        <div style="display:flex;flex-direction:row;gap:24px;flex:1;">
                            <div style="flex:1;display:flex;flex-direction:column;gap:10px;">
                                {body_block}
                                {components_html}
                            </div>
                            <div style="flex:0 0 38%;display:flex;flex-direction:column;">
                                {image_slot_html}
                            </div>
                        </div>
                    </div>'''

                else:
                    # stacked (default)
                    inside_content = f'''
                    <div style="display:flex;flex-direction:column;padding:16px {px};gap:12px;flex:1;z-index:2;">
                        {badge_html}
                        {heading_block}
                        {divider_html}
                        {body_block}
                        {components_html}
                        {image_slot_html}
                    </div>'''

            # ── Assemble full slide ──
            slide_html = f'''
            <div class="slide-container" style="
                width:1080px;height:1350px;background-color:var(--bg);color:var(--text);
                position:relative;padding:48px 0 36px 0;box-sizing:border-box;
                display:flex;flex-direction:column;justify-content:space-between;
                font-family:{b_font};font-weight:{b_weight};margin-bottom:20px;
                overflow:hidden;{extra_css}
            ">
                {accent_bar_html}
                {brand_header_html}
                {inside_content}
                {footer_html}
                {decorations_html}
            </div>'''

            slides_html_list.append(slide_html)

        # ── Full document ──
        slides_joined = "\n".join(slides_html_list)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Slides Preview - {topic_id}</title>

  <style>
     {font_import_rules}

     body {{
        margin: 0;
        padding: 0;
        overflow: auto;
        --primary: {theme_primary};
        --secondary: {theme_secondary};
        --accent: {theme_accent};
        --bg: {theme_bg};
        --text: {theme_text};
     }}

     #carousel-container {{
         display: flex;
         flex-direction: column;
         align-items: center;
         background: #f1f5f9;
         padding: 20px 0;
     }}

     .slide-container {{
         width: 1080px;
         height: 1350px;
         position: relative;
         overflow: hidden;
         box-shadow: 0 10px 30px rgba(0,0,0,0.15);
         background-color: var(--bg);
         margin-bottom: 20px;
     }}
  </style>
</head>
<body>
  <div id="carousel-container">
    {slides_joined}
  </div>

  <script>
    document.querySelectorAll('.image-slot').forEach((slot) => {{
      const input = slot.querySelector('input[type="file"]');
      const img = slot.querySelector('img');
      const label = slot.querySelector('label');
      const removeBtn = slot.querySelector('.remove-btn');

      if (input && img && label) {{
        input.addEventListener('change', (e) => {{
          const file = e.target.files[0];
          if (file) {{
            const reader = new FileReader();
            reader.onload = (event) => {{
              img.src = event.target.result;
              img.style.display = 'block';
              label.style.display = 'none';
              if (removeBtn) removeBtn.style.display = 'flex';
              window.parent.postMessage({{ type: 'SLIDE_IMAGE_UPLOADED' }}, '*');
            }};
            reader.readAsDataURL(file);
          }}
        }});
      }}

      if (removeBtn && input && img && label) {{
        removeBtn.addEventListener('click', (e) => {{
          e.stopPropagation();
          e.preventDefault();
          img.src = '';
          img.style.display = 'none';
          label.style.display = 'flex';
          removeBtn.style.display = 'none';
          input.value = '';
          window.parent.postMessage({{ type: 'SLIDE_IMAGE_UPLOADED' }}, '*');
        }});
      }}
    }});
  </script>
</body>
</html>
"""

        # ── Save to disk ──
        project_root = Path(__file__).resolve().parents[5]
        render_topic_id = f"{week_id}_{topic_id}"
        output_dir = project_root / "data" / "exports" / render_topic_id
        output_dir.mkdir(parents=True, exist_ok=True)

        html_file_path = output_dir / "slides.html"
        html_file_path.write_text(html_content, encoding="utf-8")

        if context.logger:
            context.logger.event("design_engine.generate_html", {
                "topic_id": topic_id,
                "file_path": str(html_file_path),
                "slides": total_slides,
            })

        self.save_artifact(
            context=context,
            phase="05_content",
            topic_id=topic_id,
            filename="slides.html",
            content=html_content,
        )

        tc.rendered_code = html_content

        updated_content = dict(content_dict)
        updated_content[topic_id] = tc

        return {
            "content": updated_content,
            "carousel_status": "done",
            "pipeline_status": "content_creation",
        }
