"""Example 4: Detect new items via maxitem and fetch user karma."""

from hn_engine import get_maxitem, get_item, get_user


def main() -> None:
    print("=== Max Item & User Karma Demo ===\n")

    # Get current max item
    max_id = get_maxitem()
    print(f"Current max item ID: {max_id}\n")

    # Fetch the most recent item
    latest = get_item(max_id)
    if latest:
        print(f"Latest item: #{max_id}")
        print(f"  Type: {latest.get('type')}")
        print(f"  By: {latest.get('by')}")
        print(f"  Title: {latest.get('title', '(no title)')[:80]}...")
    else:
        print(f"Item #{max_id} is null (deleted or not yet available)")

    # Fetch a known user and show karma
    username = "jl"
    user = get_user(username)
    if user:
        print(f"\nUser @{username}:")
        print(f"  Karma: {user.get('karma', 0)}")
        print(f"  Created: {user.get('created', 'unknown')}")
        about = user.get("about", "")
        if about:
            print(f"  About: {about[:100]}...")
    else:
        print(f"\nUser @{username} not found")


if __name__ == "__main__":
    main()
