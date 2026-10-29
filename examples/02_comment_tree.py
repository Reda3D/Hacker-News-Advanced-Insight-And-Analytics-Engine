"""Example 2: Bounded comment tree traversal."""

from hn_engine import get_comment_tree, sanitize_html


def main() -> None:
    # Dropbox launch post (HN item 8863)
    story_id = 8863
    print(f"=== Comment Tree for Story {story_id} ===\n")

    tree = get_comment_tree(story_id, max_depth=2, max_nodes=50)
    print(f"Fetched {len(tree)} nodes (max_depth=2, max_nodes=50)\n")

    for node_id, node in tree.items():
        if node.get("type") != "comment":
            continue

        depth = node.get("_depth", 0)
        author = node.get("by", "unknown")
        text = sanitize_html(node.get("text", ""))
        indent = "  " * depth

        print(f"{indent}#{node_id} by {author}:")
        # Print first 120 chars of the comment
        preview = text[:120].replace("\n", " ")
        print(f"{indent}  {preview}...\n")


if __name__ == "__main__":
    main()
