"""User profile retrieval."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

from hn_engine.client import HNClient
from hn_engine.errors import ValidationError
from hn_engine.items import _default_client

logger = logging.getLogger(__name__)


def get_user(
    username: str,
    *,
    client: HNClient | None = None,
) -> dict[str, Any] | None:
    """Fetch a user profile by case-sensitive username.

    Args:
        username: Non-empty, case-sensitive username string.
        client: Optional ``HNClient`` instance.

    Returns:
        The user dict, or ``None`` if the user does not exist.

    Raises:
        ValidationError: If ``username`` is empty or not a string.
        HNError: On HTTP or network failures.
    """
    if not isinstance(username, str):
        raise ValidationError("username must be a string", field="username")
    if not username.strip():
        raise ValidationError("username must not be empty", field="username")

    c = client or _default_client()
    # HN usernames are case-sensitive and may contain characters that need URL encoding
    encoded = quote(username, safe="")
    data = c.get(f"user/{encoded}.json")

    if data is None:
        logger.debug("User %r returned null (does not exist)", username)
        return None

    return dict(data)
