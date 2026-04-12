from __future__ import annotations


class AuseconError(Exception):
    """Base exception for the ausecon MCP server."""


class AuseconValidationError(ValueError, AuseconError):
    """Raised when tool inputs are invalid."""


class AuseconUpstreamError(RuntimeError, AuseconError):
    """Raised when an upstream ABS or RBA request fails."""


class AuseconParseError(RuntimeError, AuseconError):
    """Raised when an upstream ABS or RBA payload cannot be parsed."""
