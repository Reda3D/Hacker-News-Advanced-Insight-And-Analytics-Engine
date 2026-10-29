"""Tests for input validation in items.py."""

import pytest

from hn_engine.errors import ValidationError
from hn_engine.items import get_comment_tree, get_item, item_type_traits


class TestItemTypeTraits:
    def test_story(self):
        traits = item_type_traits("story")
        assert traits["has_title"] is True
        assert traits["has_url"] is True

    def test_ask_is_story_variant(self):
        traits = item_type_traits("ask")
        assert traits["has_title"] is True
        assert traits["has_url"] is False

    def test_comment(self):
        traits = item_type_traits("comment")
        assert traits["has_title"] is False
        assert traits["has_kids"] is True

    def test_unknown_type_raises(self):
        with pytest.raises(ValidationError, match="Unknown item type"):
            item_type_traits("foobar")


class TestGetItemValidation:
    def test_bool_rejected(self):
        with pytest.raises(ValidationError, match="positive integer"):
            get_item(True)

    def test_negative_rejected(self):
        with pytest.raises(ValidationError, match="> 0"):
            get_item(-5)

    def test_zero_rejected(self):
        with pytest.raises(ValidationError, match="> 0"):
            get_item(0)

    def test_string_rejected(self):
        with pytest.raises(ValidationError, match="positive integer"):
            get_item("8863")


class TestGetCommentTreeValidation:
    def test_negative_depth(self):
        with pytest.raises(ValidationError, match="non-negative"):
            get_comment_tree(8863, max_depth=-1)

    def test_zero_nodes(self):
        with pytest.raises(ValidationError, match="positive integer"):
            get_comment_tree(8863, max_nodes=0)

    def test_bool_depth_rejected(self):
        with pytest.raises(ValidationError, match="non-negative"):
            get_comment_tree(8863, max_depth=True)
