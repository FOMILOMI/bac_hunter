from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Optional, Dict

try:
	from ..http_client import HttpClient
	from ..config import Settings, Identity
	from ..storage import Storage
except Exception:
	from http_client import HttpClient
	from config import Settings, Identity
	from storage import Storage


@dataclass
class SmartAuthIntel:
	login_urls: List[str]
	signup_urls: List[str]
	reset_urls: List[str]
	oauth_urls: List[str]
	saml_urls: List[str]
	admin_hints: List[str]
	api_key_hints: List[str]
	session_hint: Optional[str]
	extra: Dict[str, str]


class SmartAuthDetector:
	"""Augmented auth detector that layers advanced heuristics over light discovery.

	- Detects login/signup/reset forms and well-known OAuth/SAML endpoints
	- Hints for admin panels and API keys
	- Infers session mechanism from headers and content
	"""

	LOGIN_RE = re.compile(r"\b(login|signin|sign-in|/auth/|/account/login|/user/login)\b", re.IGNORECASE)
	SIGNUP_RE = re.compile(r"\b(register|signup|sign-up|create[-_ ]?account)\b", re.IGNORECASE)
	RESET_RE = re.compile(r"\b(reset|forgot[-_ ]?password|recover)\b", re.IGNORECASE)
	OAUTH_RE = re.compile(r"\b(oauth|openid|/.well-known/(?:oauth|openid))\b", re.IGNORECASE)
	SAML_RE = re.compile(r"\b(saml|/sso|/saml2|/saml/acs)\b", re.IGNORECASE)
	ADMIN_RE = re.compile(r"\b(admin|/admin|/administrator|/wp-admin|/manage|/dashboard)\b", re.IGNORECASE)
	APIKEY_RE = re.compile(r"(?i)(api[-_ ]?key|x-api-key|Authorization:\s*Api[- ]?Key|Bearer\s+[A-Za-z0-9-_\.]+)")

	WELL_KNOWN = [
		"/.well-known/openid-configuration",
		"/.well-known/oauth-authorization-server",
	]

	def __init__(self, settings: Settings, http: HttpClient, db: Storage):
		self.s = settings
		self.http = http
		self.db = db

	async def analyze(self, base_url: str, identity: Optional[Identity] = None) -> SmartAuthIntel:
		from urllib.parse import urljoin
		identity = identity or (self.s.identities[0] if self.s.identities else Identity(name="anon"))
		start = base_url if base_url.endswith('/') else base_url + '/'
		text = ""
		try:
			resp = await self.http.get(start, headers={"X-BH-Identity": identity.name, **identity.headers()})
			self.db.save_page(self.db.ensure_target(base_url), start, resp.status_code, resp.headers.get("content-type"), resp.content)
			text = resp.text or ""
		except Exception:
			text = ""

		# Collect from anchors and inline scripts
		links = re.findall(r"href=[\"']([^\"'#>\s]+)[\"']", text, flags=re.IGNORECASE)
		candidates = [urljoin(start, u) for u in links]
		# Also collect well-known endpoints
		candidates.extend(urljoin(start, p) for p in self.WELL_KNOWN)

		login_urls = sorted({u for u in candidates if self.LOGIN_RE.search(u)})
		signup_urls = sorted({u for u in candidates if self.SIGNUP_RE.search(u)})
		reset_urls = sorted({u for u in candidates if self.RESET_RE.search(u)})
		oauth_urls = sorted({u for u in candidates if self.OAUTH_RE.search(u)})
		saml_urls = sorted({u for u in candidates if self.SAML_RE.search(u)})
		admin_hints = sorted({u for u in candidates if self.ADMIN_RE.search(u)})

		# API key hints from text and inline JS
		api_key_hints = []
		for m in self.APIKEY_RE.finditer(text):
			val = m.group(0)
			if val and val not in api_key_hints:
				api_key_hints.append(val[:120])

		# Probe a subset of candidates to confirm availability
		confirmed: List[str] = []
		for u in list(dict.fromkeys(login_urls + signup_urls + reset_urls + oauth_urls + saml_urls + admin_hints))[:20]:
			try:
				r = await self.http.get(u, headers=identity.headers())
				self.db.save_page(self.db.ensure_target(base_url), u, r.status_code, r.headers.get("content-type"), r.content if (r.status_code < 400 and (r.headers.get("content-type", "").lower().startswith("text/"))) else b"")
				if r.status_code in (200, 302, 401, 403):
					confirmed.append(u)
			except Exception:
				pass

		# Session mechanism hint
		session_hint: Optional[str] = None
		try:
			set_cookie = (resp.headers.get("set-cookie") or "").lower()
			if any(t in set_cookie for t in ("session", "sid", "csrftoken", "xsrf", "jwt")):
				session_hint = "cookie"
			wa = (resp.headers.get("www-authenticate") or "").lower()
			if "bearer" in wa:
				session_hint = session_hint or "bearer"
		except Exception:
			pass

		return SmartAuthIntel(
			login_urls=login_urls,
			signup_urls=signup_urls,
			reset_urls=reset_urls,
			oauth_urls=oauth_urls,
			saml_urls=saml_urls,
			admin_hints=admin_hints,
			api_key_hints=api_key_hints,
			session_hint=session_hint,
			extra={"confirmed": str(len(confirmed))},
		)

