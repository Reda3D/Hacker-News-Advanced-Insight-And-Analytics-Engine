"""Item retrieval and bounded comment-tree traversal."""

from __future__ import annotations

import logging
from typing import Any

from hn_engine.client import HNClient
from hn_engine.errors import HNError, ValidationError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Item type traits
# ---------------------------------------------------------------------------

ITEM_TYPES = {"job", "story", "comment", "poll", "pollopt"}

ITEM_TRAITS: dict[str, dict[str, bool]] = {
    "job": {
        "has_title": True, "has_text": True, "has_kids": False,
        "has_url": True, "has_parts": False,
    },
    "story": {
        "has_title": True, "has_text": True, "has_kids": True,
        "has_url": True, "has_parts": False,
    },
    "ask": {
        "has_title": True, "has_text": True, "has_kids": True,
        "has_url": False, "has_parts": False,
    },
    "comment": {
        "has_title": False, "has_text": True, "has_kids": True,
        "has_url": False, "has_parts": False,
    },
    "poll": {
        "has_title": True, "has_text": True, "has_kids": True,
        "has_url": False, "has_parts": True,
    },
    "pollopt": {
        "has_title": False, "has_text": True, "has_kids": False,
        "has_url": False, "has_parts": False,
    },
}


def item_type_traits(item_type: str) -> dict[str, bool]:
    """Return the trait map for a given item type.

    Args:
        item_type: One of ``job``, ``story``, ``comment``, ``poll``, ``pollopt``.
            ``ask`` is treated as a variant of ``story``.

    Returns:
        A dict with boolean flags: ``has_title``, ``has_text``,
        ``has_kids``, ``has_url``, ``has_parts``.

    Raises:
        ValidationError: If the type is unknown.
    """
    normalized = "ask" if item_type == "ask" else item_type
    if normalized not in ITEM_TRAITS:
        raise ValidationError(f"Unknown item type: {item_type!r}", field="item_type")
    return ITEM_TRAITS[normalized].copy()


# ---------------------------------------------------------------------------
# Item fetching
# ---------------------------------------------------------------------------

DEFAULT_CLIENT: HNClient | None = None


def _default_client() -> HNClient:
    """Return a lazily-initialized default client."""
    global DEFAULT_CLIENT  # noqa: PLW0603
    if DEFAULT_CLIENT is None:
        DEFAULT_CLIENT = HNClient()
    return DEFAULT_CLIENT


def get_item(
    item_id: int,
    *,
    client: HNClient | None = None,
) -> dict[str, Any] | None:
    """Fetch a single item by its numeric ID.

    Args:
        item_id: Positive integer item identifier.
        client: Optional ``HNClient`` instance. Uses a global default if omitted.

    Returns:
        The item dict, or ``None`` if the item is deleted, dead, or unknown.

    Raises:
        ValidationError: If ``item_id`` is not a positive integer.
        HNError: On HTTP or network failures.
    """
    if not isinstance(item_id, int) or isinstance(item_id, bool):
        raise ValidationError("item_id must be a positive integer", field="item_id")
    if item_id <= 0:
        raise ValidationError("item_id must be > 0", field="item_id")

    c = client or _default_client()
    data = c.get(f"item/{item_id}.json")

    if data is None:
        logger.debug("Item %d returned null (deleted or unknown)", item_id)
        return None

    if not isinstance(data, dict):
        raise HNError(
            f"Expected dict for item {item_id}, got {type(data).__name__}",
            retryable=False,
        )

    return data


# ---------------------------------------------------------------------------
# Comment tree traversal
# ---------------------------------------------------------------------------

CommentTree = dict[int, dict[str, Any]]


def get_comment_tree(
    item_id: int,
    *,
    max_depth: int = 3,
    max_nodes: int = 200,
    client: HNClient | None = None,
) -> CommentTree:
    """Fetch a story and recursively traverse its comment tree.

    The traversal is **bounded** to prevent runaway recursion on
    heavily-commented stories.

    Args:
        item_id: The story / poll / comment ID to start from.
        max_depth: Maximum recursion depth (0 = root item only).
        max_nodes: Maximum total nodes to fetch.
        client: Optional ``HNClient`` instance.

    Returns:
        A flat dict mapping node IDs to their item data. Each node
        includes a ``_depth`` key indicating its depth relative to the root.

    Raises:
        ValidationError: If bounds are invalid.
        HNError: On HTTP or network failures.
    """
    if not isinstance(max_depth, int) or isinstance(max_depth, bool) or max_depth < 0:
        raise ValidationError("max_depth must be a non-negative integer", field="max_depth")
    if not isinstance(max_nodes, int) or isinstance(max_nodes, bool) or max_nodes < 1:
        raise ValidationError("max_nodes must be a positive integer", field="max_nodes")

    c = client or _default_client()
    tree: CommentTree = {}
    fetched_count = 0

    def _traverse(node_id: int, depth: int) -> None:
        nonlocal fetched_count
        if fetched_count >= max_nodes:
            return
        if depth > max_depth:
            return

        data = get_item(node_id, client=c)
        if data is None:
            return

        data["_depth"] = depth
        tree[node_id] = data
        fetched_count += 1

        kids = data.get("kids", [])
        if not isinstance(kids, list):
            logger.warning("Item %d has non-list kids: %s", node_id, type(kids).__name__)
            return

        for child_id in kids:
            if fetched_count >= max_nodes:
                break
            _traverse(child_id, depth + 1)

    _traverse(item_id, 0)
    logger.info("Fetched %d nodes for item %d (max_depth=%d, max_nodes=%d)",
                len(tree), item_id, max_depth, max_nodes)
    return tree
