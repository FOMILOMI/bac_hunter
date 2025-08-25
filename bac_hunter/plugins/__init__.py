try:
    from .base import Plugin
    from .recon import RobotsRecon, SitemapRecon, JSEndpointsRecon, GraphQLRecon, SmartEndpointDetector, AuthDiscoveryRecon
except Exception:
    from plugins.base import Plugin
    from plugins.recon import RobotsRecon, SitemapRecon, JSEndpointsRecon, GraphQLRecon, SmartEndpointDetector, AuthDiscoveryRecon

__all__ = ["Plugin", "RobotsRecon", "SitemapRecon", "JSEndpointsRecon", "GraphQLRecon", "SmartEndpointDetector", "AuthDiscoveryRecon"]
