from __future__ import annotations
from typing import Dict, Any, Optional, List

from ..http_client import HttpClient
from ..config import Settings, Identity
from ..storage import Storage


class AuthAnalyzer:
	"""Detects basic auth flows and session behaviors; maps hierarchy heuristically.
	This is a non-intrusive stub focusing on cookie/bearer presence and status codes.
	"""

	def __init__(self, settings: Settings, http: HttpClient, db: Storage):
		self.s = settings
		self.http = http
		self.db = db

	async def analyze_auth_flow(self, base_url: str, unauth: Optional[Identity], auth: Optional[Identity]) -> Dict[str, Any]:
		start = base_url if base_url.endswith('/') else base_url + '/'
		result: Dict[str, Any] = {"login_hint": None, "session_token_hint": None, "role_map": {}, "oauth": {"well_known": None, "issuer": None}}
		# 1) Check if login link exists on homepage
		try:
			resp = await self.http.get(start)
			if resp.status_code == 200 and resp.text:
				if "login" in resp.text.lower() or "signin" in resp.text.lower():
					result["login_hint"] = "login-linked"
		except Exception:
			pass
		# 2) Session token hint and heuristic sniffing of Set-Cookie/JWT
		if auth and (auth.cookie or auth.auth_bearer):
			result["session_token_hint"] = "cookie" if auth.cookie else "bearer"
		else:
			try:
				home = await self.http.get(start)
				set_cookie_headers: List[str] = [v for k, v in home.headers.items() if k.lower() == "set-cookie"]
				cand = None
				for sc in set_cookie_headers:
					low = sc.lower()
					if any(t in low for t in ("session", "sid", "token", "jwt")):
						cand = "cookie"; break
				if not cand and ("authorization" in {k.lower() for k in home.headers.keys()}):
					cand = "bearer"
				if cand:
					result["session_token_hint"] = cand
			except Exception:
				pass
		# 3) Simple role effect: compare a few known paths
		candidates = ["/admin", "/dashboard", "/api/", "/settings"]
		role_map: Dict[str, Dict[str, int]] = {}
		for path in candidates:
			url = start.rstrip('/') + path
			st_un = None
			st_auth = None
			try:
				if unauth:
					ru = await self.http.get(url, headers=unauth.headers())
					st_un = ru.status_code
				if auth:
					ra = await self.http.get(url, headers=auth.headers())
					st_auth = ra.status_code
			except Exception:
				continue
			role_map[path] = {"unauth": st_un or 0, "auth": st_auth or 0}
		result["role_map"] = role_map
		# 4) Try well-known OpenID Connect configuration
		try:
			wk = await self.http.get(start.rstrip('/') + '/.well-known/openid-configuration')
			if wk.status_code == 200 and wk.headers.get('content-type','').lower().startswith('application/json'):
				j = wk.json()
				result["oauth"]["well_known"] = True
				result["oauth"]["issuer"] = j.get('issuer')
		except Exception:
			pass
		return result