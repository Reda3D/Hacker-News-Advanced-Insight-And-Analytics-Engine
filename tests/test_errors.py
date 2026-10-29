"""Tests for the error hierarchy."""


from hn_engine.errors import HNError, NetworkError, NotFoundError, RateLimitError, ValidationError


class TestHNError:
    def test_basic_message(self):
        err = HNError("something went wrong")
        assert str(err) == "something went wrong"
        assert err.retryable is False

    def test_with_url_and_status(self):
        err = HNError("HTTP 503", url="https://example.com", status=503, retryable=True)
        assert "HTTP 503" in str(err)
        assert "example.com" in str(err)
        assert err.url == "https://example.com"
        assert err.status == 503
        assert err.retryable is True


class TestValidationError:
    def test_not_retryable(self):
        err = ValidationError("bad input", field="item_id")
        assert err.retryable is False
        assert err.field == "item_id"


class TestNetworkError:
    def test_always_retryable(self):
        err = NetworkError("connection refused", url="https://example.com")
        assert err.retryable is True
        assert err.url == "https://example.com"


class TestRateLimitError:
    def test_defaults(self):
        err = RateLimitError("too many requests", retry_after=120)
        assert err.status == 429
        assert err.retry_after == 120
        assert err.retryable is True


class TestNotFoundError:
    def test_not_retryable(self):
        err = NotFoundError("item not found", url="https://example.com")
        assert err.status == 404
        assert err.retryable is False
