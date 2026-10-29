"""Tests for the HTTP client with mocked responses."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from hn_engine.client import HNClient
from hn_engine.errors import HNError, NetworkError, RateLimitError


class TestHNClientRetries:
    def test_success_on_first_try(self):
        client = HNClient()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": 8863, "title": "Test"}

        with patch.object(client.session, "get", return_value=mock_resp):
            data = client.get("item/8863.json")
            assert data["id"] == 8863

    def test_retry_on_503_then_success(self):
        client = HNClient(max_retries=3, backoff_base=0.01)
        fail_resp = MagicMock()
        fail_resp.status_code = 503
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"id": 8863}

        with patch.object(
            client.session, "get", side_effect=[fail_resp, ok_resp]
        ) as mock_get:
            data = client.get("item/8863.json")
            assert data["id"] == 8863
            assert mock_get.call_count == 2

    def test_exhaust_retries_on_503(self):
        client = HNClient(max_retries=2, backoff_base=0.01)
        fail_resp = MagicMock()
        fail_resp.status_code = 503

        with patch.object(client.session, "get", return_value=fail_resp):
            with pytest.raises(HNError):
                client.get("item/8863.json")

    def test_rate_limit_error(self):
        client = HNClient(max_retries=1)
        resp = MagicMock()
        resp.status_code = 429
        resp.headers = {"Retry-After": "120"}

        with patch.object(client.session, "get", return_value=resp):
            with pytest.raises(RateLimitError) as exc_info:
                client.get("item/8863.json")
            assert exc_info.value.retry_after == 120

    def test_network_error_on_timeout(self):
        client = HNClient(max_retries=1)

        with patch.object(
            client.session, "get", side_effect=requests.exceptions.Timeout()
        ):
            with pytest.raises(NetworkError):
                client.get("item/8863.json")

    def test_non_retryable_error_immediate(self):
        client = HNClient(max_retries=3)
        resp = MagicMock()
        resp.status_code = 400
        resp.text = "Bad Request"

        with patch.object(client.session, "get", return_value=resp):
            with pytest.raises(HNError, match="HTTP 400"):
                client.get("item/8863.json")

    def test_context_manager(self):
        with HNClient() as client:
            assert client is not None
