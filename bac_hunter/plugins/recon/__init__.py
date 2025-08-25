try:
	from .robots import RobotsRecon
	from .sitemap import SitemapRecon  
	from .js_endpoints import JSEndpointsRecon
	from .graphql import GraphQLRecon
	from .smart_detector import SmartEndpointDetector
	from .auth_discovery import AuthDiscoveryRecon
except Exception:
	from plugins.recon.robots import RobotsRecon
	from plugins.recon.sitemap import SitemapRecon
	from plugins.recon.js_endpoints import JSEndpointsRecon
	from plugins.recon.graphql import GraphQLRecon
	from plugins.recon.smart_detector import SmartEndpointDetector
	from plugins.recon.auth_discovery import AuthDiscoveryRecon

__all__ = ["RobotsRecon", "SitemapRecon", "JSEndpointsRecon", "GraphQLRecon", "SmartEndpointDetector", "AuthDiscoveryRecon"]
