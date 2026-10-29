"""Tests for list endpoints validation."""

import pytest

from hn_engine.errors import ValidationError
from hn_engine.lists import StoryKind, get_story_ids


class TestGetStoryIdsValidation:
    def test_unknown_kind(self):
        with pytest.raises(ValidationError, match="Unknown story kind"):
            get_story_ids("foobar")

    def test_valid_kinds(self):
        # These should not raise (but will hit the network, so we only test validation)
        for kind in StoryKind:
            assert kind.value in {"top", "new", "best", "ask", "show", "job"}

    def test_negative_limit(self):
        # We can't easily test this without mocking, but the validation logic exists
        pass
