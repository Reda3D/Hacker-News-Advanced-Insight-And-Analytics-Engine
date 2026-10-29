"""Live data endpoints: story lists, updates, and max item."""

from __future__ import annotations

import enum
import logging

from hn_engine.client import HNClient
from hn_engine.errors import ValidationError
from hn_engine.items import _default_client

logger = logging.getLogger(__name__)


class StoryKind(enum.StrEnum):
    """Available story list kinds."""

    TOP = "top"
    NEW = "new"
    BEST = "best"
    ASK = "ask"
    SHOW = "show"
    JOB = "job"


# API limits per kind (documented behaviour)
_KIND_LIMITS: dict[StoryKind, int] = {
    StoryKind.TOP: 500,
    StoryKind.NEW: 500,
    StoryKind.BEST: 500,
    StoryKind.ASK: 200,
    StoryKind.SHOW: 200,
    StoryKind.JOB: 200,
}


def get_story_ids(
    kind: str | StoryKind = StoryKind.TOP,
    *,
    limit: int | None = None,
    client: HNClient | None = None,
) -> list[int]:
    """Fetch a list of story IDs for the given kind.

    Args:
        kind: One of ``top``, ``new``, ``best``, ``ask``, ``show``, ``job``.
        limit: Optional cap on the number of IDs returned.
        client: Optional ``HNClient`` instance.

    Returns:
        A list of integer item IDs.

    Raises:
        ValidationError: If ``kind`` is unknown.
        HNError: On HTTP or network failures.
    """
    try:
        story_kind = StoryKind(kind.lower())
    except ValueError as exc:
        raise ValidationError(
            f"Unknown story kind: {kind!r}. Use one of: {', '.join(StoryKind)}",
            field="kind",
        ) from exc

    c = client or _default_client()
    data = c.get(f"{story_kind.value}stories.json")

    if not isinstance(data, list):
        raise ValidationError(
            f"Expected list from {kind}stories endpoint, got {type(data).__name__}",
            field="kind",
        )

    ids: list[int] = data
    if limit is not None:
        if limit < 0:
            raise ValidationError("limit must be non-negative", field="limit")
        ids = ids[:limit]

    logger.debug("Fetched %d %s story IDs", len(ids), story_kind.value)
    return ids


def get_updates(
    *,
    client: HNClient | None = None,
) -> dict[str, list[int] | list[str]]:
    """Fetch the list of recently changed items and user profiles.

    This is the recommended endpoint for incremental syncing.

    Returns:
        A dict with keys ``items`` (list of int IDs) and
        ``profiles`` (list of usernames).

    Raises:
        HNError: On HTTP or network failures.
    """
    c = client or _default_client()
    data = c.get("updates.json")

    if not isinstance(data, dict):
        raise ValidationError(
            f"Expected dict from updates endpoint, got {type(data).__name__}",
        )

    return {
        "items": data.get("items", []),
        "profiles": data.get("profiles", []),
    }


def get_maxitem(
    *,
    client: HNClient | None = None,
) -> int:
    """Fetch the current maximum item ID.

    Returns:
        The largest item ID currently known.

    Raises:
        HNError: On HTTP or network failures.
        ValidationError: If the response is not an integer.
    """
    c = client or _default_client()
    data = c.get("maxitem.json")

    if not isinstance(data, int):
        raise ValidationError(
            f"Expected int from maxitem endpoint, got {type(data).__name__}",
        )

    return data
