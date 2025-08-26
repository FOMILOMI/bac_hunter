from __future__ import annotations
import re
import hashlib
from typing import Dict, Optional, Tuple

try:
	import httpx  # type: ignore
except Exception:
	httpx = None  # type: ignore

# Lightweight HTML text extraction (no external deps)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_JSON_DENY_KEYS = ("error", "message", "code", "status")

class AccessOracle:
	"""Domain-scoped allow/deny oracle using coarse signatures.
	- Maintains login/denial signatures and success templates to avoid FP from random 404s or soft-login pages.
	- Pure in-memory; callers can optionally persist via Storage.learning().
	"""
	
	def __init__(self):
		self._deny_sigs: Dict[str, str] = {}
		self._allow_sigs: Dict[str, str] = {}
		self._json_deny_templates: Dict[str, str] = {}
		# Cache stability per URL: last two status codes and a flip counter
		self._instability: Dict[str, Tuple[int, int, int]] = {}
	
	def _domain_of(self, url: str) -> str:
		try:
			from urllib.parse import urlparse
			return urlparse(url).netloc
		except Exception:
			return ""
	
	def _text_fingerprint(self, text: str) -> str:
		# Strip tags, collapse whitespace, hash
		t = _HTML_TAG_RE.sub(" ", text)
		t = _WS_RE.sub(" ", t).strip().lower()
		return hashlib.sha1(t.encode(errors="ignore")).hexdigest()[:16]
	
	def _is_login_like_text(self, text: str) -> bool:
		lt = text.lower()
		return any(x in lt for x in ("login", "sign in", "signin", "password", "two-factor", "mfa"))
	
	def _json_fingerprint(self, body: bytes) -> str:
		try:
			import json
			obj = json.loads(body.decode(errors="ignore"))
			# Collect a template of top-level keys that indicate denial
			keys = sorted([k for k in obj.keys() if isinstance(k, str)]) if isinstance(obj, dict) else []
			hint = "|".join(keys)
			return hashlib.md5(hint.encode()).hexdigest()[:16]
		except Exception:
			return ""
	
	def observe_response(self, url: str, response) -> None:
		"""Feed responses to train denial/allow signatures and update stability tracking."""
		try:
			status = int(getattr(response, "status_code", 0) or 0)
		except Exception:
			status = 0
		domain = self._domain_of(url)
		ct = (getattr(response, "headers", {}) or {}).get("content-type", "").lower()
		text = ""
		try:
			if hasattr(response, "text") and isinstance(response.text, str):
				text = response.text[:8000]
		except Exception:
			pass
		if status in (401, 403):
			if text:
				self._deny_sigs[domain] = self._text_fingerprint(text)
			return
		# 302/307 redirects to login-like pages are also denial signatures
		try:
			if status in (302, 307):
				loc = (response.headers.get("Location") or response.headers.get("location") or "").lower()
				if any(x in loc for x in ("login", "signin", "auth", "session")):
					self._deny_sigs[domain] = hashlib.sha1(loc.encode()).hexdigest()[:16]
		except Exception:
			pass
		# Successful pages (2xx) that look like owned resource can be an allow signature (only if not login-like)
		if 200 <= status < 300 and text and not self._is_login_like_text(text):
			self._allow_sigs[domain] = self._text_fingerprint(text)
			# JSON denial template capture
			if "json" in ct:
				fp = self._json_fingerprint(getattr(response, "content", b""))
				if fp:
					self._json_deny_templates[domain] = fp
		# Stability tracking
		key = f"{url}"
		prev = self._instability.get(key, (status, status, 0))
		last1, last2, flips = prev
		new_flips = flips + (1 if status != last1 else 0)
		self._instability[key] = (status, last1, new_flips)
	
	def is_unstable(self, url: str, threshold: int = 2) -> bool:
		st = self._instability.get(url)
		return bool(st and st[2] >= threshold)
	
	def is_denial(self, url: str, response) -> bool:
		"""Return True when response matches recorded denial signatures for the domain."""
		try:
			status = int(getattr(response, "status_code", 0) or 0)
		except Exception:
			status = 0
		if status in (401, 403):
			return True
		domain = self._domain_of(url)
		ct = (getattr(response, "headers", {}) or {}).get("content-type", "").lower()
		text = ""
		try:
			text = response.text[:8000]
		except Exception:
			pass
		if status in (302, 307):
			try:
				loc = (response.headers.get("Location") or response.headers.get("location") or "").lower()
				if any(x in loc for x in ("login", "signin", "auth", "session")):
					return True
			except Exception:
				pass
		if text and domain in self._deny_sigs:
			return self._text_fingerprint(text) == self._deny_sigs[domain]
		if "json" in ct and hasattr(response, "content") and domain in self._json_deny_templates:
			return self._json_fingerprint(response.content) == self._json_deny_templates[domain]
		return False
	
	def is_allowed(self, url: str, response) -> bool:
		try:
			status = int(getattr(response, "status_code", 0) or 0)
		except Exception:
			status = 0
		if 200 <= status < 300:
			# Avoid login-like 200s
			text = ""
			try:
				text = response.text[:8000]
			except Exception:
				pass
			if text and self._is_login_like_text(text):
				return False
			return True
		return False
	
	def classify(self, url: str, response) -> str:
		if self.is_denial(url, response):
			return "deny"
		if self.is_allowed(url, response):
			return "allow"
		return "unknown"