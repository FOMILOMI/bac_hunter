from __future__ import annotations
import asyncio
import random
from dataclasses import dataclass
from typing import List, Optional, Dict

try:
	from ..config import Identity, Settings
	from ..http_client import HttpClient
	from ..storage import Storage
except Exception:
	from config import Identity, Settings
	from http_client import HttpClient
	from storage import Storage


@dataclass
class GeneratedAccount:
	identity: Identity
	email: str
	password: str
	role: str
	verified: bool = False


class DisposableEmailProvider:
	"""Thin abstraction to plug disposable email services.

	This is a stub that simulates a disposable email inbox and OTP retrieval.
	In a real integration, implement an async client to a provider (e.g., temp-mail).
	"""

	async def create_inbox(self) -> Dict[str, str]:
		local = f"tester{random.randint(1000, 999999)}"
		domain = "example.test"
		return {"address": f"{local}@{domain}", "id": local}

	async def fetch_latest_otp(self, inbox_id: str) -> Optional[str]:
		# Simulate not found
		await asyncio.sleep(0.1)
		return None


class CaptchaSolver:
	"""Pluggable CAPTCHA solver stub. Returns None by default."""

	async def solve(self, html: str) -> Optional[str]:
		await asyncio.sleep(0.05)
		return None


class IntelligentIdentityFactory:
	"""Zero-config identity creation and registration flow helper."""

	def __init__(self, settings: Settings, http: HttpClient, db: Storage):
		self.s = settings
		self.http = http
		self.db = db
		self.mail = DisposableEmailProvider()
		self.captcha = CaptchaSolver()

	async def generate(self, base_url: str, role: str = "user") -> GeneratedAccount:
		from urllib.parse import urljoin
		inbox = await self.mail.create_inbox()
		email = inbox["address"]
		password = f"Bh!{random.randint(100000, 999999)}aA"
		name = f"auto-{role}-{random.randint(10,9999)}"
		identity = Identity(name=name)
		# Best effort registration by probing common paths
		register_paths = [
			"/register", 
			"/signup",
			"/users/register",
			"/account/create",
		]
		start = base_url if base_url.endswith('/') else base_url + '/'
		verified = False
		for path in register_paths:
			reg_url = urljoin(start, path)
			try:
				# Attempt a generic JSON registration (common modern stacks)
				r = await self.http.post(reg_url, json={"email": email, "password": password, "name": name}, headers=identity.headers())
				if r.status_code in (200, 201, 202, 302):
					self.db.add_finding_for_url(reg_url, "identity_registered", f"{email}", 0.4)
					verified = True
					break
			except Exception:
				continue
		return GeneratedAccount(identity=identity, email=email, password=password, role=role, verified=verified)

	async def login(self, base_url: str, account: GeneratedAccount) -> Identity:
		from urllib.parse import urljoin
		# Attempt a simple login on common endpoints
		login_paths = ["/login", "/session", "/api/login", "/auth/login", "/users/sign_in"]
		start = base_url if base_url.endswith('/') else base_url + '/'
		cookie_header: Optional[str] = None
		bearer: Optional[str] = None
		for path in login_paths:
			url = urljoin(start, path)
			try:
				r = await self.http.post(url, json={"email": account.email, "password": account.password}, headers=account.identity.headers())
				# Extract cookie
				set_cookie = r.headers.get("set-cookie", "")
				if set_cookie:
					cookie_header = set_cookie.split(";", 1)[0]
				# Extract bearer from JSON {token: ...}
				try:
					js = r.json()
					bearer = js.get("token") or js.get("access_token") or bearer
				except Exception:
					pass
				if r.status_code in (200, 201, 204, 302):
					break
			except Exception:
				continue
		return Identity(name=account.identity.name, base_headers=account.identity.base_headers, cookie=cookie_header, auth_bearer=bearer)

