"""Optional caching layer with TTL support."""

from __future__ import annotations

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


try:
    from cachetools import TTLCache
    _HAS_CACHETOOLS = True
except ImportError:  # pragma: no cover
    _HAS_CACHETOOLS = False


class HNCache:
    """Simple TTL cache wrapper for HN API responses.

    Uses ``cachetools.TTLCache`` when available; otherwise degrades
    gracefully to a no-op passthrough.

    Args:
        maxsize: Maximum number of entries.
        ttl: Time-to-live in seconds.
    """

    def __init__(self, maxsize: int = 1024, ttl: float = 300.0) -> None:
        """Initialize the cache with the given size and TTL."""
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache: Any = None
        self._hits = 0
        self._misses = 0

        if _HAS_CACHETOOLS:
            self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
            logger.debug("Using TTLCache (maxsize=%d, ttl=%.0fs)", maxsize, ttl)
        else:
            logger.warning("cachetools not installed — HNCache is a no-op passthrough")

    def get(self, key: str) -> Any | None:
        """Retrieve a cached value by key."""
        if self._cache is None:
            self._misses += 1
            return None
        try:
            value = self._cache[key]
            self._hits += 1
            return value
        except KeyError:
            self._misses += 1
            return None

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache."""
        if self._cache is not None:
            self._cache[key] = value

    def invalidate(self, key: str) -> None:
        """Remove a single key from the cache."""
        if self._cache is not None:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear the entire cache."""
        if self._cache is not None:
            self._cache.clear()
        self._hits = 0
        self._misses = 0

    @property
    def stats(self) -> dict[str, int | float]:
        """Return cache statistics."""
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "total": total,
            "hit_rate": round(self._hits / total, 4) if total > 0 else 0.0,
        }

    def cached(self, ttl: float | None = None) -> Callable[..., Any]:
        """Decorator that caches a function's return value.

        Args:
            ttl: Optional override TTL for this specific function.
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Build a cache key from function name + args
                key_parts = [func.__qualname__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                key = "|".join(key_parts)

                value = self.get(key)
                if value is not None:
                    return value

                value = func(*args, **kwargs)
                self.set(key, value)
                return value
            return wrapper
        return decorator
