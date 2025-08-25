from __future__ import annotations
import asyncio
from typing import List
from urllib.parse import urljoin

try:
	from ..config import Settings, Identity
	from ..http_client import HttpClient
	from ..storage import Storage
except Exception:
	from config import Settings, Identity
	from http_client import HttpClient
	from storage import Storage


class PathScanner:
    """Lightweight fallback directory/path scanner when external tools are missing.

    - Tries a compact, curated list of sensitive paths
    - Respects global/per-host RPS from Settings via HttpClient
    - Stores interesting responses (200/206/401/403) as findings
    """

    DEFAULT_WORDLIST: List[str] = [
        "admin/",
        "admin",
        "login",
        "dashboard",
        "user",
        "users",
        "api/",
        "api/v1/",
        "graphql",
        ".env",
        ".git/HEAD",
        "server-status",
        "wp-admin/",
        "wp-login.php",
        "config",
        "settings",
        "internal",
        "private",
        "debug",
    ]

    def __init__(self, settings: Settings, http: HttpClient, db: Storage, paths: List[str] | None = None):
        self.s = settings
        self.http = http
        db.ensure_target  # type: ignore[func-returns-value]
        self.db = db
        self.paths = paths or list(dict.fromkeys(self.DEFAULT_WORDLIST))

    async def run(self, base_url: str, identity: Identity | None = None) -> List[str]:
        identity = identity or self.s.identities[0]
        found: List[str] = []

        async def probe(path: str):
            url = urljoin(base_url.rstrip('/') + '/', path)
            h = identity.headers()
            h["X-BH-Identity"] = identity.name
            try:
                resp = await self.http.get(url, headers=h)
                if resp.status_code in (200, 206, 401, 403):
                    self.db.add_finding_for_url(url, "endpoint", f"status={resp.status_code}", 0.15)
                    found.append(url)
            except Exception:
                pass

        await asyncio.gather(*(probe(p) for p in self.paths[:100]))
        return found