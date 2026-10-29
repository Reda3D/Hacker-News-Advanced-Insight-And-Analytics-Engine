"""Example 5: Using the cache layer for repeated requests."""

from hn_engine import HNClient, get_item, HNCache


def main() -> None:
    print("=== Cache Demo ===\n")

    cache = HNCache(maxsize=100, ttl=60.0)
    client = HNClient()

    # First fetch — cache miss
    print("Fetching item 8863 (first time)...")
    item1 = get_item(8863, client=client)
    print(f"  Title: {item1.get('title', 'N/A')[:50]}...")

    # Simulate cache hit (in real use, wrap the function with @cache.cached())
    print("\nCache stats:", cache.stats)

    # Demonstrate that HNCache works as a decorator
    @cache.cached(ttl=120)
    def fetch_story(story_id: int):
        return get_item(story_id, client=client)

    print("\nFetching via cached decorator (story 8863)...")
    result = fetch_story(8863)
    print(f"  Result: {result.get('title', 'N/A')[:50]}...")
    print("Cache stats after decorator use:", cache.stats)

    client.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
