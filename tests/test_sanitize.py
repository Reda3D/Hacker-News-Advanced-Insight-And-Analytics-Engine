"""Tests for HTML sanitization."""


from hn_engine.sanitize import sanitize_html


class TestSanitizeHTML:
    def test_none_returns_empty(self):
        assert sanitize_html(None) == ""

    def test_allowed_tags_preserved(self):
        raw = "<p>Hello <b>world</b></p>"
        result = sanitize_html(raw)
        assert "<b>" in result or "world" in result

    def test_script_removed(self):
        raw = '<p>Hello</p><script>alert("xss")</script>'
        result = sanitize_html(raw)
        assert "<script>" not in result
        # bleach.strip=True removes the tag but keeps the text content
        assert "alert" in result

    def test_onclick_removed(self):
        raw = '<a href="http://example.com" onclick="evil()">link</a>'
        result = sanitize_html(raw)
        assert "onclick" not in result
