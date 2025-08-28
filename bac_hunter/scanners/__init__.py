"""Scanners package aggregator.

Provides a stable import path for scanning plugins and base classes while
keeping backward compatibility with `bac_hunter.plugins`.
"""

from __future__ import annotations

try:
    from ..plugins.base import Plugin  # type: ignore
except Exception:  # pragma: no cover
    from plugins.base import Plugin  # type: ignore

# Recon scanners re-export
try:
    from ..plugins.recon import (  # type: ignore
        RobotsRecon,
        SitemapRecon,
        JSEndpointsRecon,
        GraphQLRecon,
        SmartEndpointDetector,
        AuthDiscoveryRecon,
        OAuthOIDCRecon,
        SPATester,
    )
except Exception:  # pragma: no cover
    from plugins.recon import (  # type: ignore
        RobotsRecon,
        SitemapRecon,
        JSEndpointsRecon,
        GraphQLRecon,
        SmartEndpointDetector,
        AuthDiscoveryRecon,
        OAuthOIDCRecon,
        SPATester,
    )

__all__ = [
    "Plugin",
    "RobotsRecon",
    "SitemapRecon",
    "JSEndpointsRecon",
    "GraphQLRecon",
    "SmartEndpointDetector",
    "AuthDiscoveryRecon",
    "OAuthOIDCRecon",
    "SPATester",
]

