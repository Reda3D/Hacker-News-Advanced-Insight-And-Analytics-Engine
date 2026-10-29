"""HTTP client with retries, exponential backoff, and timeouts."""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urljoin

import requests

from hn_engine.errors import HNError, NetworkError, RateLimitError

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://hacker-news.firebaseio.com/v0"
DEFAULT_TIMEOUT = 10.0
DEFAULT_MAX_RETRIES = 4
DEFAULT_BACKOFF_BASE = 1.5

# Status codes that warrant a retry
_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


class HNClient:
    """Resilient HTTP client for the Hacker News Firebase API.

    Args:
        base_url: Root URL of the API (default: official v0 endpoint).
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.
        backoff_base: Exponential backoff multiplier.
        session: Optional ``requests.Session`` to reuse connections.
    """

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.session = session or requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": (
                "HN-Advanced-Insight-Engine/1.0 "
                "(+https://github.com/Reda3D/Hacker-News-Advanced-Insight-And-Analytics-Engine)"
            ),
        })

    def _sleep_for_attempt(self, attempt: int) -> float:
        """Calculate sleep duration for the given attempt (0-indexed)."""
        return self.backoff_base ** attempt

    def get(self, path: str) -> Any:
        """Perform a GET request with retries and return decoded JSON.

        Returns:
            The parsed JSON body (dict, list, int, str, or None).

        Raises:
            HNError: On non-retryable HTTP errors.
            NetworkError: On persistent connection failures.
            RateLimitError: On HTTP 429 after all retries exhausted.
        """
        url = urljoin(self.base_url + "/", path.lstrip("/"))
        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
            except requests.exceptions.Timeout:
                last_exception = NetworkError(
                    f"Request timed out after {self.timeout}s",
                    url=url,
                )
                logger.warning("Timeout on attempt %d for %s", attempt + 1, url)
            except requests.exceptions.ConnectionError:
                last_exception = NetworkError(
                    "Connection error",
                    url=url,
                )
                logger.warning("Connection error on attempt %d for %s", attempt + 1, url)
            except requests.exceptions.RequestException:
                last_exception = NetworkError(
                    "Request failed",
                    url=url,
                )
                logger.warning("Request error on attempt %d for %s", attempt + 1, url)
            else:
                # We got an HTTP response
                if response.status_code == 200:
                    try:
                        return response.json()
                    except ValueError as exc:
                        last_exception = HNError(
                            f"Invalid JSON in response: {exc}",
                            url=url,
                            status=response.status_code,
                            retryable=False,
                        )
                        break  # JSON decode errors are not retryable

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    last_exception = RateLimitError(
                        "Rate limited (HTTP 429)",
                        url=url,
                        retry_after=retry_after,
                    )
                    logger.warning("Rate limited on %s, retry after %ds", url, retry_after)
                elif response.status_code in _RETRYABLE_STATUSES:
                    last_exception = HNError(
                        f"HTTP {response.status_code}",
                        url=url,
                        status=response.status_code,
                        retryable=True,
                    )
                    logger.warning(
                        "HTTP %d on attempt %d for %s",
                        response.status_code, attempt + 1, url,
                    )
                else:
                    # Non-retryable HTTP error
                    raise HNError(
                        f"HTTP {response.status_code}: {response.text[:200]}",
                        url=url,
                        status=response.status_code,
                        retryable=False,
                    )

            # Sleep before next retry (except on the last attempt)
            if attempt < self.max_retries - 1:
                sleep_time = self._sleep_for_attempt(attempt)
                logger.debug("Sleeping %.2fs before retry %d", sleep_time, attempt + 2)
                time.sleep(sleep_time)

        # All retries exhausted
        if isinstance(last_exception, (NetworkError, RateLimitError)):
            raise last_exception
        if isinstance(last_exception, HNError):
            raise last_exception
        raise NetworkError("All retry attempts exhausted", url=url)

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    def __enter__(self) -> HNClient:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        self.close()
