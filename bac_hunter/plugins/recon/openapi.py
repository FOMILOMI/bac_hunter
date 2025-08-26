from __future__ import annotations
import logging
from typing import List, Set
from urllib.parse import urljoin

try:
	from ...storage import Storage
	from ...http_client import HttpClient
	from ...config import Settings
	from ..base import Plugin
except Exception:
	from storage import Storage
	from http_client import HttpClient
	from config import Settings
	from plugins.base import Plugin

log = logging.getLogger("recon.openapi")

COMMON_OPENAPI_PATHS = [
	"/openapi.json", "/swagger.json", "/v1/openapi.json", "/v2/openapi.json", "/api-docs", "/api/docs", "/swagger/v1/swagger.json"
]

class OpenAPIRecon(Plugin):
	name = "openapi"
	category = "recon"

	async def run(self, base_url: str, target_id: int) -> List[str]:
		found: List[str] = []
		for p in COMMON_OPENAPI_PATHS:
			u = urljoin(base_url, p)
			try:
				r = await self.http.get(u)
				if r.status_code != 200 or 'json' not in (r.headers.get('content-type','').lower()):
					continue
				# naive parse
				import json
				obj = json.loads(r.text)
				paths = obj.get('paths') or {}
				for rel in list(paths.keys())[:500]:
					full = urljoin(base_url, rel)
					found.append(full)
					# Slightly elevate score for documented endpoints
					self.db.add_finding(target_id, "endpoint", full, evidence="openapi", score=0.4)
			except Exception:
				continue
		log.info("%s -> %d endpoints", self.name, len(found))
		return list(dict.fromkeys(found))