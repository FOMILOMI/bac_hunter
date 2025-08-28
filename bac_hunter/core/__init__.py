"""Core module aggregator for BAC Hunter.

This package exposes the primary core components under a clean namespace
without breaking backward compatibility. Existing modules continue to live
at the top-level (e.g., `bac_hunter/http_client.py`), while this package
re-exports their public APIs to enable a more modular import style:

    from bac_hunter.core import HttpClient, Settings, Storage

Over time, core implementations can be moved into this package without
changing external imports.
"""

from __future__ import annotations

# Re-export core configuration and primitives
try:
    from ..config import Settings, Identity  # type: ignore
except Exception:  # pragma: no cover - fallback for direct execution contexts
    from config import Settings, Identity  # type: ignore

try:
    from ..http_client import HttpClient  # type: ignore
except Exception:  # pragma: no cover
    from http_client import HttpClient  # type: ignore

try:
    from ..session_manager import SessionManager  # type: ignore
except Exception:  # pragma: no cover
    from session_manager import SessionManager  # type: ignore

try:
    from ..rate_limiter import RateLimiter, AdaptiveRateLimiter, TokenBucket  # type: ignore
except Exception:  # pragma: no cover
    from rate_limiter import RateLimiter, AdaptiveRateLimiter, TokenBucket  # type: ignore

try:
    from ..storage import Storage  # type: ignore
except Exception:  # pragma: no cover
    from storage import Storage  # type: ignore

__all__ = [
    "Settings",
    "Identity",
    "HttpClient",
    "SessionManager",
    "RateLimiter",
    "AdaptiveRateLimiter",
    "TokenBucket",
    "Storage",
]

