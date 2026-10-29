"""Custom exception hierarchy for the HN Engine."""

from __future__ import annotations


class HNError(Exception):
    """Base exception for all HN Engine errors.

    Attributes:
        message: Human-readable error description.
        url: The URL that caused the failure (if applicable).
        status: HTTP status code (if applicable).
        retryable: Whether the caller should retry this request.
    """

    def __init__(
        self,
        message: str,
        *,
        url: str | None = None,
        status: int | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.url = url
        self.status = status
        self.retryable = retryable

    def __str__(self) -> str:
        parts = [self.message]
        if self.url:
            parts.append(f"URL: {self.url}")
        if self.status:
            parts.append(f"HTTP {self.status}")
        return " | ".join(parts)


class ValidationError(HNError):
    """Raised when input parameters fail validation."""

    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message, retryable=False)
        self.field = field


class NetworkError(HNError):
    """Raised on connection failures, DNS issues, or socket timeouts."""

    def __init__(self, message: str, *, url: str | None = None) -> None:
        super().__init__(message, url=url, retryable=True)


class RateLimitError(HNError):
    """Raised when the API signals rate limiting (HTTP 429)."""

    def __init__(self, message: str, *, url: str | None = None, retry_after: int = 60) -> None:
        super().__init__(message, url=url, status=429, retryable=True)
        self.retry_after = retry_after


class NotFoundError(HNError):
    """Raised when an item or user does not exist (HTTP 404 or null response)."""

    def __init__(self, message: str, *, url: str | None = None) -> None:
        super().__init__(message, url=url, status=404, retryable=False)
