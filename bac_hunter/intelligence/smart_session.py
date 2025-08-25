from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional

try:
	from ..config import Identity, Settings
	from ..http_client import HttpClient
except Exception:
	from config import Identity, Settings
	from http_client import HttpClient


@dataclass
class SessionState:
	identity: Identity
	active: bool
	last_token: Optional[str] = None


class SmartSessionManager:
	"""Maintain multiple sessions, refresh tokens, and tag requests by identity."""

	def __init__(self, settings: Settings, http: HttpClient):
		self.s = settings
		self.http = http
		self._sessions: Dict[str, SessionState] = {}

	def register(self, identity: Identity) -> None:
		self._sessions[identity.name] = SessionState(identity=identity, active=True, last_token=identity.auth_bearer)

	def get(self, name: str) -> Optional[Identity]:
		st = self._sessions.get(name)
		return st.identity if st else None

	def all(self):
		return [s.identity for s in self._sessions.values()]

	async def refresh_if_needed(self, name: str) -> Identity:
		# Gracefully handle unknown names by creating a lightweight identity
		st = self._sessions.get(name)
		if st is None:
			anon = Identity(name=name or "anon")
			self._sessions[name] = SessionState(identity=anon, active=True, last_token=anon.auth_bearer)
			st = self._sessions[name]
		# Placeholder: attempt refresh if bearer exists and a refresh endpoint is common.
		if st.identity.auth_bearer and st.active:
			for path in ("/auth/refresh", "/api/token/refresh", "/session/refresh"):
				try:
					url = self._guess_base(st.identity) + path
					r = await self.http.post(url, headers=st.identity.headers())
					if r.status_code in (200, 204):
						try:
							js = r.json()
							new_token = js.get("token") or js.get("access_token")
							if new_token:
								st.identity.auth_bearer = new_token
								st.last_token = new_token
								break
						except Exception:
							pass
				except Exception:
					continue
		return st.identity

	def _guess_base(self, identity: Identity) -> str:
		# Without binding to a specific target, fallback to placeholder; callers should use absolute URLs.
		return ""