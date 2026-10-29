"""Example 1: Fetch top 10 stories with sanitized titles."""

from hn_engine import get_story_ids, get_item, sanitize_html, StoryKind


def main() -> None:
    print("=== Top 10 Stories on Hacker News ===\n")
    top_ids = get_story_ids(StoryKind.TOP, limit=10)

    for rank, item_id in enumerate(top_ids, start=1):
        item = get_item(item_id)
        if item is None:
            continue

        title = sanitize_html(item.get("title", "(no title)"))
        score = item.get("score", 0)
        author = item.get("by", "unknown")
        url = item.get("url", f"https://news.ycombinator.com/item?id={item_id}")

        print(f"{rank:2}. {title}")
        print(f"    {score} points by {author}")
        print(f"    {url}\n")


if __name__ == "__main__":
    main()
