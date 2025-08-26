from __future__ import annotations
import logging
from typing import List
from urllib.parse import urljoin

from ..base import Plugin

log = logging.getLogger("recon.oauth")

WELL_KNOWN = [
	"/.well-known/openid-configuration",
	"/.well-known/oauth-authorization-server",
]

class OAuthOIDCRecon(Plugin):
	name = "oauth_oidc"
	category = "recon"

	async def run(self, base_url: str, target_id: int) -> List[str]:
		found: List[str] = []
		for path in WELL_KNOWN:
			u = urljoin(base_url.rstrip('/') + '/', path.lstrip('/'))
			try:
				r = await self.http.get(u)
			except Exception:
				continue
			if r.status_code == 200 and 'application/json' in (r.headers.get('content-type','').lower()):
				self.db.add_finding(target_id, 'oauth_well_known', u, 'ok', 0.5)
				found.append(u)
		return found