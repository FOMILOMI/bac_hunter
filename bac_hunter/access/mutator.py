from __future__ import annotations
import logging
from typing import Dict, List, Tuple
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

try:
	from ..config import Identity, Settings
	from ..http_client import HttpClient
	from ..storage import Storage
	from .comparator import ResponseComparator
except Exception:
	from config import Identity, Settings
	from http_client import HttpClient
	from storage import Storage
	from access.comparator import ResponseComparator

log = logging.getLogger("access.mutator")


class RequestMutator:
    """Generates and tests safe request mutations.
    - GET query boolean flips and parameter swaps
    - GET->POST with form body mirroring query (optional)
    """

    def __init__(self, settings: Settings, http: HttpClient, db: Storage):
        self.s = settings
        self.http = http
        self.db = db
        self.cmp = ResponseComparator()

    def _boolean_flips(self, url: str) -> List[str]:
        sp = urlsplit(url)
        params = parse_qsl(sp.query, keep_blank_values=True)
        outs: List[str] = []
        for i, (k, v) in enumerate(params):
            lv = (v or "").lower()
            if lv in ("true", "false", "1", "0", "yes", "no"):
                new = params.copy()
                new[i] = (k, "false" if lv in ("true", "1", "yes") else "true")
                outs.append(urlunsplit((sp.scheme, sp.netloc, sp.path, urlencode(new, doseq=True), sp.fragment)))
        return outs[:2]

    def _swap_two_params(self, url: str) -> List[str]:
        sp = urlsplit(url)
        params = parse_qsl(sp.query, keep_blank_values=True)
        if len(params) < 2:
            return []
        new = params[:]
        new[0], new[1] = new[1], new[0]
        return [urlunsplit((sp.scheme, sp.netloc, sp.path, urlencode(new, doseq=True), sp.fragment))]

    async def run_get_mutations(self, url: str, ident: Identity):
        try:
            base = await self.http.get(url, headers=ident.headers())
        except Exception:
            return
        variants = []
        variants += self._boolean_flips(url)
        variants += self._swap_two_params(url)
        for v in variants[:3]:
            try:
                r = await self.http.get(v, headers=ident.headers())
            except Exception:
                continue
            diff = self.cmp.compare(base.status_code, len(base.content), base.headers.get("content-type"), None,
                                    r.status_code, len(r.content), r.headers.get("content-type"), None)
            if r.status_code in (200, 206) and (not diff.same_status or not diff.same_length_bucket):
                self.db.add_finding_for_url(v, type_="mutation_suspect", evidence=f"get-mutation {diff.hint}", score=0.55)

    async def run_get_to_post(self, url: str, ident: Identity):
        sp = urlsplit(url)
        if not sp.query:
            return
        form = dict(parse_qsl(sp.query, keep_blank_values=True))
        try:
            a = await self.http.get(url, headers=ident.headers())
            b = await self.http.post(urlunsplit((sp.scheme, sp.netloc, sp.path, "", sp.fragment)), data=form, headers=ident.headers())
        except Exception:
            return
        diff = self.cmp.compare(a.status_code, len(a.content), a.headers.get("content-type"), None,
                                b.status_code, len(b.content), b.headers.get("content-type"), None)
        if b.status_code in (200, 201, 202, 206) and (not diff.same_status or not diff.same_length_bucket):
            self.db.add_finding_for_url(url, type_="get_to_post", evidence=f"shape/status changed ({diff.hint})", score=0.5)

