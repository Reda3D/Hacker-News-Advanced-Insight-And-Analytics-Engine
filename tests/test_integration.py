"""Integration tests — these hit the real HN API.

Run with: pytest tests/test_integration.py -v -m integration

These tests are marked as ``integration`` because they make live network
requests. They are skipped by default.
"""

import pytest

from hn_engine import (
    HNClient,
    StoryKind,
    get_comment_tree,
    get_item,
    get_maxitem,
    get_story_ids,
    get_updates,
    get_user,
    sanitize_html,
)

pytestmark = pytest.mark.integration


class TestItemEndpoint:
    def test_fetch_known_story(self):
        # Story 8863 is the famous Dropbox launch post
        item = get_item(8863)
        assert item is not None
        assert item["type"] == "story"
        assert "title" in item
        assert item["by"] == "dhouston"

    def test_fetch_unknown_item_returns_none(self):
        item = get_item(999999999)
        assert item is None

    def test_fetch_comment(self):
        # Comment 2921983 by Peter Norvig
        item = get_item(2921983)
        assert item is not None
        assert item["type"] == "comment"
        assert item["by"] == "norvig"


class TestUserEndpoint:
    def test_fetch_known_user(self):
        user = get_user("jl")
        assert user is not None
        assert user["id"] == "jl"
        assert "karma" in user

    def test_fetch_unknown_user_returns_none(self):
        user = get_user("this_user_definitely_does_not_exist_12345")
        assert user is None


class TestListEndpoints:
    def test_top_stories(self):
        ids = get_story_ids(StoryKind.TOP, limit=10)
        assert isinstance(ids, list)
        assert len(ids) == 10
        assert all(isinstance(i, int) for i in ids)

    def test_new_stories(self):
        ids = get_story_ids(StoryKind.NEW, limit=5)
        assert isinstance(ids, list)
        assert len(ids) <= 5

    def test_updates(self):
        updates = get_updates()
        assert "items" in updates
        assert "profiles" in updates
        assert isinstance(updates["items"], list)
        assert isinstance(updates["profiles"], list)

    def test_maxitem(self):
        max_id = get_maxitem()
        assert isinstance(max_id, int)
        assert max_id > 0


class TestCommentTree:
    def test_bounded_traversal(self):
        # Fetch a shallow tree from the Dropbox story
        tree = get_comment_tree(8863, max_depth=1, max_nodes=20)
        assert isinstance(tree, dict)
        assert len(tree) <= 20
        # Root should be at depth 0
        assert tree[8863]["_depth"] == 0

    def test_zero_depth(self):
        tree = get_comment_tree(8863, max_depth=0, max_nodes=10)
        assert len(tree) == 1
        assert 8863 in tree


class TestSanitization:
    def test_sanitize_real_html(self):
        item = get_item(2921983)
        assert item is not None
        raw = item.get("text", "")
        clean = sanitize_html(raw)
        assert "<script>" not in clean
        assert "javascript:" not in clean


class TestClientContextManager:
    def test_context_manager(self):
        with HNClient() as client:
            item = get_item(8863, client=client)
            assert item is not None
