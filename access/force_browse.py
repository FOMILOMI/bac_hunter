from __future__ import annotations
import logging
from typing import Iterable

try:
	from ..config import Identity, Settings
	from ..http_client import HttpClient
	from ..storage import Storage
except Exception:
	from config import Identity, Settings
	from http_client import HttpClient
	from storage import Storage

log = logging.getLogger("access.fb")

SUSPECT_CODES = {200, 206, 302, 401, 403}

class ForceBrowser:
    def __init__(self, settings: Settings, http: HttpClient, db: Storage):
        self.s = settings
        self.http = http
        self.db = db

    async def try_paths(self, paths: Iterable[str], unauth: Identity, auth: Identity):
        for u in paths:
            r0 = await self.http.get(u, headers=unauth.headers())
            self.db.save_probe(url=u, identity=unauth.name, status=r0.status_code, length=len(r0.content), content_type=r0.headers.get("content-type"), body=b"")
            r1 = await self.http.get(u, headers=auth.headers())
            self.db.save_probe(url=u, identity=auth.name, status=r1.status_code, length=len(r1.content), content_type=r1.headers.get("content-type"), body=b"")
            if (r0.status_code in SUSPECT_CODES or r1.status_code in SUSPECT_CODES) and r1.status_code != 404:
                evidence = f"unauth={r0.status_code} auth={r1.status_code}"
                score = 0.5 if r0.status_code == 200 else 0.35
                self.db.add_finding_for_url(u, type_="force_browse", evidence=evidence, score=score)