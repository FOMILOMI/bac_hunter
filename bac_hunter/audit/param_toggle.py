from __future__ import annotations
import logging
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from typing import Dict, List

try:
	from ..config import Settings, Identity
	from ..http_client import HttpClient
	from ..storage import Storage
	from ..access.comparator import ResponseComparator
except ImportError:
	from config import Settings, Identity
	from http_client import HttpClient
	from storage import Storage
	from access.comparator import ResponseComparator

log = logging.getLogger("audit.toggle")

TOGGLE_KEYS = [
    "is_admin", "admin", "role", "can_view", "is_active", "enabled", "approved",
]

class ParamToggle:
    """Low-noise boolean/role toggles on GET query only (no POST/PUT). Compares body len buckets.
    Emits finding type: 'toggle_suspect'
    """

    def __init__(self, settings: Settings, http: HttpClient, db: Storage):
        self.s = settings
        self.http = http
        self.db = db
        self.cmp = ResponseComparator()

    def _toggle_query(self, url: str) -> List[str]:
        sp = urlsplit(url)
        q = dict(parse_qsl(sp.query, keep_blank_values=True))
        outs: List[str] = []
        for k in list(q.keys()):
            lk = k.lower()
            if lk in TOGGLE_KEYS:
                v = (q.get(k) or "").lower()
                nv = "false" if v in ("true", "1", "yes") else "true"
                q2 = q.copy(); q2[k] = nv
                outs.append(urlunsplit((sp.scheme, sp.netloc, sp.path, urlencode(q2, doseq=True), sp.fragment)))
        return outs[:2]  # cap per URL

    async def run(self, urls: List[str], ident: Identity):
        for u in urls:
            toggles = self._toggle_query(u)
            if not toggles:
                continue
            try:
                r0 = await self.http.get(u, headers=ident.headers())
            except (AttributeError, OSError, ValueError) as e:
                log.debug(f"Failed to fetch base URL {u}: {e}")
                continue
            for t in toggles:
                try:
                    r1 = await self.http.get(t, headers=ident.headers())
                except (AttributeError, OSError, ValueError) as e:
                    log.debug(f"Failed to fetch toggle URL {t}: {e}")
                    continue
                diff = self.cmp.compare(r0.status_code, len(r0.content), r0.headers.get("content-type"), None,
                                        r1.status_code, len(r1.content), r1.headers.get("content-type"), None)
                if r1.status_code in (200,206) and (not diff.same_status or not diff.same_length_bucket):
                    self.db.add_finding_for_url(t, type_="toggle_suspect", evidence=f"query toggle changed response ({diff.hint})", score=0.6)