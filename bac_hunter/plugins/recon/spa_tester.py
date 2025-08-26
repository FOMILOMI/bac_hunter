from __future__ import annotations
import logging
from typing import List

from ..base import Plugin

log = logging.getLogger("recon.spa")

SPA_HEADERS = {
	"X-Requested-With": "XMLHttpRequest",
	"Accept": "application/json, text/plain, */*",
}

class SPATester(Plugin):
	name = "spa_tester"
	category = "recon"

	async def run(self, base_url: str, target_id: int) -> List[str]:
		urls: List[str] = []
		try:
			with self.db.conn() as c:
				for (u,) in c.execute("SELECT url FROM findings WHERE target_id=? AND type='endpoint'", (target_id,)):
					urls.append(u)
		except Exception:
			pass
		seen = set(); urls = [u for u in urls if not (u in seen or seen.add(u))]
		for u in urls[:50]:
			try:
				r = await self.http.get(u, headers=SPA_HEADERS, context="spa:test")
				if r.status_code in (200, 206) and 'json' in (r.headers.get('content-type','').lower()):
					self.db.add_finding(target_id, 'spa_behavior', u, 'json-with-xhr', 0.3)
			except Exception:
				continue
		return []