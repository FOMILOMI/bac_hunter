from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict

try:
	from ..config import Settings, Identity
	from ..http_client import HttpClient
except Exception:
	from config import Settings, Identity
	from http_client import HttpClient


@dataclass
class RichTargetProfile:
	kind: str
	auth_hint: Optional[str]
	server: Optional[str]
	framework: Optional[str]
	features: Dict[str, bool]


class IntelligentTargetProfiler:
	"""Augmented profiler that extracts richer context to guide tests."""

	def __init__(self, settings: Settings, http: HttpClient):
		self.s = settings
		self.http = http

	async def profile(self, base_url: str, identity: Optional[Identity] = None) -> RichTargetProfile:
		identity = identity or (self.s.identities[0] if self.s.identities else Identity(name="anon"))
		from urllib.parse import urljoin
		try:
			resp = await self.http.get(base_url.rstrip('/'), headers=identity.headers())
		except Exception:
			return RichTargetProfile(kind="unknown", auth_hint=None, server=None, framework=None, features={})
		ct = (resp.headers.get("content-type") or "").lower()
		kind = "api" if "application/json" in ct else ("web" if "text/html" in ct else "unknown")
		if kind == "web":
			body = resp.text or ""
			if body.count("<script") >= 3 or "id=\"root\"" in body:
				kind = "spa"
		wa = (resp.headers.get("www-authenticate") or "").lower()
		auth_hint = "basic" if "basic" in wa else ("bearer" if "bearer" in wa else None)
		set_cookie = (resp.headers.get("set-cookie") or "").lower()
		if not auth_hint and any(t in set_cookie for t in ("session", "csrftoken", "xsrf")):
			auth_hint = "cookie"
		server = resp.headers.get("server")
		framework = None
		powered = (resp.headers.get("x-powered-by") or "").lower()
		if "express" in powered:
			framework = "node-express"
		elif "laravel" in powered:
			framework = "laravel"
		elif "wordpress" in (resp.text[:2000] or "").lower():
			framework = "wordpress"
		features = {
			"cors": "access-control-allow-origin" in {k.lower(): v for k, v in resp.headers.items()},
			"hsts": "strict-transport-security" in {k.lower(): v for k, v in resp.headers.items()},
		}
		return RichTargetProfile(kind=kind, auth_hint=auth_hint, server=server, framework=framework, features=features)

