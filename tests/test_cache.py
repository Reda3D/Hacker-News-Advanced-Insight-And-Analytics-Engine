"""Tests for the cache layer."""

from hn_engine.cache import HNCache


class TestHNCache:
    def test_basic_set_and_get(self):
        cache = HNCache()
        assert cache.get("key") is None
        cache.set("key", "value")
        assert cache.get("key") == "value"

    def test_stats_initially_zero(self):
        cache = HNCache()
        stats = cache.stats
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == 0.0

    def test_clear_resets_stats(self):
        cache = HNCache()
        cache._hits = 5
        cache._misses = 3
        cache.clear()
        assert cache.stats["hits"] == 0
        assert cache.stats["misses"] == 0
