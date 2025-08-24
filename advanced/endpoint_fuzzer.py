from __future__ import annotations
import logging
from typing import Iterable, List
from urllib.parse import urlsplit, urlunsplit

from ..config import Settings, Identity
from ..http_client import HttpClient
from ..storage import Storage

log = logging.getLogger("advanced.fuzzer")


class EndpointFuzzer:
	"""Safe, low-noise endpoint fuzzer that appends small path candidates.
	- Only performs GET requests
	- Records pages and potential endpoints
	"""

	CANDIDATES = [
		"admin", "login", "logout", "dashboard", "settings",
		"api", "api/v1", "api/v2", "health", "status",
	]

	def __init__(self, settings: Settings, http: HttpClient, db: Storage):
		self.settings = settings
		self.http = http
		self.db = db

	def _variants(self, base_url: str) -> List[str]:
		sp = urlsplit(base_url)
		base = urlunsplit((sp.scheme, sp.netloc, sp.path.rstrip('/'), '', ''))
		out: List[str] = []
		for p in self.CANDIDATES:
			out.append(base + '/' + p)
		return out

	async def run(self, base_url: str, target_id: int, ident: Identity | None = None, max_candidates: int = 20) -> List[str]:
		ident = ident or Identity(name="anon")
		found: List[str] = []
		for u in self._variants(base_url)[:max_candidates]:
			try:
				r = await self.http.get(u, headers=ident.headers())
				self.db.save_page(target_id, u, r.status_code, r.headers.get("content-type"), r.content)
				if r.status_code in (200, 206) and r.content:
					self.db.add_finding(target_id, "endpoint", u, evidence="fuzzer", score=0.25)
					found.append(u)
			except Exception:
				continue
		log.info("fuzzer found %d endpoints", len(found))
		return found