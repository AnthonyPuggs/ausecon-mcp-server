from __future__ import annotations


class AuseconError(Exception):
    """Base exception for the ausecon MCP server."""


class AuseconValidationError(ValueError, AuseconError):
    """Raised when tool inputs are invalid."""


class AuseconUpstreamError(RuntimeError, AuseconError):
    """Raised when an upstream ABS or RBA request fails."""


class AuseconNotFoundError(AuseconUpstreamError):
    """Raised when an upstream source returns HTTP 404 for the requested resource."""

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


class AuseconParseError(RuntimeError, AuseconError):
    """Raised when an upstream ABS or RBA payload cannot be parsed."""
