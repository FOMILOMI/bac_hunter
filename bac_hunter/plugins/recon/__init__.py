try:
	from .robots import RobotsRecon
	from .sitemap import SitemapRecon  
	from .js_endpoints import JSEndpointsRecon
	from .graphql import GraphQLRecon
	from .smart_detector import SmartEndpointDetector
	from .auth_discovery import AuthDiscoveryRecon
	from .oauth_oidc import OAuthOIDCRecon
	from .spa_tester import SPATester
	from .openapi import OpenAPIRecon
except Exception:
	from plugins.recon.robots import RobotsRecon
	from plugins.recon.sitemap import SitemapRecon
	from plugins.recon.js_endpoints import JSEndpointsRecon
	from plugins.recon.graphql import GraphQLRecon
	from plugins.recon.smart_detector import SmartEndpointDetector
	from plugins.recon.auth_discovery import AuthDiscoveryRecon
	from plugins.recon.oauth_oidc import OAuthOIDCRecon
	from plugins.recon.spa_tester import SPATester
	from plugins.recon.openapi import OpenAPIRecon

__all__ = ["RobotsRecon", "SitemapRecon", "JSEndpointsRecon", "GraphQLRecon", "SmartEndpointDetector", "AuthDiscoveryRecon", "OAuthOIDCRecon", "SPATester", "OpenAPIRecon"]
