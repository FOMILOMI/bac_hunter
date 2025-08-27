from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

try:
	from ..config import Settings, Identity
	from ..http_client import HttpClient
except ImportError:
	from config import Settings, Identity
	from http_client import HttpClient


@dataclass
class TargetProfile:
	kind: str  # "web" | "api" | "spa" | "unknown"
	auth_hint: Optional[str] = None  # "basic" | "bearer" | "cookie" | None
	server: Optional[str] = None
	framework: Optional[str] = None


class TargetProfiler:
	"""Probe a target root and infer basic characteristics to adjust scanning."""

	def __init__(self, settings: Settings, http: HttpClient):
		self.s = settings
		self.http = http

	async def profile(self, base_url: str, identity: Identity | None = None) -> TargetProfile:
		identity = identity or self.s.identities[0]
		h = identity.headers()
		h["X-BH-Identity"] = identity.name
		kind = "unknown"
		auth_hint = None
		server = None
		framework = None
		try:
			resp = await self.http.get(base_url.rstrip('/'))
			ct = (resp.headers.get("content-type") or "").lower()
			server = resp.headers.get("server")
			if "application/json" in ct:
				kind = "api"
			elif "text/html" in ct:
				# Heuristic SPA: large html with many script tags or root returns app shell
				body = resp.text[:4000]
				if body.count("<script") >= 3 or "<app-" in body or "id=\"root\"" in body:
					kind = "spa"
				else:
					kind = "web"
			wa = resp.headers.get("www-authenticate", "").lower()
			if "basic" in wa:
				auth_hint = "basic"
			elif "bearer" in wa or "oauth" in wa:
				auth_hint = "bearer"
			# Cookie-based auth hint
			set_cookie = resp.headers.get("set-cookie", "").lower()
			if set_cookie and ("session" in set_cookie or "csrftoken" in set_cookie or "xsrf" in set_cookie):
				auth_hint = auth_hint or "cookie"
			# Framework hints
			powered = (resp.headers.get("x-powered-by") or "").lower()
			if "express" in powered:
				framework = "node-express"
			elif "laravel" in powered:
				framework = "laravel"
			elif "wordpress" in (resp.text[:2000] or "").lower():
				framework = "wordpress"
		except (AttributeError, OSError, ValueError) as e:
			# Log the error for debugging but don't fail the profiling
			pass
		return TargetProfile(kind=kind, auth_hint=auth_hint, server=server, framework=framework)