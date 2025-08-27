try:
    from .base import Plugin
    from .recon import RobotsRecon, SitemapRecon, JSEndpointsRecon, GraphQLRecon, SmartEndpointDetector, AuthDiscoveryRecon
    from .graphql_test import GraphQLTester
except ImportError:
    from plugins.base import Plugin
    from plugins.recon import RobotsRecon, SitemapRecon, JSEndpointsRecon, GraphQLRecon, SmartEndpointDetector, AuthDiscoveryRecon
    from plugins.graphql_test import GraphQLTester

__all__ = ["Plugin", "RobotsRecon", "SitemapRecon", "JSEndpointsRecon", "GraphQLRecon", "SmartEndpointDetector", "AuthDiscoveryRecon", "GraphQLTester"]
