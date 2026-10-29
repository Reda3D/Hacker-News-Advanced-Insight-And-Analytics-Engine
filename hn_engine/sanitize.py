"""HTML sanitization with an explicit allow-list."""

from __future__ import annotations

import re

try:
    import bleach
    _HAS_BLEACH = True
except ImportError:  # pragma: no cover
    _HAS_BLEACH = False


# Conservative allow-list matching HN's HTML subset
_ALLOWED_TAGS = {
    "p", "br",
    "i", "em",
    "b", "strong",
    "a",
    "pre", "code",
    "ul", "ol", "li",
    "blockquote",
}

_ALLOWED_ATTRIBUTES = {
    "a": ["href", "rel"],
}

_ALLOWED_PROTOCOLS = {"http", "https", "mailto"}


def sanitize_html(raw: str | None) -> str:
    """Sanitize raw HTML from HN fields for safe display.

    Uses ``bleach`` if available; falls back to a plain-text stripper
    otherwise.

    Args:
        raw: Raw HTML string, or ``None``.

    Returns:
        Sanitized HTML (or plain text if bleach is not installed).
    """
    if raw is None:
        return ""

    if _HAS_BLEACH:
        return str(bleach.clean(
            raw,
            tags=_ALLOWED_TAGS,
            attributes=_ALLOWED_ATTRIBUTES,
            protocols=_ALLOWED_PROTOCOLS,
            strip=True,
        ))

    # Fallback: strip all tags with a simple regex
    return re.sub(r"<[^>]+>", "", raw)
