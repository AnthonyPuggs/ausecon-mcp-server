from __future__ import annotations


class AuseconError(Exception):
    """Base exception for the ausecon MCP server."""


class AuseconValidationError(ValueError, AuseconError):
    """Raised when tool inputs are invalid."""


class AuseconResponseTooLargeError(AuseconValidationError):
    """Raised when an upstream download exceeds the per-request size limit.

    A validation error rather than an upstream failure: the request is too broad, so the
    caller should narrow it, and no stale-cache fallback applies.
    """


class AuseconUpstreamError(RuntimeError, AuseconError):
    """Raised when an upstream ABS or RBA request fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        body: str | None = None,
        url: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body
        self.url = url


class AuseconNotFoundError(AuseconUpstreamError):
    """Raised when an upstream source returns HTTP 404 for the requested resource."""


class AuseconParseError(RuntimeError, AuseconError):
    """Raised when an upstream ABS or RBA payload cannot be parsed."""
