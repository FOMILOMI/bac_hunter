from __future__ import annotations
import logging
from typing import Optional, Tuple

try:
	from ..http_client import HttpClient
	from ..config import Settings, Identity
	from ..storage import Storage
	from .comparator import ResponseComparator, DiffResult
except Exception:
	from http_client import HttpClient
	from config import Settings, Identity
	from storage import Storage
	from access.comparator import ResponseComparator, DiffResult

log = logging.getLogger("access.diff")

class DifferentialTester:
    def __init__(self, settings: Settings, http: HttpClient, db: Storage, comparator: Optional[ResponseComparator] = None):
        self.s = settings
        self.http = http
        self.db = db
        self.cmp = comparator or ResponseComparator()

    async def fetch(self, url: str, ident: Identity) -> Tuple[int, int, Optional[str], Optional[bytes]]:
        r = await self.http.get(url, headers=ident.headers())
        body = r.content if (r.headers.get("content-type", "").lower().startswith("application/json") or len(r.content) <= 4096) else b""
        self.db.save_probe(url=url, identity=ident.name, status=r.status_code, length=len(r.content), content_type=r.headers.get("content-type"), body=body)
        return r.status_code, len(r.content), r.headers.get("content-type"), body

    async def compare_identities(self, url: str, a: Identity, b: Identity) -> DiffResult:
        a_stat, a_len, a_ct, a_body = await self.fetch(url, a)
        b_stat, b_len, b_ct, b_body = await self.fetch(url, b)
        diff = self.cmp.compare(a_stat, a_len, a_ct, a_body, b_stat, b_len, b_ct, b_body)
        self.db.save_comparison(url=url, id_a=a.name, id_b=b.name, same_status=diff.same_status, same_length_bucket=diff.same_length_bucket, json_keys_overlap=diff.json_keys_overlap, hint=diff.hint)
        if not diff.same_status or (not diff.same_length_bucket and diff.json_keys_overlap < 0.5):
            score = 0.6 if not diff.same_status else 0.4
            self.db.add_finding_for_url(url, type_="differential", evidence=diff.hint, score=score)
        return diff