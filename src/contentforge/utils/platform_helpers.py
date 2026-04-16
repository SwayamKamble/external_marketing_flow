"""Platform-specific helper utilities for ContentForge.

Character counting, hashtag validation, caption formatting,
and platform-specific rules enforcement.
"""

from __future__ import annotations

import re
from typing import Any

from contentforge.core.config_loader import ConfigLoader


def count_chars(text: str, include_hashtags: bool = True) -> int:
    """Count characters in a caption.

    Args:
        text: The caption text.
        include_hashtags: Whether to include hashtag section in count.

    Returns:
        Character count.
    """
    if not include_hashtags:
        # Remove hashtag section (lines starting with multiple #tags)
        lines = text.split("\n")
        filtered = [
            line for line in lines
            if not re.match(r"^[#\w\s]+$", line) or line.startswith("# ")
        ]
        text = "\n".join(filtered)

    return len(text)


def validate_caption(
    caption: str,
    platform: str,
    config: ConfigLoader | None = None,
    platform_rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a caption against platform rules.

    Args:
        caption: The caption text to validate.
        platform: Platform name (e.g., "instagram").
        config: ConfigLoader instance (loads rules from YAML).
        platform_rules: Pre-loaded platform rules dict.

    Returns:
        Dict with validation results: {valid, issues, char_count, hashtag_count}.
    """
    # Load rules
    if platform_rules is None and config:
        all_rules = config.get_platform_rules()
        platform_rules = all_rules.get("platforms", {}).get(platform, {})

    if not platform_rules:
        return {
            "valid": True,
            "issues": [],
            "char_count": len(caption),
            "hashtag_count": count_hashtags(caption),
        }

    issues = []
    char_limit = platform_rules.get("caption_char_limit", 999999)
    hashtag_range = platform_rules.get("hashtag_range", [0, 30])

    # Check character limit
    char_count = len(caption)
    if char_count > char_limit:
        issues.append(
            f"Caption exceeds {platform} limit: {char_count}/{char_limit} chars"
        )

    # Check hashtag count
    hashtag_count = count_hashtags(caption)
    min_hashtags, max_hashtags = hashtag_range
    if hashtag_count < min_hashtags:
        issues.append(
            f"Too few hashtags for {platform}: {hashtag_count} (min: {min_hashtags})"
        )
    if hashtag_count > max_hashtags:
        issues.append(
            f"Too many hashtags for {platform}: {hashtag_count} (max: {max_hashtags})"
        )

    # Check for CTA
    cta_indicators = ["?", "👇", "↓", "comment", "share", "save", "follow", "👆", "🔖", "🔥"]
    has_cta = any(indicator.lower() in caption.lower() for indicator in cta_indicators)
    if not has_cta:
        issues.append(f"Missing CTA for {platform}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "char_count": char_count,
        "char_limit": char_limit,
        "hashtag_count": hashtag_count,
        "hashtag_range": hashtag_range,
    }


def count_hashtags(text: str) -> int:
    """Count hashtags in text.

    Args:
        text: Text containing hashtags.

    Returns:
        Number of hashtags found.
    """
    return len(re.findall(r"#\w+", text))


def extract_hashtags(text: str) -> list[str]:
    """Extract all hashtags from text.

    Args:
        text: Text containing hashtags.

    Returns:
        List of hashtag strings (including the # prefix).
    """
    return re.findall(r"#\w+", text)


def format_caption_for_platform(
    caption: str,
    hashtags: list[str],
    cta: str,
    platform: str,
) -> str:
    """Format a caption with hashtags and CTA for a specific platform.

    Args:
        caption: Main caption body.
        hashtags: List of hashtags.
        cta: Call-to-action text.
        platform: Target platform.

    Returns:
        Formatted caption string.
    """
    parts = [caption.strip()]

    if cta:
        parts.append(f"\n{cta}")

    if hashtags:
        if platform == "x":
            # X: hashtags inline, minimal
            parts.append("\n" + " ".join(hashtags[:3]))
        elif platform == "instagram":
            # Instagram: hashtags on new lines at the end
            parts.append("\n.\n.\n.\n" + " ".join(hashtags))
        elif platform == "linkedin":
            # LinkedIn: few hashtags at the end
            parts.append("\n\n" + " ".join(hashtags[:5]))
        elif platform == "threads":
            # Threads: minimal or no hashtags
            if hashtags:
                parts.append("\n" + " ".join(hashtags[:3]))

    return "\n".join(parts)


def get_week_id() -> str:
    """Get the current ISO week ID (e.g., '2026-W16')."""
    from datetime import datetime
    now = datetime.now()
    year, week, _ = now.isocalendar()
    return f"{year}-W{week:02d}"


def get_day_name() -> str:
    """Get the current day name in lowercase."""
    from datetime import datetime
    return datetime.now().strftime("%A").lower()
