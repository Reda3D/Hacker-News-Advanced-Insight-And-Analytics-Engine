"""Example 3: Incremental sync loop using updates endpoint."""

import time

from hn_engine import get_updates, get_item


def main() -> None:
    print("=== Incremental Sync Demo ===\n")
    print("Polling /v0/updates.json every 45 seconds.")
    print("Press Ctrl+C to stop.\n")

    seen_items: set[int] = set()
    iteration = 0

    try:
        while True:
            iteration += 1
            updates = get_updates()
            new_count = 0

            for item_id in updates["items"]:
                if item_id in seen_items:
                    continue

                item = get_item(item_id)
                if item is None:
                    continue

                seen_items.add(item_id)
                new_count += 1
                item_type = item.get("type", "unknown")
                title = item.get("title", "(no title)")
                print(f"[{iteration:03d}] New {item_type}: {title[:60]}...")

            if new_count == 0:
                print(f"[{iteration:03d}] No new items.")

            time.sleep(45)
    except KeyboardInterrupt:
        print(f"\nStopped. Total unique items seen: {len(seen_items)}")


if __name__ == "__main__":
    main()
